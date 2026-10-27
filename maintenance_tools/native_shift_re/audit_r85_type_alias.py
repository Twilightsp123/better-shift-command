#!/usr/bin/env python3
"""BSC R85 exact EXE type-specific +0x738 false-setter guard; NO live Hook."""
import hashlib,json,struct,sys
from pathlib import Path
class Drift(ValueError):pass
HERE=Path(__file__).resolve().parent
BASE=0x140000000
def typecheck(kind):
    if kind not in ('ordinary_member','other_vector','stack_local','other_dword'):
        raise Drift('TYPE_UNKNOWN')
    return {'actual_member':kind=='ordinary_member','same_shift_generation_proven':False}
def verify(data,m):
    if len(data)!=m['exe_size'] or hashlib.sha256(data).hexdigest()!=m['exe_sha256']:
        raise Drift('EXACT_SHA_SIZE_REQUIRED')
    if data[:2]!=b'MZ':raise Drift('NOT_MZ')
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if not 0x40<=pe<0x1000 or data[pe:pe+4]!=b'PE\0\0':raise Drift('NOT_PE')
    if struct.unpack_from('<H',data,pe+4)[0]!=0x8664 or struct.unpack_from('<H',data,pe+24)[0]!=0x20b:
        raise Drift('NOT_WIN64_PE')
    if struct.unpack_from('<Q',data,pe+48)[0]!=BASE:raise Drift('IMAGEBASE_DRIFT')
    opt=struct.unpack_from('<H',data,pe+20)[0];sections=[]
    for i in range(struct.unpack_from('<H',data,pe+6)[0]):
        p=pe+24+opt+i*40
        _,r,size,o=struct.unpack_from('<IIII',data,p+8)
        if o+size>len(data):raise Drift('SECTION_OOB')
        sections.append((r,size,o))
    def read(r,n):
        for a,size,o in sections:
            if a<=r and r+n<=a+size:return data[o+r-a:o+r-a+n]
        raise Drift('RVA_OOB')
    exception,sz=struct.unpack_from('<II',data,pe+24+112+3*8)
    owners={}
    for i in range(sz//12):
        a,end,u=struct.unpack('<III',read(exception+i*12,12));owners[a]=end
    for fn,(start,end) in m['bounds'].items():
        if owners.get(int(start,16))!=int(end,16):raise Drift('UNWIND_'+fn)
    for site,d in m['pins'].items():
        r=int(site,16);by=bytes.fromhex(d['hex']);lo,hi=m['bounds'][d['owner']]
        if r<int(lo,16) or r+len(by)>int(hi,16):raise Drift('PIN_OWNER_'+site)
        if read(r,len(by))!=by:raise Drift('PIN_DRIFT_'+site)
    for site,dest in m['calls'].items():
        r=int(site,16);code=read(r,5)
        if code[0]!=0xe8 or r+5+struct.unpack_from('<i',code,1)[0]!=int(dest,16):
            raise Drift('E8_DRIFT_'+site)
    p=int(m['ordinary_member_vtable'],16)+0x4a0
    if struct.unpack('<Q',read(p,8))[0]!=BASE+int(m['ordinary_member_method_4a0'],16):
        raise Drift('VTABLE_4A0')
    for addr,expected in {'02fa6088':'4c8bf2','02fa66f8':'498d8e38070000',
        '02fa6734':'e883d3feff','02f93acb':'8b01','02f93ad7':'394104',
        '02f93b02':'48894308','02f9d16c':'49898638070000',
        '03052f82':'4c89a338070000','03075202':'488b8b38070000',
        '0311f405':'488b4720','0329b276':'48898538070000'}.items():
        if m['pins'][addr]['hex']!=expected:raise Drift('TYPED_LAYOUT_'+addr)
    return {'grade':'EXACT_EXE_STATIC_ONLY','pins':len(m['pins']),
        'E8':len(m['calls']),'unwind_functions':len(m['bounds']),
        'foreign_vector_header_proven':True,
        'member_runtime_writer_proven':False,
        'same_shift_epoch_proven':False,'gameplay_patch_authorized':False}
if __name__=='__main__':
    try:
        m=json.loads((HERE/'r85_type_alias_pins.json').read_text())
        print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
    except (IndexError,ValueError,OSError,struct.error) as e:
        print('FAIL_CLOSED',e);sys.exit(2)
