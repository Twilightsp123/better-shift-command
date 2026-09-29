#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'controller_tools'))
import pack_tools
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('pack',type=Path);ap.add_argument('bridge_dll',type=Path);ns=ap.parse_args()
    raw=ns.pack.read_bytes();data=pack_tools.parse_pack(raw);bridge=ns.bridge_dll.read_bytes();minhook=(ROOT/'baseline/minhook.x64.dll').read_bytes()
    expected=pack_tools.selfcontained(ROOT,(ROOT/'source/better_shift_command.lua').read_bytes(),bridge,minhook)
    if raw!=expected: raise SystemExit('FAIL: pack is not deterministic v1.2.1 build')
    if pack_tools.decode_payload(data[pack_tools.BRIDGE_PATH])!=bridge: raise SystemExit('FAIL: embedded bridge differs')
    if pack_tools.decode_payload(data[pack_tools.MINHOOK_PATH])!=minhook: raise SystemExit('FAIL: embedded MinHook differs')
    c=data[pack_tools.CONTROLLER_PATH]
    for m in (b'local CONTROLLER_VERSION = "1.2.1"',b'local RUN_ID = "V1_2_1"',b'BETTER_SHIFT_COMMAND_V1.2.1',b'local DEBUG_TELEMETRY = false',b'1.0.15-r4-evidence-v3-validated-userdata-root',b'NATIVE_FUTURE_OVERRUN'):
        if m not in c: raise SystemExit('FAIL: missing v1.2.1 release marker '+repr(m))
    for m in (b'RAW_RMB_DOWN',b'RMB_EXIT_TRACE',b'read_input_snapshot'):
        if m in c: raise SystemExit('FAIL: temporary RMB diagnostic present '+repr(m))
    print('PASS: deterministic Better Shift Command v1.2.1 release pack')
    print('bridge_sha256='+sha(bridge));print('minhook_sha256='+sha(minhook));print('pack_sha256='+sha(raw))
if __name__=='__main__':main()
