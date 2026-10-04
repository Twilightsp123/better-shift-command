"""Read-only WH3 PE inventory for the promoted BSC native map.

The address inventory comes from native_maps/CURRENT, never from parsing C++.
Optional sites remain non-gating.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'maintenance_tools'))
from native_map_config import current_map_path
from pe_tools import PE as BasePE, parse_rva

TOKENS=('number_of_men_alive','initial_number_of_men','is_in_melee','current_target','unit_distance','position','is_moving','is_idle','ordered_width')


class PE(BasePE):
    def occurrences(self,token:str,cap:int=64)->list[dict]:
        rows=[]
        for enc in ('ascii','utf-16le'):
            needle=token.encode(enc)+(b'\0' if enc=='ascii' else b'\0\0')
            start=0
            while len(rows)<cap:
                off=self.data.find(needle,start)
                if off<0:
                    break
                start=off+len(needle)
                rva=self.file_to_rva(off)
                if rva is not None:
                    rows.append(dict(token=token,encoding=enc,file_offset=hex(off),rva=hex(rva)))
        return rows


def load_map(path:Path)->dict:
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema')!=1:
        raise ValueError('unsupported native map schema')
    if len(data.get('core',{}))!=16:
        raise ValueError('expected 16 mandatory core sites')
    return data


def inventory(path:Path,map_path:Path)->dict:
    native_map=load_map(map_path)
    locked=native_map['game']['sha256'].lower()
    if not path.is_file() or path.stat().st_size==0:
        raise ValueError('EXE missing or empty')
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        pe=PE(mm);sha=hashlib.sha256(mm).hexdigest()
        def row(name,spec,required):
            rva=parse_rva(spec['rva']);expected=bytes.fromhex(spec['guard'])
            actual=pe.read_rva(rva,len(expected))
            actual_hex=actual.hex() if actual is not None else None
            return dict(name=name,rva=hex(rva),expected=spec['guard'],actual=actual_hex,match=actual_hex==spec['guard'].lower(),required=required)
        core=[row(name,spec,True) for name,spec in native_map['core'].items()]
        optional=[row(name,spec,False) for name,spec in native_map.get('optional',{}).items()]
        core_ok=all(x['match'] for x in core)
        return dict(
            schema=3,
            mode='BSC_PROMOTED_NATIVE_MAP',
            map_id=native_map['map_id'],
            map_path=str(map_path),
            exe_name=path.name,
            exe_sha256=sha,
            locked_sha256=locked,
            build_match=sha==locked,
            core_ready=sha==locked and core_ok,
            image_base=hex(pe.image_base),
            size_of_image=hex(pe.image_size),
            pe_timestamp=hex(pe.timestamp),
            sections=pe.sections,
            core_anchors=core,
            optional_anchors=optional,
            lua_name_candidates=[row for name in TOKENS for row in pe.occurrences(name)],
            classification='CORE_COMMAND_MAP_ONLY; OPTIONAL_PHYSICAL/SMART_SITES_NOT_RELEASE_GATES',
            exe_modified=False,
        )


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--map',type=Path,default=current_map_path(ROOT))
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    data=inventory(a.exe,a.map)
    (a.out/'exe_inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=[f"# BSC seed list from {data['map_id']}. Optional sites never authorize core release."]
    lines += ['CORE_'+r['name']+'\t'+r['rva'] for r in data['core_anchors'] if r['match']]
    lines += ['OPTIONAL_'+r['name']+'\t'+r['rva'] for r in data['optional_anchors'] if r['match']]
    lines += ['LUA_'+r['token']+'_'+r['encoding']+'\t'+r['rva'] for r in data['lua_name_candidates']]
    (a.out/'seeds.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    summary={
        'map_id':data['map_id'],
        'build_match':data['build_match'],
        'core_matches':sum(r['match'] for r in data['core_anchors']),
        'core_total':len(data['core_anchors']),
        'optional_matches':sum(r['match'] for r in data['optional_anchors']),
        'optional_total':len(data['optional_anchors']),
        'core_ready':data['core_ready'],
        'exe_modified':False,
    }
    print(json.dumps(summary))
    if not data['core_ready']:
        raise SystemExit('CORE_BUILD_MISMATCH: inventory saved; do not enable current command mapping')


if __name__=='__main__':
    main()
