#!/usr/bin/env python3
"""Offline conservative analysis of one short WH3 source/goal provenance trace.

A source-matched packet is NOT evidence of queued Shift nor of physical
crowding, and a missing hook is not evidence that a command never occurred.
"""
import argparse
from collections import Counter, defaultdict
import json
import math
import itertools
import struct
from pathlib import Path

SOURCE_RET = {'0x3284b81': 'POSTCTOR_REWRITE',
              '0x3265d45': 'B_CACHE',
              '0x30d5515': 'A_DIRECT'}


def goal_xz(raw):
    if not isinstance(raw,str):return None
    try:
        b=bytes.fromhex(raw)
        if len(b)<12:return None
        x,z=struct.unpack_from('<f',b,0)[0],struct.unpack_from('<f',b,8)[0]
        return (x,z) if math.isfinite(x) and math.isfinite(z) else None
    except (ValueError,struct.error):return None


def post_turn_motion(events):
    """Observed signed actor displacement, NOT native physical integrator proof."""
    turn_events=[x for x in events if x.get('ev')=='MOTOR_GOAL_REVERSAL'
                 and x.get('member') and x.get('group') and
                 isinstance(x.get('groupTick'),int)]
    group_windows=defaultdict(dict)
    for e in turn_events:
        grp,tick,member=e['group'],e['groupTick'],e['member']
        pos=e.get('x'),e.get('z')
        old=goal_xz(e.get('oldGoal24'))
        if old is None or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in pos):continue
        dx,dz=old[0]-pos[0],old[1]-pos[1]
        magnitude=math.hypot(dx,dz)
        if magnitude<0.01:continue
        group_windows[(grp,tick)][member]={'old_axis':(dx/magnitude,dz/magnitude),
            'samples':{},'cosine':e.get('headingCosine')}
    position_events=[x for x in events if x.get('ev')=='GROUP_TICK_POSITION'
                     and isinstance(x.get('turnStartTick'),int)]
    for e in position_events:
        pair=(e.get('group'),e.get('turnStartTick'))
        if pair not in group_windows:continue
        tick=e.get('groupTick')
        pos=(e.get('x'),e.get('z'))
        if not isinstance(tick,int) or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in pos):continue
        member=e.get('member')
        obj=group_windows[pair].get(member)
        if obj is None:continue
        obj['samples'].setdefault(tick,pos)
    result=[]
    for (grp,start),members in group_windows.items():
        stats=[]
        for member,datum in members.items():
            steps=sorted(datum['samples'].items())
            axis=datum['old_axis']
            dot_progress=[(tick2, (pos2[0]-pos1[0])*axis[0]+(pos2[1]-pos1[1])*axis[1])
                  for (tick1,pos1),(tick2,pos2) in zip(steps,steps[1:])
                  if tick2>tick1]
            positive=[tick for tick,v in dot_progress if v>0.002]
            negative=[tick for tick,v in dot_progress if v< -0.002]
            stats.append({'sampled_tick_count':len(steps),
             'old_heading_forward_intervals':len(positive),
             'old_heading_reverse_intervals':len(negative),
             'first_reverse_tick':min(negative) if negative else None,
             'first_sample_tick':steps[0][0] if steps else None,
             'last_sample_tick':steps[-1][0] if steps else None})
        result.append({'group':'<private-group-identity-suppressed>',
          'turn_start_tick':start,'reversal_members_observed':len(members),
          'members_with_2plus_group_tick_positions':sum(z['sampled_tick_count']>=2 for z in stats),
          'old_heading_forward_intervals':sum(z['old_heading_forward_intervals'] for z in stats),
          'old_heading_reverse_intervals':sum(z['old_heading_reverse_intervals'] for z in stats),
          'earliest_sampled_reverse_tick':min((z['first_reverse_tick'] for z in stats if z['first_reverse_tick'] is not None), default=None),
          'per_member_summary':stats[:24]})
    return result



CORE_SOURCE_KINDS = ('NATIVE_MEMBER_SEND','MEMBER_RECEIVER','DEFERRED_PACKET',
                     'GOAL_WRITE_PRE','GOAL_WRITE_POST','QUEUED_CONTINUATION',
                     'NATIVE_MOVE_ISSUER','GOAL_READ','NATIVE_GOAL_DIRECTION')

def closest_member_separations(events):
    """Within-group sample-member *center* distance; not a collision test."""
    windows=defaultdict(lambda:defaultdict(dict))
    for e in events:
        if e.get('ev')!='GROUP_TICK_POSITION':continue
        group,start,tick,member=(e.get('group'),e.get('turnStartTick'),
                                e.get('groupTick'),e.get('member'))
        x,z=e.get('x'),e.get('z')
        if not group or not isinstance(start,int) or not isinstance(tick,int) or not member:continue
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (x,z)):continue
        windows[(group,start)][tick][member]=(x,z)
    result=[]
    for (_,start),ticks in sorted(windows.items(),key=lambda z:z[0][1]):
        all_pairs=[]
        for tick,persons in ticks.items():
            for (a,pa),(b,pb) in itertools.combinations(persons.items(),2):
                all_pairs.append((math.dist(pa,pb),tick,a,b))
        if not all_pairs:continue
        dist,tick,a,b=min(all_pairs)
        first=ticks[min(ticks)]
        last=ticks[max(ticks)]
        start_dist=math.dist(first[a],first[b]) if a in first and b in first else None
        end_dist=math.dist(last[a],last[b]) if a in last and b in last else None
        result.append({'turn_start_tick':start,
                       'sampled_tick_count':len(ticks),
                       'sampled_distinct_members':len(set().union(*(set(z) for z in ticks.values()))),
                       'min_horizontal_member_center_distance':round(dist,6),
                       'min_distance_tick':tick,
                       'same_pair_start_sample_distance':round(start_dist,6) if start_dist is not None else None,
                       'same_pair_end_sample_distance':round(end_dist,6) if end_dist is not None else None,
                       'physical_collision_proven':False,
                       'sampled_members_only':True})
    return result


def analyze(rows):
    all_events = [r for r in rows if isinstance(r, dict) and r.get('type') == 'event']
    event_counts = Counter(r.get('ev', '?') for r in all_events)
    sent_by = Counter()
    recv_by = Counter()
    source_matched = Counter()
    actors = defaultdict(set)
    groups = defaultdict(set)
    deferred = Counter()
    goal_post = Counter()
    old_goal_impact = Counter()
    invalid_rva = 0
    turns = defaultdict(set)
    turn_positions = defaultdict(lambda: defaultdict(list))
    for row in all_events:
        event = row.get('ev')
        unit = row.get('unit')
        group = row.get('group')
        member = row.get('member')
        if group and member:
            groups[group].add(member)
        if unit and member:
            actors[unit].add(member)
        if event == 'NATIVE_MEMBER_SEND':
            sent_by[row.get('source', 'UNKNOWN')] += 1
        elif event == 'MEMBER_RECEIVER':
            rv = row.get('returnRva')
            source = row.get('source', 'OTHER_OR_UNKNOWN')
            recv_by[source] += 1
            if rv in SOURCE_RET and source != SOURCE_RET[rv]:
                invalid_rva += 1
            if row.get('explicitlyMatchedSender') is True:
                source_matched[source] += 1
        elif event == 'DEFERRED_PACKET':
            deferred[row.get('source', '?')] += 1
        elif event == 'MOTOR_GOAL_REVERSAL':
            if row.get('group') and row.get('groupTick') is not None:
                turns[(row['group'],row['groupTick'])].add(row.get('member'))
        elif event == 'POST_TURN_POSITION':
            if row.get('group') and row.get('groupTick') is not None:
                turn_positions[row['group']][row.get('member')].append((row['groupTick'],
                        row.get('x'), row.get('z')))
        elif event == 'GOAL_WRITE_POST':
            goal_post[row.get('group') or '?'] += 1
        elif event == 'NATIVE_GOAL_DIRECTION':
            old_goal_impact[row.get('group') or '?'] += 1
    summary = next((r for r in reversed(rows) if isinstance(r,dict) and
                    r.get('type') == 'summary'), None)
    agent_attempted=(summary or {}).get('eventCounts',{})
    # Legacy agent counted 21,534 queue entry attempts but saved only 1,697;
    # all sender identity records were lost to the 1,700 non-priority cap.
    saved_loss={k:max(0,int(n)-event_counts.get(k,0))
                for k,n in agent_attempted.items() if isinstance(n,int)}
    critical_lost={k:saved_loss[k] for k in CORE_SOURCE_KINDS if saved_loss.get(k,0)}
    total_calculated_loss=sum(saved_loss.values())
    loss_reconciles=(summary or {}).get('dropped')==total_calculated_loss if summary else None
    sender_triggered_no_record=not sent_by and agent_attempted.get('NATIVE_MEMBER_SEND',0)>0

    has_ready = any(isinstance(r,dict) and r.get('type') == 'ready' for r in rows)
    errors = [r for r in rows if isinstance(r, dict) and r.get('type') in ('probe_error','bad_payload')]
    groups_ranked = sorted(((key,len(members)) for key,members in groups.items()),
                           key=lambda x: -x[1])
    if not has_ready or not summary or errors or invalid_rva:
        grade = 'INCOMPLETE_OR_INSTRUMENTATION_ERROR'
    elif sender_triggered_no_record and critical_lost:
        grade = 'NATIVE_SOURCE_EVENTS_TRIGGERED_BUT_DROPPED_BY_LOGGER'
    elif source_matched and any(source_matched.values()):
        grade = 'RUNTIME_NATIVE_SOURCE_MATCH_CONFIRMED'
    elif recv_by:
        grade = 'RECEIVER_HIT_BUT_NATIVE_SENDER_UNMATCHED'
    elif sent_by:
        grade = 'NATIVE_SENDER_HIT_BUT_RECEIVER_UNMATCHED'
    else:
        grade = 'NO_SAMPLED_NATIVE_SENDER_EVENTS'
    return {
        'schema':'bsc.n1.source_plus_motor_one_shot.v2',
        'grade':grade,
        'ready_observed':has_ready,
        'summary_observed':bool(summary),
        'probe_errors_count':len(errors),
        'return_rva_classification_mismatch':invalid_rva,
        'record_count':len(rows),
        'event_counts':dict(event_counts),
        'sampled_senders':dict(sent_by),
        'sampled_receivers':dict(recv_by),
        'sender_to_receiver_strict_matches':dict(source_matched),
        'deferred_dispatch_source_counts':dict(deferred),
        'goal_post_event_count_by_group':dict(goal_post),
        'native_direction_predicate_samples_by_group':dict(old_goal_impact),
        'same_group_tick_native_motor_goal_reversals':[
          {'group':group,'tick':clock,'distinct_members':len(actors)}
          for (group,clock),actors in sorted(turns.items()) if len(actors)>=2],
        'sampled_post_reversal_displacement':post_turn_motion(all_events),
        'sampled_close_approaches':closest_member_separations(all_events),
        'overlapping_turns_using_existing_sampling_window':[
          {'reversal_tick':t,'tracked_from_tick':min(eligible)}
          for (g,t) in sorted(turns)
          if not any(e.get('ev')=='GROUP_TICK_POSITION' and
                     e.get('group')==g and e.get('turnStartTick')==t
                     for e in all_events)
          for eligible in [[r.get('turnStartTick') for r in all_events
                           if r.get('ev')=='GROUP_TICK_POSITION' and
                           r.get('group')==g and isinstance(r.get('turnStartTick'),int) and
                           r['turnStartTick']<t<=r['turnStartTick']+18]]
          if eligible],
        'turn_window_position_samples_by_group':{
          group:{'distinct_members':len(members),
                 'members_with_at_least_4_clock_samples':sum(
                     len({tick for tick,_,_ in samples})>=4
                     for samples in members.values())}
          for group,members in turn_positions.items()},
        'distinct_sampled_unit_owners':len(actors),
        'groups_ranked_by_distinct_sampled_members':groups_ranked[:12],
        'complete_source_counts_if_agent_summary':(summary or {}).get('sourceCounts',{}),
        'agent_attempted_event_counts':dict(agent_attempted),
        'agent_event_counts_dropped_by_logger':saved_loss,
        'core_identity_records_dropped':critical_lost,
        'logger_drop_count_reconciles':loss_reconciles,
        'logger_drop_count_reconstructed':total_calculated_loss,
        'native_sender_hook_executions':agent_attempted.get('NATIVE_MEMBER_SEND',0),
        'native_receiver_hook_executions':agent_attempted.get('MEMBER_RECEIVER',0),
        'queued_hook_executions_from_agent_summary':agent_attempted.get('QUEUED_CONTINUATION',0),
        'native_move_issuer_hook_executions_from_agent_summary':agent_attempted.get('NATIVE_MOVE_ISSUER',0),
        'native_sender_pointer_pair_counts':(summary or {}).get('pointerPairedSourceCounts',{}),
        'native_receiver_return_rva_counts':(summary or {}).get('receiverReturnCounts',{}),
        'queue_manager_total_hook_calls':(summary or {}).get('queueManagerCalls'),
        'agent_dropped_events':(summary or {}).get('dropped'),
        'agent_detach_errors':(summary or {}).get('detachErrors'),
        'native_queued_hook_events':event_counts['QUEUED_CONTINUATION'],
        'untyped_member_field60_warning':(
            'member+0x60 sampled values were never confirmed to be native formation ordinals; '
            'sampling order or physical arrangement must not be inferred from them'),
        'native_move_issuer_events':event_counts['NATIVE_MOVE_ISSUER'],
        'old_goal_incompatible_with_native_route_proven':False,
        'physical_crowding_causality_proven':False,
        'patch_authorized':False,
        'limitations':[
            'Sender/receiver exact return-RVA attribution does not establish RMB vs Shift player input.',
            'The group task 0x03ADD608 is distinct from B route-cache 0x03AE00E8.',
            'Native GOAL_READ is a guarded action predicate, not necessarily a physics integrator.',
            'Only a real gameplay run with correct task/order identity could attribute conflicting old/new movement.',
            'Unlogged source event counts in the agent summary are NOT absent native events.',
            'Sampled horizontal center distances are not soldier radii or a proof of collision.',
        ]
    }


def read_jsonl(path):
    rows=[]
    for lineno,line in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(),1):
        if not line.strip():continue
        try:rows.append(json.loads(line))
        except json.JSONDecodeError as ex:
            raise ValueError('INVALID_JSONL_LINE_'+str(lineno)) from ex
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--out',default=Path('bsc_once_source_report.json'),type=Path)
    opt=parser.parse_args()
    result=analyze(read_jsonl(opt.input))
    opt.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ANALYSIS_GRADE:',result['grade'])
    print('Sources:',result['sender_to_receiver_strict_matches'])
    print('Distinct sampled members per group:',result['groups_ranked_by_distinct_sampled_members'][:3])
    print('Saved:',opt.out.resolve())

if __name__=='__main__':main()
