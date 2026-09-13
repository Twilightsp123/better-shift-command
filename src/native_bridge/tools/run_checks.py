"""Build and execute the actual source/test targets. Never launches Warhammer."""
from __future__ import annotations
import argparse,json,os,platform,shutil,subprocess,sys,time
from pathlib import Path
from product import ROOT,code_digest,save_json,verify_sources

def execute(command:list[str],log:Path,cwd:Path)->int:
 log.parent.mkdir(parents=True,exist_ok=True)
 with log.open('w',encoding='utf-8') as out:
  out.write('$ '+' '.join(command)+'\n');out.flush()
  try:p=subprocess.run(command,cwd=cwd,stdout=out,stderr=subprocess.STDOUT,check=False,timeout=900)
  except Exception as e:out.write(type(e).__name__+': '+str(e)+'\n');return 125
 return p.returncode

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'output/offline');ap.add_argument('--cmake',default='cmake');ap.add_argument('--config',choices=['Debug','Release'],default='Debug');ap.add_argument('--generator');ap.add_argument('--sanitize',action='store_true');ap.add_argument('--experimental-issue',action='store_true');a=ap.parse_args()
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);result={'status':'FAIL','platform':platform.platform(),'python':sys.version,'windows_dll_built':False,'windows_private_process_smoke':False,'game_runtime_tested':False,'production_release_approved':False,'experimental_issue_build':a.experimental_issue,'steps':[]};start=code_digest()
 try:
  result['input_check']=verify_sources();build=out/'build'
  command=[a.cmake,'-S',str(ROOT),'-B',str(build),'-DCMAKE_BUILD_TYPE='+a.config,'-DWH3_ALLOW_UNVALIDATED_NATIVE_ISSUE='+('ON' if a.experimental_issue else 'OFF')]
  if a.sanitize:command+=['-DWH3_SANITIZE=ON']
  if a.generator:command+=['-G',a.generator,'-A','x64']
  ctest=Path(a.cmake).with_name('ctest.exe' if os.name=='nt' else 'ctest') if Path(a.cmake).is_absolute() else Path('ctest')
  jobs=[('python',[sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),' -p'.strip(),'test_product.py','-v']),('configure',command),('build',[a.cmake,'--build',str(build),'--config',a.config,'--parallel','4']),('ctest',[str(ctest),'--test-dir',str(build),'-C',a.config,'--output-on-failure','-V'])]
  for name,cmd in jobs:
   rc=execute(cmd,out/(name+'.log'),ROOT);result['steps'].append({'name':name,'exit_code':rc,'log':name+'.log'});print(name,rc,flush=True)
   if rc:raise RuntimeError(name+' failed; see '+str(out/(name+'.log')))
  if start!=code_digest():raise RuntimeError('Source changed during tests')
  result['status']='PASS';result['source_digest']=start
  result['windows_dll_built']=os.name=='nt';result['windows_private_process_smoke']=os.name=='nt'
  result['lua_fixture_run']=shutil.which('texlua') is not None
  result['note']='C++ native calls and frame oracle are fixtures; not a WH3 battle or native host Lua VM.'
 except Exception as e:result['error']=str(e);print('FAIL',e)
 save_json(out/'result.json',result);return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
