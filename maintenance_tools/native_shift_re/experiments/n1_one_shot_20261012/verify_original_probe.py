#!/usr/bin/env python3
"""Read-only exact-original SHA/PE/unwind/x64 instruction boundary proof.

This verifier is for the development machine with GNU objdump; the Windows
runtime probe independently checks original opcode bytes before attaching.
"""
import argparse
import bisect
import hashlib
import json
import mmap
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

EXPECTED_SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
EXPECTED_BASE=0x140000000
SEND_SITES={0x03284b7b:0x03284b81,0x03265d3f:0x03265d45,0x030d550f:0x030d5515}
GROUP_TICK_OWNERSHIP_GUARDS={
    0x02dd57ba:'488bd9',  # group native Tick saves RCX in RBX
    0x02dd57d9:'8b8398000000',  # reads same group+0x98 clock
}

class PE:
    def __init__(self,path):
        self.path=Path(path)
        with self.path.open('rb') as f:
            self.sha=hashlib.file_digest(f,'sha256').hexdigest()
        if self.sha!=EXPECTED_SHA:raise ValueError('WRONG_GAME_SHA256')
        self.fd=self.path.open('rb')
        self.mm=mmap.mmap(self.fd.fileno(),0,access=mmap.ACCESS_READ)
        b=self.mm
        if b[:2]!=b'MZ':raise ValueError('INVALID_MZ')
        nt=struct.unpack_from('<I',b,0x3c)[0]
        if b[nt:nt+4]!=b'PE\0\0':raise ValueError('INVALID_PE')
        machine,num=struct.unpack_from('<HH',b,nt+4)
        if machine!=0x8664:raise ValueError('NOT_X64')
        optional=nt+24
        magic=struct.unpack_from('<H',b,optional)[0]
        base=struct.unpack_from('<Q',b,optional+24)[0]
        if magic!=0x20b or base!=EXPECTED_BASE:raise ValueError('NOT_ORIGINAL_X64_PE_IMAGEBASE')
        hdr_size=struct.unpack_from('<H',b,nt+20)[0]
        self.sections=[]
        for i in range(num):
            site=optional+hdr_size+i*40
            virtual,rva,raw_size,off=struct.unpack_from('<IIII',b,site+8)
            flags=struct.unpack_from('<I',b,site+36)[0]
            self.sections.append((rva,raw_size,off,flags))
        er,sz=struct.unpack_from('<II',b,optional+112+3*8)
        if sz%12:raise ValueError('BAD_PDATA_SIZE')
        self.unwind=list(struct.iter_unpack('<III',self.read(er,sz)))
        self.starts=[x[0] for x in self.unwind]
        if len(self.unwind)!=209180:raise ValueError('ORIGINAL_UNWIND_COUNT_CHANGED')
    def read(self,rva,size,code=False):
        for rv,n,off,flags in self.sections:
            if rv<=rva and rva+size<=rv+n:
                if code and not(flags&0x20000000):raise ValueError('RVA_NOT_CODE')
                return bytes(self.mm[off+rva-rv:off+rva-rv+size])
        raise ValueError('RVA_NOT_MAPPED:'+hex(rva))
    def owner(self,rva):
        i=bisect.bisect_right(self.starts,rva)-1
        if i<0:return None
        a,b,c=self.unwind[i]
        if a<=rva<b:return a,b
        return None
    def disassemble(self,a,b):
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(self.read(a,b-a,True));tmp.flush()
            cmd=['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel',
                 '--adjust-vma='+hex(a),tmp.name]
            r=subprocess.run(cmd,capture_output=True,text=True)
            if r.returncode:raise ValueError('OBJDUMP_FAILED:'+r.stderr[-400:])
            return r.stdout
    def close(self):
        self.mm.close();self.fd.close()


def parse_pins(js):
    text=Path(js).read_text(encoding='utf8')
    matches=re.findall(r"\[0x([0-9a-fA-F]+),'([0-9a-fA-F]+)'\]",text)
    if len(matches)<10:raise ValueError('PROBE_PINS_TOO_FEW')
    guards={}
    for rva,hexcode in matches:
        r=int(rva,16)
        if r in guards:raise ValueError('DUPLICATE_HOOK_SITE:'+hex(r))
        if len(hexcode)%2:raise ValueError('ODD_OPCODE_LENGTH')
        guards[r]=hexcode.lower()
    return guards


def disasm_starts(asm):
    starts=set()
    for line in asm.splitlines():
        fields=line.split('\t')
        if len(fields)<3:continue
        m=re.match(r'^\s*([0-9a-f]+):',fields[0])
        if m and re.match(r'^\s*[a-z][a-z0-9_.]*',fields[-1]):
            starts.add(int(m.group(1),16))
    return starts


def verify(exe,js):
    if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED_FOR_INSTRUCTION_BOUNDARIES')
    pins=parse_pins(js)
    pe=PE(exe)
    cache={};results=[]
    try:
        for site,hexcode in sorted(pins.items()):
            if pe.read(site,len(hexcode)//2,True).hex()!=hexcode:
                raise ValueError('ORIGINAL_OPCODE_MISMATCH:'+hex(site))
            span=pe.owner(site)
            if not span:raise ValueError('NO_NATIVE_UNWIND_OWNER:'+hex(site))
            if span not in cache:cache[span]=disasm_starts(pe.disassemble(*span))
            if site not in cache[span]:raise ValueError('MID_INSTRUCTION_HOOK:'+hex(site))
            results.append({'rva':hex(site),'size':len(hexcode)//2,
                            'bytes':hexcode,'function':hex(span[0])})
        for site,raw in GROUP_TICK_OWNERSHIP_GUARDS.items():
            if pe.read(site,len(raw)//2,True).hex()!=raw:
                raise ValueError('GROUP_TICK_OWNER_OR_CLOCK_CHANGED:'+hex(site))
        for site,ret in SEND_SITES.items():
            assert site+6==ret
            if pe.read(site,6,True)!=bytes.fromhex('ff9068030000'):
                raise ValueError('NATIVE_V368_CALL_CHANGED:'+hex(site))
        for site,target in [(0x3265b0a,0x3284304),(0x3282f0f,0x3284304)]:
            data=pe.read(site,5,True)
            if data[0]!=0xe8 or site+5+struct.unpack_from('<i',data,1)[0]!=target:
                raise ValueError('NATIVE_TASK_SENDER_CALL_CHANGED:'+hex(site))
        for slot,target in [(0x3add618,0x3282e48),(0x3ae00f8,0x3281520)]:
            value=struct.unpack('<Q',pe.read(slot,8))[0]
            if value!=EXPECTED_BASE+target:raise ValueError('NATIVE_TASK_VTABLE_CHANGED')
        return {'schema':'bsc.n1.source_probe_strict_original.v1','exe_sha256':pe.sha,
          'verified_hook_count':len(results),'verified':results,
          'native_sender_calls':{hex(k):hex(v) for k,v in SEND_SITES.items()},
          'verified_task_constructor_to_sender_calls':2,
          'verified_distinct_task_vtables':2,
          'group_tick_receiver_owner_and_clock_guards':len(GROUP_TICK_OWNERSHIP_GUARDS),
          'proof_level':'ORIGINAL_EXE_STATIC_OPCODE_UNWIND_AND_DISASSEMBLY',
          'frida_windows_attach_tested':False,
          'game_behavior_fixed':False,'native_patch_authorized':False}
    finally:pe.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--probe',type=Path,default=Path(__file__).with_name('one_shot_native_source.js'))
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    result=verify(a.exe,a.probe)
    if a.out:
        if a.out.resolve()==a.exe.resolve():p.error('REFUSE_EXE_OVERWRITE')
        a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('ORIGINAL_EXE_STATIC_PASS',result['verified_hook_count'],'hooks, PE/unwind/objdump, task identities')

if __name__=='__main__':main()
