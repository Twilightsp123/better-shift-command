# Ghidra Jython post-script: label BSC relocation candidates from unresolved.json.
# Usage (headless example):
# analyzeHeadless <project_dir> <project_name> -import Warhammer3.exe \
#   -scriptPath maintenance_tools/ghidra \
#   -postScript BscRelocationSeeds.py <path-to-unresolved.json>

import json

args=getScriptArgs()
if not args:
    raise Exception("expected unresolved.json path")
with open(args[0],"r") as f:
    data=json.load(f)

base=currentProgram.getImageBase().getOffset()
listing=currentProgram.getListing()
symbol_table=currentProgram.getSymbolTable()

count=0
for site,item in data.get("sites",{}).items():
    for idx,candidate in enumerate(item.get("candidates",[]),1):
        rva=int(candidate["rva"],16)
        addr=toAddr(base+rva)
        label="BSC_candidate_%s_%d"%(site,idx)
        createLabel(addr,label,True)
        code=listing.getCodeUnitAt(addr)
        if code:
            code.setComment(code.PLATE_COMMENT,
                "BSC relocation fallback candidate\nold RVA: %s\nmethod: %s"%
                (item.get("old_rva"),item.get("method")))
        count+=1
print("BSC relocation labels created: %d"%count)
