#!/usr/bin/env python3
"""WH3 9.0.3: successful native MOVE continuation clears old shortTask stack.

Read-only SHA-pinned static audit; no executable modification, no game hooks.
In reentry state manager+0x250=0, clear is skipped. Other queue paths differ.
"""
import argparse,json,re,shutil,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE
import audit_move_shorttask_resume_gate as prior

SHA="518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
PINS={int(a,16):bytes.fromhex(b) for a,b in (line.split() for line in """
0304433C 488bc4
03044539 83bb102d000001
03044540 0f868a000000
03044546 488d7b10
0304455F 488b01
03044562 ff5040
03044568 4885c0
0304456B 7463
0304458E 498b4618
03044596 ff5038
0304459B 7433
0304459D ff4618
030445A8 488bd6
030445AB ff5048
030445B1 e85ab7f0ff
030445B6 488b4b08
030445BA 33d2
030445BC e89bb7f0ff
030445C1 488b0b
030445C4 488b89f8320000
030445CB e8f4b40800
030445D0 488bcb
030445D3 e8d8edffff
02F4FD5C 48895c2408
02F4FD70 80b95002000000
02F4FD7C 745b
02F4FD7E c6815002000000
02F4FD85 399140020000
02F4FD8B 7645
02F4FD8D 488da900020000
02F4FD94 8b7d40
02F4FD9C 488b4cfd00
02F4FDA6 488b01
02F4FDA9 ba01000000
02F4FDAE ff10
02F4FDB0 8b44fd08
02F4FDB4 298344020000
02F4FDBA 8b44fd08
02F4FDBE 018348020000
02F4FDC4 ff8b40020000
02F4FDCA 39b340020000
02F4FDD0 77c2
02F4FDD2 c6835002000001
03043537 66c781500200000100
03043540 8b8940020000
03043550 80bb5002000001
0304357B 7521
0304357D ff5210
03043583 807e1801
03043589 8bd7
0304358E e8c9c7f0ff
0304359E ff5218
03043635 c6835002000001
03043769 488d8b78020000
03043770 e8c70b0000
03043775 488d8ba02f0000
0304377C e89ffdffff
030433B0 48895c2408
030433BF 83b9102d000000
030433E3 e83c000000
03043424 48895c2408
0304342E 80b91801000001
03043456 488b4910
0304345A 33d2
0304345C e8fbc8f0ff
03043461 488b07
0304346B ff5008
03026084 488b5318
03026091 e81a9ff0ff
030260AF e88066f0ff
030CFAC4 4053
030CFAE4 e953c40000
""".strip().splitlines())}
E8={0x030445B1:0x02F4FD10,0x030445BC:0x02F4FD5C,0x030445CB:0x030CFAC4,
0x030445D3:0x030433B0,0x030433E3:0x03043424,0x0304345C:0x02F4FD5C,
0x03043770:0x0304433C,0x0304377C:0x03043520,0x0304358E:0x02F4FD5C,
0x03026091:0x02F2FFB0,0x030260AF:0x02F2C734}
E9={0x030CFAE4:0x030DBF3C}
BRANCH={0x03044540:(0x0F86,0x030445D0),0x0304456B:(0x74,0x030445D0),
0x0304459B:(0x74,0x030445D0),0x02F4FD7C:(0x74,0x02F4FDD9),
0x02F4FD8B:(0x76,0x02F4FDD2),0x02F4FDD0:(0x77,0x02F4FD94)}
VTABLE={0x0390B4F8:0x03025D70,0x0390B528:0x008D3350,
0x0390B530:0x03039FB0,0x0390B538:0x03040864,
0x03ABBE28:0x02F561E8,0x03ABBE30:0x008D3280}

def branch_target(site,code,opcode):
 if opcode<0x100:
  if len(code)!=2 or code[0]!=opcode:raise ValueError('WRONG_SHORT_BRANCH')
  return site+2+struct.unpack_from('<b',code,1)[0]
 if len(code)!=6 or code[:2]!=struct.pack('>H',opcode):raise ValueError('WRONG_NEAR_BRANCH')
 return site+6+struct.unpack_from('<i',code,2)[0]

def simulate(*,queue_count,provider_returns_old,successor_accepts,manager_enabled,old_tasks,next_activation_adds_task):
 """Synthetic guard model, not a game or collision simulation."""
 success=bool(queue_count>1 and provider_returns_old and successor_accepts)
 stack=list(old_tasks)
 if success and manager_enabled:stack=[]
 if next_activation_adds_task:stack.append('new_short_task')
 return dict(handoff_success_path=success,cleanup_requested=success,
  cleanup_accepted_by_manager=bool(success and manager_enabled),
  remaining_old_short_tasks=[x for x in stack if x!='new_short_task'],
  old_task_can_resume_by_later_top_pop=any(x!='new_short_task' for x in stack),
  this_is_a_synthetic_fixture_not_WH3_runtime=True)

def audit(exe):
 old=prior.audit(exe)  # pins queue+8 -> typed UnitRoot+0x2FA0 manager
 if not old['manager_type_proven']:raise ValueError('MANAGER_POINTER_NOT_TYPED')
 pe=StrictPE(Path(exe))
 try:
  if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
  if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
  caches={}
  for at,code in PINS.items():
   if pe.read(at,len(code),True)!=code:raise ValueError('OPCODE_DRIFT:'+hex(at))
   owner=pe.function(at)
   if not owner:raise ValueError('UNWIND_OWNER_MISSING:'+hex(at))
   if owner not in caches:
    dis=pe.disasm(owner[0],owner[1]-owner[0])
    caches[owner]={int(m.group(1),16) for line in dis.splitlines()
     if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line))}
   if at not in caches[owner]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for table,op in ((E8,0xe8),(E9,0xe9)):
   for at,target in table.items():
    raw=pe.read(at,5,True)
    if raw[0]!=op or at+5+struct.unpack_from('<i',raw,1)[0]!=target:
     raise ValueError('CALL_OR_JUMP_DRIFT:'+hex(at))
  for at,(op,target) in BRANCH.items():
   if branch_target(at,pe.read(at,2 if op<256 else 6,True),op)!=target:
    raise ValueError('BRANCH_DRIFT:'+hex(at))
  for at,target in VTABLE.items():
   if struct.unpack('<Q',pe.read(at,8))[0]!=pe.base+target:
    raise ValueError('VTABLE_DRIFT:'+hex(at))
  if pe.read(0x008D3280,3,True)!=bytes.fromhex('c20000'):
   raise ValueError('SHORTTASK_NONLAST_CALLBACK_DRIFT')
  return dict(schema='bsc.n1.queued_move_success_manager_stack_clear.v1',
   sha256=pe.sha,proof_level='EXACT_ORIGINAL_EXE_STATIC',
   checked_opcode_instruction_starts=len(PINS),unwind_owners=len(caches),
   direct_E8=len(E8),direct_E9=len(E9),branch_targets=len(BRANCH),vtable_entries=len(VTABLE),
   old_big_task_handoff='0x030445AB calls next MOVE+0x48',
   old_move_slot_pop='0x030445B1 -> 0x02F4FD10',
   same_manager_pointer='[queue+0x08] at 0x030445B6',
   requested_full_clear='0x030445BA EDX=0; 0x030445BC -> 0x02F4FD5C(manager,0)',
   group_cleanup_after='0x030445CB -> 0x030CFAC4',
   next_slot_activation_after='0x030445D3 -> 0x030433B0 (conditional)',
   manager_plus250_zero_skips_cleanup=True,
   manager_plus250_nonzero_decrements_count_to_zero=True,
   normal_unit_order='queue 0x03043770 then task manager tick 0x0304377C',
   normal_manager_tick_return_sets_plus250_one=True,
   old_short_task_can_resume_after_normal_successful_clear=False,
   reentrant_manager_guard_zero_exception_unresolved=True,
   failed_handoff_other_paths_not_excluded=True,
   physical_crowding_cause_proven=False,native_patch_authorized=False)
 finally:pe.close()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error('NEVER_OVERWRITE_EXE')
 result=audit(a.exe)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PASS',result['checked_opcode_instruction_starts'],'original instruction guards; no patch')
