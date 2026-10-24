#!/usr/bin/env python3
"""R71 lightweight exact-build PE audit; no process access or Hook code.
The full local R71 ZIP additionally verifies objdump instruction boundaries and actual PFH5 sources.
"""
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
class AuditError(ValueError):pass
def check(data,m):
    if len(data)!=m['exe_size'] or hashlib.sha256(data).hexdigest()!=m['exe_sha256']:
        raise AuditError('FAIL_CLOSED_SHA')
    if data[:2]!=b'MZ':raise AuditError('NOT_MZ')
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if pe>0x1000 or data[pe:pe+4]!=b'PE\\0\\0':raise AuditError('NOT_PE')
    if struct.unpack_from('<H',data,pe+4)[0]!=0x8664 or struct.unpack_from('<H',data,pe+24)[0]!=0x20b:
        raise AuditError('NOT_AMD64')
    if struct.unpack_from('<Q',data,pe+48)[0]!=0x140000000:raise AuditError('IMAGEBASE')
    n=struct.unpack_from('<H',data,pe+6)[0];opt=struct.unpack_from('<H',data,pe+20)[0]
    sections=[]
    for i in range(n):
        j=pe+24+opt+40*i
        _,rva,size,off=struct.unpack_from('<IIII',data,j+8)
        if off+size>len(data):raise AuditError('SECTION_BOUNDS')
        sections.append((rva,size,off))
    def get(rva,length):
        for base,size,off in sections:
            if base<=rva and rva+length<=base+size:return data[off+rva-base:off+rva-base+length]
        raise AuditError('RVA_OOB')
    drva,dsize=struct.unpack_from('<II',data,pe+24+112+3*8)
    tick=int(m['tick_rva'],16)
    found=False
    for i in range(dsize//12):
        first,end,info=struct.unpack('<III',get(drva+12*i,12))
        if first==tick:
            found=True
            if end!=int(m['tick_end_rva'],16) or info!=int(m['tick_unwind_rva'],16):
                raise AuditError('UNWIND_IDENTITY_DRIFT')
            u=get(info,4)
            if u[1]!=m['tick_prolog_length'] or u[2]!=m['tick_unwind_slots']:
                raise AuditError('UNWIND_PROLOGUE_DRIFT')
            break
    if not found:raise AuditError('TICK_UNWIND_MISSING')
    if get(tick,7).hex()!=m['stolen_first_two_instructions_bytes']:
        raise AuditError('CAVE_PREFIX_DRIFT')
    for k,v in m['pins'].items():
        if get(int(k,16),len(v)//2)!=bytes.fromhex(v):raise AuditError('PIN_DRIFT_'+k)
    for k,target in m['e8_edges'].items():
        r=int(k,16);b=get(r,5)
        if b[0]!=0xe8 or r+5+struct.unpack_from('<i',b,1)[0]!=int(target,16):
            raise AuditError('CALL_DRIFT_'+k)
    vt=int(m['ordinary_member_vtable_rva'],16)+0x18
    if struct.unpack('<Q',get(vt,8))[0]!=0x140000000+tick:raise AuditError('MEMBER_VTABLE_DRIFT')
    return {'original_exe_static':True,'pins':len(m['pins']),'e8':len(m['e8_edges']),
        'unwind_prolog_bytes':m['tick_prolog_length'],'hook_authorized':False,
        'worker_lifetime_proven':False,'member_cross_snapshot_atomic':False}
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: python audit_r71_tick_safety.py matching_Warhammer3.exe')
    try:
        m=json.loads((HERE/'r71_tick_safety_manifest.json').read_text())
        print(json.dumps(check(Path(sys.argv[1]).read_bytes(),m),indent=2))
    except (OSError,ValueError,IndexError,struct.error) as e:
        print('FAIL_CLOSED',str(e));raise SystemExit(2)
