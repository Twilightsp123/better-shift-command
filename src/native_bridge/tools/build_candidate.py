"""Windows one-command builder. Local MSVC, CTest, DLL smoke, no installation."""
from __future__ import annotations
import argparse,json,os,shutil,subprocess,sys,datetime
from pathlib import Path
from product import *

def find_cmake()->str:
 value=shutil.which('cmake')
 if value:return value
 for root in [os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'),os.environ.get('ProgramFiles','C:/Program Files')]:
  p=Path(root)/'Microsoft Visual Studio/2019/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
  if p.is_file():return str(p)
 raise FileNotFoundError('Existing cmake.exe not found; no tool download or account needed. Use --cmake full_path.')
def gather_receipt(result:dict,pre:dict,dll:Path,root:Path=ROOT)->dict:
 if result.get('status')!='PASS' or not result.get('windows_private_process_smoke') or not result.get('windows_dll_built'):raise FormatError('Actual Windows build and private-process smoke must pass')
 if result.get('source_digest')!=code_digest(root):raise FormatError('Receipt belongs to different source')
 if pre.get('status')!='PASS':raise FormatError('Actual game EXE preflight required')
 return {'schema':1,'version':VERSION,'source_digest':result['source_digest'],'windows_build':'PASS','windows_private_process_smoke':'PASS','game_runtime_tested':False,'production_release_approved':False,'experimental_issue_build':result.get('experimental_issue_build',False),'exe_preflight':pre,'dll':verify_candidate_pe(dll)}
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--out',type=Path);ap.add_argument('--cmake');ap.add_argument('--generator',default='Visual Studio 16 2019');ap.add_argument('--experimental-issue',action='store_true');a=ap.parse_args()
 if os.name!='nt':print('This build entry requires Windows x64/MSVC. Use run_checks.py for portable tests.');return 2
 output=(a.out or ROOT/'output'/('Windows_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))).resolve();output.mkdir(parents=True,exist_ok=False)
 status={'status':'FAIL','game_started':False,'game_modified':False}
 try:
  verify_sums();verify_sources();pre=preflight(a.exe);save_json(output/'preflight.json',pre)
  cmd=[sys.executable,str(ROOT/'tools/run_checks.py'),'--out',str(output/'checks'),'--cmake',a.cmake or find_cmake(),'--config','Release','--generator',a.generator]
  if a.experimental_issue:cmd+=['--experimental-issue']
  rc=subprocess.run(cmd,check=False).returncode
  if rc:raise RuntimeError('Build/tests failed: '+str(output/'checks/result.json'))
  result=json.loads((output/'checks/result.json').read_text(encoding='utf-8'))
  choices=list((output/'checks/build').rglob('wh3_native_bridge.dll'))
  if len(choices)!=1:raise FormatError('Expected exactly one newly compiled DLL')
  receipt=gather_receipt(result,pre,choices[0]);candidate=output/'WH3_Native_Bridge_Integrated_Candidate';candidate.mkdir()
  (candidate/'payload').mkdir();shutil.copy2(choices[0],candidate/'payload/wh3_native_bridge.dll');shutil.copy2(ROOT/'dist/zzz_queue_probe.pack',candidate/'payload/zzz_queue_probe.pack');shutil.copy2(ROOT/'baseline/minhook.x64.dll',candidate/'payload/minhook.x64.dll')
  for directory in ['src','include','tests','tools','lua','dist','evidence','baseline','docs','validation','history']:
   if (ROOT/directory).exists():shutil.copytree(ROOT/directory,candidate/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  for p in ROOT.iterdir():
   if p.is_file() and p.suffix in ('.ps1','.md','.txt'):shutil.copy2(p,candidate/p.name)
  shutil.copy2(ROOT/'CMakeLists.txt',candidate/'CMakeLists.txt')
  logs=candidate/'windows_validation';logs.mkdir()
  for p in (output/'checks').glob('*.log'):shutil.copy2(p,logs/p.name)
  for p in [output/'checks/result.json',output/'preflight.json']:shutil.copy2(p,logs/p.name)
  receipt['payload_sha256']={p.name:file_hash(p) for p in (candidate/'payload').iterdir()}
  save_json(candidate/'candidate_manifest.json',receipt)
  # The candidate now contains compiled artifacts; regenerate its file manifest.
  from release_archive import write_sums
  write_sums(candidate)
  zip_path=output/'WH3_Native_Bridge_Integrated_Candidate.zip';zip_tree(candidate,zip_path)
  status={'status':'PASS','candidate_zip':str(zip_path),'candidate_sha256':file_hash(zip_path),'game_started':False,'game_modified':False,'production_release_approved':False}
  print('FINAL_CANDIDATE_ZIP='+str(zip_path));print('No installation and no game launch were performed.')
 except Exception as e:status['error']=str(e);print('FAIL:',e)
 save_json(output/'BUILD_RESULT.json',status);return 0 if status['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
