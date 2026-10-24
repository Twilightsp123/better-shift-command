#!/usr/bin/env python3
"""R70 bounded public pin subset; exact-executable evidence, NO live Hook."""
import hashlib, json, struct, sys
from pathlib import Path
BASE=0x140000000
HERE=Path(__file__).resolve().parent
class ContractError(ValueError):pass
def call_target(site,hexcode):
    raw=bytes.fromhex(hexcode)
    if len(raw)!=5 or raw[0]!=0xe8:raise ContractError("NOT_E8")
    return site+5+struct.unpack_from("<i",raw,1)[0]
def verify(data,manifest):
    if len(data)!=manifest["size"] or hashlib.sha256(data).hexdigest()!=manifest["sha256"]:
        raise ContractError("EXE_SHA_OR_SIZE_MISMATCH")
    if data[:2]!=b"MZ":raise ContractError("NOT_MZ")
    pe=struct.unpack_from("<I",data,0x3c)[0]
    if data[pe:pe+4]!=b"PE\0\0":raise ContractError("NOT_PE")
    if struct.unpack_from("<H",data,pe+4)[0]!=0x8664 or struct.unpack_from("<H",data,pe+24)[0]!=0x20b:raise ContractError("NOT_AMD64")
    if struct.unpack_from("<Q",data,pe+48)[0]!=BASE:raise ContractError("NOT_BASE")
    count=struct.unpack_from("<H",data,pe+6)[0];opt=struct.unpack_from("<H",data,pe+20)[0];sections=[]
    for k in range(count):
        p=pe+24+opt+k*40
        _,r,size,o=struct.unpack_from("<IIII",data,p+8)
        if o+size>len(data):raise ContractError("SECTION_BOUNDS")
        sections.append((r,size,o))
    def get(r,n):
        for a,length,off in sections:
            if a<=r and r+n<=a+length:return data[off+r-a:off+r-a+n]
        raise ContractError("RVA_BOUNDS")
    for addr,raw in manifest["pins"].items():
        r=int(addr,16);v=bytes.fromhex(raw)
        if get(r,len(v))!=v:raise ContractError("PIN_DRIFT_"+addr)
    for addr,target in manifest["e8"].items():
        if call_target(int(addr,16),get(int(addr,16),5).hex())!=int(target,16):
            raise ContractError("CALL_DRIFT_"+addr)
    return {"grade":"EXACT_EXE_STATIC_ONLY","pins":len(manifest["pins"]),
            "mode_reset_to_gate_proven":False,"gameplay_patch_authorized":False}
if __name__=="__main__":
    try:
        m=json.loads((HERE/"r70_focus_pins.json").read_text())
        print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
    except (IndexError,OSError,ValueError,struct.error) as e:
        print("FAIL_CLOSED",str(e));raise SystemExit(2)
