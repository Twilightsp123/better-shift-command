#!/usr/bin/env python3
"""Static-only source/API/binary contract audit of R49 sampler and supplied mods.

Does not execute any native DLL, patch the game, or claim runtime safety.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from audit_r47_action_fingerprints_20261020 import (
    WH3_SHA, DERPY_SHA, MEM_SHA, BUILD, IMAGEBASE,
    MEMBER_VTABLE, MEMBER_TICK, MEMBER_MOTION,
    PE, audit as r47_audit, selected_scripts, single_pack,
)

TICK_BYTES=bytes.fromhex('488bc448895810')
GATE_BYTES=bytes.fromhex('4438bff806000075094438bf00060000755c')
HERE=Path(__file__).resolve().parent
SAMPLER=HERE/'bsc_r49_guarded_passive_sampler_research.lua'
PREFLIGHT=HERE/'r49_spatial_evidence_preflight.py'


def audit(exe,derpy,memreader):
    baseline=r47_audit(exe,derpy,memreader)
    raw=Path(exe).read_bytes()
    pe=PE(raw)
    if pe.bytes(MEMBER_TICK,len(TICK_BYTES))!=TICK_BYTES:
        raise ValueError('R49_TICK_BYTES_DRIFT')
    if pe.bytes(0x03087378,len(GATE_BYTES))!=GATE_BYTES:
        raise ValueError('R49_GATE_BYTES_DRIFT')
    if pe.vtable_pointer(MEMBER_VTABLE+0x18)!=MEMBER_TICK or pe.vtable_pointer(MEMBER_VTABLE+0x20)!=MEMBER_MOTION:
        raise ValueError('R49_MEMBER_TYPE_METHOD_DRIFT')
    p=selected_scripts(single_pack(memreader),[
        'script/memreader_plus/releases/0_13_0.lua',
        'script/memreader_plus/0_13_0/loader.lua',
        'script/memreader_plus/0_13_0/bin.lua',
    ])
    release=p['script/memreader_plus/releases/0_13_0.lua'].decode('utf8')
    loader=p['script/memreader_plus/0_13_0/loader.lua'].decode('utf8')
    binary_lua=p['script/memreader_plus/0_13_0/bin.lua']
    if "return '0_13_0'" not in release or '_G.memreader_plus_release = release' not in loader:
        raise ValueError('MEMREADER_RELEASE_CONTRACT_DRIFT')
    for name in ('ticks','elapsed_us','read_original','hook_info','read_struct','ud_topointer','read_pointer'):
        if name.encode('ascii') not in binary_lua:
            raise ValueError('MEMREADER_BINARY_METHOD_NAME_MISSING:'+name)
    d=selected_scripts(single_pack(derpy),['script/derpy_tp/platform.lua'])
    platform=d['script/derpy_tp/platform.lua'].decode('utf8')
    for s in ('["6acec6f4"]','MODELS_N, MODELS_DATA, MODEL_POS = 0xa4, 0xa8, 0x88','local function obj_of(unit)',
              'mr.ud_topointer(unit)','mr.read_pointer(obj, MODELS_DATA)'):
        if s not in platform:
            raise ValueError('DERPY_MEMBER_ACCESS_SOURCE_DRIFT:'+s)
    src=SAMPLER.read_text('utf8')
    for token in ('mr.ticks()','mr.elapsed_us(began)','roster:sub(',"mr.read(array,0,n*8)",
                  'roster_epoch','read_duration_us','read_offset_us',
                  'intra_sample_full_roster_stable','cross_snapshot_lifetime_proven=false',
                  'function M.sample(', 'function M.reset('):
        if token not in src:raise ValueError('R49_SAMPLER_SOURCE_DRIFT:'+token)
    # Only functional code, not comments. Even uncalled write/hook functions banned.
    noncomments='\n'.join(l.split('--',1)[0] for l in src.splitlines())
    for forbidden in (r'\bmr\.write\s*\(',r'\bmr\.call\s*\(',r'\bmr\.patch\s*\(',
                      r'\bmr\.hook\s*\(',r'\bmr\.game_alloc\s*\(',
                      r'\bmr\.code_cave\s*\(',r'\bmr\.patcher\s*\(',
                      r'\:\s*(?:hook|cave|patch)\s*\(',r'\bcm\:callback\s*\('):
        if re.search(forbidden,noncomments):raise ValueError('R49_NOT_PASSIVE:'+forbidden)
    result={
        'schema':'bsc.n1.r49_memreader_passive_contract_static.v1',
        'evidence_type':'REAL_FILES_STATIC_AND_OFFLINE_LUA_API_MOCK',
        'exe_sha256':WH3_SHA,'derpy_pack_sha256':DERPY_SHA,'memreader_pack_sha256':MEM_SHA,
        'pe_timestamp':format(BUILD,'08x'),'exe_imagebase':hex(IMAGEBASE),
        'verified_external_action_vtable_slots':baseline['verified_action_vtable_slots'],
        'verified_member_vtable_slots':baseline['verified_regular_member_vtable_slots'],
        'verified_queued_tick_original_bytes':len(TICK_BYTES),
        'verified_queue_gate_original_bytes':len(GATE_BYTES),
        'api_names_present_in_bundled_native_payload':7,
        'original_loader_release':'0_13_0',
        'sampler_no_write_hook_patch_functions':True,
        'runtime_hooks_not_installed':True,
        'live_gameplay_capture_run':False,
        'runtime_pointer_race_safe_proven':False,
        'same_pointer_same_lifetime_proven':False,
        'formation_crowding_root_cause_proven':False,
        'native_gameplay_patch_authorized':False,
    }
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--derpy',type=Path,required=True)
    ap.add_argument('--memreader',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    if args.output and args.output.resolve() in {args.exe.resolve(),args.derpy.resolve(),args.memreader.resolve()}:
        ap.error('refusing to overwrite evidence inputs')
    result=audit(args.exe,args.derpy,args.memreader)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print('R49_STATIC_PASS',result['verified_external_action_vtable_slots'],
          'action slots and',result['verified_member_vtable_slots'],
          'member slots; ORIGINAL BYTES VERIFIED; NO PATCH')

if __name__=='__main__':main()
