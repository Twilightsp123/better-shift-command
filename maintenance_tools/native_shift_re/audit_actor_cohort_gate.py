#!/usr/bin/env python3
"""WH3 original EXE: read-only exact-build actor mode-cohort evidence.

Purpose: prove timing difference between direct member goal receipt and the
conditional per-actor mode reassessment in one actor-update family.  This is
NOT proof of V3 branch execution or a validated native crowding fix.
"""
import argparse
import collections
import hashlib
import json
import mmap
import struct
import sys
from pathlib import Path

ORIGINAL_SHA256 = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
BASE = 0x140000000

# Original EXE instruction-aligned RVA bytes, pinned independently of the input.
PIN = {
    'cohort_source_global_rate': (0x0308201F, '8b055752c800'),
    'cohort_numerator_ms': (0x03082028, 'f30f1005d8ae8900'),
    'cohort_divide_ms_by_global_rate': (0x03082035, 'f30f5ec1'),
    'cohort_float_to_integer_helper': (0x03082039, 'e8265b50fd'),
    'cohort_actor_owner': (0x0308203E, '488b4f58'),
    'cohort_group_tick_controller': (0x03082047, '488b8140040000'),
    'cohort_group_tick_value': (0x0308204E, '8b8098000000'),
    'cohort_group_tick_mod': (0x03082054, '41f7f0'),
    'cohort_actor_ordinal': (0x03082057, '8b4760'),
    'cohort_actor_ordinal_mod': (0x0308205E, '41f7f0'),
    'cohort_compare_remainders': (0x03082061, '3bca'),
    'cohort_skip_if_other_bucket': (0x03082063, '752b'),
    'cohort_current_actor_mode': (0x03082065, '8b9718030000'),
    'cohort_compute_next_actor_mode': (0x0308206E, 'e859f6feff'),
    'cohort_compare_next_and_current_mode': (0x03082073, '3b8718030000'),
    'cohort_skip_if_unchanged': (0x03082079, '7415'),
    'cohort_write_new_mode_indirect': (0x0308208B, 'e88c6affff'),
    'cohort_continue_general_actor_tick': (0x03082090, 'f6870801000010'),
    'later_general_actor_update_is_not_gated_by_cohort':(0x03082165, 'e81a34feff'),
    'direct_member_packet_pose': (0x0307328B, 'e808ba0e00'),
    'direct_member_packet_set_mode_argument': (0x0307329C, 'c644242001'),
    'direct_member_packet_mode_update': (0x030732A4, 'e873580000'),
    'direct_member_packet_cache_tail': (0x030732C0, 'e90f3cfeff'),
    'actor_mode_change_writes_plus318': (0x0307902F, '89b718030000'),
    'actor_update_other_subtype_tail': (0x02F854AC, 'e903ca0f00'),
    'float_rounding_half': (0x00587B71, 'f30f58054f503903'),
    'float_truncation_to_int': (0x00587B79, 'f3480f2cc0'),
    'branch_b_preclassification_bit7_clear': (0x03263C00, '80a3100b00007f'),
    'branch_b_preclassification_bit7_set': (0x03263C0A, '0883100b0000'),
    # Every remaining subtype updater makes one statically proven call into
    # the common 0x03081EB4 update layer. Some callsites are conditional.
    'subtype_spline_calls_common_tick': (0x02F84070, 'e83fde0f00'),
    'subtype_2f566dc_calls_common_tick': (0x02F566E9, 'e8c6b71200'),
    'subtype_2dd70a4_calls_common_tick': (0x02DD71A4, 'e80bad2a00'),
    'subtype_3128d98_calls_common_tick': (0x03128DA1, 'e80e91f5ff'),
    'subtype_2f854b4_calls_common_tick': (0x02F8551A, 'e895c90f00'),
    'subtype_30811d4_calls_common_tick': (0x0308121A, 'e8950c0000'),
    'subtype_3129948_calls_common_tick': (0x03129955, 'e85a85f5ff'),
}
CALLS = {
    'period_divisor_float_rounder': (0x03082039,0x00587B64),
    'staggered_member_mode_compute': (0x0308206E,0x030716CC),
    'staggered_member_mode_commit': (0x0308208B,0x03078B1C),
    'immediate_member_pose': (0x0307328B,0x0315EC98),
    'immediate_member_mode_commit': (0x030732A4,0x03078B1C),
    'common_member_continued_update': (0x03082165,0x03065584),
    'subtype_spline_to_common':(0x02F84070,0x03081EB4),
    'subtype_2f566dc_to_common':(0x02F566E9,0x03081EB4),
    'subtype_2dd70a4_to_common':(0x02DD71A4,0x03081EB4),
    'subtype_3128d98_to_common':(0x03128DA1,0x03081EB4),
    'subtype_2f854b4_to_common':(0x02F8551A,0x03081EB4),
    'subtype_30811d4_to_common':(0x0308121A,0x03081EB4),
    'subtype_3129948_to_common':(0x03129955,0x03081EB4),
}
JUMPS = {
    'second_subtype_forwards_to_common_actor_update':(0x02F854AC,0x03081EB4),
    'member_packet_cache_tail':(0x030732C0,0x03056ED4),
}
DATA = {
    'milliseconds_numerator_f32': (0x0391CF08, '<f', 1000.0),
    'global_rate_initial_u32': (0x03D0727C, '<I', 100),
    'float_rounding_half_f32': (0x0391CBC8, '<f', 0.5),
}
ACTOR_METHOD_COUNTS = {0x03081EB4:10, 0x02F854AC:9, 0x02F83F44:8,
                       0x02F566DC:4, 0x02DD70A4:3,
                       0x03128D98:1,0x02F854B4:1,0x030811D4:1,0x03129948:1}
SUBTYPE_COMMON_CALL_SITES={
    0x02F83F44:0x02F84070, 0x02F566DC:0x02F566E9,
    0x02DD70A4:0x02DD71A4, 0x03128D98:0x03128DA1,
    0x02F854B4:0x02F8551A, 0x030811D4:0x0308121A,
    0x03129948:0x03129955,
}
COMMON_MEMBER_RECEIVERS = {0x0306B9F0,0x0306B9CC,0x03117CE0}

class OriginalPE:
    def __init__(self, path):
        self.path=Path(path)
        h=hashlib.sha256()
        with self.path.open('rb') as fd:
            while True:
                b=fd.read(1<<20)
                if not b:break
                h.update(b)
        self.sha=h.hexdigest()
        if self.sha!=ORIGINAL_SHA256:raise ValueError('ORIGINAL_EXE_SHA_MISMATCH '+self.sha)
        self.fp=self.path.open('rb')
        self.mm=mmap.mmap(self.fp.fileno(),0,access=mmap.ACCESS_READ)
        b=self.mm
        if b[:2]!=b'MZ':raise ValueError('BAD_DOS')
        nt=struct.unpack_from('<I',b,0x3c)[0]
        if b[nt:nt+4]!=b'PE\x00\x00':raise ValueError('BAD_PE')
        machine,n=struct.unpack_from('<HH',b,nt+4)
        if machine!=0x8664:raise ValueError('NOT_X64')
        optional=nt+24; optional_size=struct.unpack_from('<H',b,nt+20)[0]
        if struct.unpack_from('<Q',b,optional+24)[0]!=BASE:raise ValueError('IMAGE_BASE_DIFFERENT')
        self.sections=[]
        for i in range(n):
            pos=optional+optional_size+i*40
            name=bytes(b[pos:pos+8]).split(b'\0')[0].decode('ascii')
            virtual,rva,raw_size,file_pos=struct.unpack_from('<IIII',b,pos+8)
            flags=struct.unpack_from('<I',b,pos+36)[0]
            if file_pos+raw_size>len(b):raise ValueError('BAD_SECTION_SIZE')
            self.sections.append((name,rva,raw_size,file_pos,flags))
    def read(self,rva,size,code=None):
        for name,start,length,off,flags in self.sections:
            if start<=rva and rva+size<=start+length:
                if code is not None and bool(flags&0x20000000)!=code:
                    raise ValueError('SECTION_KIND_MISMATCH '+name+' '+hex(rva))
                return self.mm[off+rva-start:off+rva-start+size]
        raise ValueError('RVA_NOT_MAPPED '+hex(rva))
    def close(self):
        self.mm.close();self.fp.close()
    def ptr(self,rva):
        return struct.unpack('<Q',self.read(rva,8))[0]-BASE
    def actor_method_census(self):
        # Anchor the constructor-recognized actor family in the original
        # +0x3F8 class virtual, not all arbitrary vtable-like memory.
        needle=struct.pack('<Q', BASE+0x008F37B0)
        found={}
        for _,start,size,off,flags in self.sections:
            if flags&0x20000000:continue
            region=self.mm[off:off+size]
            pos=0
            while True:
                at=region.find(needle,pos)
                if at<0:break
                pos=at+1
                vt=start+at-0x3F8
                if vt<start or vt%8 or vt+0x400>start+size:continue
                if self.ptr(vt+0x368) in COMMON_MEMBER_RECEIVERS:
                    found[vt]=self.ptr(vt+0x18)
        return collections.Counter(found.values())

def rel32_at(pe,site,opcode):
    b=pe.read(site,5,code=True)
    if b[0]!=opcode:raise ValueError('OPCODE_NOT_E8_E9 '+hex(site))
    return (site+5+struct.unpack_from('<i',b,1)[0])&0xffffffff

def scheduled_for_mode_recheck(group_counter:int, member_ordinal:int, buckets:int)->bool:
    if not (isinstance(buckets,int) and 1<=buckets<65536):raise ValueError('INVALID_DIVISOR')
    if not (0<=group_counter<1<<32 and 0<=member_ordinal<1<<32):raise ValueError('NOT_U32')
    return (group_counter%buckets)==(member_ordinal%buckets)

def audit(path:Path):
    pe=OriginalPE(path)
    try:
        for label,(rva,hx) in PIN.items():
            if pe.read(rva,len(hx)//2,code=True)!=bytes.fromhex(hx):
                raise ValueError('MACHINE_GUARD_FAILED '+label)
        for label,(site,dest) in CALLS.items():
            if rel32_at(pe,site,0xE8)!=dest:raise ValueError('CALL_DEST_MISMATCH '+label)
        for label,(site,dest) in JUMPS.items():
            if rel32_at(pe,site,0xE9)!=dest:raise ValueError('JUMP_DEST_MISMATCH '+label)
        vals={}
        for name,(rva,fmt,expected) in DATA.items():
            v=struct.unpack(fmt,pe.read(rva,struct.calcsize(fmt)))[0]
            if v!=expected:raise ValueError('ORIGINAL_CONSTANT_CHANGED '+name)
            vals[name]=v
        divisor=round(vals['milliseconds_numerator_f32']/vals['global_rate_initial_u32'])
        # Helper uses 0.5 followed by truncation for a positive float.
        if divisor!=10:raise ValueError('DIVISOR_MISMATCH')
        actual=pe.actor_method_census()
        if actual!=collections.Counter(ACTOR_METHOD_COUNTS):
            raise ValueError('MEMBER_SUBTYPE_CENSUS_MISMATCH '+str(actual))
        all_common=actual[0x03081EB4]+actual[0x02F854AC]+sum(actual[v] for v in SUBTYPE_COMMON_CALL_SITES)
        if all_common!=38:raise ValueError('UNACCOUNTED_ACTOR_TYPE')
        groups={str(k):[i for i in range(60) if i%divisor==k] for k in range(divisor)}
        return {
          'schema':'bsc.903.original_actor_mode_cohort.v1',
          'exe_sha256':pe.sha,'machine_guards':len(PIN),
          'checked_direct_calls':len(CALLS), 'checked_direct_jumps':len(JUMPS),
          'initial_default_divisor':divisor,
          'rate_may_change_during_game':True,
          'actor_update_vtable_census':{hex(k):n for k,n in sorted(actual.items())},
          'common_actor_tick_direct_or_thunk_vtables':actual[0x03081EB4]+actual[0x02F854AC],
          'common_actor_tick_statically_reachable_vtables':all_common,
          'subtype_common_tick_call_edges':{hex(v):hex(site) for v,site in SUBTYPE_COMMON_CALL_SITES.items()},
          'subtype_calls_may_be_conditional':True,
          'conditional_mode_recheck':
              '((owner+0x440)->+0x98 % divisor) == ((actor+0x60) % divisor); only then 0x030716CC and changed-mode 0x03078B1C',
          'direct_member_receiver':
              '0x03073224 via 0x030732A4 invokes the same 0x03078B1C outside the periodic gate (conditional A/0x26 path)',
          'other_actor_processing':
              '0x03082165 still calls 0x03065584 irrespective of cohort gate; the mode gate does NOT mean the soldier moves only one out of ten ticks',
          'synthetic_60_consecutive_ordinals_NOT_V3':groups,
          'v3_mode_path_reached':'UNKNOWN',
          'patch_status':'NO_PATCH_AUTHORIZED'
        }
    finally:pe.close()

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--exe',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True)
    v=a.parse_args(argv)
    if v.exe.resolve()==v.out.resolve():a.error('cannot overwrite original EXE')
    try:
        result=audit(v.exe)
        v.out.parent.mkdir(parents=True,exist_ok=True)
        v.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    except (OSError,ValueError,struct.error) as err:
        print('STATIC_AUDIT_DENIED:',err,file=sys.stderr);return 2
    print('PASS',result['machine_guards'],'opcode guards',result['checked_direct_calls'],'calls',result['checked_direct_jumps'],'jumps',result['common_actor_tick_statically_reachable_vtables'],'statically common tick actor vtables; no native patch')
    return 0
if __name__=='__main__':sys.exit(main())