#!/usr/bin/env python3
"""Conservative read-before-goal-write evidence grader, NOT collision proof."""
import argparse
import json
from pathlib import Path

def classify_events(events):
    runs={};read_examples=[];queued=0;errors=0
    for e in events:
        kind=e.get('ev')
        if e.get('type')=='probe_error':errors+=1;continue
        if kind=='QUEUED_CONTINUATION':queued+=1;continue
        key=(e.get('actor'),e.get('traceId'))
        if kind in ('B_DEFERRED_RECEIVE','DIRECT_ACTION_RESET'):
            runs[key]={
                'kind':kind,'time':e.get('ms'),'first_write':None,
                'read_unchanged_before_write':0,'read_after_write':0,
                'near_shift_time_only':e.get('queuedContinuationNearInTime',
                                            e.get('nearQueuedContinuation',False)),
                'group':e.get('group'),'old_goal':e.get('goalRaw')}
        elif key in runs:
            r=runs[key]
            if kind=='GOAL_READ':
                if not e.get('motorWriteSinceReceive') and e.get('goalEqualToAtReceive'):
                    r['read_unchanged_before_write']+=1
                    if len(read_examples)<40:
                        read_examples.append({'member':key[0],'trace_id':key[1],
                                              'ms':e.get('ms'),'groupTick':e.get('groupTick')})
                elif e.get('motorWriteSinceReceive'):r['read_after_write']+=1
            elif kind=='GOAL_WRITE_PRE' and r['first_write'] is None:
                r['first_write']=e.get('ms')
    stats={}
    for kind in ('B_DEFERRED_RECEIVE','DIRECT_ACTION_RESET'):
        subset=[v for v in runs.values() if v['kind']==kind]
        stats[kind]=dict(
            member_task_instances=len(subset),
            instance_reads_old_goal_before_write=sum(v['read_unchanged_before_write']>0 for v in subset),
            goal_write_seen=sum(v['first_write'] is not None for v in subset),
            goal_commit_delays_ms=[v['first_write']-v['time'] for v in subset
                 if v['first_write'] is not None and v['time'] is not None],
            shift_queue_temporal_nearby_only=sum(bool(v['near_shift_time_only']) for v in subset))
    return {
       'schema':'bsc.n1.goal_handoff_one_shot_analysis.v1',
       'native_queued_continuation_hook_events':queued,
       'cases':stats,'examples_read_prewrite':read_examples,
       'probe_error_count':errors,
       'meaning':'Only proves native member action read an unchanged goal after receiving B packet if such an event exists.',
       'shift_b_object_identity_matched':False,
       'geometric_conflict_proven':False,
       'physical_collision_proven':False,
       'game_repair_proven':False}

def analyze(path):
    events=[]
    for line_no,line in enumerate(Path(path).read_text(encoding='utf8').splitlines(),1):
        if not line.strip():continue
        try:events.append(json.loads(line))
        except json.JSONDecodeError as e:raise ValueError('MALFORMED_JSONL_'+str(line_no)) from e
    return classify_events(events)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    result=analyze(a.input)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Old goal read examples:',len(result['examples_read_prewrite']),
          'conflict proven:',result['geometric_conflict_proven'])
if __name__=='__main__':main()
