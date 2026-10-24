#!/usr/bin/env python3
"""SHA-gated, read-only R68 mode evidence. No game loading, memory writes or Hook."""
import hashlib,json,struct,sys
from pathlib import Path
BASE=0x140000000
MANIFEST=Path(__file__).with_name('r68_member_mode_pins.json')
class EvidenceMismatch(ValueError):pass
def model(old,new,a=7,b=11):
    if old==new:return (old,a,b,False)
    if old in (1,2) and new==0:a=b=0
    return (new,a,b,True)
def verify(data,manifest):
    if len(data)!=manifest['size_bytes'] or hashlib.sha256(data).hexdigest()!=manifest['sha256']:
        raise EvidenceMismatch('EXE_SHA_OR_SIZE_DRIFT')
    if data[:2]!=b'MZ':raise EvidenceMismatch('NOT_MZ')
    n=struct.unpack_from('<I',data,0x3c)[0]
    if data[n:n+4]!=b'PE\0\0' or struct.unpack_from('<H',data,n+4)[0]!=0x8664 or struct.unpack_from('<H',data,n+24)[0]!=0x20b:
        raise EvidenceMismatch('NOT_PE_AMD64')
    if struct.unpack_from('<Q',data,n+48)[0]!=BASE:raise EvidenceMismatch('IMAGEBASE_DRIFT')
    count=struct.unpack_from('<H',data,n+6)[0]
    opt=struct.unpack_from('<H',data,n+20)[0]
    secs=[]
    for i in range(count):
        p=n+24+opt+i*40
        _,r,size,off=struct.unpack_from('<IIII',data,p+8)
        if off+size>len(data):raise EvidenceMismatch('SECTION_BOUNDS')
        secs.append((r,size,off))
    def get(r,size):
        for base,length,off in secs:
            if base<=r and r+size<=base+length:return data[off+r-base:off+r-base+size]
        raise EvidenceMismatch('RVA_BOUNDS')
    for k,v in manifest['pins'].items():
        raw=bytes.fromhex(v)
        if get(int(k,16),len(raw))!=raw:raise EvidenceMismatch('PIN_DRIFT_'+k)
    for vt,slots in manifest['vtables'].items():
        for slot,target in slots.items():
            value=struct.unpack('<Q',get(int(vt,16)+int(slot,16),8))[0]
            if value!=BASE+int(target,16):raise EvidenceMismatch('VTABLE_DRIFT')
    for p,t in manifest['e8_edges'].items():
        addr=int(p,16); b=get(addr,5)
        if b[0]!=0xe8 or addr+5+struct.unpack_from('<i',b,1)[0]!=int(t,16):
            raise EvidenceMismatch('E8_DRIFT')
    pins=manifest['pins']
    for k,b in {'0307d9d9':'21913c020000','0307d9df':'2191c8010000','0307d9e5':'899104010000','03070b66':'41ff9300010000','03070b9c':'41ff93e8000000','03071ecf':'ff90e0000000','0307facc':'ff90e0000000','0316143f':'ff90e0000000','031647a4':'ff90e0000000'}.items():
        if pins[k]!=b:raise EvidenceMismatch('SEMANTIC_DRIFT_'+k)
    return {'grade':'EXACT_EXE_STATIC','pin_count':len(pins),'vtable_slots':sum(map(len,manifest['vtables'].values())),'shift_hit_proven':False,'patch_authorized':False}
if __name__=='__main__':
    try:
        m=json.loads(MANIFEST.read_text()); print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
    except (IndexError,ValueError,OSError,struct.error) as e:
        print('FAIL_CLOSED',e);sys.exit(2)
