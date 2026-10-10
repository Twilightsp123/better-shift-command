#!/usr/bin/env python3
"""Read-only exact-9.0.3 unit member-layer audit. NEVER authorizes a Hook."""
import argparse, hashlib, json, mmap, struct
from pathlib import Path
from audit_903_formation_entry import TARGET_SHA256, digest_file, pe_sections, read_executable, e8_target

# These are independent of the earlier position-aggregation scout.
# Meanings are structural only: no claim that any collection is a soldier array.
GUARDS = {
 "same_root_A_count": (0x0303D6B3, "8b8f84010000"),
 "same_root_A_ptr": (0x0303D6C4, "488b8788010000"),
 "same_root_A_container": (0x0303D6CF, "488d8f80010000"),
 "same_root_B_count": (0x0303D73D, "8b8f14010000"),
 "same_root_B_ptr": (0x0303D74E, "488b8718010000"),
 "same_root_B_container": (0x0303D759, "488d8f10010000"),
 "A_position_count": (0x030421F3, "448b8184010000"),
 "A_position_array": (0x030421EC, "488b9188010000"),
 "A_position_x": (0x0304220C, "f30f109988000000"),
 "A_position_z": (0x0304221F, "f30f109190000000"),
 "B_iteration_count": (0x03043E6C, "8b8114010000"),
 "B_iteration_array": (0x03043E65, "488bb118010000"),
 "B_entry": (0x03043E7F, "488b3e"),
 "B_entry_virtual_440": (0x03043E99, "ff9040040000"),
 "A_nested_array": (0x03043FBC, "488bb088010000"),
 "A_nested_count": (0x03043FC3, "8b8084010000"),
 "A_nested_entry": (0x03043FD2, "488b0e"),
 "A_entry_virtual_58": (0x03043FE1, "ff5058"),
 "child_array": (0x03043FED, "4c8bb0e80b0000"),
 "child_count": (0x03043FF4, "8b80e40b0000"),
 "child_entry": (0x03044003, "498b3e"),
 "unit_after_queue_update": (0x03043784, "e89f3e0000"),
 "later_virtual_20": (0x03047659, "ff5020"),
}
CALLS = {
 "unit_to_position_aggregate": (0x03043722, 0x030421A4),
 "unit_to_group_coordinate": (0x0304372A, 0x0302AE0C),
 "unit_to_queue": (0x03043770, 0x0304433C),
 "unit_to_post_order_callbacks": (0x03043784, 0x03047628),
}

def verify(exe: Path):
 sha = digest_file(exe)
 if sha != TARGET_SHA256:
  raise ValueError("EXE_SHA256_MISMATCH")
 with exe.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
  sections = pe_sections(mm)
  ins, edges = [], []
  for name, (rva, hexstr) in GUARDS.items():
   expected = bytes.fromhex(hexstr)
   if read_executable(mm, sections, rva, len(expected)) != expected:
    raise ValueError("BYTE_MISMATCH:"+name)
   ins.append({"name":name, "rva":hex(rva), "bytes":hexstr})
  for name, (site, target) in CALLS.items():
   got = e8_target(site, read_executable(mm, sections, site, 5))
   if got != target:
    raise ValueError("CALL_MISMATCH:"+name)
   edges.append({"name":name, "rva":hex(site), "to":hex(target)})
 return {
  "schema":"bsc.n1_9_0_3_distinct_member_layers.v1",
  "exe_sha256":sha, "instructions":ins, "direct_calls":edges,
  "proved":"same root has two distinct pointer/count collections; one has a nested virtual child array",
  "unknown":["actual soldier and formation-slot types", "model heading/arrival writer",
             "intra-unit crowding cause", "runtime ABI and lifetime"],
  "runtime_patch_authorized":False,
 }

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--exe", required=True, type=Path)
 p.add_argument("--report", required=True, type=Path)
 a=p.parse_args()
 if a.exe.resolve()==a.report.resolve():
  p.error("refusing to overwrite EXE")
 record=verify(a.exe)
 a.report.parent.mkdir(parents=True,exist_ok=True)
 a.report.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
 print("STATIC",len(record["instructions"]),"guards",len(record["direct_calls"]),"calls; PATCH=false")

if __name__=="__main__":
 main()
