#!/usr/bin/env python3
"""Conservative source-matched, same-member GOAL_READ -> direction decision proof.

Does not claim old target was incompatible with CA gradual Shift turn, physical
collision, or that a gameplay fix has been built/validated.
"""
import argparse,json
from pathlib import Path
def analyze(events):
    queue=[];instances={};reads=0;decisions=0;commits=0;errors=[]
    for e in events:
        if not isinstance(e,dict):continue
        if e.get('type') in ('probe_error','error'):errors.append(e)
        if e.get('type')!='event':continue
        ev=e.get('ev')
        if ev=='QUEUED_CONTINUATION':
            queue.append({'root':e.get('root'),'group':e.get('group'),'atMs':e.get('atMs')})
            continue
        actor=e.get('member') or e.get('actor')
        ident=e.get('traceId')
        if ev in ('B_DEFERRED_RECEIVE','DIRECT_ACTION_RESET'):
            if not actor or not isinstance(ident,int):continue
            k=(actor,ident);source=e.get('source',{})
            instances[k]={'kind':ev,'receivedAt':e.get('atMs'),
              'B_fanout':bool(source.get('memberFanoutMatched')),
              'queue_identity':bool(source.get('queuedUnitIdentityMatches')),
              'group':source.get('memberFanoutGroup'),
              'old_reads_before_write':0,'old_direction_decisions':[],
              'commits':0,'commit_delay_ms':None}
            continue
        k=(actor,ident)
        if k not in instances:continue
        s=instances[k]
        if ev=='GOAL_READ':
            reads+=1
            if (e.get('goalUnchangedSinceReceive') is True and
                e.get('writeSeenSinceReceive') is False):
                s['old_reads_before_write']+=1
        elif ev=='OLD_GOAL_DIRECTION_DECISION':
            decisions+=1
            al=e.get('predicateReturn')
            if (al in (0,1) and e.get('goalUnchangedSinceReceive') is True and
                e.get('writeSeenSinceReceive') is False and
                e.get('lastGoalReadSameThread') is True and
                e.get('lastGoalReadWithin100ms') is True):
                s['old_direction_decisions'].append({
                    'atMs':e.get('atMs'),'predicateReturn':al,
                    'branchIfFalse':e.get('branchIfFalse')})
        elif ev=='GOAL_COMMIT_POST':
            commits+=1;s['commits']+=1
            if s['commit_delay_ms'] is None:
                a=e.get('atMs');b=s['receivedAt']
                if isinstance(a,(int,float)) and isinstance(b,(int,float)):
                    s['commit_delay_ms']=a-b
    deferred=[(k,v) for k,v in instances.items() if v['kind']=='B_DEFERRED_RECEIVE']
    direct=[(k,v) for k,v in instances.items() if v['kind']=='DIRECT_ACTION_RESET']
    matched=[(k,v) for k,v in deferred if v['B_fanout']]
    old_reads=[(k,v) for k,v in matched if v['old_reads_before_write']>0]
    direction=[(k,v) for k,v in old_reads if v['old_direction_decisions']]
    queued=[(k,v) for k,v in direction if v['queue_identity']]
    def summarize(rows):
        return {'instances':len(rows),
          'old_goal_reads_before_commit':sum(v['old_reads_before_write']>0 for _,v in rows),
          'old_goal_direction_decisions':sum(bool(v['old_direction_decisions']) for _,v in rows),
          'completed_goal_writes':sum(v['commits']>0 for _,v in rows),
          'commit_delays_ms':[v['commit_delay_ms'] for _,v in rows
                              if v['commit_delay_ms'] is not None]}
    if errors:grade='PROBE_ERRORS_REFUSE_EVIDENCE'
    elif not queue and not instances:grade='NO_NATIVE_EVENTS'
    elif queued:grade='QUEUE_LINKED_B_OLD_GOAL_DIRECTION_DECISION'
    elif direction:grade='B_FANOUT_LINKED_OLD_GOAL_DIRECTION_DECISION'
    elif old_reads:grade='B_FANOUT_LINKED_OLD_GOAL_READ'
    elif matched:grade='B_FANOUT_TO_DEFERRED_RECEIVE_ONLY'
    else:grade='NO_SOURCE_MATCHED_B_RECEIVE'
    return {'schema':'bsc.n1.goal_branch_v2.analysis','grade':grade,
      'queue_events':len(queue),'sampled_goal_reads':reads,
      'sampled_direction_results':decisions,'completed_goal_writes':commits,
      'instrumentation_error_count':len(errors),
      'B_deferred_all':summarize(deferred),
      'B_source_packet_matched':summarize(matched),
      'direct_action_reset_control':summarize(direct),
      'old_direction_with_B_fanout_count':len(direction),
      'old_direction_queue_unit_identity_count':len(queued),
      'examples':[{'member':k[0],'traceId':k[1],'group':v['group'],
        'queue_identity_matched':v['queue_identity'],
        'old_direction_decisions':v['old_direction_decisions'][:3],
        'goal_commit_delay_ms':v['commit_delay_ms']} for k,v in direction[:20]],
      'geometric_route_conflict_proven':False,
      'physical_crowding_proven':False,'native_fix_proven':False,
      'reason':'Read and branch use of unchanged motor goal is distinct from incompatibility with native gradual route or collision causality.'}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();data=[]
    for n,line in enumerate(a.input.read_text(encoding='utf8').splitlines(),1):
        if not line.strip():continue
        try:data.append(json.loads(line))
        except ValueError as ex:raise ValueError('INVALID_JSONL_LINE:'+str(n)) from ex
    result=analyze(data)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(result['grade'])
if __name__=='__main__':main()
