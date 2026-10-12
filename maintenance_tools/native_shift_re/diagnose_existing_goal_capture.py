#!/usr/bin/env python3
"""Offline-only diagnosis for actual BSC one-shot JSONL; no game attachment.

A hook called B_DEFERRED_RECEIVE is a receiver branch, NOT confirmation that
the packet came from the separately identified cached B-route constructor.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import median

def diagnose(path):
    counters=Counter()
    source=Counter()
    flags=Counter();qword44=Counter();post_ctor_rewrite_fingerprint=0
    members=Counter()
    errors=[]
    received={}
    first_posts={}
    first_pres={}
    reads=[]
    all_pres=[]
    summary=None
    lines=0
    for line_no,line in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(),1):
        if not line.strip():continue
        lines+=1
        try:item=json.loads(line)
        except ValueError:
            errors.append('INVALID_LINE_'+str(line_no))
            continue
        if not isinstance(item,dict):continue
        event=item.get('ev')
        counters[event or item.get('type','unknown')]+=1
        if item.get('type')=='probe_error':errors.append('PROBE_ERROR_'+str(line_no))
        if event=='SUMMARY':summary=item
        if event=='B_DEFERRED_RECEIVE':
            # This is a mode-gated receiver hook, not a B source identity hook.
            s=item.get('source') or {}
            source['mode_gated_deferred_receives']+=1
            source['matched_B_fanout']+=int(s.get('memberFanoutMatched') is True)
            source['matched_queued_identity']+=int(s.get('queuedUnitIdentityMatches') is True)
            members[item.get('member')]+=1
            received[item.get('traceId')]=item
            try:
                raw=bytes.fromhex(item['packet58'])
                flags[raw[0x50]]+=1
                qword44[int.from_bytes(raw[0x44:0x4c], 'little')]+=1
                # Proven separate native sender 0x03284B55..0x03284B7B
                # starts with ctor flag06 and rewrites +0x50 to 02 and +0x44 to zero.
                if (len(raw)==0x58 and raw[0x50]==2 and
                    int.from_bytes(raw[0x44:0x4c],'little')==0 and
                    (raw[0x51]&1)==0 and
                    int.from_bytes(raw[0x38:0x3c],'little')==1 and
                    raw[0x3c:0x40]==bytes.fromhex('00004040')):
                    post_ctor_rewrite_fingerprint+=1
            except (ValueError,KeyError,IndexError,TypeError):
                errors.append('INVALID_PACKET_BYTES_'+str(line_no))
        if event=='GOAL_READ':reads.append(item)
        if event=='GOAL_COMMIT_PRE':
            all_pres.append(item)
            first_pres.setdefault(item.get('traceId'),item)
        if event=='GOAL_COMMIT_POST':
            first_posts.setdefault(item.get('traceId'),item)
    # Original EXE RVA 0x02F5F940 == 80 c9 06 (OR CL, 0x06).
    # A packet immediately produced by that builder must have both bit1
    # and bit2 set; this alone is NOT a positive identity classifier.
    incompatible=sum(v for f,v in flags.items() if f & 0x06 != 0x06)
    incompatible_qword44=sum(v for k,v in qword44.items() if k!=3)
    first_latencies=[]
    changed=0
    for ident,recv in received.items():
        post=first_posts.get(ident)
        pre=first_pres.get(ident)
        if post:
            first_latencies.append(post['atMs']-recv['atMs'])
        if pre and pre.get('proposed24')!=pre.get('before24'):
            changed+=1
    old_reads=sum(bool(x.get('goalUnchangedSinceReceive'))
                  and x.get('writeSeenSinceReceive') is False for x in reads)
    if errors:reason='INCOMPLETE_OR_PROBE_ERROR'
    elif counters['B_MEMBER_FANOUT']==0 and not received:reason='NO_B_FANOUT_OR_RECEIVE_CAPTURED'
    elif received and post_ctor_rewrite_fingerprint==len(received) and source['matched_B_fanout']==0:
        reason='POST_CTOR_REWRITE_COMPATIBLE_CALLER_UNVERIFIED'
    elif incompatible==len(received) and incompatible_qword44==len(received) and received and source['matched_B_fanout']==0:
        reason='NOT_UNMODIFIED_CTOR_CALLER_UNVERIFIED'
    elif counters['B_MEMBER_FANOUT']>0 and not received:reason='B_FANOUT_BUT_NO_DEFERRED_RECEIVE'
    elif received and source['matched_B_fanout']==0:reason='RECEIVE_PRESENT_BUT_NO_PACKET_IDENTITY_MATCH'
    else:reason='B_MATCHED_OR_OTHER'
    return {
      'reason':reason,'input_record_count':lines,
      'event_counts':dict(counters),'source_matching':dict(source),
      'packet_flag50_counts':{hex(k):v for k,v in sorted(flags.items())},
      'packet_qword44_counts':{hex(k):v for k,v in sorted(qword44.items())},
      'packet_count_incompatible_with_B_ctor_qword44':incompatible_qword44,
      'known_B_constructor_RVA':'0x02F5F940',
      'known_B_constructor_opcode':'80c906',
      'packet_count_incompatible_with_known_B_constructor':incompatible,
      'packet_count_matching_proven_post_ctor_rewrite_fingerprint':post_ctor_rewrite_fingerprint,
      'post_ctor_rewrite_native_site':'0x03284B55 through 0x03284B7B',
      'post_ctor_rewrite_caller_executed_in_trace':None,
      'distinct_sampled_members':len(members),
      'receives_per_member':dict(members),
      'first_actual_goal_writes':len(first_posts),
      'first_writes_changing_prior_goal':changed,
      'first_write_delay_ms':{
        'minimum':min(first_latencies) if first_latencies else None,
        'median':median(first_latencies) if first_latencies else None,
        'maximum':max(first_latencies) if first_latencies else None},
      'goal_writes_idempotent':sum(x.get('before24')==x.get('proposed24') for x in all_pres),
      'read_old_goal_before_first_write':old_reads,
      'capture_summary':summary,'errors':errors[:10],
      'B_route_execution_confirmed':False,'queued_Shift_execution_confirmed':False,
      'game_fix_proven':False,
      'interpretation':(
       'A mode-gated deferred receiver hook does NOT identify its packet producer. '
       '0x02F5F8DC sets 0x06 and +0x44=3, but another original sender '
       '0x03284B55..0x03284B7B explicitly clears bit 0x04 and +0x44 '
       'BEFORE member virtual+0x368 dispatch. Thus 0x02/+0x44=0 '
       'cannot exclude this native constructor family. '
       'The 28/28 field fingerprint is source-compatible, not an actual '
       'sender return-IP or queued Shift instance match.'
      )
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    result=diagnose(a.input)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(result['reason'])
if __name__=='__main__':main()
