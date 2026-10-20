#!/usr/bin/env python3
"""SHA-pinned static action fingerprint audit: user WH3 EXE vs Derpy and BSC.

Read-only. No DLL execution, hooking, patching or re-distribution of EXE/MOD.
"""
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path

WH3_SHA='9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496'
DERPY_SHA='a40d086d57f8d4857caff782680b62f490cf5e9d772723c9b50f69bee9e32176'
MEM_SHA='9e63d8feacb92c0b35ec327884bda558fe453dbdba945ee9d9c848deec1f7878'
BUILD=0x6ACEC6F4
IMAGEBASE=0x140000000
# vtable RVA, +0x08, +0x10. Derpy fields / R41-R45 independently grounded.
VTABLES={
    'walk_a':(0x03919350,0x0325F000,0x03264B70),
    'walk_b':(0x03AE2400,0x008F9E80,0x03262850),
    'move_a_b2_special':(0x039199F8,0x0325E824,0x03263AF8),
    'b2_general':(0x03919B28,0x0325D9FC,0x03261688),
    'move_b':(0x03AE1928,0x0325ECE4,0x032643BC),
    'state16_cached_vector':(0x03AE22D0,0x0325E4B4,0x032621E0),
    'melee':(0x03AD24B8,0x030813D8,0x030877EC),
}
MEMBER_VTABLE=0x03912950
MEMBER_TICK=0x03086F04
MEMBER_MOTION=0x030592BC


def single_pack(zipfile_path):
    with zipfile.ZipFile(zipfile_path) as z:
        infos=[x for x in z.infolist() if not x.is_dir()]
        if len(infos)!=1 or not infos[0].filename.lower().endswith('.pack'):
            raise ValueError('EXPECTED_EXACTLY_ONE_PACK')
        return z.read(infos[0])


def selected_scripts(pack, names):
    if pack[:4]!=b'PFH5':raise ValueError('INVALID_PFH5')
    count,index_size=struct.unpack_from('<II',pack,16)
    if count<1 or count>1000:raise ValueError('PACK_COUNT_DRIFT')
    cursor=28; entries=[]
    for _ in range(count):
        size=struct.unpack_from('<I',pack,cursor)[0];cursor+=4
        flag=pack[cursor];cursor+=1
        end=pack.index(b'\0',cursor)
        path=pack[cursor:end].decode().replace('\\','/');cursor=end+1
        if '..' in path.split('/'):raise ValueError('UNSAFE_PACK_PATH')
        entries.append((path,size))
    if cursor+4!=32+index_size:raise ValueError('BAD_PFH5_INDEX')
    if cursor+sum(size for _,size in entries)!=len(pack):raise ValueError('BAD_PFH5_SIZE')
    out={}
    for name,size in entries:
        if name in names:out[name]=pack[cursor:cursor+size]
        cursor+=size
    if len(out)!=len(names):raise ValueError('MISSING_EXPECTED_SOURCE')
    return out


class PE:
    def __init__(self,raw):
        self.raw=raw
        if len(raw)<512 or raw[:2]!=b'MZ':raise ValueError('NOT_PE')
        p=struct.unpack_from('<I',raw,0x3c)[0]
        if raw[p:p+4]!=b'PE\0\0':raise ValueError('NOT_PE')
        self.timestamp=struct.unpack_from('<I',raw,p+8)[0]
        self.base=struct.unpack_from('<Q',raw,p+24+24)[0]
        self.machine=struct.unpack_from('<H',raw,p+4)[0]
        secbase=p+24+struct.unpack_from('<H',raw,p+20)[0]
        self.sections=[]
        for i in range(struct.unpack_from('<H',raw,p+6)[0]):
            o=secbase+i*40
            size,rva,rawsize,off=struct.unpack_from('<IIII',raw,o+8)
            self.sections.append((rva,rawsize,off))
    def bytes(self,rva,n):
        for start,size,off in self.sections:
            if start<=rva and rva+n<=start+size:
                return self.raw[off+rva-start:off+rva-start+n]
        raise ValueError('UNMAPPED_RVA:'+hex(rva))
    def vtable_pointer(self,rva):return struct.unpack('<Q',self.bytes(rva,8))[0]-self.base


def audit(exe,derpyzip,memzip):
    raw=Path(exe).read_bytes()
    game_sha=hashlib.sha256(raw).hexdigest()
    if game_sha != WH3_SHA:raise ValueError('GAME_SHA_MISMATCH')
    pe=PE(raw)
    if (pe.machine,pe.base,pe.timestamp)!=(0x8664,IMAGEBASE,BUILD):
        raise ValueError('PE_METADATA_MISMATCH')
    derpy=single_pack(derpyzip)
    mem=single_pack(memzip)
    if hashlib.sha256(derpy).hexdigest()!=DERPY_SHA:raise ValueError('DERPY_MOD_DRIFT')
    if hashlib.sha256(mem).hexdigest()!=MEM_SHA:raise ValueError('MEMREADER_MOD_DRIFT')
    dp=selected_scripts(derpy,['script/derpy_tp/platform.lua'])['script/derpy_tp/platform.lua'].decode()
    mp=selected_scripts(mem,['script/memreader_plus/0_13_0/sites.lua'])['script/memreader_plus/0_13_0/sites.lua'].decode()
    if '"6acec6f4"' not in dp or 'MODELS_N, MODELS_DATA, MODEL_POS = 0xa4, 0xa8, 0x88' not in dp:
        raise ValueError('DERPY_LAYOUT_DRIFT')
    for name,rva in {'walk_a':0x3919350,'walk_b':0x3ae2400,
                     'move_a_b2_special':0x39199f8,'move_b':0x3ae1928,'melee':0x3ad24b8}.items():
        if not re.search(r'\b(?:walk_a|walk_b|move_a|move_b|melee)\s*=\s*0x'+format(rva,'x')+r'\b',dp):
            raise ValueError('DERPY_RVA_SOURCE_MISSING:'+name)
    # read_original is intentionally not used as a sole patch-absence check.
    for required in ('plus.read_original(', 'plus.read(', 'plus.hook_info('):
        if required not in mp:raise ValueError('MEMREADER_API_SOURCE_MISSING:'+required)
    pins=[]
    for name,(vt,fn8,fn10) in VTABLES.items():
        got8=pe.vtable_pointer(vt+8)
        got10=pe.vtable_pointer(vt+0x10)
        if (got8,got10)!=(fn8,fn10):
            raise ValueError('ACTION_VTABLE_DRIFT:'+name)
        pins.append({'type':name,'vtable_rva':hex(vt),'virtual_08':hex(got8),'virtual_10':hex(got10)})
    if pe.vtable_pointer(MEMBER_VTABLE+0x18)!=MEMBER_TICK or pe.vtable_pointer(MEMBER_VTABLE+0x20)!=MEMBER_MOTION:
        raise ValueError('MEMBER_VTABLE_DRIFT')
    return {'schema':'bsc.n1.r47_passive_action_fingerprint_static.v1',
            'exe_sha256':game_sha,'derpy_pack_sha256':DERPY_SHA,'memreader_pack_sha256':MEM_SHA,
            'pe_timestamp':hex(BUILD), 'source':'uploaded original EXE and MOD packs',
            'verified_action_vtable_slots':len(VTABLES)*2,
            'verified_regular_member_vtable_slots':2,
            'vtable_fingerprints':pins,
            'patch_absence_guard':'check both live mr.read and mr.read_original plus hook_info; not atomic',
            'derpy_empirical_note':'author comments say regiment walk did not follow just-written standalone goal and idle soldier can be displaced; not independent BSC proof',
            'exe_only_static':True,'game_runtime_sampled':False,
            'root_cause_proven':False,'gameplay_patch_authorized':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--derpy',type=Path,required=True)
    p.add_argument('--memreader',type=Path,required=True)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    for q in (a.exe,a.derpy,a.memreader):
        if a.out and a.out.resolve()==q.resolve():p.error('cannot overwrite any input')
    report=audit(a.exe,a.derpy,a.memreader)
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('STATIC_ONLY_PASS',report['verified_action_vtable_slots'],'action vtable slots;',
          report['verified_regular_member_vtable_slots'],'member slots; NO PATCH')

if __name__=='__main__':main()
