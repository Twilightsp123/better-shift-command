#!/usr/bin/env python3
"""BSC R53: SHA-guarded, read-only investigation of queued MOVE heading provenance.

This is a static code audit, NOT a measured Shift trajectory and NOT a patch.
"""
import argparse, bisect, hashlib, json, re, struct, subprocess, tempfile
from pathlib import Path

EXPECTED_SHA = '9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496'
BASE = 0x140000000
# Independently frozen new-build instruction encodings (RVA, complete instruction bytes).
PINS = {
 0x0302AE74:'488bc4',
 0x0302AF5F:'f6839a00000002',  # MOVEslot+0x9a & 0x2
 0x0302AF6D:'0f840a010000',    # slot bit2=0 -> live Group heading
 0x0302AF7A:'440fb78398000000',# saved slot+0x98 heading
 0x0302AF95:'e816cafeff',     # route config shared
 0x0302B0BC:'488b89f8320000',# current UnitRoot Group
 0x0302B0C3:'4881c1380b0000',# Group+0xb38
 0x0302B0CA:'e8bd4fd2ff',    # Group geometry fetch
 0x0302B0D9:'e86e700f00',    # route input geometry
 0x0302B0E7:'f3410f5c02',    # x difference
 0x0302B0EC:'f3410f5c4a04', # z difference
 0x0302B0F2:'e8958915fe',    # angle-like helper
 0x0302B0F7:'f30f590561718f00', # 65536/(2*pi) conversion factor
 0x0302B0FF:'e84c294cfd',    # float -> compact code helper
 0x0302B119:'440fb7c0',      # R8d = AX compact heading
 0x0302B126:'e885c8feff',    # same route config
 0x0302B191:'4c897590',      # shortTask descriptor alias of MOVEslot+0xa0
 0x0302B1B3:'e8c065f0ff',    # create shortTask
 0x030179B0:'488bc4',
 0x030179C7:'410fb7d8',      # save r8w in ebx
 0x030179DF:'4180b894000000',# group/context gate
 0x030179ED:'83b98401000000',# Root+0x184 route build gate
 0x03017A28:'80bc24d8000000', # stack flag selects richer builder
 0x03017A69:'440fb7cb',      # pass preserved angle in R9
 0x03017A79:'e8bea00d00',    # call route builder
 0x03017ABB:'48898770020000',# root+0x270 route update
 0x0303777D:'804f5a06',      # conditional descriptor+0x5a flag normalization
 0x03037791:'66897758',      # conditional descriptor+0x58 heading write
 0x0312214C:'4883ec28',     # local or reference-frame goal position resolver
 0x03122153:'488b4918',     # input goal reference object
 0x0312215C:'4883c118',     # matrix reference offset
 0x03122160:'e803b5e1ff',   # affine frame transform helper
 0x03122167:'418b00',       # direct xyz fallback
}
EDGES = {
 0x0302AF95:0x030179B0,
 0x0302B0CA:0x02D5008C,
 0x0302B0D9:0x0312214C,
 0x0302B0F2:0x01183A8C,
 0x0302B0FF:0x004EDA50,
 0x0302B126:0x030179B0,
 0x0302B1B3:0x02F31778,
 0x03017A79:0x030F1B3C,
 0x03122160:0x02F3D668,
}
JCC={0x0302AF6D:0x0302B07D}
RAD_TO_U16_RVA=0x03922260

class PE:
 def __init__(self, path):
  self.path=Path(path)
  h=hashlib.sha256()
  with self.path.open('rb') as f:
   while b:=f.read(2**20):h.update(b)
  if h.hexdigest()!=EXPECTED_SHA:raise ValueError('EXE_SHA_DRIFT')
  self.data=self.path.read_bytes()
  d=self.data
  if d[:2]!=b'MZ':raise ValueError('MZ_MISSING')
  p=struct.unpack_from('<I',d,0x3c)[0]
  if d[p:p+4]!=b'PE\0\0':raise ValueError('PE_MISSING')
  machine,count=struct.unpack_from('<HH',d,p+4)
  if machine!=0x8664:raise ValueError('NOT_X64')
  opt=p+24
  if struct.unpack_from('<Q',d,opt+24)[0]!=BASE:raise ValueError('IMAGEBASE_CHANGED')
  sht=opt+struct.unpack_from('<H',d,p+20)[0]
  self.sections=[]
  for k in range(count):
   q=sht+40*k
   name=d[q:q+8].split(b'\0')[0].decode('latin-1')
   vsize,va,rsize,raw=struct.unpack_from('<IIII',d,q+8)
   chars=struct.unpack_from('<I',d,q+36)[0]
   self.sections.append((name,va,rsize,raw,chars))
  # WH3 stores x64 RUNTIME_FUNCTION records inside a nonstandard section,
  # so use PE OptionalHeader DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION].
  exception_rva,exception_size=struct.unpack_from('<II',d,opt+112+3*8)
  if not exception_rva or exception_size < 12 or exception_size>6_000_000:raise ValueError('BAD_EXCEPTION_DIR')
  pdata_bytes=self.read(exception_rva,exception_size)
  self.funcs=[]
  for i in range(0,len(pdata_bytes)-11,12):
   start,end,unwind=struct.unpack_from('<III',pdata_bytes,i)
   if start<end and unwind and self.is_exec(start):self.funcs.append((start,end))
  self.funcs.sort()
  self.starts=[s for s,_ in self.funcs]
 def read(self,rva,n):
  for name,va,size,raw,ch in self.sections:
   if va<=rva and rva+n<=va+size:return self.data[raw+(rva-va):raw+(rva-va)+n]
  raise ValueError(f'UNMAPPED_RVA:{rva:x}')
 def is_exec(self,rva):
  return any(va<=rva<va+size and ch & 0x20000000 for _,va,size,_,ch in self.sections)
 def owner(self,rva):
  i=bisect.bisect_right(self.starts,rva)-1
  if i<0:return None
  start,end=self.funcs[i]
  return (start,end) if start<=rva<end else None
 def instructions(self,owner):
  start,end=owner
  with tempfile.NamedTemporaryFile() as f:
   f.write(self.read(start,end-start));f.flush()
   out=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel',
    '--no-show-raw-insn',f'--adjust-vma=0x{start:x}',f.name],capture_output=True,text=True,check=True).stdout
  instructions={}
  for line in out.splitlines():
   m=re.match(r'^\s*([0-9a-fA-F]+):\s+(.+)$',line)
   if m:instructions[int(m.group(1),16)]=m.group(2)
  return instructions

def audit(exe):
 pe=PE(exe)
 owners={}
 for at,raw in PINS.items():
  if not pe.is_exec(at) or pe.read(at,len(bytes.fromhex(raw)))!=bytes.fromhex(raw):
   raise ValueError('OPCODE_DRIFT:'+hex(at))
  owner=pe.owner(at)
  if not owner:raise ValueError('MISSING_UNWIND_OWNER:'+hex(at))
  if owner not in owners:owners[owner]=pe.instructions(owner)
  if at not in owners[owner]:raise ValueError('MID_INSTRUCTION:'+hex(at))
 for at,to in EDGES.items():
  b=pe.read(at,5)
  if b[0]!=0xE8 or at+5+struct.unpack_from('<i',b,1)[0]!=to:raise ValueError('DIRECT_CALL_DRIFT:'+hex(at))
 for at,to in JCC.items():
  b=pe.read(at,6)
  if b[:2]!=b'\x0f\x84' or at+6+struct.unpack_from('<i',b,2)[0]!=to:raise ValueError('BRANCH_DRIFT:'+hex(at))
 factor=struct.unpack('<f',pe.read(RAD_TO_U16_RVA,4))[0]
 expected=65536/(2*3.141592653589793)
 if abs(factor-expected)>0.002:raise ValueError('ANGULAR_SCALE_CHANGED')
 # Check the native ABI transfer: each branch sets R8 before the SAME route builder.
 # The first uses slot+0x98, the second an ANGLE converted to ushort.
 decoded=owners[pe.owner(0x0302AF95)]
 for source,call in [(0x0302AF7A,0x0302AF95),(0x0302B119,0x0302B126)]:
  for at,op in decoded.items():
   if source<at<call and re.match(r'\s*(?:mov|xor|lea|add|sub|pop|and|or|shl|shr|movzx)\s+r8(?:b|w|d)?\b',op):
    raise ValueError('HEADING_ARG_CLOBBERED:'+hex(at))
 return dict(schema='bsc.n1.R53.native_queued_turn_heading.v1',proof='EXACT_USER_EXE_STATIC',
   sha256=EXPECTED_SHA,executable_bytes_verified=len(PINS),verified_call_targets=len(EDGES),
   verified_branches=len(JCC),unwind_functions=len(owners),
   branch_slot_flag='MOVEslot+0x9A bit 0x02',
   saved_source='slot+0x98 ushort -> route_config R8W',
   live_source='UnitRoot+0x32F8 Group spatial point compared to goal resolved via frame-aware 0x0312214C -> XZ displacement -> angle helper -> uint16 -> route_config R8W',
   same_route_builder='0x030179B0',route_angle_forwarded='0x030179C7 R8W -> EBX; 0x03017A69 BX -> R9D; 0x03017A79 call 0x030F1B3C',
   new_route_binding_site='0x03017ABB writes UnitRoot+0x270 on guarded branch',
   heading_units_per_radian=factor,heading_full_circle_units=65536,
   route_commit_conditional=True,
   two_heading_sources_for_queued_move=True,
   label_shift_exclusively=False,live_player_crowding_cause_proven=False,
   native_gameplay_patch_authorized=False)

def main():
 cli=argparse.ArgumentParser()
 cli.add_argument('--exe',required=True,type=Path)
 cli.add_argument('--out',type=Path)
 opt=cli.parse_args()
 if opt.out and opt.exe.resolve()==opt.out.resolve():cli.error('NO_OVERWRITE_EXE')
 x=audit(opt.exe)
 if opt.out:opt.out.write_text(json.dumps(x,indent=2)+'\n')
 print('PASS',x['executable_bytes_verified'],'full instructions',x['verified_call_targets'],'calls',x['verified_branches'],'branch',x['unwind_functions'],'unwind funcs')
if __name__=='__main__':main()
