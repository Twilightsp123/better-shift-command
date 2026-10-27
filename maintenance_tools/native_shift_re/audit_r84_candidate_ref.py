#!/usr/bin/env python3
"""BSC R84 exact-current-EXE static evidence. No process memory or native Hook."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=0x140000000
class Drift(ValueError):pass
def simulate(member_pointer,selected_pointer,member_epoch=None,route_epoch=None):
    return {'same_pointer':member_pointer==selected_pointer,
            'epoch_match_if_known':None if member_epoch is None or route_epoch is None else member_epoch==route_epoch,
            'actual_shift_leg_proven':False,'gameplay_patch_authorized':False}
def verify(data,m):
    if len(data)!=m['exe_size'] or hashlib.sha256(data).hexdigest()!=m['exe_sha256']:
        raise Drift('SHA_SIZE_FAIL_CLOSED')
    if data[:2]!=b'MZ':raise Drift('NOT_MZ')
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if pe<0x40 or pe>=0x1000 or data[pe:pe+4]!=b'PE\0\0':raise Drift('NOT_PE')
    if struct.unpack_from('<H',data,pe+4)[0]!=0x8664 or struct.unpack_from('<H',data,pe+24)[0]!=0x20b:
        raise Drift('NOT_PE64')
    if struct.unpack_from('<Q',data,pe+48)[0]!=BASE:raise Drift('IMAGEBASE')
    opt=struct.unpack_from('<H',data,pe+20)[0];sections=[]
    for i in range(struct.unpack_from('<H',data,pe+6)[0]):
        k=pe+24+opt+40*i
        _,r,size,o=struct.unpack_from('<IIII',data,k+8)
        if o+size>len(data):raise Drift('SECTION')
        sections.append((r,size,o))
    def read(r,n):
        for a,length,o in sections:
            if a<=r and r+n<=a+length:return data[o+r-a:o+r-a+n]
        raise Drift('RVA')
    e,size=struct.unpack_from('<II',data,pe+24+112+3*8)
    func={}
    for i in range(size//12):
        a,z,u=struct.unpack('<III',read(e+i*12,12));func[a]=z
    for owner,(a,z) in m['function_owners'].items():
        if func.get(int(a,16))!=int(z,16):raise Drift('FUNCTION_'+owner)
    for a,item in m['pins'].items():
        r=int(a,16);v=bytes.fromhex(item['hex'])
        lo,hi=m['function_owners'][item['owner']]
        if r<int(lo,16) or r+len(v)>int(hi,16) or read(r,len(v))!=v:
            raise Drift('PIN_'+a)
    for a,target in m['e8_edges'].items():
        r=int(a,16);v=read(r,5)
        if v[0]!=0xe8 or r+5+struct.unpack_from('<i',v,1)[0]!=int(target,16):
            raise Drift('E8_'+a)
    vt=int(m['ordinary_member_vtable'],16)+0x4a0
    if struct.unpack('<Q',read(vt,8))[0]!=BASE+int(m['member_method_4a0'],16):
        raise Drift('MEMBER_VTABLE_4A0')
    for a,h in {'03052f82':'4c89a338070000','03075202':'488b8b38070000',
      '0307520e':'e851170b00','0311f405':'488b4720',
      '0311f410':'448b88a0000000','031269bf':'41c680d100000001',
      '0300bb6a':'898738070000','0303a16a':'898638070000'}.items():
        if m['pins'][a]['hex']!=h:raise Drift('TYPED_FIELD_'+a)
    if m['builder_direct_writes_in_bounded_function'] or len(m['builder_direct_read_sites'])!=7:
        raise Drift('BOUNDED_SCOPED_READ_CONTRACT')
    return {'grade':'EXACT_EXE_STATIC_ONLY','pins':len(m['pins']),
      'e8':len(m['e8_edges']),'owners':len(m['function_owners']),
      'ordinary_member_virtual_4a0_verified':True,
      'candidate_builder_direct_reads':len(m['builder_direct_read_sites']),
      'candidate_builder_direct_writes':0,
      'runtime_member_738_writer_proven':False,
      'gameplay_patch_authorized':False}
if __name__=='__main__':
    try:
        import os
        m=json.loads((ROOT/'r84_candidate_ref_pins.json').read_text())
        print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
    except (IndexError,OSError,ValueError,struct.error) as ex:
        print('FAIL_CLOSED',ex);sys.exit(2)
