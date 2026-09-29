#!/usr/bin/env python3
from pathlib import Path
import argparse,sys,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'controller_tools'))
import pack_tools
p=argparse.ArgumentParser();p.add_argument('pack',type=Path);p.add_argument('bridge_dll',type=Path);a=p.parse_args()
raw=a.pack.read_bytes();bridge=a.bridge_dll.read_bytes();minhook=(ROOT/'baseline/minhook.x64.dll').read_bytes()
expected=pack_tools.selfcontained(ROOT,(ROOT/'source/better_shift_command.lua').read_bytes(),bridge,minhook)
if raw!=expected: raise SystemExit('FAIL: pack is not deterministic CorePath RC8 build')
d=pack_tools.parse_pack(raw)
if pack_tools.decode_payload(d[pack_tools.BRIDGE_PATH])!=bridge: raise SystemExit('FAIL: embedded Bridge differs')
if pack_tools.decode_payload(d[pack_tools.MINHOOK_PATH])!=minhook: raise SystemExit('FAIL: embedded MinHook differs')
c=d[pack_tools.CONTROLLER_PATH]
for m in (b'1.3.0',b'V1_3_0',b'BETTER_SHIFT_COMMAND_V1.3.0',b'PHYSICAL_EVIDENCE_MODE = "QUARANTINED"',b'NATIVE_FUTURE_OVERRUN'):
    if m not in c: raise SystemExit('FAIL: missing candidate marker '+repr(m))
print('PASS: deterministic CorePath RC8 candidate pack')
print('bridge_sha256='+hashlib.sha256(bridge).hexdigest());print('minhook_sha256='+hashlib.sha256(minhook).hexdigest());print('pack_sha256='+hashlib.sha256(raw).hexdigest())
