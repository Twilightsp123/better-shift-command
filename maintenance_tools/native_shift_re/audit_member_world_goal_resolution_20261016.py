#!/usr/bin/env python3
"""Original WH3: member goal record -> optional affine world point -> movement.

Strict SHA, PE/unwind, decoded starts, E8/JCC guards. Read-only; no patch.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA
HERE=Path(__file__).resolve().parent
PINFILE=HERE/'steering_goal_frame_pins_20261016.txt'
CALLS={
 0x030822F9:0x03054B84,0x03082301:0x03088808,
 0x03055029:0x0311CED4,0x0311CEE8:0x02F38640,
 0x03088A49:0x03060D74,0x030720E3:0x0311954C,
 0x030723D9:0x0311954C,
}
BRANCHES={
 0x0311CEE2:0x0311CEEF,0x03055017:0x03055161,
 0x0305507C:0x030550B0,0x03055137:0x03055161,
 0x03088849:0x03088A4E,0x030888EA:0x03088A4E,
}
REQUIRED={
 0x0311CEDB:'488b4910',0x0311CEE4:'4883c118',
 0x0305501D:'488d8fe0010000',0x03055036:'f30f5c9f880000',
 0x02F386B4:'f30f1112',0x02F386C5:'f30f117208',
 0x02F386CE:'f30f115a04',
 0x03060E5A:'0f1183e0010000',0x03060E66:'f20f118bf00100',
 0x030720D1:'488d9338080000',0x030723CC:'488d9338080000',
}
def pins():
 d={}
 for i,line in enumerate(PINFILE.read_text('utf8').splitlines(),1):
  w=line.split('#',1)[0].split()
  if not w:continue
  if len(w)!=2:raise ValueError('INVALID_ROW:'+str(i))
  at=int(w[0],16)
  if at in d:raise ValueError('DUPLICATE_PIN')
  d[at]=bytes.fromhex(w[1])
 if len(d)!=98:raise ValueError('PIN_INVENTORY_DRIFT')
 for at,raw in REQUIRED.items():
  if d.get(at)!=bytes.fromhex(raw):raise ValueError('FIELD_OWNER_DRIFT:'+hex(at))
 return d
def affine_world(local_xyz,translation,matrix3):
 """0x02F38640: three affine axis dot-products plus translation."""
 if len(local_xyz)!=3 or len(translation)!=3 or len(matrix3)!=3 or any(len(row)!=3 for row in matrix3):
  raise ValueError('EXPECTED_3X3_AFFINE')
 return tuple(translation[r]+sum(matrix3[r][c]*local_xyz[c] for c in range(3)) for r in range(3))
def resolved_goal(local_xyz,anchor_matrix=None):
 if anchor_matrix is None:return tuple(local_xyz)
 origin,mat=anchor_matrix
 return affine_world(local_xyz,origin,mat)
def branch_target(at,raw):
 if len(raw)==2 and 0x70<=raw[0]<=0x7f:
  return at+2+struct.unpack_from('<b',raw,1)[0]
 if len(raw)==6 and raw[0]==0x0f and 0x80<=raw[1]<=0x8f:
  return at+6+struct.unpack_from('<i',raw,2)[0]
 raise ValueError('NOT_JCC:'+hex(at))
def audit(exe):
 pe=OriginalEXE(Path(exe))
 try:
  if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
  data=pins();cache={}
  for at,raw in data.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:
    raise ValueError('OPCODE_DRIFT:'+hex(at))
   owner=pe.owner(at)
   if owner is None:raise ValueError('NO_UNWIND_OWNER:'+hex(at))
   span=owner[:2]
   if span not in cache:cache[span]=pe.starts_in(*span)
   if at not in cache[span]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for at,target in CALLS.items():
   raw=pe.read(at,5)
   if raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=target:
    raise ValueError('E8_TARGET_DRIFT:'+hex(at))
  for at,target in BRANCHES.items():
   if branch_target(at,data[at])!=target:raise ValueError('BRANCH_DRIFT:'+hex(at))
  # A deliberately synthetic counterexample, not a gameplay trace.
  identity=((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
  flip=((-1.,0.,0.),(0.,1.,0.),(0.,0.,-1.))
  if resolved_goal((1.,0.,0.),((0.,0.,0.),identity))!=(1.,0.,0.) or \
     resolved_goal((1.,0.,0.),((0.,0.,0.),flip))!=(-1.,0.,0.):
   raise ValueError('AFFINE_MODEL_DRIFT')
  return {
   'schema':'bsc.n1.member_goal_world_frame_consumer.v1',
   'proof':'EXACT_ORIGINAL_EXE_STATIC','original_exe_sha256':pe.sha,
   'verified_instruction_starts':len(data),'verified_e8':len(CALLS),
   'verified_jcc':len(BRANCHES),
   'route_to_goal':'member+0x838 record -> 0x0311954C -> member+0x1E0 local xyz/+0x1F0 anchor',
   'steering':'member Tick 0x030822F9 calls 0x03054B84; 0x03055029 calls 0x0311CED4',
   'world_resolution':'if member+0x1F0 non-null, use anchor+0x18 affine 0x02F38640; else copy local xyz',
   'movement_input':'resolved xyz - member+0x88/+0x8c/+0x90; branch compares normalized direction, current velocity and speed',
   'other_goal_writer':'member Tick 0x03082301 -> 0x03088808 guarded status 0x78/0x79 and random gate -> 0x03060D74 writing member+0x1E0/+0x1F0',
   'same_local_target_can_resolve_different_world_target':True,
   'specific_SHIFT_instance_anchor_mismatch_observed':False,
   'steering_or_avoidance_crowding_causality_proven':False,
   'gameplay_patch_authorized':False}
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():p.error('NEVER_OVERWRITE_GAME_EXE')
 d=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
 print('PASS',d['verified_instruction_starts'],'opcodes',d['verified_e8'],'E8',d['verified_jcc'],'JCC; NO PATCH')
if __name__=='__main__':main()
