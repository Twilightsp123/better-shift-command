"""Read-only PE inventory for BSC reverse work. It never loads or modifies an EXE.
No dependency beyond Python 3.10+. All pointers/RVAs are serialized as strings.
"""
from __future__ import annotations
import argparse, hashlib, json, mmap, re, struct
from pathlib import Path
from typing import Any

TOKENS = ('number_of_men_alive','initial_number_of_men','is_in_melee',
          'current_target','unit_distance','position','is_moving','is_idle','ordered_width')

class PE:
    def __init__(self, data: Any):
        self.data = data
        def need(o: int, n: int) -> None:
            if o < 0 or n < 0 or o + n > len(data): raise ValueError('truncated PE')
        need(0,64)
        if data[:2] != b'MZ': raise ValueError('not MZ')
        off=struct.unpack_from('<I',data,0x3c)[0];need(off,24)
        if data[off:off+4] != b'PE\0\0': raise ValueError('not PE')
        machine, count, timestamp, _, _, opt_size, _=struct.unpack_from('<HHIIIHH',data,off+4)
        if machine!=0x8664 or not 1<=count<=96: raise ValueError('requires x64 PE with sane sections')
        opt=off+24;need(opt,opt_size)
        if opt_size<112 or struct.unpack_from('<H',data,opt)[0]!=0x20b: raise ValueError('requires PE32+')
        self.image_base=struct.unpack_from('<Q',data,opt+24)[0]
        self.image_size=struct.unpack_from('<I',data,opt+56)[0]
        self.headers_size=struct.unpack_from('<I',data,opt+60)[0];self.timestamp=timestamp;self.sections=[]
        need(opt+opt_size,count*40)
        for i in range(count):
            o=opt+opt_size+i*40;name=data[o:o+8].split(b'\0')[0].decode('ascii','replace')
            vs,va,rs,rp=struct.unpack_from('<IIII',data,o+8);flags=struct.unpack_from('<I',data,o+36)[0]
            need(rp,rs)
            self.sections.append(dict(name=name,rva=va,virtual_size=vs,raw_size=rs,raw_offset=rp,flags=flags))
    def file_to_rva(self, off: int) -> int | None:
        if 0<=off<min(self.headers_size,len(self.data)): return off
        for s in self.sections:
            if s['raw_offset']<=off<s['raw_offset']+s['raw_size']:
                return s['rva']+off-s['raw_offset']
        return None
    def rva_to_file(self, rva: int, size: int=1) -> int | None:
        if 0<=rva and rva+size<=min(self.headers_size,len(self.data)): return rva
        for s in self.sections:
            if s['rva']<=rva and rva+size<=s['rva']+s['raw_size']:
                return s['raw_offset']+rva-s['rva']
        return None # virtual zero-filled bytes are not file-backed
    def occurrences(self, token: str, cap: int=64) -> list[dict]:
        rows=[]
        for enc in ('ascii','utf-16le'):
            needle=token.encode(enc)+(b'\0' if enc=='ascii' else b'\0\0');start=0
            while len(rows)<cap:
                off=self.data.find(needle,start)
                if off<0: break
                start=off+len(needle);rva=self.file_to_rva(off)
                if rva is not None:rows.append(dict(token=token,encoding=enc,file_offset=hex(off),rva=hex(rva)))
        return rows

def inventory(path: Path, backend: Path) -> dict:
    text=backend.read_text(encoding='utf-8')
    locked=re.search(r'constexpr const char\* exe_hash="([a-f0-9]{64})"',text)
    specs=re.findall(r'\{(0x[0-9a-fA-F]+),"([0-9a-fA-F]+)"\}',text)
    names_match=re.search(r'constexpr const char\* hook_names\[\]=\{(.*?)\};',text,re.S)
    names=re.findall(r'"([^"]+)"',names_match.group(1)) if names_match else []
    if not locked or len(specs)!=16 or len(names)!=16: raise ValueError('backend anchor inventory not recognized')
    if not path.is_file() or path.stat().st_size==0: raise ValueError('EXE missing or empty')
    with path.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        pe=PE(mm);sha=hashlib.sha256(mm).hexdigest();anchors=[]
        for name,(rva_text,guard) in zip(names,specs):
            rva=int(rva_text,16);expected=bytes.fromhex(guard);off=pe.rva_to_file(rva,len(expected))
            actual=bytes(mm[off:off+len(expected)]).hex() if off is not None else None
            anchors.append(dict(name=name,rva=hex(rva),expected=guard,actual=actual,match=actual==guard))
        return dict(schema=1,exe_name=path.name,exe_sha256=sha,locked_sha256=locked.group(1),
            build_match=sha==locked.group(1),image_base=hex(pe.image_base),size_of_image=hex(pe.image_size),
            pe_timestamp=hex(pe.timestamp),sections=pe.sections,anchors=anchors,
            lua_name_candidates=[row for name in TOKENS for row in pe.occurrences(name)],
            classification='STATIC_CANDIDATES_ONLY_NOT_VALIDATED_OFFSETS',exe_modified=False)

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--exe',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--backend',type=Path,default=Path(__file__).resolve().parents[1]/'src/native_bridge/src/platform_windows.cpp')
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    data=inventory(a.exe,a.backend)
    (a.out/'exe_inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# BSC seed list: tag<TAB>RVA. String hits are candidates, not discovered fields.']
    lines+=['HOOK_'+r['name']+'\t'+r['rva'] for r in data['anchors'] if r['match']]
    lines+=['LUA_'+r['token']+'_'+r['encoding']+'\t'+r['rva'] for r in data['lua_name_candidates']]
    (a.out/'seeds.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'build_match':data['build_match'],'anchor_matches':sum(r['match'] for r in data['anchors']),
        'string_candidates':len(data['lua_name_candidates']),'exe_modified':False}))
    if not data['build_match'] or not all(r['match'] for r in data['anchors']):
        raise SystemExit('BUILD_MISMATCH: inventory saved; do not enable current native mapping or reuse old offsets')
if __name__=='__main__':main()
