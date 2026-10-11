#!/usr/bin/env python3
"""Strict/read-only BSC WH3 full native MOVE chain auditor.

Loads a source-frozen, exact-SHA manifest of original native instruction bytes,
resolved direct calls, vtable slots, function boundaries, and typed object
ownership. Proves a *static* program-level graph, not a V3 runtime branch or
safe patch. Zero binary writes, no injection, no game process interaction.

Examples:
    python audit_wh3_full_native_chain.py --exe /path/to/Warhammer3.exe \\
      --out native_proof.json --dot native_known_graph.dot
    python audit_wh3_full_native_chain.py --manifest full_chain_manifest.json \\
      --exe /path/to/Warhammer3.exe --no-disasm
"""
import argparse
import bisect
import hashlib
import json
import mmap
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

DEFAULT_MANIFEST = Path(__file__).with_name('full_chain_manifest.json')
EXPECTED_SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
EXPECTED_IMAGE_BASE = 0x140000000

class StrictPE:
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open('rb') as stream:
            self.sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        if self.sha != EXPECTED_SHA:
            raise ValueError('SHA_MISMATCH: refusing wrong EXE; got ' + self.sha)
        self._fd = self.path.open('rb')
        self._mm = mmap.mmap(self._fd.fileno(), 0, access=mmap.ACCESS_READ)
        mem = self._mm
        if mem[:2] != b'MZ': raise ValueError('NOT_PE_MZ')
        ntheader = struct.unpack_from('<I', mem, 0x3c)[0]
        if mem[ntheader:ntheader+4] != b'PE\0\0':
            raise ValueError('NOT_PE_SIGNATURE')
        machine, number = struct.unpack_from('<HH', mem, ntheader+4)
        if machine != 0x8664: raise ValueError('NOT_WIN64_X64')
        optional_size = struct.unpack_from('<H', mem, ntheader+20)[0]
        optional = ntheader+24
        self.base = struct.unpack_from('<Q', mem, optional+24)[0]
        if self.base != EXPECTED_IMAGE_BASE:
            raise ValueError('IMAGE_BASE_CHANGED')
        self.sections = []
        for i in range(number):
            s = optional + optional_size + 40*i
            name = mem[s:s+8].split(b'\0')[0].decode('ascii')
            virtual_size, rva, raw_size, raw_offset = struct.unpack_from('<IIII', mem, s+8)
            flags = struct.unpack_from('<I', mem, s+36)[0]
            self.sections.append((name, rva, raw_size, raw_offset, virtual_size, flags))
        er, es = struct.unpack_from('<II', mem, optional+112+3*8)
        if es % 12:raise ValueError('BAD_RUNTIME_FUNCTION_TABLE')
        self.unwind = list(struct.iter_unpack('<III', self.read(er, es)))
        self.starts = [x[0] for x in self.unwind]
    def close(self):
        self._mm.close()
        self._fd.close()
    def read(self,rva,length,code=False):
        for name,s,rawsize,offset,virtual,flags in self.sections:
            if s<=rva and rva+length<=s+rawsize:
                if code and not flags&0x20000000:
                    raise ValueError('NON_EXEC_INSTRUCTION: '+hex(rva))
                return bytes(self._mm[offset+rva-s:offset+rva-s+length])
        raise ValueError('RVA_OUT_OF_IMAGE: '+hex(rva))
    def function(self,rva):
        k=bisect.bisect_right(self.starts,rva)-1
        if k>=0:
            start,end,unwind=self.unwind[k]
            if start<=rva<end:return start,end
        return None
    def disasm(self, start, length):
        with tempfile.NamedTemporaryFile(mode='w+b') as tmp:
            tmp.write(self.read(start,length,True));tmp.flush()
            args=['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel',
                  '--adjust-vma='+hex(start),tmp.name]
            result=subprocess.run(args,capture_output=True,text=True,check=False)
            if result.returncode:
                raise ValueError('OBJDUMP_FAILED: '+result.stderr[-300:])
            return result.stdout

def from_hex(value):return int(value,16)

def read_manifest(path):
    data=json.loads(Path(path).read_text(encoding='utf8'))
    if data.get('schema')!='bsc.wh3.original_move_fullchain.static.v1':
        raise ValueError('MANIFEST_SCHEMA_MISMATCH')
    if data.get('exe_sha256')!=EXPECTED_SHA or from_hex(data.get('image_base','0'))!=EXPECTED_IMAGE_BASE:
        raise ValueError('MANIFEST_TARGET_MISMATCH')
    return data

def verify(pe,manifest,disasm_enabled):
    checks=Counter()
    if len(pe.unwind)!=manifest['unwind_function_count']:
        raise ValueError('UNWIND_FUNCTION_COUNT_CHANGED')
    for item in manifest['guard_sites']:
        rva=from_hex(item['site']);expected=bytes.fromhex(item['pattern'])
        if pe.read(rva,len(expected),True)!=expected:
            raise ValueError('OPCODE_GUARD_MISMATCH: '+item['description']+' @'+hex(rva))
        checks['opcode_guards']+=1
    for item in manifest['direct_edges']:
        site=from_hex(item['site']);dest=from_hex(item['callee']);data=pe.read(site,5,True)
        if data[0] != (0xE8 if item['kind']=='call' else 0xE9):
            raise ValueError('DIRECT_EDGE_NOT_CALL_OR_JUMP: '+hex(site))
        observed=(site+5+struct.unpack_from('<i',data,1)[0])&0xffffffff
        if observed!=dest:raise ValueError('DIRECT_EDGE_TARGET_MISMATCH: '+hex(site))
        checks['verified_curated_edges']+=1
    for item in manifest['vtable_entries']:
        slot=from_hex(item['slot']);actual=struct.unpack('<Q',pe.read(slot,8))[0]
        if actual!=pe.base+from_hex(item['implementation']):
            raise ValueError('VTABLE_WRONG: '+hex(slot))
        checks['vtable_entries']+=1
    catalog={n['rva']:n for n in manifest['known_nodes']}
    for item in manifest['known_nodes']:
        a=item['rva'];fn=pe.function(a)
        if item['has_unwind']:
            if fn is None or fn[0]!=a or fn[1]-a!=item['size']:
                raise ValueError('ORIGINAL_FUNCTION_BOUNDARY_CHANGED: '+hex(a))
        if pe.read(a,len(bytes.fromhex(item['head'])),True).hex()!=item['head']:
            raise ValueError('FUNCTION_PROLOGUE_CHANGED: '+hex(a))
        checks['native_node_functions']+=1
    by_owner={}
    for edge in manifest['all_decoded_outgoing_calls']:
        owner=from_hex(edge['owner']);site=from_hex(edge['site']);dest=from_hex(edge['dest'])
        if owner not in catalog:raise ValueError('GRAPH_OWNER_NOT_SELECTED: '+hex(owner))
        fn=pe.function(site)
        if fn is None or fn[0]!=owner:
            # Valid leaf functions (no PE unwind) are admitted only by their explicitly pinned span.
            if catalog[owner]['has_unwind'] or not owner<=site<owner+catalog[owner]['size']:
                raise ValueError('CALL_SITE_NOT_OWNED_BY_FN: '+hex(site))
        raw=pe.read(site,5,True)
        if raw[0]!=0xe8 or (site+5+struct.unpack_from('<i',raw,1)[0])&0xffffffff!=dest:
            raise ValueError('DECODED_CALL_EDGE_CHANGED: '+hex(site))
        targetfn=pe.function(dest)
        targetstart=targetfn[0] if targetfn else dest
        if targetstart!=from_hex(edge['target_function']):
            raise ValueError('DECODED_CALLEE_OWNER_CHANGED: '+hex(site))
        by_owner.setdefault(owner,set()).add(site)
        checks['decoded_outgoing_calls']+=1
    checks['unwind_functions_total']=len(pe.unwind)
    if disasm_enabled:
        for owner,node in catalog.items():
            asm=pe.disasm(owner,node['size'])
            actual_sites=set()
            for line in asm.splitlines():
                m=re.match(r'^\s*([0-9a-f]+):\s+e8\s+(?:[0-9a-f]{2}\s+){4}call\s+0x([0-9a-f]+)',line)
                if m:actual_sites.add(int(m.group(1),16))
            if actual_sites!=by_owner.get(owner,set()):
                extra=actual_sites-by_owner.get(owner,set());missing=by_owner.get(owner,set())-actual_sites
                raise ValueError('INSTRUCTION_BOUNDARY_CHANGE: '+hex(owner)+' extra='+str(list(map(hex,extra))[:10])+' missing='+str(list(map(hex,missing))[:10]))
            checks['decoded_function_bodies']+=1
    if checks['native_node_functions']!=manifest['counts']['selected_function_nodes']:
        raise ValueError('NODE_CENSUS_MISMATCH')
    if checks['decoded_outgoing_calls']!=manifest['counts']['direct_calls_from_selected_nodes']:
        raise ValueError('DECODED_EDGE_CENSUS_MISMATCH')
    if len(manifest['native_object_ownership'])<9:raise ValueError('OBJECT_BOUNDARY_NOT_DOCUMENTED')
    if manifest['original_v3_branch_execution']!='not recorded; no code-level proof A vs B was taken':
        raise ValueError('FALSE_V3_BRANCH_PROOF')
    if manifest['patch_authorized'] is not False:raise ValueError('PATCH_NOT_ALLOWED')
    return {
      'proof_level':'original-exe-pinned static call/data graph; not a V3 branch trace',
      'sha256':pe.sha,'checks':dict(checks),
      'scope':dict(manifest['counts']),
      'object_types_reconciled':len(manifest['native_object_ownership']),
      'related_categories':{k:len(v) for k,v in manifest['categories'].items()},
      'new_member_direction_bridge':manifest['newly_connected_conditional_dataflow'],
      'open_edges':manifest['explicit_unknown_data_edges'],
      'mode_a_or_b_in_v3':'unobserved',
      'authorized_patch':False,
    }

def generate_dot(manifest):
    nodes={x['rva']:x for x in manifest['known_nodes']};lines=['digraph BSC_903 {',
       '  graph [rankdir=LR, labelloc="t",label="BSC native full-chain (original SHA; static reachability only)"];',
       '  node [shape=box,fontsize=8]; edge [arrowsize=0.6];']
    for rva,n in nodes.items():
        label=hex(rva)+('\n'+','.join(n['categories'][:2])if n['categories'] else '')
        color='lightblue' if 'GROUP_TASK_B' in n['categories'] else 'palegreen' if 'ACTOR_PER_FRAME' in n['categories'] else 'white'
        lines.append(f'  F{rva:X} [label="{label}",style=filled,fillcolor="{color}"];')
    edges=set()
    for x in manifest['all_decoded_outgoing_calls']:
        owner=from_hex(x['owner']);dest=from_hex(x['target_function'])
        if owner in nodes and dest in nodes and owner!=dest:edges.add((owner,dest))
    for a,b in sorted(edges):lines.append(f'  F{a:X} -> F{b:X};')
    lines.append('}')
    return '\n'.join(lines)+'\n'

def main():
    ar=argparse.ArgumentParser(description=__doc__)
    ar.add_argument('--exe',type=Path,required=True)
    ar.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST)
    ar.add_argument('--out',type=Path)
    ar.add_argument('--dot',type=Path)
    ar.add_argument('--no-disasm',action='store_true',help='Skip objdump instruction boundary check; byte-level guards still mandatory')
    args=ar.parse_args()
    for target in (args.out,args.dot):
        if target and target.resolve()==args.exe.resolve():ar.error('never overwrite the supplied EXE')
    try:
        m=read_manifest(args.manifest)
        pe=StrictPE(args.exe)
        try:result=verify(pe,m,not args.no_disasm and shutil.which('objdump') is not None)
        finally:pe.close()
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        if args.dot:
            args.dot.parent.mkdir(parents=True,exist_ok=True)
            args.dot.write_text(generate_dot(m),encoding='utf8')
        c=result['checks']
        print('PASS exact EXE,',c['native_node_functions'],'nodes,',c['decoded_outgoing_calls'],
              'decoded calls,',c['opcode_guards'],'pinned opcode checks,',c['vtable_entries'],
              'virtual slots,',c.get('decoded_function_bodies',0),'disassembled bodies; NO PATCH')
        return 0
    except (OSError,ValueError,struct.error,KeyError,subprocess.SubprocessError) as exc:
        print('STRICT_FULLCHAIN_AUDIT_BLOCKED:',exc,file=sys.stderr)
        return 2
if __name__=='__main__':sys.exit(main())