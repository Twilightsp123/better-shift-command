"""R86 focused current-original-EXE read-only SHA, PE and opcode verifier."""
from pathlib import Path
import hashlib,json,struct
class Drift(ValueError):pass
def verify(data,m):
    if len(data)!=m["size"] or hashlib.sha256(data).hexdigest()!=m["sha256"]:raise Drift("SHA_FAIL_CLOSED")
    if data[:2]!=b"MZ":raise Drift("MZ")
    pe=struct.unpack_from("<I",data,0x3c)[0]
    if pe<0x40 or pe>=0x1000 or data[pe:pe+4]!=b"PE\0\0":raise Drift("PE")
    if struct.unpack_from("<H",data,pe+4)[0]!=0x8664 or struct.unpack_from("<H",data,pe+24)[0]!=0x20b:raise Drift("PE64")
    if struct.unpack_from("<Q",data,pe+48)[0]!=0x140000000:raise Drift("BASE")
    opt=struct.unpack_from("<H",data,pe+20)[0];secs=[]
    for i in range(struct.unpack_from("<H",data,pe+6)[0]):
        j=pe+24+opt+i*40;_,r,z,off=struct.unpack_from("<IIII",data,j+8)
        if off+z>len(data):raise Drift("SEC")
        secs.append((r,z,off))
    def read(r,n):
        for a,z,off in secs:
            if a<=r and r+n<=a+z:return data[off+r-a:off+r-a+n]
        raise Drift("RVA")
    rva,size=struct.unpack_from("<II",data,pe+24+112+3*8);func={}
    for i in range(size//12):
        a,z,u=struct.unpack("<III",read(rva+i*12,12));func[a]=z
    for name,(start,end) in m["functions"].items():
        if func.get(int(start,16))!=int(end,16):raise Drift("UNWIND_"+name)
    for site,item in m["pins"].items():
        r=int(site,16);b=bytes.fromhex(item["hex"]);lo,hi=m["functions"][item["owner"]]
        if r<int(lo,16) or r+len(b)>int(hi,16) or read(r,len(b))!=b:raise Drift("PIN_"+site)
    for site,target in m["e8"].items():
        r=int(site,16);b=read(r,5)
        if b[0]!=0xe8 or r+5+struct.unpack_from("<i",b,1)[0]!=int(target,16):raise Drift("E8_"+site)
    for site,target in m["jcc"].items():
        r=int(site,16);b=bytes.fromhex(m["pins"][site]["hex"])
        v=r+2+struct.unpack_from("<b",b,1)[0] if len(b)==2 else r+6+struct.unpack_from("<i",b,2)[0]
        if v!=int(target,16):raise Drift("JCC_"+site)
    return {"grade":"MATCHING_EXE_STATIC_ONLY","focus_pins":len(m["pins"]),
       "calls":len(m["e8"]),"branches":len(m["jcc"]),"owners":len(m["functions"]),
       "actual_Shift_formation_member_tracks":False,"gameplay_patch_authorized":False}
