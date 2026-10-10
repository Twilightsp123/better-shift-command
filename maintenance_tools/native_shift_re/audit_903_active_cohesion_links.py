#!/usr/bin/env python3
"""Exact-build, bounded x64 direct-call audit for V3-active MOVE vs group cohesion.

READ ONLY. This intentionally does not infer edges through virtual dispatch,
indirect calls, data pointers, or unexamined function bodies. No patch site is
selected by this tool. Requires GNU objdump (x86-64) and the original WH3 EXE.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import mmap
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from scout_pe import parse_pe, InvalidPE

TARGET_SHA = "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
BASE = 0x140000000
# Fixed, bounded DISASSEMBLY WINDOWS, not asserted function boundaries.
WINDOWS = {
 "v3_move_work": (0x03025D70, 0x380),
 "unit_route": (0x0301287C, 0x190),
 "move_task_ctor": (0x02F2C734, 0x1E0),
 "move_task_tick": (0x02F561E8, 0x350),
 "group_broadcast": (0x030D52B4, 0xC0),
 "member_event_receiver": (0x0306B878, 0xA0),
 "member_pose_tick": (0x03060700, 0x320),
 "member_pose_writer": (0x0315C1E4, 0x130),
 "mode0_strategy": (0x030C9A64, 0xD0),
 "mode0_delegate": (0x030DBFD4, 0x220),
 "group_distance": (0x030D572C, 0x200),
 "group_ready": (0x030D5628, 0x90),
 "group_distance_updater": (0x030D56BC, 0x65),
 "distance_caller_a": (0x03044F70, 0x70),
 "distance_caller_b": (0x03045130, 0x70),
 "distance_caller_c": (0x032837D0, 0x65),
}
# Previously reported direct call sites; each must be re-decoded from bytes.
# Additional calls discovered in those windows are leads, not proof of reachability.
KNOWN = {
 "move_to_route_a": (0x03025E91, 0x0301287C),
 "move_to_route_b": (0x03026022, 0x0301287C),
 "move_to_task_ctor": (0x030260AF, 0x02F2C734),
 "task_to_group_event": (0x02F564A5, 0x030D52B4),
 "member_to_pose_writer": (0x0306091D, 0x0315C1E4),
 "mode0_to_delegate": (0x030C9B18, 0x030DBFD4),
 "distance_updater_caller_a": (0x03044FAF, 0x030D56BC),
 "distance_updater_caller_b": (0x0304516B, 0x030D56BC),
 "distance_updater_caller_c": (0x03283806, 0x030D56BC),
}
LINE = re.compile(r"^\s*([a-fA-F0-9]+):\s*((?:[a-fA-F0-9]{2}\s+)+)([a-zA-Z][\w.]*)\s*(.*)$")


def sha256(path):
 h = hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
   h.update(chunk)
 return h.hexdigest()


def pe_bytes(mm, pe, rva, size):
 if not (0 <= rva < 0x100000000 and 0 < size <= 0x10000):
  raise ValueError("INVALID_RVA_OR_SIZE")
 for s in pe["sections"]:
  if s.executable and s.raw_size and s.rva <= rva and rva + size <= s.rva + s.raw_size:
   offset = s.raw_start + rva - s.rva
   return bytes(mm[offset:offset + size])
 raise ValueError("NOT_FILE_BACKED_EXECUTABLE_RVA:" + hex(rva))


def direct_target(site, instruction):
 if len(instruction) != 5 or instruction[0] != 0xE8:
  raise ValueError("NOT_E8_AT:" + hex(site))
 return site + 5 + struct.unpack_from("<i", instruction, 1)[0]


def parse_objdump(output):
 """Only count confirmed instruction-boundary E8; raw byte scans are unsafe."""
 edges = []
 indirect = []
 for line in output.splitlines():
  match = LINE.match(line)
  if not match:
   continue
  site = int(match.group(1), 16)
  raw = bytes.fromhex(match.group(2))
  mnemonic = match.group(3).lower()
  if mnemonic.startswith("call"):
   if len(raw) == 5 and raw[0] == 0xE8:
    edges.append({"site": site, "target": direct_target(site, raw)})
   else:
    indirect.append(site)
 return edges, indirect


def disassemble(raw, rva, objdump):
 with tempfile.TemporaryDirectory(prefix="bsc_903_re_") as td:
  fragment = Path(td) / "slice.bin"
  fragment.write_bytes(raw)
  cmd = [objdump, "-D", "-b", "binary", "-m", "i386:x86-64",
         "-M", "intel", "--adjust-vma=" + hex(rva), str(fragment)]
  result = subprocess.run(cmd, text=True, capture_output=True, timeout=15, check=False)
  if result.returncode:
   raise ValueError("OBJDUMP_FAILED:" + result.stderr[:500])
  return parse_objdump(result.stdout)


def verified_calls(mm, pe):
 rows = []
 for label, (site, expected) in KNOWN.items():
  actual = direct_target(site, pe_bytes(mm, pe, site, 5))
  if actual != expected:
   raise ValueError("CALLSITE_TARGET_MISMATCH:" + label + ":" + hex(actual))
  rows.append({"name":label, "site":hex(site), "target":hex(actual)})
 return rows


def analyze(exe, objdump="objdump", expected_sha=TARGET_SHA):
 if sha256(exe) != expected_sha:
  raise ValueError("EXE_SHA256_MISMATCH")
 if not shutil.which(objdump):
  raise ValueError("OBJDUMP_NOT_FOUND")
 with exe.open("rb") as fd, mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ) as mm:
  pe = parse_pe(mm)
  if pe["image_base"] != BASE:
   raise ValueError("IMAGE_BASE_MISMATCH")
  known = verified_calls(mm, pe)
  windows = {}
  all_edges = []
  for label,(start,length) in WINDOWS.items():
   edges, indirect = disassemble(pe_bytes(mm, pe, start, length), start, objdump)
   windows[label] = {"rva": hex(start), "bytes":length,
     "direct_calls":len(edges), "indirect_call_sites":[hex(a) for a in indirect]}
   for edge in edges:
    all_edges.append({"window":label,"site":hex(edge["site"]),"target":hex(edge["target"])})
 # Known direct calls DO NOT provide a continuous direct path between every
 # original root. In particular the member controller and cohesion updater
 # may be connected only by indirect vtables or state-object/data flow.
 anchor_set = {rva for rva,_ in WINDOWS.values()}
 anchor_hits = [e for e in all_edges if int(e["target"],16) in anchor_set]
 return {"schema":"bsc.n1_903.active_cohesion_links.v1", "exe_sha256":expected_sha,
  "image_base":hex(BASE), "grade":"EXACT_SHA_STATIC_BOUNDED_INSTRUCTION_DECODE",
  "known_direct_calls_verified":known, "windows":windows,
  "all_scoped_direct_calls":all_edges, "scoped_anchor_targets":anchor_hits,
  "limits":["Disassembly windows are NOT verified function boundaries",
    "Missing direct E8 edges cannot exclude indirect/virtual/dataflow links",
    "group distance evaluator cannot be assumed called in V3 mode0",
    "member+0x2E0 controller producer and desired target writer remain unverified"],
  "runtime_patch_authorized":False,"windows_tested":False,"wh3_tested":False}


def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--exe",required=True,type=Path)
 p.add_argument("--report",required=True,type=Path)
 p.add_argument("--objdump",default="objdump")
 args=p.parse_args(argv)
 if args.exe.resolve()==args.report.resolve():
  p.error("report cannot overwrite the EXE")
 try:
  result=analyze(args.exe,args.objdump)
  args.report.parent.mkdir(parents=True,exist_ok=True)
  args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
  print("STATIC_ONLY:",len(result["known_direct_calls_verified"]),"anchor calls verified;")
  print("direct calls in scopes:",len(result["all_scoped_direct_calls"]),"; NO PATCH")
  return 0
 except (ValueError,OSError,InvalidPE,struct.error,subprocess.TimeoutExpired) as e:
  print("ACTIVE_COHESION_AUDIT_BLOCKED:",e,file=sys.stderr)
  return 2


if __name__=="__main__":
 sys.exit(main())
