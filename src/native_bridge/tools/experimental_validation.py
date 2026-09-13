from __future__ import annotations
import argparse,datetime,json,os,re,shutil,subprocess,tempfile,zipfile
from pathlib import Path
from product import *

STATE=ROOT/'game_validation'/'last_install_state.json'
MANAGED={'wh3_native_bridge.dll':'wh3_native_bridge.dll','zzz_queue_probe.pack':'data/zzz_queue_probe.pack'}
VALIDATION_PACK=ROOT/'dist'/'zzz_queue_probe_validation.pack'
TAG=b'[BRIDGE_GAMEVAL_V050]'
REQUIRED=[b'ENTER',b'CAL_MOVE_ACCEPTED',b'CAL_ATTACK_ACCEPTED',b'EXPERIMENTAL_ARM_PASS',b'OWN_MOVE_PASS',b'STALE_GATE_PASS',b'PLAYER_RMB_PASS',b'OWN_ATTACK_PASS',b'VALIDATION_PASS']

def atomic_copy(src:Path,dst:Path):
 dst.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=dst.name+'.wh3val_',dir=dst.parent)
 try:
  with os.fdopen(fd,'wb') as w,src.open('rb') as r:shutil.copyfileobj(r,w);w.flush();os.fsync(w.fileno())
  os.replace(tmp,dst)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)

def game_closed():
 if os.name!='nt':return
 r=subprocess.run(['tasklist','/FI','IMAGENAME eq Warhammer3.exe','/FO','CSV','/NH'],capture_output=True,text=True,check=False)
 if r.returncode or 'warhammer3.exe' in r.stdout.lower():raise FormatError('Close Warhammer3.exe first')

def carrier_enabled(game:Path):
 p=game/'used_mods.txt'
 if not p.is_file():return False
 t=p.read_text(encoding='utf-8-sig',errors='replace');t=re.sub(r'/\*.*?\*/','',t,flags=re.S)
 return re.search(r'^\s*mod\s+"zzz_queue_probe\.pack"\s*;\s*(?://[^\r\n]*)?$',t,re.M|re.I) is not None

def extract_candidate(z:Path,tmp:Path)->Path:
 safe_extract(z,tmp);p=tmp/'candidate_manifest.json'
 if not p.is_file():raise FormatError('candidate_manifest.json missing')
 return tmp

def validate_candidate(cand:Path,z:Path,game:Path):
 verify_sums(cand);src=verify_sources(cand);m=json.loads((cand/'candidate_manifest.json').read_text(encoding='utf-8'))
 if m.get('windows_build')!='PASS' or m.get('windows_private_process_smoke')!='PASS':raise FormatError('Windows build/private-process receipt missing')
 if m.get('production_release_approved') is not False:raise FormatError('Expected non-release validation candidate')
 if m.get('experimental_issue_build') is not True:raise FormatError('Candidate is NOT -ExperimentalIssue')
 if m.get('source_digest')!=code_digest(cand):raise FormatError('Candidate source digest mismatch')
 pre=preflight(game/'Warhammer3.exe',cand)
 payload=m.get('payload_sha256',{})
 if set(payload)!={'wh3_native_bridge.dll','zzz_queue_probe.pack','minhook.x64.dll'}:raise FormatError('Payload manifest incomplete')
 for n,h in payload.items():
  if file_hash(cand/'payload'/n)!=h:raise FormatError('Payload hash mismatch: '+n)
 pe=verify_candidate_pe(cand/'payload/wh3_native_bridge.dll')
 if file_hash(game/'minhook.x64.dll')!=BASELINE_HASHES['minhook.x64.dll']:raise FormatError('Installed MinHook differs; validation refuses to overwrite it')
 if not carrier_enabled(game):raise FormatError('used_mods.txt does not already enable zzz_queue_probe.pack; no load-order rewrite performed')
 return m,pre,pe

def install(candidate_zip:Path,game:Path):
 game_closed();verify_sums(ROOT)
 if not VALIDATION_PACK.is_file():raise FormatError('Validation pack missing')
 for n,rel in MANAGED.items():
  got=file_hash(game/rel)
  if got!=BASELINE_HASHES[n]:raise FormatError('Managed baseline differs before validation: '+rel+' '+got)
 with tempfile.TemporaryDirectory(prefix='wh3_val_cand_') as t:
  cand=extract_candidate(candidate_zip,Path(t));m,pre,pe=validate_candidate(cand,candidate_zip,game)
  stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f');backup=ROOT/'game_validation'/'backups'/stamp;backup.mkdir(parents=True)
  files=[]
  for n,rel in MANAGED.items():shutil.copy2(game/rel,backup/n);files.append({'relative':rel,'backup':n,'old_sha256':file_hash(backup/n)})
  newdll=cand/'payload'/'wh3_native_bridge.dll';newpack=VALIDATION_PACK
  record={'schema':2,'mode':'EXPERIMENTAL_GAME_VALIDATION','installed_at':stamp,'game_root':str(game.resolve()),'candidate_zip':str(candidate_zip.resolve()),'candidate_zip_sha256':file_hash(candidate_zip),'candidate_manifest':m,'preflight':pre,'candidate_pe':pe,'backup':str(backup.resolve()),'files':files,'validation_pack_sha256':file_hash(newpack),'state':'PREPARED'}
  (backup/'candidate_manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8');(backup/'install_receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
  try:
   atomic_copy(newdll,game/'wh3_native_bridge.dll');atomic_copy(newpack,game/'data/zzz_queue_probe.pack')
   record['installed_sha256']={'wh3_native_bridge.dll':file_hash(game/'wh3_native_bridge.dll'),'zzz_queue_probe.pack':file_hash(game/'data/zzz_queue_probe.pack')}
   if record['installed_sha256']['wh3_native_bridge.dll']!=m['payload_sha256']['wh3_native_bridge.dll'] or record['installed_sha256']['zzz_queue_probe.pack']!=file_hash(newpack):raise FormatError('Post-install hash mismatch')
   record['state']='INSTALLED_FOR_ONE_GAME_VALIDATION';(backup/'install_receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');STATE.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
   return record
  except Exception:
   for row in files:atomic_copy(backup/row['backup'],game/row['relative'])
   record['state']='ROLLED_BACK_AFTER_INSTALL_ERROR';(backup/'install_receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');raise

def load_state():
 if not STATE.is_file():raise FormatError('No validation install state found')
 return json.loads(STATE.read_text(encoding='utf-8'))

def rollback(game:Path|None=None):
 game_closed();s=load_state();g=Path(s['game_root']) if game is None else game
 if g.resolve()!=Path(s['game_root']).resolve():raise FormatError('Game root differs from receipt')
 backup=Path(s['backup']);
 for row in s['files']:
  old=backup/row['backup'];cur=g/row['relative'];
  if file_hash(old)!=row['old_sha256']:raise FormatError('Backup changed: '+row['backup'])
  if file_hash(cur) not in (row['old_sha256'],s.get('installed_sha256',{}).get(row['backup'],'__none__')):raise FormatError('Managed file changed by another writer: '+row['relative'])
 for row in s['files']:atomic_copy(backup/row['backup'],g/row['relative'])
 s['state']='ROLLED_BACK';s['rolled_back_at']=datetime.datetime.now().isoformat();STATE.write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8');return s

def log_candidates(game:Path):
 roots=[]
 app=os.environ.get('APPDATA');user=os.environ.get('USERPROFILE')
 if app: roots += [Path(app)/'The Creative Assembly'/'Warhammer3'/'logs',Path(app)/'The Creative Assembly'/'Warhammer3']
 roots += [game, game/'logs']
 seen=set();out=[]
 for r in roots:
  if not r.exists():continue
  try:
   for p in r.rglob('script_log*.txt'):
    if p in seen:continue
    seen.add(p)
    try:
     if p.stat().st_size<=100*1024*1024:out.append(p)
    except OSError:pass
  except OSError:pass
 return sorted(out,key=lambda p:p.stat().st_mtime_ns,reverse=True)

def find_log(game:Path,explicit:Path|None):
 c=[explicit] if explicit else log_candidates(game)
 for p in c:
  if p and p.is_file():
   b=p.read_bytes()
   if TAG in b:return p,b
 raise FormatError('No script_log containing [BRIDGE_GAMEVAL_V050] found; use -LogPath')

def collect_and_rollback(logpath:Path|None,outdir:Path):
 game_closed();s=load_state();game=Path(s['game_root']);p,b=find_log(game,logpath)
 text=b.decode('utf-8',errors='replace');markers={k.decode(): (TAG+b' '+k) in b or k in b for k in REQUIRED}
 fail_lines=[x for x in text.splitlines() if '[BRIDGE_GAMEVAL_V050]' in x and ('VALIDATION_FAIL' in x or 'FAIL ' in x)]
 passed=all(markers.values()) and not fail_lines
 stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f');work=ROOT/'game_validation'/'results'/stamp;work.mkdir(parents=True)
 shutil.copy2(p,work/p.name);Path(work/'install_receipt.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
 summary={'schema':1,'validation_pass':passed,'markers':markers,'fail_lines':fail_lines,'source_log':str(p),'installed_before_rollback':{rel:file_hash(game/rel) for rel in MANAGED.values()},'candidate_zip_sha256':s['candidate_zip_sha256'],'candidate_manifest_experimental':s['candidate_manifest'].get('experimental_issue_build'),'note':'exact_source/verified_issue intentionally remain false globally; acceptance is journal/event scoped.'}
 (work/'VALIDATION_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 # preserve evidence first, then rollback regardless of PASS/FAIL
 rb=rollback(game);(work/'ROLLBACK_RESULT.json').write_text(json.dumps(rb,indent=2)+'\n',encoding='utf-8')
 outdir.mkdir(parents=True,exist_ok=True);z=outdir/('WH3_Game_Validation_Result_'+stamp+'.zip')
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
  for q in sorted(work.iterdir()):zz.write(q,q.name)
 return z,summary

def candidate_manifest_matches_current(m:dict)->bool:
 return (m.get('experimental_issue_build') is True and
         m.get('version') == VERSION and
         m.get('source_digest') == code_digest(ROOT) and
         m.get('windows_build') == 'PASS' and
         m.get('windows_private_process_smoke') == 'PASS')

def locate_unlocked():
 roots=[Path.home()/'Downloads',ROOT/'output']
 hits=[]
 for r in roots:
  if not r.exists():continue
  for pat in ('WH3_Native_Bridge_Integrated_Candidate_Unlocked.zip','WH3_Native_Bridge_Integrated_Candidate.zip'):
   try:hits += list(r.rglob(pat))
   except OSError:pass
 for z in sorted(set(hits),key=lambda p:p.stat().st_mtime_ns,reverse=True):
  try:
   with zipfile.ZipFile(z) as zz:m=json.loads(zz.read('candidate_manifest.json'))
   if candidate_manifest_matches_current(m):return z
  except Exception:pass
 return None

def main():
 ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
 q=sub.add_parser('locate');
 q=sub.add_parser('install');q.add_argument('--candidate',type=Path,required=True);q.add_argument('--game-root',type=Path,required=True)
 q=sub.add_parser('rollback');q.add_argument('--game-root',type=Path)
 q=sub.add_parser('finish');q.add_argument('--log',type=Path);q.add_argument('--out',type=Path,required=True)
 a=ap.parse_args()
 try:
  if a.cmd=='locate':
   z=locate_unlocked();print(str(z) if z else '');return 0 if z else 3
  if a.cmd=='install':print(json.dumps(install(a.candidate,a.game_root),indent=2));return 0
  if a.cmd=='rollback':print(json.dumps(rollback(a.game_root),indent=2));return 0
  if a.cmd=='finish':z,s=collect_and_rollback(a.log,a.out);print('VALIDATION_PASS='+str(s['validation_pass']).lower());print('RESULT_ZIP='+str(z));return 0 if s['validation_pass'] else 4
 except Exception as e:print('FAIL:',e);return 1
if __name__=='__main__':raise SystemExit(main())
