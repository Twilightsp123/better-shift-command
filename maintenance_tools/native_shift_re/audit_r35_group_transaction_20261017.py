#!/usr/bin/env python3
"""BSC R35: read-only, SHA-scoped WH3 Group/packet transaction audit.

Purpose: constrain what a MOVE shortTask actually binds at creation, what Group is
consulted at packet dispatch, the A/B timing split, and which checks come later.
This is not a gameplay bug proof, a native patch, or an injectable observer.
"""
import argparse,bisect,hashlib,json,mmap,re,struct,subprocess,tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
SHA='9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496'
IMAGE_BASE=0x140000000
SIZED=232531920
PIN_FILE=HERE/'r35_pins.txt'
LEAF_GROUPS={'descriptor_leaf','getter_leaf','clear_slot_leaf'}
# A small positive callgraph; never equate static reachability with real Shift hits.
E8={
 0x0302B1B3:0x02F31778, 0x02F317C8:0x02F31878,
 0x02F5B400:0x0327ECA4, 0x02F5B42D:0x03268CEC, 0x02F5B532:0x030D4B50,
 0x02F5B580:0x030D4B50,0x02F5B5AD:0x02D678FC,
 0x0327ECC6:0x02DC7E30,0x0327ED17:0x030DA5D8,
 0x0327ED28:0x02F3F0FC,0x0327ED3C:0x03268920,
 0x030DA681:0x03102B28,0x030DA68F:0x030DA51C,
 0x03268D24:0x03268BD8,0x03268A6B:0x0306DC90,0x032862A6:0x032862C4,
 0x03286445:0x0326A994,
}
JUMPS={
 0x02F5B405:0x02F5B4B3,
 0x0327ECCD:0x0327ED1E,
 0x032863B7:0x0328645E,
}
VTABLE={
 (0x03AE5820,0x10):0x03286288,
 (0x03AE5800,0x10):0x032863A0,
}

class PE:
 def __init__(self,path):
  self.path=Path(path)
  self.fp=self.path.open('rb')
  self.d=mmap.mmap(self.fp.fileno(),0,access=mmap.ACCESS_READ)
  d=self.d
  if d[:2]!=b'MZ':raise ValueError('NOT_PE_MZ')
  head=struct.unpack_from('<I',d,0x3c)[0]
  if d[head:head+4]!=b'PE\x00\x00':raise ValueError('NOT_PE_SIGNATURE')
  if struct.unpack_from('<H',d,head+4)[0]!=0x8664:raise ValueError('NOT_X64')
  opt=head+24
  if struct.unpack_from('<H',d,opt)[0]!=0x20b:raise ValueError('NOT_PE32_PLUS')
  self.base=struct.unpack_from('<Q',d,opt+24)[0]
  count=struct.unpack_from('<H',d,head+6)[0]
  off=opt+struct.unpack_from('<H',d,head+20)[0]
  self.sections=[]
  for i in range(count):
   p=off+i*40
   name=d[p:p+8].split(b'\x00')[0].decode('ascii')
   virt,va,rs,rp=struct.unpack_from('<IIII',d,p+8)
   flags=struct.unpack_from('<I',d,p+36)[0]
   self.sections.append((name,va,max(virt,rs),rs,rp,flags))
  ex,sz=struct.unpack_from('<II',d,opt+112+3*8)
  if sz%12:raise ValueError('INVALID_PDATA')
  start=self.off(ex)
  self.runtime=[struct.unpack_from('<III',d,i) for i in range(start,start+sz,12)]
  self.starts=[r[0] for r in self.runtime]
 def off(self,rva):
  for name,start,vsize,raw,off,flags in self.sections:
   if start<=rva<start+vsize:
    if rva-start>=raw:raise ValueError('UNMAPPED_FILE_DATA')
    return off+rva-start
  raise ValueError('NO_SECTION:'+hex(rva))
 def read(self,rva,n):return self.d[self.off(rva):self.off(rva)+n]
 def owner(self,addr):
  i=bisect.bisect_right(self.starts,addr)-1
  return (self.runtime[i][:2] if i>=0 and self.runtime[i][0]<=addr<self.runtime[i][1] else None)
 def is_executable(self,addr):
  for name,start,virtual,raw,off,flags in self.sections:
   if start<=addr<start+virtual:return bool(flags&0x20000000)
  return False
 def close(self):self.d.close();self.fp.close()

def get_pins():
 groups={};name=None;range_=None
 for line in PIN_FILE.read_text('utf-8').splitlines():
  m=re.match(r'^# (\w+) bounds=([0-9a-fA-F]+):([0-9a-fA-F]+)',line)
  if m:
   name=m[1];range_=(int(m[2],16),int(m[3],16));groups[name]=(range_,{});continue
  s=line.split('#',1)[0].split()
  if not s:continue
  if len(s)!=2 or name is None:raise ValueError('MALFORMED_MANIFEST')
  addr=int(s[0],16)
  if addr in groups[name][1]:raise ValueError('DUPLICATE_PIN')
  groups[name][1][addr]=bytes.fromhex(s[1])
 if len(groups)!=15 or sum(len(g[1]) for g in groups.values())!=119:
  raise ValueError('PIN_INVENTORY_DRIFT')
 return groups

def disasm(p,lo,hi):
 with tempfile.NamedTemporaryFile(suffix='.bin') as f:
  f.write(p.read(lo,hi-lo));f.flush()
  o=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel',
        '--no-show-raw-insn',f'--adjust-vma={lo}',f.name],
        text=True,capture_output=True,check=True,timeout=20)
 return {int(m[1],16):m[2] for line in o.stdout.splitlines()
         if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(.+)$',line))}

def branch_dest(site,raw):
 if raw[0]==0xe9 and len(raw)==5:return site+5+struct.unpack_from('<i',raw,1)[0]
 if raw[0]==0xeb and len(raw)==2:return site+2+struct.unpack_from('<b',raw,1)[0]
 if 0x70<=raw[0]<=0x7f and len(raw)==2:return site+2+struct.unpack_from('<b',raw,1)[0]
 if raw[0]==0x0f and 0x80<=raw[1]<=0x8f and len(raw)==6:
  return site+6+struct.unpack_from('<i',raw,2)[0]
 raise ValueError('INVALID_BRANCH_SITE:'+hex(site))

def audit(exe):
 p=PE(exe)
 try:
  if p.base!=IMAGE_BASE:raise ValueError('IMAGEBASE_MISMATCH')
  if len(p.d)!=SIZED:raise ValueError('EXE_SIZE_MISMATCH')
  with open(exe,'rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
  if actual!=SHA:raise ValueError('EXE_SHA256_MISMATCH:'+actual)
  groups=get_pins();pins={};decoded={};validated_owners=set();used_leaf=[]
  for name,(span,entries) in groups.items():
   lo,hi=span
   if lo>=hi:raise ValueError('INVALID_GROUP_RANGE')
   if name in LEAF_GROUPS:
    if p.owner(lo) is not None:raise ValueError('LEAF_PDATA_CHANGED:'+name)
    decoded[name]=disasm(p,lo,hi)
    used_leaf.append(name)
   else:
    owner=p.owner(lo)
    if owner is None or owner!=(lo,hi):raise ValueError('UNWIND_FUNCTION_DRIFT:'+name)
    if not p.is_executable(lo):raise ValueError('NONEXEC_FUNCTION')
    decoded[name]=disasm(p,lo,hi)
    validated_owners.add(owner)
   for addr,raw in entries.items():
    if addr<lo or addr>=hi:raise ValueError('PIN_OUTSIDE_GROUP:'+hex(addr))
    if addr not in decoded[name]:raise ValueError('NOT_REAL_INSTRUCTION_START:'+hex(addr))
    if p.read(addr,len(raw))!=raw:raise ValueError('CODE_DRIFT:'+hex(addr))
    if addr in pins:raise ValueError('DUPLICATE_CROSS_GROUP')
    pins[addr]=raw
  for call,target in E8.items():
   raw=pins.get(call)
   if raw is None or len(raw)!=5 or raw[0]!=0xe8:
    raise ValueError('NO_PINNED_E8:'+hex(call))
   actual=call+5+struct.unpack_from('<i',raw,1)[0]
   if actual!=target:raise ValueError('E8_TARGET_DRIFT:'+hex(call))
  for site,target in JUMPS.items():
   if branch_dest(site,pins[site])!=target:raise ValueError('CONTROL_FLOW_DRIFT:'+hex(site))
  for (table,slot),target in VTABLE.items():
   value=struct.unpack('<Q',p.read(table+slot,8))[0]
   if value!=IMAGE_BASE+target:raise ValueError('VTABLE_SLOT_DRIFT:'+hex(table))
  # The A/B direct member loops do not reload UnitRoot+0x32F8.
  for name in ('A_member_fanout','B_member_fanout'):
   if '0x32f8' in '\n'.join(decoded[name].values()).lower():
    raise ValueError('DIRECT_FANOUT_REFETCH_DRIFT:'+name)
  # The Group binding occurs immediately before dispatch, without an intervening
  # identity comparison. This says nothing about indirect guards elsewhere.
  cb=decoded['callback']
  ordering=(0x02F5B3F0,0x02F5B3F4,0x02F5B3F9,0x02F5B400,0x02F5B405,
            0x02F5B4B3,0x02F5B529,0x02F5B577)
  if not all(x in cb for x in ordering) or tuple(sorted(ordering))!=ordering:
   raise ValueError('DISPATCH_TO_POST_SWEEP_ORDER_DRIFT')
  between=[x for site,x in cb.items() if 0x02F5B3F9<site<0x02F5B400]
  if between:raise ValueError('NEW_GUARD_BEFORE_GROUP_DISPATCH')
  # Verify concrete member arrays/count and method calls (not just a search for 0x32F8).
  need={
   0x030DA55C:'cmp    DWORD PTR [rdi+0x24]',
   0x030DA561:'mov    rax,QWORD PTR [rdi+0x28]',
   0x030DA59B:'call   QWORD PTR [rax+0x368]',
   0x0326AA38:'cmp    DWORD PTR [rsi+0x24]',
   0x0326AA44:'mov    rax,QWORD PTR [rsi+0x28]',
   0x0326ABAF:'call   QWORD PTR [rax+0x368]',
  }
  lookup={at:op for group in decoded.values() for at,op in group.items()}
  for at,frag in need.items():
   if frag not in lookup.get(at,''):raise ValueError('FANOUT_OBJECT_TYPE_DRIFT:'+hex(at))
  return {
   'schema':'bsc.n1.wh3_r35_shorttask_group_packet_transaction.v1',
   'evidence':'READ_ONLY_NEW_EXE_NATIVE_STATIC',
   'sha256':actual, 'size':len(p.d),'imagebase':hex(p.base),
   'verified_full_instructions':len(pins),
   'verified_unwind_functions':len(validated_owners),
   'verified_no_unwind_leaf_regions':used_leaf,
   'verified_E8_calls':len(E8),'verified_control_transfers':len(JUMPS),
   'verified_vtable_slots':len(VTABLE),
   'queue_slot_alias':'MOVE slot+0xA0 -> descriptor+0x50 -> shortTask+0x80',
   'short_task_unit_identity':'task+0x08=UnitRoot; no frozen Group pointer field proven',
   'short_task_route_fields':'descriptor+0x42/+0x44 -> task+0x72/+0x74',
   'callback_latebind':'0x02F5B3F0 task+8 -> 0x02F5B3F9 UnitRoot+0x32F8 -> 0x02F5B400 group A/B dispatch',
   'dispatch_A':'mode true -> 0x0327ED17 calls 0x030DA5D8 -> 0x030DA51C direct member loop',
   'dispatch_B':'mode false -> 0x0327ED3C builds 0x03268920 Group B task; later B member packet sender independently verified',
   'B_fallback_live_root_route':'shortTask+8 UnitRoot -> B helper 0x03268CEC consumes UnitRoot+0x270; may differ from task construction route',
   'A_fallback_live_root_route':'0x0327ECDC and 0x0327ECE3 use Group+0xA10 UnitRoot+0x270 if input+0x30 is zero',
   'B_stage_vmethod':'new ctor 0x03AE5820 +0x10=0x03286288 handles route/task progress; 0x03AE5800 +0x10=0x032863A0 is a separate table slot, without proof of its Group instance linkage',
   'direct_member_fanout_current_group_reread':False,
   'direct_fanout_member_iteration':'Group+0x24 member count; Group+0x28 member vector; member virtual+0x368 for both A and B',
   'post_dispatch_root_group_list_comparisons':[hex(x) for x in (0x02F5B529,0x02F5B577)],
   'post_dispatch_cleanup_is_conditional':True,
   'no_pre_dispatch_group_generation_comparison_in_inspected_straight_line':True,
   'no_pre_dispatch_consistency_guard_anywhere_proven':False,
   'same_shift_instance_group_route_mismatch_proven':False,
   'runtime_B_dispatch_asynchronous_delay_quantified':False,
   'gameplay_fix':False,'patch_authorized':False,
  }
 finally:p.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=Path,required=True)
 ap.add_argument('--out',type=Path,default=HERE/'r35_static_evidence.json')
 args=ap.parse_args()
 if args.exe.resolve()==args.out.resolve():ap.error('CANNOT_OVERWRITE_GAME_EXE')
 report=audit(args.exe)
 args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
 print('R35_STATIC_PASS',report['verified_full_instructions'],'instructions',report['verified_E8_calls'],'E8',report['verified_control_transfers'],'jumps',report['verified_vtable_slots'],'vtable; NO PATCH')

if __name__=='__main__':main()
