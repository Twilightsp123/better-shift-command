#!/usr/bin/env python3
"""WH3 9.0.3 exact-EXE virtual+0x388 stack packet provenance; no game patch.

Three call sites take RDX from a local stack record, not the address of
MOVE task+0x160. Upstream data provenance remains an open question.
"""
import argparse,json,re,shutil,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE
SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
OWNER=(0x03010724,0x0301120E)
PINS={int(a,16):b for a,b in (line.split() for line in """
03010724 488bc4
0301073f 488da8d8feffff
03010746 4881ece8010000
03010ae4 e8bb3d0900
03010afc 488d5500
03010b00 488b07
03010b03 488bcf
03010b06 804d6c20
03010b0a f30f114558
03010b0f ff9088030000
03010d71 e82e3b0900
03010d9b 488d5500
03010d9f 488b07
03010da2 488bcf
03010da5 804d6c20
03010da9 f30f114558
03010dae ff9088030000
0301104d e852380900
03011065 488d5500
03011069 488b07
0301106c 488bcf
0301106f 804d6c20
03011073 f30f114558
03011078 ff9088030000
""".strip().splitlines())}
PACKETS={
0x03010B0F:(0x03010AFC,0x03010B00,0x03010B03,0x03010B06,0x03010B0A),
0x03010DAE:(0x03010D9B,0x03010D9F,0x03010DA2,0x03010DA5,0x03010DA9),
0x03011078:(0x03011065,0x03011069,0x0301106C,0x0301106F,0x03011073)}
SOURCES={0x03010AE4:0x030A48A4,0x03010D71:0x030A48A4,0x0301104D:0x030A48A4}
def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  if pe.sha!=SHA:raise ValueError('WRONG_EXE')
  if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
  if pe.function(OWNER[0])!=OWNER:raise ValueError('FRAME_UNWIND_BOUNDARY_CHANGED')
  asm=pe.disasm(OWNER[0],OWNER[1]-OWNER[0])
  starts={int(m.group(1),16) for line in asm.splitlines()
   if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line))}
  for site,raw in PINS.items():
   if site not in starts or pe.read(site,len(raw)//2,True).hex()!=raw:
    raise ValueError('INSTRUCTION_DRIFT:'+hex(site))
  for site,dest in SOURCES.items():
   raw=pe.read(site,5,True)
   if raw[0]!=0xE8 or site+5+struct.unpack_from('<i',raw,1)[0]!=dest:
    raise ValueError('SOURCE_CALL_DRIFT:'+hex(site))
  for site,seq in PACKETS.items():
   if not all(OWNER[0]<=at<site<OWNER[1] for at in seq):
    raise ValueError('WRONG_FRAME_OR_ORDER:'+hex(site))
   if PINS[site]!='ff9088030000' or PINS[seq[0]]!='488d5500':
    raise ValueError('V388_RDX_STACK_RECORD_CHANGED:'+hex(site))
   if (PINS[seq[1]],PINS[seq[2]])!=('488b07','488bcf'):
    raise ValueError('MEMBER_RECEIVER_CHANGED:'+hex(site))
   if (PINS[seq[3]],PINS[seq[4]])!=('804d6c20','f30f114558'):
    raise ValueError('STACK_PACKET_FIELDS_CHANGED:'+hex(site))
  return dict(
   schema='bsc.n1.virtual388_stack_packet_provenance.v1',
   exe_sha256=pe.sha,grade='EXACT_ORIGINAL_EXE_STATIC',
   exact_instructions=len(PINS),direct_source_E8=len(SOURCES),
   bounded_virtual388_stack_dispatches=len(PACKETS),
   owner='0x03010724',
   frame_setup='RBP=entry RSP-0x128; reserve 0x1E8 bytes',
   pointer='RDX=LEA [RBP+0] before each virtual+0x388 call',
   local_fields='[RBP+0x6C] OR 0x20, [RBP+0x58] float32',
   callsites=[f'0x{x:08X}' for x in PACKETS],
   caller_stack_offset_plus158_is_not_MOVE_task_plus158=True,
   direct_input_is_MOVE_task_plus160=False,
   upstream_original_move_task_pointer_identity_proven=False,
   receiver_dynamic_vtable_identity_unobserved=True,
   native_patch_authorized=False)
 finally:pe.close()
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error('NEVER_OVERWRITE_EXE')
 r=audit(a.exe)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('PASS',r['exact_instructions'],'opcode starts,',r['bounded_virtual388_stack_dispatches'],'stack packets; NO PATCH')
