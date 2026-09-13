"""Deterministic source-bundle packaging; clean-copy validation is a separate run."""
from __future__ import annotations
import argparse,json,shutil,tempfile
from pathlib import Path
from product import ROOT,file_hash,zip_tree,save_json,verify_sources,safe_extract,verify_sums
EXCLUDED={'output','build','build-local','.git','__pycache__'}
def write_sums(root:Path)->int:
 rows=[]
 for p in sorted(root.rglob('*')):
  rel=p.relative_to(root)
  if p.is_file() and p.name!='SHA256SUMS.txt' and not (set(rel.parts)&EXCLUDED) and p.suffix not in ('.pyc','.pyo'):
   rows.append(file_hash(p)+'  '+rel.as_posix())
 (root/'SHA256SUMS.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8');return len(rows)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--zip',type=Path,required=True);a=ap.parse_args()
 verify_sources()
 with tempfile.TemporaryDirectory(prefix='wh3_release_') as td:
  stage=Path(td)/ROOT.name
  shutil.copytree(ROOT,stage,ignore=shutil.ignore_patterns(*EXCLUDED,'*.pyc','*.pyo'))
  n=write_sums(stage);zip_tree(stage,a.zip)
  clean=Path(td)/'unpacked';safe_extract(a.zip,clean);assert verify_sums(clean)==n;verify_sources(clean)
 print(json.dumps({'zip':str(a.zip),'sha256':file_hash(a.zip),'file_count':n,'crc_and_manifest':'PASS'},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
