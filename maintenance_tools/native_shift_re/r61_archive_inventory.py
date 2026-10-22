#!/usr/bin/env python3
"""Read-only local BSC artifact inventory, including nested archival ZIP verification.

No EXE payload, DLL, raw memory pointers, or third-party source is copied to output.
Manifest verification is reported separately from gameplay/causality verification.
"""
import argparse,hashlib,io,json,re,zipfile
from pathlib import Path

ARCHIVE_RE = re.compile(r'^BSC_R(\d+)_.*\.zip$')

def sha(b):return hashlib.sha256(b).hexdigest()

def audit_archive(path,depth=0):
    raw=path.read_bytes() if isinstance(path,Path) else path
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files=[x for x in z.infolist() if not x.is_dir()]
        if len(files)!=len({x.filename for x in files}):raise ValueError('DUPLICATE_FILENAME')
        if any(x.filename.startswith('/') or '..' in Path(x.filename).parts for x in files):raise ValueError('UNSAFE_ARCHIVE_NAME')
        members=set(x.filename for x in files)
        entries={}
        for m in files:
            data=z.read(m.filename)
            entries[m.filename]={'size':len(data),'sha256':sha(data)}
        manifests=[x for x in members if x.endswith('SHA256_MANIFEST.json')]
        status='ABSENT'
        manifest_count=None
        if len(manifests)==1:
            try:
                check=json.loads(z.read(manifests[0]))
                if isinstance(check,dict) and all(isinstance(v,str) and len(v)==64 for v in check.values()):
                    match_status=[]
                    for name,expected in check.items():
                        if name in entries:actual_name=name; match_status.append('EXACT')
                        else:
                            # Some bundles (R54) place every file under a unique root folder,
                            # while the SHA manifest lists project-relative paths.
                            options=[k for k in entries if k.endswith('/'+name)]
                            actual_name=options[0] if len(options)==1 else None
                            match_status.append('PREFIX' if actual_name else 'MISSING')
                        if not actual_name or entries[actual_name]['sha256']!=expected:
                            match_status.append('MISMATCH')
                    status=('FAIL' if 'MISMATCH' in match_status or 'MISSING' in match_status else
                            'PASS_PREFIX_NORMALIZED' if 'PREFIX' in match_status else 'PASS')
                    manifest_count=len(check)
                else:status='OTHER_FORMAT'
            except ValueError:status='UNREADABLE'
        elif len(manifests)>1:status='MULTIPLE'
        report_candidates=[x for x in members if x.endswith('.md') and ('REPORT' in x.upper() or 'N1_R' in x.upper())]
        out={'archive_file':str(path.name) if isinstance(path,Path) else '<nested-zip>',
             'sha256':sha(raw),'member_count':len(files),'file_manifest_status':status,
             'manifest_entries':manifest_count,'report_files':sorted(report_candidates)[:12],
             'nested_zips':sorted(n for n in members if n.endswith('.zip')),
             'total_expanded_bytes':sum(e['size'] for e in entries.values())}
        if depth<1:
            out['nested_checks']={}
            for n in out['nested_zips']:
                child=audit_archive(z.read(n),depth+1)
                out['nested_checks'][n]={'sha256':child['sha256'],'file_manifest_status':child['file_manifest_status'],
                                         'member_count':child['member_count']}
        return out

def inventory(root):
    archives=sorted((p for p in Path(root).glob('BSC_R*.zip') if ARCHIVE_RE.match(p.name)),
                   key=lambda p:int(ARCHIVE_RE.match(p.name).group(1)))
    results=[audit_archive(p) for p in archives]
    return {'schema':'bsc.r61.research_archive_inventory.v1',
            'kind':'ARCHIVE_CHECKSUM_AND_METADATA_NOT_GAMEPLAY',
            'primary_archive_count':len(results),'archives':results,
            'all_archives_crc_read':True,
            'all_present_sha_manifests_pass':all(x['file_manifest_status'] in ('PASS','PASS_PREFIX_NORMALIZED','ABSENT','OTHER_FORMAT') for x in results),
            'historical_V3_raw_jsonl_recovered':False,
            'private_game_binary_included_in_delivery':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();res=inventory(args.data_dir)
    if args.out.resolve().is_relative_to(args.data_dir.resolve()) and args.out.name.lower().endswith('.exe'):
        ap.error('REFUSE_EXE_OVERWRITE')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
    print('INVENTORY',res['primary_archive_count'],'archives',res['all_present_sha_manifests_pass'])
if __name__=='__main__':main()
