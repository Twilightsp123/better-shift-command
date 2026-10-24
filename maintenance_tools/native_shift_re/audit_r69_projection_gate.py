#!/usr/bin/env python3
"""R69 exact-build read-only binary evidence, not a native gameplay patch."""
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
class EvidenceError(ValueError):pass
def synthetic_gate(old,new,value):
    if old!=new and old in (1,2) and new==0:value=0.0
    return {'value':value,'below_threshold':0.01>value}
def verify(data,manifest):
    if len(data)!=manifest['exe_size'] or hashlib.sha256(data).hexdigest()!=manifest['exe_sha256']:
        raise EvidenceError('FAIL_CLOSED_SHA_SIZE')
    if data[:2]!=b'MZ':raise EvidenceError('NOT_MZ')
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if data[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',data,pe+4)[0]!=0x8664 or struct.unpack_from('<H',data,pe+24)[0]!=0x20b:
        raise EvidenceError('NOT_PE64_AMD64')
    if struct.unpack_from('<Q',data,pe+48)[0]!=0x140000000:raise EvidenceError('IMAGEBASE_DRIFT')
    n=struct.unpack_from('<H',data,pe+6)[0];opt=struct.unpack_from('<H',data,pe+20)[0];sections=[]
    for i in range(n):
        p=pe+24+opt+i*40
        _,rva,sz,raw=struct.unpack_from('<IIII',data,p+8)
        if raw+sz>len(data):raise EvidenceError('SECTION_OOB')
        sections.append((rva,sz,raw))
    def get(rva,size):
        for v,n,o in sections:
            if v<=rva and rva+size<=v+n:return data[o+rva-v:o+rva-v+size]
        raise EvidenceError('BAD_RVA')
    except_rva,except_size=struct.unpack_from('<II',data,pe+24+112+3*8)
    funcs={}
    for i in range(except_size//12):
        s,e,u=struct.unpack('<III',get(except_rva+i*12,12));funcs[s]=e
    for fn,(first,last) in manifest['unwind_functions'].items():
        if funcs.get(int(first,16))!=int(last,16):raise EvidenceError('UNWIND_'+fn)
    for s,rec in manifest['pins'].items():
        address=int(s,16);hexstr=rec['hex'];first,last=manifest['unwind_functions'][rec['fn']]
        if not int(first,16)<=address<int(last,16):raise EvidenceError('PIN_RANGE')
        if get(address,len(hexstr)//2)!=bytes.fromhex(hexstr):raise EvidenceError('PIN_DRIFT_'+s)
    for s,t in manifest['e8_edges'].items():
        b=get(int(s,16),5)
        if b[0]!=0xe8 or (int(s,16)+5+struct.unpack_from('<i',b,1)[0])!=int(t,16):
            raise EvidenceError('E8_DRIFT_'+s)
    f=struct.unpack('<f',get(int(manifest['threshold_rva'],16),4))[0]
    if not 0.00999999<f<0.01000001:raise EvidenceError('THRESHOLD_DRIFT')
    return {'whole_instruction_pins':len(manifest['pins']),'e8_edges':len(manifest['e8_edges']),'unwind_functions':len(manifest['unwind_functions']),'float32_gate':f,'root_cause_proven':False,'gameplay_patch_authorized':False}
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: audit_r69_projection_gate.py matching_Warhammer3.exe')
    try:print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),json.loads((HERE/'r69_projection_pins.json').read_text())),indent=2))
    except (OSError,ValueError,struct.error) as e:print('FAIL_CLOSED',e);raise SystemExit(2)
