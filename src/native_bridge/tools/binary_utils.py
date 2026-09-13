"""Bounded, read-only PE/PFH5 utilities. No process access and no DLL loading."""
from __future__ import annotations
import hashlib
import struct
from pathlib import Path

BRIDGE_SHA256 = '685e460901602e29806acf986add1c3b44bae45f4f5ec668f32f6882ed2f18a4'
EXE_SHA256 = 'b7315fa718fd84e2e018e2c4df06600e9df0076156b474f148d9d558c939aa55'
OLD_PACK_SHA256 = '38592558f6c87081836de8f6b617b2254081e53d6c3f53332a67613f29d8dab9'
VPATH = r'script\battle\mod\queue_probe.lua'
BACKEND_EXPORTS = ('MH_Initialize', 'MH_CreateHook', 'MH_QueueEnableHook',
                   'MH_ApplyQueued', 'MH_RemoveHook', 'MH_Uninitialize')

class FormatError(ValueError):
    pass

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def file_hash(path: Path) -> str:
    stat = path.stat()
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    after = path.stat()
    if (stat.st_size, stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise FormatError('File changed while hashing: ' + str(path))
    return h.hexdigest()

class PE:
    """PE32+ reader supporting disk-backed RVAs, direct exports and imports."""
    def __init__(self, data: bytes):
        self.data = data
        if self.bytes(0, 2) != b'MZ': raise FormatError('MZ missing')
        self.nt = self.u32(0x3c)
        if self.bytes(self.nt, 4) != b'PE\0\0': raise FormatError('PE signature missing')
        self.machine = self.u16(self.nt + 4)
        self.timestamp = self.u32(self.nt + 8)
        count = self.u16(self.nt + 6)
        opt_len = self.u16(self.nt + 20)
        self.opt = self.nt + 24
        if self.u16(self.opt) != 0x20b or opt_len < 112: raise FormatError('PE32+ required')
        if not 1 <= count <= 96: raise FormatError('Invalid section count')
        self.bytes(self.opt, opt_len)
        self.base = self.u64(self.opt + 24)
        self.size = self.u32(self.opt + 56)
        self.header_size = self.u32(self.opt + 60)
        self.directory_count = min(self.u32(self.opt + 108), (opt_len - 112)//8, 16)
        self.sections = []
        for i in range(count):
            p = self.opt + opt_len + 40*i
            raw = self.bytes(p, 40)
            name = raw[:8].split(b'\0')[0].decode('ascii', 'replace')
            vs, va, size, offset = struct.unpack_from('<IIII', raw, 8)
            if size: self.bytes(offset, size)
            self.sections.append(dict(name=name, va=va, virtual_size=vs, size=size,
                                      offset=offset, flags=struct.unpack_from('<I', raw, 36)[0]))
    def bytes(self, offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset > len(self.data) - size:
            raise FormatError('Read outside file')
        return self.data[offset:offset+size]
    def u16(self,p): return struct.unpack('<H',self.bytes(p,2))[0]
    def u32(self,p): return struct.unpack('<I',self.bytes(p,4))[0]
    def u64(self,p): return struct.unpack('<Q',self.bytes(p,8))[0]
    def offset(self, rva: int, size: int = 1) -> int:
        if size < 0 or rva < 0: raise FormatError('Negative RVA/size')
        if rva < self.header_size and rva + size <= self.header_size:
            self.bytes(rva,size); return rva
        matches = [s for s in self.sections if s['va'] <= rva and rva+size <= s['va']+s['size']]
        if len(matches) != 1: raise FormatError('RVA not uniquely disk backed: %#x' % rva)
        s = matches[0]; return s['offset'] + rva - s['va']
    def at(self,rva,size): return self.bytes(self.offset(rva,size),size)
    def cstr(self,rva,limit=512):
        raw=bytearray()
        for i in range(limit):
            c=self.at(rva+i,1)
            if c == b'\0':
                try: return raw.decode('ascii')
                except UnicodeDecodeError as e: raise FormatError('Non-ASCII PE string') from e
            raw.extend(c)
        raise FormatError('Unterminated PE string')
    def directory(self,n):
        return struct.unpack('<II',self.bytes(self.opt+112+n*8,8)) if n < self.directory_count else (0,0)
    def executable(self,rva):
        return any(s['va']<=rva<s['va']+s['size'] and s['flags']&0x20000000 for s in self.sections)
    def exports(self):
        er,es=self.directory(0)
        if not er: return {}
        d=self.at(er,40)
        nf,nn,af,an,ao=struct.unpack_from('<IIIII',d,20)
        if nf > 100000 or nn > nf: raise FormatError('Export counts invalid')
        functions=struct.unpack('<%dI'%nf,self.at(af,nf*4)) if nf else ()
        names=struct.unpack('<%dI'%nn,self.at(an,nn*4)) if nn else ()
        ordinals=struct.unpack('<%dH'%nn,self.at(ao,nn*2)) if nn else ()
        out={}
        for nr,o in zip(names,ordinals):
            if o>=nf: raise FormatError('Export ordinal out of range')
            name=self.cstr(nr); rva=functions[o]
            if name in out: raise FormatError('Duplicate export name')
            out[name]={'rva':rva,'forwarded':er<=rva<er+es,'executable':self.executable(rva)}
        return out
    def imports(self):
        ir,sz=self.directory(1)
        if not ir:return []
        out=[]
        for i in range(min(sz//20,4096)):
            d=struct.unpack('<5I',self.at(ir+i*20,20))
            if not any(d):return out
            if not d[3]:raise FormatError('Import name missing')
            out.append(self.cstr(d[3]))
        raise FormatError('Import descriptors not terminated')

def require_exports(pe: PE,names):
    if pe.machine != 0x8664: raise FormatError('Windows x64 machine required')
    exports=pe.exports()
    for name in names:
        e=exports.get(name)
        if not e or e['forwarded'] or not e['executable']:
            raise FormatError('Missing/non-direct/non-executable export: '+name)
    return exports

def bridge_profile(data: bytes) -> dict:
    if sha256(data) != BRIDGE_SHA256: raise FormatError('Not the byte-locked baseline DLL')
    pe=PE(data); require_exports(pe,['luaopen_wh3_native_bridge'])
    methods={}
    for i in range(13):
        n,f=struct.unpack('<QQ',pe.at(0x8120+16*i,16))
        methods[pe.cstr(n-pe.base)]='%#x'%(f-pe.base)
    guards=[]
    for i in range(4):
        row=pe.at(0x8210+i*48,48)
        name,rva,length=struct.unpack_from('<QII',row)
        if length>32:raise FormatError('Guard length changed')
        guards.append({'name':pe.cstr(name-pe.base),'rva':rva,'bytes_hex':row[16:16+length].hex()})
    backend='minhook.x64.dll'
    if backend.encode('utf-16le')+b'\0\0' not in data: raise FormatError('Backend name changed')
    return {'dll_sha256':BRIDGE_SHA256,'exe_sha256':EXE_SHA256,'backend':backend,
            'required_backend_exports':list(BACKEND_EXPORTS),'lua_method_rvas':methods,'guards':guards}

def pack(lua: bytes) -> bytes:
    # Same PFH5 / Mod / uncompressed single-entry layout as the supplied carrier.
    index=struct.pack('<I',len(lua))+b'\0'+VPATH.encode('ascii')+b'\0'
    return struct.pack('<4s6I',b'PFH5',3,0,0,1,len(index),0)+index+lua

def unpack(data: bytes) -> bytes:
    if len(data)<28:raise FormatError('Pack header truncated')
    sig,typ,dc,ds,n,isz,stamp=struct.unpack_from('<4s6I',data)
    if (sig,typ,dc,ds,n)!=(b'PFH5',3,0,0,1):raise FormatError('Not the single-file PFH5 Mod carrier')
    if isz<7 or 28+isz>len(data):raise FormatError('Pack index invalid')
    index=data[28:28+isz]
    length=struct.unpack_from('<I',index)[0]
    if index[4]!=0 or index[5:]!=VPATH.encode('ascii')+b'\0':raise FormatError('Pack entry mismatch')
    body=data[28+isz:]
    if len(body)!=length:raise FormatError('Pack body length mismatch')
    return body
