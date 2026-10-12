#!/usr/bin/env python3
"""Offline-only existing WH3 one-shot log diagnosis. Never attaches to game."""
import argparse
from collections import Counter
import json
from pathlib import Path

def diagnose(path):
    counters=Counter();source=Counter();meta=Counter();errors=[]
    for line_no,line in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(),1):
        if not line.strip():continue
        try:item=json.loads(line)
        except ValueError as ex:
            errors.append('INVALID_LINE_'+str(line_no));continue
        if not isinstance(item,dict):continue
        counters[item.get('ev') or item.get('type','unknown')]+=1
        if item.get('ev')=='B_DEFERRED_RECEIVE':
            s=item.get('source') or {}
            source['receives']+=1
            source['matched_B_fanout']+=int(s.get('memberFanoutMatched') is True)
            source['matched_queued_identity']+=int(s.get('queuedUnitIdentityMatches') is True)
        if item.get('type')=='probe_error':errors.append('PROBE_ERROR_'+str(line_no))
        if item.get('ev')=='SUMMARY':
            meta['droppedEvents']=item.get('droppedEvents',0)
    if errors:reason='INCOMPLETE_OR_PROBE_ERROR'
    elif counters['B_MEMBER_FANOUT']==0 and not source['receives']:
        reason='NO_B_FANOUT_OR_RECEIVE_CAPTURED'
    elif counters['B_MEMBER_FANOUT']>0 and not source['receives']:
        reason='B_FANOUT_BUT_NO_DEFERRED_RECEIVE'
    elif source['receives']>0 and source['matched_B_fanout']==0:
        reason='RECEIVE_PRESENT_BUT_NO_PACKET_IDENTITY_MATCH'
    else:reason='B_MATCHED_OR_OTHER'
    return dict(reason=reason,event_counts=dict(counters),source_matching=dict(source),
                meta=dict(meta),errors=errors[:10],game_fix_proven=False,
                interpretation='Absence of an event in capture does not prove the native branch never ran.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    result=diagnose(a.input);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(result['reason'])
if __name__=='__main__':main()
