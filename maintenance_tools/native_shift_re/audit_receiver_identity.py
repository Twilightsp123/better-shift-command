#!/usr/bin/env python3
"""Original WH3: exact receiver argument and virtual-slot identity re-audit.

One matching vtable OFFSET does not imply the owning object is a soldier.
The historical JSONL lacks native caller return addresses and thus cannot
uniquely attribute the captured packet to a MOVE/Shift sender.
READ ONLY. Never redistribute original EXE or live pointer traces.
"""
import argparse,collections,hashlib,json,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

GUARDS={
 "receiver_RDX_to_RBX":(0x0306ba12,"488bda"),
 "receiver_tests_packet_50":(0x0306ba2f,"f6425020"),
 "receiver_deferred_RBX_to_R8":(0x0306ba51,"4c8bc3"),
 "receiver_deferred_call":(0x0306ba5b,"e8683defff"),
 "B_ctor_sets_bit_mask_06":(0x02f5f940,"80c906"),
 "B_ctor_sets_44_to_3":(0x02f5f956,"49c7424403000000"),
 "A_member_virtual_call":(0x030d550f,"ff9068030000"),
 "B_member_virtual_call":(0x03265d3f,"ff9068030000"),
 "different_object_virtual_call":(0x0134a11b,"ff9068030000"),
 "different_object_reads_result_bool":(0x0134a121,"8ad8"),
 "different_object_getter_code_0x67":(0x0134a108,"ba67000000"),
 "other_class_virtual_call":(0x02a9029e,"ff9068030000"),
 "other_class_dispatch_factory":(0x02a90290,"e8afc40100"),
 "member_receiver_entry":(0x0306b9f0,"48895c2410"),
 "non_actor_getter_A":(0x02156045,"ff9068030000"),
 "non_actor_getter_A_tests_AL":(0x02156052,"84c0"),
 "non_actor_getter_B":(0x0279929b,"ff9068030000"),
 "non_actor_getter_B_tests_AL":(0x027992a1,"84c0"),
 "non_actor_getter_C":(0x02824291,"ff9068030000"),
 "non_actor_getter_C_tests_AL":(0x02824297,"84c0"),
 "other_class_return_as_pointer":(0x01ae122d,"ff9068030000"),
 "other_class_moves_RAX_to_RDI":(0x01ae123e,"488bf8"),
}
def audit(exe,log):
 pe=StrictPE(exe)
 try:
  for name,(site,raw) in GUARDS.items():
   if pe.read(site,len(raw)//2,True).hex()!=raw:
    raise ValueError("GUARD_FAILED:"+name)
  items=[json.loads(x) for x in Path(log).read_text(encoding="utf-8-sig").splitlines() if x.strip()]
  counts=collections.Counter(x.get("ev") or x.get("type") for x in items)
  packets=collections.Counter();types44=collections.Counter();actors=collections.Counter()
  return_addresses=0
  for row in items:
   if row.get("ev")!="B_DEFERRED_RECEIVE":continue
   blob=bytes.fromhex(row["packet58"])
   if len(blob)!=88:raise ValueError("BAD_PACKET_LENGTH")
   packets[blob[0x50]]+=1
   types44[struct.unpack_from("<Q",blob,0x44)[0]]+=1
   actors[row.get("member")]+=1
   return_addresses+=int("callerReturnRva" in row)
  return dict(schema="bsc.n1.receiver-identity-original.v1",
   original_exe_sha256=pe.sha,original_byte_guards=len(GUARDS),
   real_record_count=len(items),events=dict(counts),
   receiver_calls_mislabelled_as_B=counts["B_DEFERRED_RECEIVE"],
   packet_50=dict(packets),packet_44=dict(types44),
   actor_count=len(actors),max_receives_one_actor=max(actors.values(),default=0),
   original_caller_return_address_events=return_addresses,
   proven=[
     "receiver 0x0306BA12 preserves native RDX in RBX and 0x0306BA51 forwards RBX; register sampling was not the reason for the packet mismatch",
     "known B constructor at 0x02F5F940 OR 0x06 and 0x02F5F956 stores qword 3 at packet+0x44",
     "0x0134A11B calls virtual+0x368 but uses AL as a Boolean in a separate property-query context: raw slot matches must be typed before called actor senders"],
   not_proven=["historical packet caller return addresses were never recorded",
     "none of captured deferred calls is source-linked to an original queued Shift unit",
     "a packet containing floating geometry after +0x50 is not itself proof of a particular struct type"],
   native_patch_authorized=False)
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--exe",type=Path,required=True)
 p.add_argument("--log",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 if a.out.resolve()==a.exe.resolve():p.error("NO_EXE_OVERWRITE")
 r=audit(a.exe,a.log)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("PASS",r["original_byte_guards"],"original guards; historical sender not identifiable")
if __name__=="__main__":main()
