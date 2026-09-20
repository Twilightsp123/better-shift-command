"""Restricted, deterministic PFH5 Mod pack I/O. No native executable execution."""
from __future__ import annotations
import hashlib, re, struct
from pathlib import Path

CONTROLLER_PATH = r'script\battle\mod\better_shift_command.lua'
BRIDGE_PATH = r'script\better_shift_command\bin\bridge_Windows_NT-x64.lua'
MINHOOK_PATH = r'script\better_shift_command\bin\minhook_Windows_NT-x64.lua'
MINHOOK_SHA256 = 'df452eacdb076c35a80c795df920fd3c6f128faa3e0bccb0b7490e95f8659d54'
BRIDGE_VERSION = b'1.0.15-r4-evidence-v3-validated-userdata-root'

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def make_pack(files: list[tuple[str, bytes]]) -> bytes:
    index = bytearray(); names = set()
    for name, raw in files:
        if name in names or '\x00' in name or name.startswith(('\\','/')) or '..' in name.split('\\'):
            raise ValueError('Invalid or duplicate pack path')
        names.add(name)
        index += struct.pack('<IB', len(raw), 0) + name.encode('utf-8') + b'\0'
    return b'PFH5' + struct.pack('<6I', 3, 0, 0, len(files), len(index), 0) + bytes(index) + b''.join(raw for _,raw in files)

def parse_pack(data: bytes) -> dict[str, bytes]:
    if len(data)<28 or data[:4]!=b'PFH5': raise ValueError('Not a PFH5 file')
    flags,depcount,depsize,count,indexsize,mtime=struct.unpack_from('<6I',data,4)
    if flags!=3 or depcount or depsize or count>10000: raise ValueError('Not supported simple PFH5 Mod pack')
    end=28+indexsize
    if end>len(data): raise ValueError('Invalid index size')
    i=28;entries=[]
    for _ in range(count):
        if i+5>end: raise ValueError('Truncated index')
        size,flag=struct.unpack_from('<IB',data,i);i+=5
        z=data.find(b'\0',i,end)
        if z<0 or flag: raise ValueError('Unsupported or invalid entry')
        name=data[i:z].decode('utf-8');i=z+1;entries.append((name,size))
    if i!=end: raise ValueError('Index length mismatch')
    out={}
    for name,size in entries:
        if name in out or i+size>len(data): raise ValueError('Bad payload')
        out[name]=data[i:i+size];i+=size
    if i!=len(data): raise ValueError('Trailing data')
    return out

def encode_payload(label: str,data: bytes) -> bytes:
    rows=[f'-- Better Shift Command v1.2.2 native payload bytes: {label}',f'-- sha256={sha(data)}',f'-- size={len(data)}','return table.concat({']
    for start in range(0,len(data),4096):
        rows.append('"'+''.join(f'\\{x:03d}' for x in data[start:start+4096])+'",')
    return ('\n'.join(rows)+ '\n})\n').encode('ascii')

def decode_payload(src: bytes) -> bytes:
    text=src.decode('ascii'); chunks=re.findall(r'"((?:\\\d{3})*)"',text)
    if not chunks: raise ValueError('Unsupported embedded payload encoding')
    raw=bytes(int(x) for chunk in chunks for x in re.findall(r'\\(\d{3})',chunk))
    return raw

def native_info(bridge: bytes,minhook: bytes) -> dict:
    if sha(minhook)!=MINHOOK_SHA256: raise ValueError('Installed MinHook is not the frozen backend; no changes made')
    if len(bridge)<256 or bridge[:2]!=b'MZ': raise ValueError('Invalid Bridge PE')
    pe=struct.unpack_from('<I',bridge,0x3c)[0]
    if pe+28>len(bridge) or bridge[pe:pe+4]!=b'PE\0\0': raise ValueError('Invalid PE header')
    machine=struct.unpack_from('<H',bridge,pe+4)[0]
    magic=struct.unpack_from('<H',bridge,pe+24)[0]
    major,minor=bridge[pe+26:pe+28]
    if machine!=0x8664 or magic!=0x20b: raise ValueError('Requires Windows x64 Bridge')
    if (major,minor)!=(14,29): raise ValueError(f'Expected preserved v142/linker14.29; found {major}.{minor}; no rebuilding attempted')
    if BRIDGE_VERSION not in bridge or b'luaopen_wh3_native_bridge' not in bridge:
        raise ValueError('Needs a freshly built v1.0.15-r4 Evidence V3 DLL. Do not install an older Bridge.')
    return {'bridge_version':BRIDGE_VERSION.decode(),'bridge_sha256':sha(bridge),
            'minhook_sha256':sha(minhook),'linker':f'{major}.{minor}',
            'native_rebuilt':False,'native_source':'USER_INSTALLED_BYTES',
            'binary_trust_note':'Identity/format checks only; not a new security audit or runtime validation'}

def selfcontained(root: Path,controller: bytes,bridge: bytes,minhook: bytes) -> bytes:
    native_info(bridge,minhook)
    block=(root/'baseline/selfcontained_bootstrap.lua').read_text(encoding='utf-8')
    block=block.replace('@@BRIDGE_SIZE@@',str(len(bridge))).replace('@@BRIDGE_SHA256@@',sha(bridge))
    text=controller.decode('utf-8')
    if text.count('function Core.boot()')!=1 or text.count('    local lok,loader,le=pcall(package.loadlib,')!=1:
        raise ValueError('Unexpected controller bootstrap')
    text=text.replace('function Core.boot()',block+'\nfunction Core.boot()',1)
    text=text.replace('    local lok,loader,le=pcall(package.loadlib,','    ensure_embedded_native()\n    local lok,loader,le=pcall(package.loadlib,',1)
    return make_pack([(CONTROLLER_PATH,text.encode('utf-8')),
        (BRIDGE_PATH,encode_payload('wh3_native_bridge.dll',bridge)),
        (MINHOOK_PATH,encode_payload('minhook.x64.dll',minhook)),
        (r'script\better_shift_command\licenses\MINHOOK_LICENSE.txt',(root/'baseline/MINHOOK_LICENSE.txt').read_bytes()),
        (r'script\better_shift_command\licenses\THIRD_PARTY_NOTICES.txt',
         b'Better Shift Command v1.2.2. Native Bridge ABI 1.0.15-r4-evidence-v3-validated-userdata-root; frozen MinHook runtime. See MINHOOK_LICENSE.txt.\n')])
