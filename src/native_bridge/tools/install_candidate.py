"""Transactional install/rollback of ONLY our two mod files, explicit opt-in.
No game execution, EXE patching or load-order rewriting. Receipt-gated.
"""
from __future__ import annotations
import argparse,datetime,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
from product import *
MANAGED={'wh3_native_bridge.dll':'wh3_native_bridge.dll','zzz_queue_probe.pack':'data/zzz_queue_probe.pack'}
def atomic_copy(source:Path,dest:Path)->None:
 dest.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix=dest.name+'.wh3tmp_',dir=dest.parent)
 try:
  with os.fdopen(fd,'wb') as w,source.open('rb') as r:shutil.copyfileobj(r,w);w.flush();os.fsync(w.fileno())
  os.replace(tmp,dest)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def ensure_game_closed()->None:
 if os.name!='nt':raise FormatError('Install/rollback requires Windows; portable tests call file-only transactions')
 r=subprocess.run(['tasklist','/FI','IMAGENAME eq Warhammer3.exe','/FO','CSV','/NH'],capture_output=True,text=True,check=False)
 if r.returncode or 'warhammer3.exe' in r.stdout.lower():raise FormatError('Close Warhammer3.exe before changing mod files')
def is_carrier_enabled(text:str)->bool:
 text=re.sub(r'/\*.*?\*/','',text,flags=re.S)
 return re.search(r'^\s*mod\s+"zzz_queue_probe\.pack"\s*;\s*(?://[^\r\n]*)?$',text,re.M|re.I) is not None

def candidate_check(root:Path,game:Path)->dict:
 verify_sums(root);verify_sources(root)
 p=root/'candidate_manifest.json'
 if not p.is_file():raise FormatError('No Windows-built candidate manifest: SOURCE ZIP IS NOT INSTALLABLE')
 m=json.loads(p.read_text(encoding='utf-8'))
 if m.get('windows_build')!='PASS' or m.get('windows_private_process_smoke')!='PASS':raise FormatError('Windows receipt missing')
 if m.get('source_digest')!=code_digest(root):raise FormatError('Built-source receipt mismatch')
 if m.get('experimental_issue_build'):raise FormatError('Experimental issue build is review-only; installer refuses it')
 preflight(game/'Warhammer3.exe',root)
 for n,h in m.get('payload_sha256',{}).items():
  if n not in ('wh3_native_bridge.dll','zzz_queue_probe.pack','minhook.x64.dll') or file_hash(root/'payload'/n)!=h:raise FormatError('Payload checksum mismatch')
 if set(m.get('payload_sha256',{}))!={'wh3_native_bridge.dll','zzz_queue_probe.pack','minhook.x64.dll'}:raise FormatError('Payload manifest incomplete')
 verify_candidate_pe(root/'payload/wh3_native_bridge.dll')
 if file_hash(game/'minhook.x64.dll')!=BASELINE_HASHES['minhook.x64.dll']:raise FormatError('Installed MinHook differs; no overwrite performed')
 for n,relative in MANAGED.items():
  if file_hash(game/relative)!=BASELINE_HASHES[n]:raise FormatError('Managed baseline differs: '+relative)
 used=game/'used_mods.txt'
 if not used.is_file() or not is_carrier_enabled(used.read_text(encoding='utf-8-sig',errors='replace')):raise FormatError('Existing used_mods.txt does not mention the test carrier; configuration unchanged')
 return m
def install_transaction(root:Path,game:Path,backup:Path,expected:dict)->dict:
 # Independently checks current files again immediately before modification.
 for n,rel in MANAGED.items():
  if file_hash(game/rel)!=BASELINE_HASHES[n]:raise FormatError('Baseline changed before write')
 backup.mkdir(parents=True,exist_ok=False)
 record={'schema':1,'game_root':str(game.resolve()),'files':[],'state':'PREPARED'}
 for n,rel in MANAGED.items():
  shutil.copy2(game/rel,backup/n)
  record['files'].append({'relative':rel,'backup_name':n,'old_sha256':file_hash(backup/n),'new_sha256':file_hash(root/'payload'/n)})
 save_json(backup/'rollback_manifest.json',record)
 try:
  for row in record['files']:
   n=row['backup_name'];rel=row['relative']
   if file_hash(root/'payload'/n)!=expected[n]:raise FormatError('Candidate changed before write')
   atomic_copy(root/'payload'/n,game/rel)
   if file_hash(game/rel)!=row['new_sha256']:raise FormatError('Post-write verification failed')
  record['state']='INSTALLED';save_json(backup/'rollback_manifest.json',record);return record
 except Exception:
  record['state']='ROLLED_BACK_AFTER_ERROR'
  for row in record['files']:atomic_copy(backup/row['backup_name'],game/row['relative'])
  save_json(backup/'rollback_manifest.json',record);raise

def rollback_transaction(backup:Path,game:Path)->dict:
 m=json.loads((backup/'rollback_manifest.json').read_text(encoding='utf-8'))
 if Path(m['game_root']).resolve()!=game.resolve():raise FormatError('Backup is for a different game folder')
 rows=m['files']
 if len(rows)!=2 or {r['relative'] for r in rows}!=set(MANAGED.values()):raise FormatError('Rollback scope invalid')
 for row in rows:
  if row['backup_name'] not in MANAGED or MANAGED[row['backup_name']]!=row['relative']:raise FormatError('Unsafe rollback entry')
  if file_hash(backup/row['backup_name'])!=row['old_sha256']:raise FormatError('Backup changed')
  if file_hash(game/row['relative']) not in (row['old_sha256'],row['new_sha256']):raise FormatError('Installed file changed by another writer; rollback refused')
 for row in rows:atomic_copy(backup/row['backup_name'],game/row['relative'])
 m['state']='ROLLED_BACK';save_json(backup/'rollback_manifest.json',m);return m

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--game-root',type=Path,required=True);ap.add_argument('--apply',action='store_true');ap.add_argument('--accept-unvalidated-hooks',action='store_true');ap.add_argument('--rollback',type=Path);a=ap.parse_args()
 try:
  ensure_game_closed()
  if a.rollback:
   if not a.apply:print('Rollback dry run: '+str(a.rollback));return 0
   print(json.dumps(rollback_transaction(a.rollback,a.game_root),indent=2));return 0
  m=candidate_check(ROOT,a.game_root)
  if not a.apply:print('INSTALL_PREFLIGHT=PASS. No files changed. Candidate hooks have no game-runtime approval.');return 0
  if not a.accept_unvalidated_hooks:raise FormatError('Explicit --accept-unvalidated-hooks required; this is not a gameplay-validated release')
  backup=a.game_root/('wh3_bridge_backup_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
  install_transaction(ROOT,a.game_root,backup,m['payload_sha256']);print('INSTALLED. ROLLBACK_BACKUP='+str(backup));return 0
 except Exception as e:print('FAIL:',e);return 1
if __name__=='__main__':raise SystemExit(main())
