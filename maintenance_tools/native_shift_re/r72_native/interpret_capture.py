#!/usr/bin/env python3
"""R72 offline-only event protocol gate; never infer a live-game causal result.
This reads synthetic events, not memory, and cannot make non-atomic samples atomic.
"""
import json
from collections import defaultdict

SCHEMA='bsc.r72.synthetic.v1'

def interpret(obj):
    if not isinstance(obj,dict) or obj.get('schema')!=SCHEMA:
        raise ValueError('SCHEMA_REJECTED')
    entries=obj.get('events')
    if not isinstance(entries,list) or len(entries)>100000:
        raise ValueError('EVENT_BUDGET_REJECTED')
    groups=defaultdict(list)
    for i,e in enumerate(entries):
        if not isinstance(e,dict) or set(e)!={'member_token','owner_epoch','tick_sequence','thread_tag','phase','x_bits','z_bits'}:
            raise ValueError('EVENT_FIELDS_REJECTED')
        for k,v in e.items():
            if type(v) is not int or v<0 or v >= (1<< (64 if k=='member_token' else 32)):
                raise ValueError('EVENT_VALUE_REJECTED')
        if not e['member_token'] or not e['owner_epoch']:
            raise ValueError('ANONYMOUS_LIFETIME_MISSING')
        groups[(e['owner_epoch'],e['member_token'],e['thread_tag'])].append(e['tick_sequence'])
    for seq in groups.values():
        if seq != sorted(set(seq)):
            raise ValueError('MEMBER_TIME_ORDER_REJECTED')
    return {
        'grade':'OFFLINE_SYNTHETIC_MEMBER_LOCAL_ONLY',
        'events':len(entries),
        'local_tracks':len(groups),
        'cross_member_atomicity':False,
        'game_instance_identity_proven':False,
        'worker_lifetime_proven':False,
        'gameplay_root_cause_proven':False,
        'native_game_hook_authorized':False,
    }

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('json_file')
    args=p.parse_args()
    with open(args.json_file,encoding='utf8') as stream:
        print(json.dumps(interpret(json.load(stream)),indent=2))
