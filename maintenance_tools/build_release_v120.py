#!/usr/bin/env python3
"""Build the deterministic Better Shift Command v1.2.0 self-contained PFH5 pack. No install/game launch."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'controller_tools'))
import pack_tools
def main():
    ap=argparse.ArgumentParser();ap.add_argument('bridge_dll',type=Path);ap.add_argument('output_pack',type=Path);ns=ap.parse_args()
    data=pack_tools.selfcontained(ROOT,(ROOT/'source/better_shift_command.lua').read_bytes(),ns.bridge_dll.read_bytes(),(ROOT/'baseline/minhook.x64.dll').read_bytes())
    ns.output_pack.parent.mkdir(parents=True,exist_ok=True);ns.output_pack.write_bytes(data);print(ns.output_pack)
if __name__=='__main__':main()
