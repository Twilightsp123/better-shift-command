#!/usr/bin/env python3
"""Fixed-original-EXE read-only audit: queued MOVE activation vs Group late bind."""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE
MANIFEST=Path(__file__).with_name('queued_latebind_pins_20261017.txt')
E8={
0x030445B1:0x02F4FD10,0x030445BC:0x02F4FD5C,0x030445CB:0x030CFAC4,
0x030445D3:0x030433B0,0x030433E3:0x03043424,
0x030434A4:0x02F3A0D4,0x0302DB8E:0x0301B8E4,
0x0301B902:0x030197A8,0x0301B91F:0x0301B834,
0x02F56404:0x03279E40,0x03279E62:0x02DC2E04,
0x03279EB3:0x030D554C,0x03279ED8:0x03263AB0}
CALLER_DIRECT={(0x030433E3,0x03043424),(0x03043406,0x02F4FD10)}
NESTED_DIRECT={(0x0304345C,0x02F4FD5C),(0x03043472,0x030376C8),(0x030434A4,0x02F3A0D4)}
def pins():
 out={}
 for line in MANIFEST.read_text('utf8').splitlines():
  a=line.split('#',1)[0].split()
  if not a:continue
  if len(a)!=2:raise ValueError('BAD_PIN')
  at=int(a[0],16)
  if at in out:raise ValueError('DUPLICATE_PIN')
  out[at]=bytes.fromhex(a[1])
 if len(out)!=39:raise ValueError('PIN_COUNT_DRIFT')
 return out
def all_e8(pe,site):
 o=pe.owner(site)
 if not o:raise ValueError('OWNER_MISSING')
 lo,hi=o[:2];out=set()
 # GNU objdump instruction starts, exact 5-byte direct E8
 starts=pe.starts_in(lo,hi)
 for at in starts:
  if pe.read(at,1)==b'\xe8':
   raw=pe.read(at,5)
   out.add((at,at+5+struct.unpack_from('<i',raw,1)[0]))
 return out
def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('EXE_DRIFT')
  d=pins();owners={}
  for at,raw in d.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:
    raise ValueError('CODE_DRIFT:'+hex(at))
   o=pe.owner(at)
   if not o:raise ValueError('NO_OWNER:'+hex(at))
   b=o[:2]
   if b not in owners:owners[b]=pe.starts_in(*b)
   if at not in owners[b]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for at,target in E8.items():
   b=d[at]
   if len(b)!=5 or b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=target:
    raise ValueError('E8_TARGET_DRIFT:'+hex(at))
  if all_e8(pe,0x030433B0)!=CALLER_DIRECT or all_e8(pe,0x03043424)!=NESTED_DIRECT:
   raise ValueError('QUEUE_ACTIVATION_EXTRA_DIRECT_EDGE')
  if d[0x0304346B]!=bytes.fromhex('ff5008') or d[0x0304348B]!=bytes.fromhex('ff5010'):
   raise ValueError('QUEUED_VIRTUAL_DISPATCH_DRIFT')
  if d[0x02F563F4]!=bytes.fromhex('488b4b08') or d[0x02F563FD]!=bytes.fromhex('488b89f8320000'):
   raise ValueError('TASK_GROUP_BINDING_IDENTITY_DRIFT')
  for at in (0x02F5627B,0x02F563FD,0x02F5649E):
   if d[at]!=bytes.fromhex('488b89f8320000'):raise ValueError('GROUP_READ_DRIFT')
  if not(0x02F563F4<0x02F563FD<0x02F56404):raise ValueError('CALLBACK_TIME_DRIFT')
  return dict(schema='bsc.n1.queued_group_latebind.v1',proof='EXACT_ORIGINAL_EXE_STATIC',
   sha256=pe.sha,opcode_starts=len(d),verified_e8=len(E8),
   verified_unwind_functions=len(owners),
   queue_activation='0x030445D3 -> 0x030433B0 -> 0x030433E3 -> 0x03043424',
   queue_has_virtual_calls=['0x0304346B +0x08','0x0304348B +0x10'],
   separate_immediate_group_builder='0x0302DB8E -> 0x0301B8E4',
   callback_late_bound_group_reads=['0x02F5627B','0x02F563FD','0x02F5649E'],
   callback_dispatch='0x02F563F4 task+8 UnitRoot -> 0x02F563FD root+0x32F8 -> 0x02F56404 0x03279E40',
   A_dispatch='0x03279EB3 -> 0x030D554C',
   B_dispatch='0x03279ED8 -> 0x03263AB0',
   direct_immediate_group_rebuild_in_queue_activator=False,
   indirect_or_future_group_rebuild_excluded=False,
   shift_instance_group_epoch_mismatch_proven=False,
   gameplay_patch_authorized=False)
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.exe.resolve()==a.out.resolve():p.error('EXE_OVERWRITE_FORBIDDEN')
 report=audit(a.exe)
 if a.out:a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf8')
 print('PASS',report['opcode_starts'],'opcodes',report['verified_e8'],'E8; NO PATCH')
if __name__=='__main__':main()
