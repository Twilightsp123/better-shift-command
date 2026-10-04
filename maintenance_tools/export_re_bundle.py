#!/usr/bin/env python3
"""Stage-7 fallback evidence bundle for unresolved WH3 native-map sites.

The ZIP deliberately excludes Warhammer3.exe. It contains only relocation
metadata, candidate function bytes/fingerprints, and seed RVAs so a maintainer
can open the local EXE in Ghidra/BinDiff without repeating earlier triage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import tempfile
import zipfile
from pathlib import Path

from pe_tools import PE, function_fingerprint, parse_rva
from resolve_relations import load_map, run as resolve_run


def touched_relationships(native_map: dict, site: str) -> list[dict]:
    out=[]
    for rel in native_map.get("relationships",[]):
        values=[]
        for key in ("left","right","site","caller","callee"):
            if key in rel:
                values.append(rel[key])
        values.extend(rel.get("anchors",[]))
        if site in values:
            out.append(rel)
    return out


def build(exe: Path, map_path: Path, out_zip: Path, force: bool=False) -> dict:
    native_map=load_map(map_path)
    report=resolve_run(exe,map_path)
    unresolved=[name for name,row in report["core"].items() if not row["resolved"]]
    if not unresolved and not force:
        raise ValueError("Stage 6 resolved every core site; Stage 7 fallback is not needed")

    with exe.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        pe=PE(mm)
        sha=hashlib.sha256(mm).hexdigest()
        items={}
        for name in unresolved:
            row=report["core"][name]
            spec=native_map["core"][name]
            candidates=[]
            for text_rva in row["candidates"]:
                rva=parse_rva(text_rva)
                fp=function_fingerprint(mm,pe,rva)
                fn=pe.runtime_function(rva)
                if fn is not None:
                    raw=pe.read_rva(fn.begin,min(fn.size,4096))
                    begin=fn.begin
                else:
                    begin=max(0,rva-128)
                    raw=pe.read_rva(begin,256)
                candidates.append({
                    "rva":f"0x{rva:08X}",
                    "function_fingerprint":fp,
                    "evidence_begin":f"0x{begin:08X}",
                    "evidence_bytes":None if raw is None else raw.hex(),
                })
            items[name]={
                "old_rva":spec["rva"],
                "old_guard":spec["guard"],
                "normalization":spec.get("normalization"),
                "relationships":touched_relationships(native_map,name),
                "method":row["method"],
                "candidates":candidates,
            }

    manifest={
        "schema":1,
        "tool":"export_re_bundle",
        "source_map_id":native_map["map_id"],
        "source_map_path":str(map_path),
        "exe_sha256":sha,
        "unresolved_sites":unresolved,
        "exe_included":False,
        "purpose":"Ghidra/BinDiff fallback only after Stages 1-6 fail to uniquely resolve a mandatory site",
    }
    payload={"manifest":manifest,"sites":items,"relationship_audit":report["relationship_audit"]}
    seeds=["# site\trva\tlabel"]
    for name,item in items.items():
        for i,c in enumerate(item["candidates"],1):
            seeds.append(f"{name}\t{c['rva']}\tBSC_candidate_{name}_{i}")

    out_zip.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out_zip,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
        z.writestr("unresolved.json",json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
        z.writestr("seeds.tsv","\n".join(seeds)+"\n")
        z.writestr("README.txt",
            "Open the matching local Warhammer3.exe in Ghidra.\n"
            "Run maintenance_tools/ghidra/BscRelocationSeeds.py with unresolved.json as its first script argument.\n"
            "The script only labels candidate RVAs; semantic approval remains manual.\n")
    return manifest


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe",required=True,type=Path)
    ap.add_argument("--map",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--force",action="store_true")
    args=ap.parse_args()
    result=build(args.exe,args.map,args.out,args.force)
    print(json.dumps(result))


if __name__=="__main__":
    main()
