"""File-level build/product utilities. No process injection or game execution."""
from __future__ import annotations
import hashlib, json, os, re, shutil, struct, tempfile, zipfile
from pathlib import Path
from binary_utils import PE, FormatError, file_hash, pack, unpack, require_exports
ROOT=Path(__file__).resolve().parents[1]
VERSION='0.5.0-attack-native-token'
BASELINE_HASHES={
 'wh3_native_bridge.dll':'685e460901602e29806acf986add1c3b44bae45f4f5ec668f32f6882ed2f18a4',
 'minhook.x64.dll':'e9c9fa622f5220b4dd5162b817b9295c53a7978a7bd0b656eac0d29a1106e8ea',
 'zzz_queue_probe.pack':'3c6582186b026315cf2415fb5ccce11cd60f05fc1617155881bd2ed5d0e539a5',
 'queue_probe.lua':'27ec2f5ba001225ea008bb74e44fd4666dc6a264ec846194b4dd3556a61c1bcd'}
LUA_EXPORTS=['lua_'+x for x in ('settop','pushvalue','pcall','gettop','type','tolstring','tonumber','toboolean','pushnil','pushnumber','pushlstring','pushboolean','createtable','setfield','rawseti','pushcclosure')]
BACKEND_EXPORTS=['MH_Initialize','MH_CreateHook','MH_QueueEnableHook','MH_ApplyQueued','MH_RemoveHook','MH_Uninitialize']
CODE_DIRS=('src','include','tests','tools','lua','dist','evidence/guards')
CODE_FILES=('CMakeLists.txt','evidence/native_profile.json','Build_Integrated_Candidate.ps1','Install_Candidate.ps1','Rollback.ps1')
def digest_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def save_json(path:Path,obj)->None:
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def code_files(root:Path=ROOT):
 files=[]
 for directory in CODE_DIRS:
  for p in (root/directory).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo'):files.append(p)
 for name in CODE_FILES:
  p=root/name
  if p.exists():files.append(p)
 return sorted(set(files),key=lambda p:p.relative_to(root).as_posix())
def code_digest(root:Path=ROOT)->str:
 h=hashlib.sha256()
 for p in code_files(root):
  h.update(p.relative_to(root).as_posix().encode('utf-8')+b'\0');h.update(bytes.fromhex(file_hash(p)))
 return h.hexdigest()
def verify_baseline(root:Path=ROOT)->dict:
 result={}
 for name,expected in BASELINE_HASHES.items():
  got=file_hash(root/'baseline'/name)
  if got!=expected:raise FormatError('Baseline differs: '+name)
  result[name]=got
 if unpack((root/'baseline/zzz_queue_probe.pack').read_bytes())!=(root/'baseline/queue_probe.lua').read_bytes():raise FormatError('Baseline Lua carrier mismatch')
 for name,exports in [('wh3_native_bridge.dll',['luaopen_wh3_native_bridge']),('minhook.x64.dll',BACKEND_EXPORTS)]:
  require_exports(PE((root/'baseline'/name).read_bytes()),exports)
 return result
def verify_sources(root:Path=ROOT)->dict:
 baseline=verify_baseline(root)
 profile=json.loads((root/'evidence/native_profile.json').read_text(encoding='utf-8'))
 if len(profile['guards'])!=16:raise FormatError('Expected sixteen hook guards')
 seen=set()
 for g in profile['guards']:
  if g['rva'] in seen:raise FormatError('Duplicate guard RVA')
  seen.add(g['rva']);p=root/g['guard_file'];raw=p.read_bytes()
  if len(raw)!=g['length'] or digest_bytes(raw)!=g['sha256'] or raw.hex()!=g['bytes_hex']:raise FormatError('Guard content changed: '+g['name'])
 lua=(root/'lua/queue_probe.lua').read_bytes();carrier=(root/'dist/zzz_queue_probe.pack').read_bytes()
 if unpack(carrier)!=lua:raise FormatError('New pack differs from new Lua source')
 if VERSION.encode() not in lua:raise FormatError('Client/DLL version contract differs')
 return {'source_digest':code_digest(root),'baseline':baseline,'guards':len(seen),'lua_sha256':digest_bytes(lua),'pack_sha256':digest_bytes(carrier)}
def make_pack(root:Path=ROOT)->str:
 p=root/'dist/zzz_queue_probe.pack';p.parent.mkdir(exist_ok=True);p.write_bytes(pack((root/'lua/queue_probe.lua').read_bytes()));return file_hash(p)
def verify_sums(root:Path=ROOT)->int:
 p=root/'SHA256SUMS.txt'
 if not p.is_file():raise FormatError('SHA256SUMS.txt missing')
 count=0
 for line in p.read_text(encoding='utf-8').splitlines():
  expected,name=line.split('  ',1)
  q=Path(name)
  if q.is_absolute() or '..' in q.parts or not re.fullmatch('[0-9a-f]{64}',expected):raise FormatError('Unsafe hash entry')
  if file_hash(root/q)!=expected:raise FormatError('Delivery file changed: '+name)
  count+=1
 return count
def preflight(exe:Path,root:Path=ROOT)->dict:
 profile=json.loads((root/'evidence/native_profile.json').read_text(encoding='utf-8'))
 got=file_hash(exe)
 if got!=profile['exe_sha256']:raise FormatError('Game build SHA256 differs; old RVAs refused')
 pe=PE(exe.read_bytes())
 if pe.machine!=0x8664:raise FormatError('Not AMD64 executable')
 if pe.base!=int(profile['image_base'],16):raise FormatError('Image base differs')
 for g in profile['guards']:
  if pe.at(g['rva'],g['length']).hex()!=g['bytes_hex']:raise FormatError('Native entry bytes differ: '+g['name'])
 exports=require_exports(pe,LUA_EXPORTS)
 return {'status':'PASS','exe_sha256':got,'game_exe':str(exe.resolve()),'guard_count':len(profile['guards']),'host_lua_exports':{n:exports[n] for n in LUA_EXPORTS},'game_started':False,'game_modified':False}
def verify_candidate_pe(dll:Path)->dict:
 data=dll.read_bytes();pe=PE(data);exports=require_exports(pe,['luaopen_wh3_native_bridge'])
 if VERSION.encode() not in data:raise FormatError('Compiled version string absent')
 names=pe.imports()
 # /MT avoids requiring an extra redistributable deployment.
 forbidden=[n for n in names if re.match(r'(?:msvcp|vcruntime|libgcc|libstdc\+\+|lua)',n,re.I)]
 if forbidden:raise FormatError('Unexpected runtime dependency: '+','.join(forbidden))
 return {'sha256':digest_bytes(data),'machine':'AMD64','exports':exports,'imports':names,'version':VERSION}
def zip_tree(source:Path,dest:Path)->None:
 dest.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(source.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo'):
    i=zipfile.ZipInfo(p.relative_to(source).as_posix(),(2026,9,12,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o644<<16;z.writestr(i,p.read_bytes())
def safe_extract(zpath:Path,dest:Path)->None:
 with zipfile.ZipFile(zpath) as z:
  total=0;names=set()
  for i in z.infolist():
   name=i.filename.replace('\\','/');p=Path(name)
   if p.is_absolute() or '..' in p.parts or ':' in name or name in names:raise FormatError('Unsafe archive member')
   names.add(name);total+=i.file_size
   if total>100*1024*1024:raise FormatError('Archive exceeds extraction cap')
  z.extractall(dest)
