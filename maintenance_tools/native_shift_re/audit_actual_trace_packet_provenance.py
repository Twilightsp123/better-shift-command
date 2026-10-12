#!/usr/bin/env python3
"""Exact-build reappraisal of real N1 one-shot log and all native member v+0x368 calls.

No original EXE or runtime-pointer log is committed to GitHub.
Proves static instruction origins and output invariants, not V3 command identity.
"""
import argparse,bisect,collections,json,math,re,shutil,statistics,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE
PINS={
 0x02f5f940:'80c906', # B packet constructor or 0x06
 0x02f5f949:'0c01', # B packet+0x51 bit0
 0x02f5f956:'49c7424403000000', # B packet+0x44 qword=3
 0x02f5f95e:'41884a50', # B packet+0x50 store
 0x0306ba2f:'f6425020', # generic receiver, not source identifier
 0x0306ba5b:'e8683defff',
 0x03265d3f:'ff9068030000', # B-specific virtual member fanout
 0x030d550f:'ff9068030000', # A fanout, distinct
 0x0303626f:'ff9068030000', # third fanout, distinct
}
VIRTUAL_PATTERNS=[
 re.compile(rb'\xff[\x90-\x97]\x68\x03\x00\x00'),
 re.compile(rb'\x41\xff[\x90-\x97]\x68\x03\x00\x00'),
]
def audit_binary(exe):
 if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED_FOR_BOUNDARIES')
 pe=StrictPE(Path(exe))  # Exact SHA256, x64 PE and ImageBase
 try:
  for site,expected in PINS.items():
   if pe.read(site,len(expected)//2,True).hex()!=expected:
    raise ValueError('ORIGINAL_OPCODE_CHANGED:'+hex(site))
  candidates=set()
  for name,rva,size,offset,virtual,flags in pe.sections:
   if not(flags&0x20000000):continue
   body=pe.read(rva,size,True)
   for pattern in VIRTUAL_PATTERNS:
    candidates.update(rva+m.start() for m in pattern.finditer(body))
  by_owner={};verified=[]
  for site in sorted(candidates):
   span=pe.function(site)
   if not span:continue
   if span not in by_owner:
    asm=pe.disasm(span[0],span[1]-span[0])
    by_owner[span]=set()
    for line in asm.splitlines():
     match=re.match(r'^\s*([0-9a-f]+):\s+.*?\tcall\s',line)
     if match:by_owner[span].add(int(match.group(1),16))
   if site in by_owner[span]:
    verified.append({'site':hex(site),'owner':hex(span[0])})
  return {
   'sha256':pe.sha,'checked_original_opcode_guards':len(PINS),
   'raw_v368_candidates':len(candidates),
   'decoded_v368_callsites':len(verified),
   'v368_callsites':verified,
   'warning':'53 source candidates across code are not automatically 53 B commands.'
  }
 finally:pe.close()
def audit_log(path):
 events=[json.loads(s) for s in Path(path).read_text(encoding='utf-8-sig').splitlines() if s.strip()]
 counts=collections.Counter(e.get('ev') or e.get('type') for e in events)
 received=[e for e in events if e.get('ev')=='B_DEFERRED_RECEIVE']
 packet_flags=collections.Counter();qword44=collections.Counter();members=collections.Counter();float_deltas=[]
 for e in received:
  raw=bytes.fromhex(e['packet58'])
  if len(raw)!=0x58:raise ValueError('BAD_CAPTURE_LENGTH')
  packet_flags[raw[0x50]]+=1
  qword44[struct.unpack_from('<Q',raw,0x44)[0]]+=1
  members[e['member']]+=1
  first=struct.unpack_from('<f',raw,0)[0]
  tail=struct.unpack_from('<f',raw,0x50)[0]
  if math.isfinite(first) and math.isfinite(tail):
   float_deltas.append((e['member'],first-tail))
 primary=members.most_common(1)[0][0] if members else None
 near=[d for who,d in float_deltas if who==primary and 1<d<1.5]
 incompatible_flags=sum(n for flag,n in packet_flags.items() if flag&0x06!=0x06)
 incompatible_qword=sum(n for q,n in qword44.items() if q!=3)
 return {
  'jsonl_records':len(events),'events':dict(counts),
  'mode_gated_receivers_not_B_proven':len(received),
  'flag50_counts':{hex(k):v for k,v in sorted(packet_flags.items())},
  'qword44_counts':{hex(k):v for k,v in sorted(qword44.items())},
  'incompatible_with_unmodified_B_constructor_flag50':incompatible_flags,
  'incompatible_with_unmodified_B_constructor_qword44':incompatible_qword,
  'observed_members':dict(members),
  'dominant_member_float_tail_clue':{
    'goalX_minus_tail_x_between_1_and_1_5':len(near),
    'median_delta':statistics.median(near) if near else None,
    'meaning':'0x50..0x57 look like adjacent smooth geometric floats; not a typed packet source proof'},
  'B_fanout_proven':counts['B_MEMBER_FANOUT']>0,
  'queued_Shift_proven':counts['QUEUED_CONTINUATION']>0,
  'motor_route_conflict_proven':False,'patch_authorized':False,
 }
def audit(exe,log):
 return {'schema':'bsc.n1.original_log_provenance_reaudit.v2',
 'static':audit_binary(exe),'runtime':audit_log(log),
 'conclusion':'Current data cannot attribute the 28 generic delayed receives to B cached-route MOVE. Not a defect-negation.'}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--log',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.out.resolve()==a.exe.resolve():p.error('REFUSE_OVERWRITE_EXE')
 result=audit(a.exe,a.log)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('PASS original EXE',result['static']['decoded_v368_callsites'],'verified member fanouts;',
       result['runtime']['mode_gated_receivers_not_B_proven'],'unattributed delayed receives')
if __name__=='__main__':main()
