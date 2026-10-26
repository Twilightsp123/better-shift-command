#!/usr/bin/env python3
"""BSC R75 SHA-gated bounded E8 caller / unwind verifier. Offline only."""
from pathlib import Path
import bisect,hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent
BASE=0x140000000
class Closed(ValueError): pass

def verify(exe, m):
    b=Path(exe).read_bytes()
    if len(b)!=m['exe_size'] or hashlib.sha256(b).hexdigest()!=m['exe_sha256']:
        raise Closed('SHA_FAIL_CLOSED')
    if b[:2]!=b'MZ': raise Closed('MZ')
    p=struct.unpack_from('<I',b,0x3c)[0]
    if p>0x1000 or b[p:p+4]!=b'PE\x00\x00': raise Closed('PE')
    if struct.unpack_from('<H',b,p+4)[0]!=0x8664 or struct.unpack_from('<H',b,p+24)[0]!=0x20b: raise Closed('PE64')
    if struct.unpack_from('<Q',b,p+48)[0]!=BASE: raise Closed('BASE')
    opt=struct.unpack_from('<H',b,p+20)[0]
    sec={}
    for i in range(struct.unpack_from('<H',b,p+6)[0]):
        o=p+24+opt+i*40
        name=b[o:o+8].split(b'\0')[0].decode('ascii','replace')
        _,rva,length,raw=struct.unpack_from('<IIII',b,o+8)
        sec[name]=(rva,length,raw)
    def get(rva,size):
        for start,length,raw in sec.values():
            if start<=rva and rva+size<=start+length and raw+rva-start+size<=len(b):
                return b[raw+rva-start:raw+rva-start+size]
        raise Closed('RVA_'+hex(rva))
    directory,size=struct.unpack_from('<II',b,p+24+112+3*8)
    entries=[struct.unpack('<III',get(directory+i*12,12)) for i in range(size//12)]
    starts=[e[0] for e in entries]
    def owner(rva):
        j=bisect.bisect_right(starts,rva)-1
        if j<0 or rva>=entries[j][1]: raise Closed('UNWIND_'+hex(rva))
        return entries[j][0]
    if m['section'] not in sec: raise Closed('UDATA_MISSING')
    rva,length,offset=sec[m['section']]
    total=0
    for key,expected in m['direct_e8_census'].items():
        target=int(key,16)
        found=[];pos=offset
        while True:
            pos=b.find(b'\xe8',pos,offset+length-4)
            if pos<0:break
            site=rva+pos-offset
            if site+5+struct.unpack_from('<i',b,pos+1)[0]==target:
                found.append(site)
            pos+=1
        declared=[int(site,16) for site,_ in expected]
        if found!=declared: raise Closed('CENSUS_DRIFT_'+key)
        for site,fn in expected:
            addr=int(site,16)
            if owner(addr)!=int(fn,16):raise Closed('OWNER_DRIFT_'+site)
            bytes5=get(addr,5)
            if bytes5[0]!=0xe8 or addr+5+struct.unpack_from('<i',bytes5,1)[0]!=target:
                raise Closed('E8_DRIFT_'+site)
            total+=1
    return {'grade':'EXACT_EXE_STATIC_ONLY','direct_e8_sites':total,
            'actual_shift_overlap':False,'same_group_generation_proven':False,
            'native_patch_authorized':False}

def fixture(events):
    if type(events)!=list or len(events)>64:raise Closed('BUDGET')
    sessions={}
    for index,e in enumerate(events):
        if type(e)!=dict or set(e)!={'op','task','generation','thread'}:raise Closed('SCHEMA')
        op,task,g,t=e['op'],e['task'],e['generation'],e['thread']
        if op not in ('begin_sender','end_sender','begin_rebuild','end_rebuild') or type(task)!=str or not task or type(g)!=int or g<=0 or type(t)!=int or t<=0:
            raise Closed('EVENT')
        mode='sender' if op.endswith('sender') else 'rebuild'
        key=(mode,task,g)
        if op.startswith('begin'):
            if key in sessions:raise Closed('DUPLICATE')
            sessions[key]=[index,None,t]
        else:
            if key not in sessions or sessions[key][1] is not None or sessions[key][2]!=t:raise Closed('LIFETIME')
            sessions[key][1]=index
    if any(end is None for begin,end,t in sessions.values()):raise Closed('UNBALANCED')
    overlap=0
    for (kind1,task1,gen1),a in sessions.items():
        if kind1!='sender':continue
        for (kind2,task2,gen2),b in sessions.items():
            if kind2=='rebuild' and gen1==gen2 and max(a[0],b[0])<min(a[1],b[1]):
                overlap+=1
    return {'grade':'SYNTHETIC_ONLY','interval_overlap':overlap,
            'real_game_thread_overlap_proven':False,
            'gameplay_patch_authorized':False}
if __name__=='__main__':
    try:
        m=json.loads((HERE/'r75_scheduler_caller_manifest.json').read_text())
        print(json.dumps(verify(sys.argv[1],m),indent=2))
    except (IndexError,OSError,ValueError,struct.error) as e:
        print('FAIL_CLOSED',e);sys.exit(2)
