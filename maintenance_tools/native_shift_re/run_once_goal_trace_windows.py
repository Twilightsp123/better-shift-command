#!/usr/bin/env python3
"""Windows x64 exact-game, once-only native goal trace launcher.

Requires pip install frida. Only reads game data. Frida temporarily replaces
code entry bytes to install hooks, restored on script unload/detach.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

EXACT_SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()

def pid_image_path(pid):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,
                                               wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype=wintypes.BOOL
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x1000,False,pid)
    if not handle:raise ValueError('PROCESS_READ_QUERY_DENIED')
    try:
        buf=ctypes.create_unicode_buffer(32768);n=wintypes.DWORD(len(buf))
        if not kernel.QueryFullProcessImageNameW(handle,0,buf,ctypes.byref(n)):
            raise ValueError('PID_IMAGE_PATH_QUERY_FAILED')
        return Path(buf.value).resolve(strict=True)
    finally:kernel.CloseHandle(handle)

def verify_preconditions(exe,pid,out):
    exe=Path(exe).resolve(strict=True)
    if digest(exe)!=EXACT_SHA:raise ValueError('SHA_MISMATCH')
    if platform.system()!='Windows' or platform.architecture()[0]!='64bit':
        raise ValueError('WINDOWS_X64_REQUIRED')
    observed=pid_image_path(pid)
    if os.path.normcase(str(exe))!=os.path.normcase(str(observed)):
        raise ValueError('PID_EXE_NOT_IDENTICAL:'+str(observed))
    if digest(observed)!=EXACT_SHA:raise ValueError('PROCESS_EXE_SHA_CHANGED')
    if exe==Path(out).resolve():raise ValueError('NEVER_OVERWRITE_GAME_EXE')
    return exe

def run(exe,pid,out,seconds):
    if not 10<=seconds<=300:raise ValueError('INVALID_DURATION_10_TO_300')
    exe=verify_preconditions(exe,pid,out)
    try:import frida
    except ImportError as e:raise ValueError('PIP_INSTALL_FRIDA_REQUIRED') from e
    js=Path(__file__).with_name('one_shot_goal_trace.js').read_text(encoding='utf8')
    out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    info={'ready':False,'errors':[],'n':0}
    with out.open('w',encoding='utf8') as file:
        def event(msg, data):
            if msg.get('type')=='send':
                payload=msg.get('payload',{})
                if isinstance(payload,dict) and payload.get('type')=='ready':
                    info['ready']=True
                info['n']+=1
            else:
                payload={'type':'probe_error','message':msg}
                info['errors'].append(msg.get('stack','unknown'))
            file.write(json.dumps(payload,ensure_ascii=False)+'\n');file.flush()
        session=None
        try:
            session=frida.attach(pid)
            script=session.create_script(js)
            script.on('message',event)
            script.load()
            if not info['ready']:raise RuntimeError('GAME_OPCODE_GUARDS_NOT_PASSED')
            print('One-shot observation active; no gameplay commands changed.')
            try:time.sleep(seconds)
            except KeyboardInterrupt:pass
            try:script.post({'type':'stop'});time.sleep(.15)
            except Exception:pass
        finally:
            if session:session.detach()
    if info['errors']:raise RuntimeError('CAPTURE_ERROR:'+str(info['errors'][:2]))
    return info['n']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',required=True,type=Path)
    parser.add_argument('--pid',required=True,type=int)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--seconds',type=int,default=90)
    a=parser.parse_args()
    try:
        print('Saved events',run(a.exe,a.pid,a.out,a.seconds))
        return 0
    except Exception as e:
        print('FAIL_CLOSED:',e,file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
