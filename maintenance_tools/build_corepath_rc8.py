#!/usr/bin/env python3
"""Build deterministic BSC CorePath RC8 candidate PFH5 pack. No install/game launch."""
from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'controller_tools'))
import pack_tools
p=argparse.ArgumentParser();p.add_argument('bridge_dll',type=Path);p.add_argument('output_pack',type=Path);a=p.parse_args()
controller=(ROOT/'source/better_shift_command.lua').read_bytes();bridge=a.bridge_dll.read_bytes();minhook=(ROOT/'baseline/minhook.x64.dll').read_bytes()
raw=pack_tools.selfcontained(ROOT,controller,bridge,minhook);a.output_pack.parent.mkdir(parents=True,exist_ok=True);a.output_pack.write_bytes(raw)
print('PASS candidate pack');print('bridge_sha256='+pack_tools.sha(bridge));print('pack_sha256='+pack_tools.sha(raw))
