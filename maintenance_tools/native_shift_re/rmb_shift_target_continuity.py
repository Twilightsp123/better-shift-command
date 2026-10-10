#!/usr/bin/env python3
"""BSC 9.0.3: read-only exact-SHA native RMB/queued MOVE target continuity.

Exact original EXE instruction checks and a deliberately bounded recreation of
0x030DC0A0's LINEAR segment projection/phase carry. Does NOT simulate the
whole 0x030BD610 multirow placement, curved kind-1 (0x030DC304), avoidance,
or WH3 soldier locomotion. The synthetic turn uses chordal kind-0 legs only.
"""
from __future__ import annotations
import argparse, hashlib, json, math, mmap, struct
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
IMAGE_BASE=0x140000000
# Exact disassembled opcode sites, verified on user's original 9.0.3-labelled executable
GUARDS={
 'native_nonqueue_discard_old': (0x02f50425,'84d27520'),
 'rmb_shift_both_construct_move':(0x030326e4,'e8d369fdff'),
 'rmb_shift_both_move_work':(0x03025de1,'4d8b1e4d85db'),
 'shared_target_strategy': (0x030c9b18,'e8b7240100'),
 'first_leg_v38':(0x030dc049,'41ff5338'),
 'later_leg_v30':(0x030dc05b,'41ff5330'),
 'later_reference_getter':(0x030dc2da,'ff5608'),
 'later_same_leg_v38':(0x030dc2ee,'ff5638'),
 'linear_length_sqrt':(0x030dc10d,'f30f51d8'),
 'linear_projection_over_length':(0x030dc153,'f30f5ed3'),
 'linear_unspent_distance':(0x030dc183,'f30f59f3'),
 'linear_spacing_count':(0x030dc18a,'f30f5ec2'),
 'linear_integer_count':(0x030dc192,'f3480f2cf0'),
 'linear_increment_along_tangent':(0x030dc229,'f30f5987cc000000'),
 'linear_updated_residual':(0x030dc25f,'f30f5cf0'),
 'linear_residual_to_next_leg_phase':(0x030dc26c,'f30f5cd6'),
 'linear_phase_write':(0x030dc270,'f30f115318'),
 'segment_kind1_builder_sign_flag':(0x030c20aa,'837e0802'),
 'segment_kind1_halfwidth_factor':(0x0391cbc8,'0000003f'),
 'mode0_sink_append_48B':(0x030bd830,'e80f0d0000'),
 'tail_fill_v20':(0x030dc079,'498b06498bceff5020'),
 'tail_duplicate_48B':(0x030d1f82,'e8bdc5feff'),
 'per_member_task_copy':(0x030d54fc,'e867a3e8ff'),
 'member_dispatch_virtual_e8':(0x0306bb44,'41ff93e8000000'),
 'member_mode0_delegate_to_target_handler':(0x0307328b,'e808ba0e00'),
 'member_target_path_screen':(0x0315eeba,'e895bce2ff'),
 'member_target_optional_spatial_fallback':(0x0315eefb,'e8a8fafeff'),
 'spatial_query_to_grid_enumerator':(0x0314e9f3,'e8c4220000'),
 'independent_contact_same_affiliation_read':(0x030c67c2,'488b8680000000'),
 'independent_contact_same_affiliation_compare':(0x030c67c9,'48398380000000'),
 'independent_contact_same_affiliation_skip':(0x030c67d0,'0f84b2010000'),
 'spatial_point_region_test_call':(0x0314ea25,'e8c23b6efe'),
 'spatial_height_plane_coeff_z':(0x0314ea2e,'f30f104b74'),
 'spatial_height_plane_mul_z':(0x0314ea33,'f30f594d04'),
 'spatial_height_plane_coeff_x':(0x0314ea38,'f30f10436c'),
 'spatial_height_plane_mul_x':(0x0314ea3d,'f30f594500'),
 'spatial_height_plane_offset':(0x0314ea46,'f30f584b78'),
 'spatial_height_plane_divisor':(0x0314ea4b,'f30f5e4b70'),
 'spatial_writes_computed_scalar':(0x0314ea62,'f3410f110e'),
 'spatial_selects_shape_object':(0x0314ea67,'488bf3'),
 'member_target_second_spatial_query':(0x0315f1b7,'e8001bffff'),
 'member_target_direct_pose_x':(0x0315f311,'f20f118e88000000'),
 'member_target_direct_pose_z':(0x0315f33f,'898690000000'),
 'member_target_direct_facing':(0x0315f34d,'66899eb0000000'),
}
EDGES={
 'direct_MOVE_ctor':(0x030326e4,0x030090bc),
 'native_common_move_route':(0x03025e91,0x0301287c),
 'common_move_member_task':(0x030260af,0x02f2c734),
 'segmenter':(0x030c9b18,0x030dbfd4),
 'tail_copy':(0x030d1f82,0x030be544),
 'member_dispatch_copy':(0x030d54fc,0x02f5f868),
 'member_target_handler':(0x0307328b,0x0315ec98),
 'member_path_screen':(0x0315eeba,0x02f8ab54),
 'member_target_nearby_candidates':(0x0315eefb,0x0314e9a8),
 'spatial_candidate_collection':(0x0314e9f3,0x03150cbc),
 'spatial_region_predicate':(0x0314ea25,0x018325ec),
 'spatial_region_nested_contour':(0x01832604,0x0183b990),
 'member_direct_second_spatial_query':(0x0315f1b7,0x03150cbc),
}
SLOTS={
 'kind0_step':(0x0390f2b0+0x38,0x030dc0a0),
 'kind0_next':(0x0390f2b0+0x30,0x030dc2b4),
 'kind1_step':(0x0390f330+0x38,0x030dc304),
 'kind1_next':(0x0390f330+0x30,0x030dc2b4),
}

class PE:
 def __init__(self, buf):
  if len(buf)<0x100 or buf[:2]!=b'MZ':raise ValueError('INVALID_DOS_HEADER')
  nt=struct.unpack_from('<I',buf,0x3c)[0]
  if nt+24>len(buf) or buf[nt:nt+4]!=b'PE\0\0':raise ValueError('INVALID_PE_SIGNATURE')
  n=struct.unpack_from('<H',buf,nt+6)[0];sz=struct.unpack_from('<H',buf,nt+20)[0];op=nt+24
  if not 1<=n<=96 or op+sz+n*40>len(buf) or struct.unpack_from('<H',buf,nt+4)[0]!=0x8664:
   raise ValueError('NOT_X64_PE')
  if struct.unpack_from('<H',buf,op)[0]!=0x20b or struct.unpack_from('<Q',buf,op+24)[0]!=IMAGE_BASE:
   raise ValueError('PE32_IMAGE_BASE_MISMATCH')
  self.sec=[]
  for i in range(n):
   s=op+sz+i*40
   _,rva,nraw,off=struct.unpack_from('<IIII',buf,s+8)
   flags=struct.unpack_from('<I',buf,s+36)[0]
   if nraw and (off>len(buf) or nraw>len(buf)-off):raise ValueError('PE_SECTION_OUT_OF_RANGE')
   self.sec.append((rva,nraw,off,bool(flags&0x20000000)))
  self.buf=buf
 def read(self,rva,length,execute=False):
  if rva<0 or length<=0:raise ValueError('INVALID_READ')
  for start,size,off,x in self.sec:
   if start<=rva and rva+length<=start+size:
    if execute and not x:raise ValueError('NON_EXECUTABLE_SECTION')
    return bytes(self.buf[off+rva-start:off+rva-start+length])
  raise ValueError('RVA_UNMAPPED:'+hex(rva))


def verify(exe:Path):
 h=hashlib.sha256()
 with exe.open('rb') as f:
  for data in iter(lambda:f.read(4<<20),b''):h.update(data)
 if h.hexdigest()!=SHA:raise ValueError('WRONG_WARHAMMER3_EXE_SHA256')
 with exe.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
  pe=PE(b)
  for name,(rva,hx) in GUARDS.items():
   if pe.read(rva,len(hx)//2,name!='segment_kind1_halfwidth_factor')!=bytes.fromhex(hx):
    raise ValueError('OPCODE_OR_SCALAR_MISMATCH:'+name)
  for name,(site,target) in EDGES.items():
   instruction=pe.read(site,5,True)
   if instruction[0]!=0xe8 or site+5+struct.unpack_from('<i',instruction,1)[0]!=target:
    raise ValueError('DIRECT_EDGE_MISMATCH:'+name)
  for name,(slot,target) in SLOTS.items():
   if struct.unpack('<Q',pe.read(slot,8))[0]-IMAGE_BASE!=target:
    raise ValueError('VTABLE_TARGET_MISMATCH:'+name)
 return {'original_exe_sha256':h.hexdigest(),'instructions_and_native_scalar_verified':len(GUARDS),
   'native_E8_verified':len(EDGES),'segment_vtables_verified':len(SLOTS)}

@dataclass(frozen=True)
class CenterlineTarget:
    x:float
    z:float
    dx:float
    dz:float
    leg:int
    ordinal:int

def native_kind0_centerline(segments:Sequence[tuple[tuple[float,float],tuple[float,float]]],
                             count:int,spacing:float,phase:float=0.4):
 """Projected sample and carry of 0x030DC0A0, idealized callback:

 0x30DC0C3–0x30DC153 computes t=dot((R+phase*D)-start,D)/length.
 Here R=start and D is each straight segment tangent; actual WH3 R can
 originate from 0x311D0CC / per-leg reference and 0x030BD610 can output
 more than one 48B slot per callback. This is explicitly a ONE-CENTERLINE
 model only, not the game's actual formation output.

 0x30DC183-197 determines count=floor(remaining_length/spacing+1);
 0x30DC25F-270 carries spacing-(remaining-(n-1)*spacing) to next leg.
 """
 if count<0 or not math.isfinite(spacing) or spacing<=0 or not math.isfinite(phase) or phase<0:
  raise ValueError('INVALID_GEOMETRY_PARAMS')
 targets=[];remainders=[]
 for i,(p0,p1) in enumerate(segments):
  sx,sz=p0;ex,ez=p1
  dx=ex-sx;dz=ez-sz;L=math.hypot(dx,dz)
  if L<=1e-9:continue
  dx/=L;dz/=L
  if phase>L:
   remainders.append({'leg':i,'count':0,'carried_to_next':phase-L})
   phase-=L
   continue
  left=L-phase
  # +1 then trunc() mirrors CVTTSS2SI for positive values; boundary equality
  max_on_segment=int(left/spacing+1.0)
  n=min(max_on_segment,count-len(targets))
  for j in range(n):
   advance=phase+j*spacing
   targets.append(CenterlineTarget(sx+advance*dx,sz+advance*dz,dx,dz,i,len(targets)))
  if len(targets)==count:
   remainders.append({'leg':i,'count':n,'carried_to_next':None});break
  # If callbacks were not exhausted, phase moves continuously across legs.
  residual=left-(max_on_segment-1)*spacing
  phase=(spacing-residual) if residual>1e-9 else spacing
  remainders.append({'leg':i,'count':n,'carried_to_next':phase})
 return targets,remainders

def target_diagnostics(targets:Sequence[CenterlineTarget],radius:float=1.0):
 near_opposed=[];exact_duplicates=[]
 for i,a in enumerate(targets):
  for j,b in enumerate(targets[i+1:],i+1):
   d=math.hypot(a.x-b.x,a.z-b.z)
   if d<1e-7:exact_duplicates.append([i,j])
   cosine=a.dx*b.dx+a.dz*b.dz
   if j-i>=3 and d<radius and cosine<-0.25:
    near_opposed.append({'a':i,'b':j,'distance':round(d,5),'tangent_cosine':round(cosine,4)})
 return {'target_count':len(targets),'exact_duplicates':len(exact_duplicates),
         'near_opposed_pairs':len(near_opposed),
         'closest_near_opposed':min((p['distance'] for p in near_opposed),default=None),
         'examples':near_opposed[:8]}

def segment_chain(points):return list(zip(points[:-1],points[1:]))

def gradual_u_turn(radius:float=0.4,steps:int=24,limb:float=20.0):
 """Synthetic chordal analogue of CA progressive turning; NOT original kind1 curve."""
 if radius<=0 or steps<4:raise ValueError('INVALID_ARC')
 points=[(0.,0.),(limb,0.)]
 for i in range(1,steps+1):
  theta=-math.pi/2+math.pi*i/steps
  points.append((limb+radius*math.cos(theta),radius+radius*math.sin(theta)))
 points.append((0.,2*radius))
 return segment_chain(points)

def case_report(count=36,spacing=0.85,phase=0.4):
 cases={
  'RMB_long_straight':segment_chain([(0.,0.),(50.,0.)]),
  'RMB_short_straight':segment_chain([(0.,0.),(4.,0.)]),
  'queued_short_U_radius_0p4':gradual_u_turn(.4),
  'queued_wide_U_radius_2p5':gradual_u_turn(2.5),
  'queued_90_degree':segment_chain([(0.,0.),(20.,0.),(20.,20.)]),
 }
 results={}
 for name,path in cases.items():
  pts,carry=native_kind0_centerline(path,count,spacing,phase)
  results[name]={'diagnostics':target_diagnostics(pts),'segment_count':len(path),
                 'tail_clones_if_required':max(0,count-len(pts)),
                 'unique_endpoint_geometry':len(set((round(t.x,6),round(t.z,6)) for t in pts)),
                 'sample':[[round(t.x,3),round(t.z,3),t.leg] for t in pts[:5]],
                 'carry_transitions':carry[:5]}
 return results

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',required=True,type=Path)
 p.add_argument('--out',required=True,type=Path)
 a=p.parse_args(argv)
 if a.out.resolve()==a.exe.resolve():p.error('report must not overwrite EXE')
 result={'machine_evidence':verify(a.exe),'contrasts':case_report(),
    'interpretation':'Conditional CENTERLINE risk; native target-record copy, multirow layout, actual path, physics, avoidance and WH3 V3 branch not proved',
    'static_member_path':'native payload -> member virtual +0x368 -> common +0xE8 (for common member types) -> 0x03073224 -> 0x0315EC98 -> optional 0x0314E9A8 -> 0x03150CBC spatial candidates',
    'static_non_equivalence':'0x030C6788 nearby pair contact bitset skips same member+0x80 pointer but has NOT been proven to be movement collision avoidance or to run for V3',
    'spatial_resolution':'0x0314E9A8 invokes 0x03150CBC for candidate enumeration, 0x018325EC/0x0183B990 for region geometry, and calculates (a*x+b*z+c)/den before selecting geometric support. This is not proof of actor-actor steering or output-velocity correction.',
    'member_target_pose_writer':'0x0315EC98 contains direct writes at 0x0315F311 (+0x88), 0x0315F33F (+0x90), 0x0315F34D (+0xB0); this is not the per-frame rate writer 0x0315C1E4.',
    'release_patch_authorized':False,'windows_tested':False,'wh3_tested':False}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('ORIGINAL WH3 EXE PASS',len(GUARDS),'opcode/scalar',len(EDGES),'E8',len(SLOTS),'vtables')
 for k,v in result['contrasts'].items():
  print(k,':',v['diagnostics']['target_count'],'points /',
        v['diagnostics']['near_opposed_pairs'],'near-opposed /',
        v['diagnostics']['exact_duplicates'],'exact-duplicate /',
        v['tail_clones_if_required'],'possible tail-clones')
 return 0
if __name__=='__main__':raise SystemExit(main())