#!/usr/bin/env python3
"""R83 exact-EXE static field owner audit. Never accesses live WH3 process."""
from pathlib import Path
import hashlib,json,struct,sys
BASE=0x140000000
HERE=Path(__file__).parent
class Reject(ValueError):pass
def temporal(member_ctx,root_ctx,group_ctx,route_epoch=None,member_epoch=None):
    if not member_ctx or not root_ctx or not group_ctx:raise Reject('MISSING_CONTEXT')
    return {'same_context':member_ctx==root_ctx==group_ctx,
            'epoch_matches_if_known':None if route_epoch is None or member_epoch is None else route_epoch==member_epoch,
            'actual_queued_shift_identity_proven':False,'gameplay_patch_authorized':False}
def verify(data,m):
    if len(data)!=m['exe_size'] or hashlib.sha256(data).hexdigest()!=m['exe_sha256']:raise Reject('SHA_SIZE_DRIFT')
    if data[:2]!=b'MZ':raise Reject('MZ')
    p=struct.unpack_from('<I',data,0x3c)[0]
    if not 0x40<=p<0x1000 or data[p:p+4]!=b'PE\0\0':raise Reject('PE')
    if struct.unpack_from('<H',data,p+4)[0]!=0x8664 or struct.unpack_from('<H',data,p+24)[0]!=0x20b:raise Reject('AMD64')
    if struct.unpack_from('<Q',data,p+48)[0]!=BASE:raise Reject('IMAGEBASE')
    ss=[];opt=struct.unpack_from('<H',data,p+20)[0]
    for k in range(struct.unpack_from('<H',data,p+6)[0]):
        j=p+24+opt+k*40
        _,r,n,o=struct.unpack_from('<IIII',data,j+8)
        if o+n>len(data):raise Reject('SECTION')
        ss.append((r,n,o))
    def read(r,n):
        for a,z,o in ss:
            if a<=r and r+n<=a+z:return data[o+r-a:o+r-a+n]
        raise Reject('RVA')
    ex,size=struct.unpack_from('<II',data,p+24+112+3*8)
    funcs={}
    for k in range(size//12):
        a,z,u=struct.unpack('<III',read(ex+12*k,12));funcs[a]=z
    for name,(lo,hi) in m['ranges'].items():
        if name not in m['leaf_names'] and funcs.get(int(lo,16))!=int(hi,16):
            raise Reject('UNWIND_'+name)
        if name in m['leaf_names'] and int(lo,16) in funcs:raise Reject('LEAF_DRIFT')
    for site,record in m['pins'].items():
        r=int(site,16);val=bytes.fromhex(record['hex']);lo,hi=m['ranges'][record['owner']]
        if not int(lo,16)<=r or r+len(val)>int(hi,16):raise Reject('PIN_OWNER_'+site)
        if read(r,len(val))!=val:raise Reject('PIN_DRIFT_'+site)
    for site,target in m['e8_edges'].items():
        r=int(site,16);val=read(r,5)
        if val[0]!=0xe8 or r+5+struct.unpack_from('<i',val,1)[0]!=int(target,16):
            raise Reject('CALL_DRIFT_'+site)
    required={'0300b19f':'488bda','0300b1a9':'488bf9','0300b23a':'4c894938',
              '0300bad6':'888720070000','03012fe7':'488b4638',
              '03052f62':'488b4358','03052f6d':'48898320070000',
              '03020a75':'48899ef8320000','030c7dca':'48894110'}
    for r,val in required.items():
        if m['pins'][r]['hex']!=val:raise Reject('SEMANTIC_'+r)
    return {'grade':'EXACT_CURRENT_EXE_STATIC_BOUNDED','pins':len(m['pins']),
            'E8':len(m['e8_edges']),'unwind_functions':len(m['ranges'])-len(m['leaf_names']),
            'root_context_rebind_proven':False,'member_controller_runtime_rebind_proven':False,
            'queued_shift_generation_proven':False,'gameplay_patch_authorized':False}
if __name__=='__main__':
    try:
        m=json.loads((HERE/'r83_context_manifest.json').read_text())
        print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
    except (OSError,IndexError,ValueError,struct.error) as e:
        print('FAIL_CLOSED',e);raise SystemExit(2)
