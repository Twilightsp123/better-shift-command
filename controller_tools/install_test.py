"""Install/rollback a local FEG1 test, preserving installed native bytes.
Does not edit Workshop files, launcher settings, native DLLs or GitHub.
"""
from __future__ import annotations
import argparse,csv,datetime,io,json,os,subprocess,sys,uuid
from pathlib import Path
from pack_tools import CONTROLLER_PATH,parse_pack,sha,native_info,selfcontained
ROOT=Path(__file__).resolve().parents[1]
PACK_NAME='zzz_better_shift_command_steam.pack'

def dump(path:Path,obj:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temp,path)

def atomic(path:Path,raw:bytes)->None:
    temp=path.with_name(path.name+'.feg1.tmp')
    try:
        temp.write_bytes(raw)
        if sha(temp.read_bytes())!=sha(raw):raise OSError('Written pack verification failed')
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()

def running()->bool:
    if os.name!='nt':raise RuntimeError('Installation must run on Windows; no game files were changed')
    result=subprocess.run(['tasklist','/FI','IMAGENAME eq Warhammer3.exe','/FO','CSV','/NH'],capture_output=True,text=True,check=True)
    return any(row and row[0].lower()=='warhammer3.exe' for row in csv.reader(io.StringIO(result.stdout)))

def install(game:Path,root:Path=ROOT,check_process:bool=True)->dict:
    if check_process and running():raise RuntimeError('Exit Warhammer3.exe completely before installing')
    game=game.resolve()
    if not (game/'Warhammer3.exe').is_file() or not (game/'data').is_dir():raise RuntimeError('Invalid WH3 game directory')
    receipt=root/'output/install_receipt_FEG1.json'
    if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('status') in ['PREPARED','INSTALLED']:
        raise RuntimeError('Previous FEG1 install receipt still active; rollback it first')
    bridge=(game/'wh3_native_bridge.dll').read_bytes();mh=(game/'minhook.x64.dll').read_bytes()
    identity=native_info(bridge,mh)
    controller=(root/'source/better_shift_command.lua').read_bytes()
    ready=parse_pack((root/'data'/PACK_NAME).read_bytes())
    if ready.get(CONTROLLER_PATH)!=controller:raise RuntimeError('Ready test pack and source disagree')
    # A competing local source pack is not silently renamed/deleted.
    for name in ['better_shift_command.pack','zzz_queue_probe.pack']:
        other=game/'data'/name
        if other.is_file():raise RuntimeError(f'Competing local pack: {other}. Back up and disable it before this test.')
    pack=selfcontained(root,controller,bridge,mh)
    target=game/'data'/PACK_NAME
    old=target.read_bytes() if target.exists() else None
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]
    backup=root/'output'/('backup_'+stamp);backup.mkdir(parents=True)
    backup_file=backup/PACK_NAME
    if old is not None:backup_file.write_bytes(old)
    candidate=root/'output/ready_to_install'/PACK_NAME
    candidate.parent.mkdir(parents=True,exist_ok=True);candidate.write_bytes(pack)
    info={'schema':1,'test':'FEG1','status':'PREPARED','game_dir':str(game),
          'target':str(target),'backup':str(backup_file) if old is not None else None,
          'old_pack_sha256':sha(old) if old is not None else None,'installed_pack_sha256':sha(pack),
          'source_sha256':sha(controller),'native':identity,'installed_at_utc':stamp,
          'changes':['local .pack only'],'no_launcher_or_workshop_changes':True}
    dump(receipt,info)
    try:
        atomic(target,pack)
        if (game/'wh3_native_bridge.dll').read_bytes()!=bridge or (game/'minhook.x64.dll').read_bytes()!=mh:
            raise RuntimeError('Native files changed concurrently; stopping')
        info['status']='INSTALLED';dump(receipt,info)
    except Exception:
        if old is None:
            if target.exists() and sha(target.read_bytes())==sha(pack):target.unlink()
        else:atomic(target,old)
        info['status']='INSTALL_FAILED_RESTORED';dump(receipt,info);raise
    return info

def rollback(root:Path=ROOT,check_process:bool=True)->dict:
    if check_process and running():raise RuntimeError('Exit Warhammer3.exe before rollback')
    p=root/'output/install_receipt_FEG1.json';i=json.loads(p.read_text(encoding='utf-8'))
    if i.get('status') not in ['PREPARED','INSTALLED']:raise RuntimeError('No active install to roll back')
    target=Path(i['target']);game=Path(i['game_dir'])
    if target.resolve()!= (game/'data'/PACK_NAME).resolve():raise RuntimeError('Receipt target mismatch')
    if not target.is_file() or sha(target.read_bytes())!=i['installed_pack_sha256']:
        raise RuntimeError('Installed pack was changed or removed; refusing destructive rollback')
    if i['backup']:
        b=Path(i['backup']).read_bytes()
        if sha(b)!=i['old_pack_sha256']:raise RuntimeError('Backup changed; refusing rollback')
        atomic(target,b)
    else:target.unlink()
    i['status']='ROLLED_BACK';dump(p,i);return i

def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--game-dir',type=Path);ap.add_argument('--rollback',action='store_true')
    a=ap.parse_args()
    if a.rollback:i=rollback()
    else:
        if not a.game_dir:ap.error('--game-dir is required')
        i=install(a.game_dir)
    print(json.dumps(i,ensure_ascii=False,indent=2))
    if not a.rollback:
        print('INSTALL COMPLETE. No native compilation, deletion or overwrite. Enable ONLY this local Better Shift Command test provider in the Mod Manager.')
        print('Runtime marker required: build=BETTER_SHIFT_COMMAND_V1.0.2_FEG1_TEST and FEG_CONFIG version=FEG1')
if __name__=='__main__':
    raise SystemExit('Historical FEG1 installer disabled in v1.0.14. Use BUILD_AND_INSTALL_V1.0.14.ps1; v1.0.14 requires Bridge 1.0.14-r1-evidence-v2-dual-root.')
