#!/usr/bin/env python3
"""R51 static evidence for WH3 battle-script phase vs native worker lifecycle.

Does NOT connect to a running process, execute memreader DLL, install hook, or
claim that a Lua callback is a native quiescence point.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

CHECKS = {
    'derpy_battle_callbacks_are_UI_timed': ('main', r'bm:repeat_real_callback\(frame,\s*1,\s*"derpy_tp"\)'),
    'derpy_complete_callback': ('main', r'bm:register_phase_change_callback\("Complete"'),
    'derpy_pause_is_a_heuristic': ('main', r'local PAUSE_AFTER\s*=\s*0\.5'),
    'derpy_worker_thread_experience': ('platform', r'The battle runs on worker threads while the script runs'),
    'derpy_mailbox_installed_via_native_cave': ('platform', r'mr\.patcher\("derpy_tp"\):cave\("mailbox"'),
    'r49_sample_is_manual_function': ('r49', r'function M\.sample\(unit,opts\)'),
    'r49_timing_uses_elasped_us': ('r49', r'local duration=mr\.elapsed_us\(began\)'),
    'r49_full_roster_double_read': ('r49', r'if roster~=after_roster then return nil,'),
    'r50_external_clock_overridden': ('r50', r'caller_supplied_sample_clock_forbidden'),
    'r50_real_elapsed_tick': ('r50', r'local start=epoch or mr\.ticks\(\)'),
    'r51_phase_marker_only': ('r51', r'local function change\(p\)'),
    'r51_manual_capture_only': ('r51', r'function controller:capture_once\(unit,opts\)'),
    'r51_rejects_raw_pointers_in_errors': ('r51', r"return nil,'lower_sampler_rejected'"),
    'r51_cross_model_clock_guard': ('r51', r'before\.model_time_ms~=after\.model_time_ms'),
    'r51_denies_worker_quiescence_claim': ('r51', r'worker_thread_quiescence_proven=false'),
    'r51_disables_victory_and_complete': ('r51', r"p=='VictoryCountdown' or p=='Complete'"),
}

def audit(paths):
    sources={key:Path(value).read_text('utf-8') for key,value in paths.items()}
    missing=[name for name,(src,pattern) in CHECKS.items() if not re.search(pattern,sources[src])]
    if missing:
        raise ValueError('SOURCE_CONTRACT_DRIFT:'+','.join(missing))
    # Does not decide safety by presence of names alone: collect negative controls.
    r51=sources['r51']
    if re.search(r'\bmr\.(?:write|call|hook|hook_site|patch|patcher|game_alloc)\s*\(',r51):
        raise ValueError('R51_UNEXPECTED_NATIVE_MUTATION_API')
    if 'bm:repeat_real_callback' in r51 or 'bm:repeat_callback' in r51:
        raise ValueError('R51_AUTOMATED_CAPTURE_FORBIDDEN')
    callbacks=re.search(r'local function change\(p\)(.*?)\n  end\n  -- Registration',r51,re.S)
    if not callbacks or re.search(r'(?:mr|sampler|clock)\s*[.:]',callbacks.group(1)):
        raise ValueError('R51_NATIVE_READ_IN_PHASE_CALLBACK')
    return {
        'schema':'bsc.n1.r51.battle_phase_capture_research.v1',
        'proof':'ACTUAL_DERPY_PACK_EXTRACT_AND_LOCAL_R49_R50_R51_SOURCE_STATIC',
        'checks_count':len(CHECKS), 'checks':{name:True for name in CHECKS},
        'source_sha256':{key:hashlib.sha256(text.encode()).hexdigest()
                         for key,text in sources.items()},
        'observed_battle_script_timer':'UI_REAL_CALLBACK_NOT_WORKER_TICK',
        'model_clock_steady_means_worker_idle':False,
        'battle_phase_is_worker_quiescence_barrier':False,
        'engine_atomic_snapshot_proven':False,
        'real_game_lua_executed':False,
        'native_gameplay_patch_authorized':False,
        'safe_live_installation_claimed':False,
        'next_required_proof':'same-type member lifetime and worker-thread synchronization',
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for src in ('derpy-main','derpy-platform','r49','r50','r51'):
        p.add_argument('--'+src,required=True,type=Path)
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    paths={'main':args.derpy_main,'platform':args.derpy_platform,
           'r49':args.r49,'r50':args.r50,'r51':args.r51}
    if args.out and args.out.resolve() in {x.resolve() for x in paths.values()}:
        p.error('SOURCE_OVERWRITE_FORBIDDEN')
    result=audit(paths)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('R51_SOURCE_AUDIT_PASS',result['checks_count'],'checks; WORKER_BARRIER_NOT_PROVEN; NO PATCH')
if __name__=='__main__':
    main()