#!/usr/bin/env python3
"""BSC N1 — native ordinary-B packet flags and typed member task handoff.

Read-only exact-EXE forensic verifier, never patches game state.
Owner/outgoing links are PE-unwind + byte verified; never infer player Shift
instance, a motor goal, or a gameplay fix from static reachability.
"""
import argparse, bisect, hashlib, json, mmap, re, shutil, struct, subprocess, tempfile
from pathlib import Path

SHA = "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
IMAGEBASE = 0x140000000
PINS = {
    0x008F4DD0: "0fb68190000000",
    0x008F4DD7: "c0e804",
    0x008F4DDA: "2401",
    0x008F4DDC: "c3cc",
    0x02D99FD9: "0fb64150",
    0x02D9A017: "324250",
    0x02D9A01A: "2410",
    0x02D9A01C: "32c1",
    0x02D9A01E: "41884050",
    0x02D9A06B: "c3",
    0x03082353: "413ac7",
    0x03082356: "753e",
    0x02ECA989: "488d4b18",
    0x02ECA999: "e82a4e0900",
    0x02F448E4: "488d8fe0050000",
    0x02F448F5: "488d97c8050000",
    0x02F448FC: "e8c7ae0100",
    0x03265C69: "e832470000",
    0x03265D3F: "ff9068030000",
    0x0326A3B9: "807c247800",
    0x0326A3CA: "7562",
    0x0326A3E3: "e8fcf1e6ff",
    0x0326A3E8: "84c0",
    0x0326A3EA: "7542",
    0x0326A402: "c644243800",
    0x0326A40A: "c644243000",
    0x0326A423: "e8b454cfff",
    0x0326A428: "804e5008",
    0x0326A445: "c644243800",
    0x0326A44D: "c644243001",
    0x0326A466: "e87154cfff",
    0x02F5F8DC: "8b02",
    0x02F5F915: "0fb6442438",
    0x02F5F924: "0fb64c2440",
    0x02F5F932: "c0e104",
    0x02F5F935: "0ac8",
    0x02F5F940: "80c906",
    0x02F5F95E: "41884a50",
    0x0306BA23: "e8dc73d5ff",
    0x0306BA2B: "84c0",
    0x0306BA2F: "f6425020",
    0x0306BA35: "488d8f90040000",
    0x0306BA41: "488d8fa8040000",
    0x0306BA54: "488d9790040000",
    0x0306BA5B: "e8683defff",
    0x02DB0AC2: "389130010000",
    0x02DB0AD5: "c6833001000000",
    0x0324C148: "48895110",
    0x0324C163: "c6823001000001",
    0x02F5F7D8: "e837c92e00",
    0x02F5F7DD: "488d0534669a00",
    0x02F5F7EE: "e881a7e3ff",
    0x02F5F82E: "f30f118f98000000",
    0x02F5F84A: "898fa0000000",
    0x02F83B2A: "80b99c00000000",
    0x02F83B65: "807b2000",
    0x02F83B78: "488bcb",
    0x02F83B85: "f6839000000080",
    0x02F83BB8: "e8bb35feff",
    0x02F83BCD: "e8a669ffff",
    0x02F83BDD: "e8d2ec2c00",
    0x02F6B184: "8b81a0000000",
    0x02F6B18A: "398298000000",
    0x02F6B1C5: "e8aebfffff",
    0x02F6B1D6: "e99df30000",
    0x02F6B1DB: "e810ee0000",
    0x02F7A6D9: "ff90b0050000",
    0x02F7A116: "ff9080050000",
    0x02F7A17D: "ff9068050000",
    0x0306AD1A: "488db928030000",
    0x0306AD34: "e8d75cd4ff",
    0x0306AD48: "e8abeb1d00",
    0x0306AD8D: "e87e5cd4ff",
    0x0306A99A: "488d9928030000",
    0x0306A9A7: "e86460d4ff",
    0x0306A9BB: "e890e91d00",
    0x0306A906: "488d9928030000",
    0x0306A913: "e8f860d4ff",
    0x0306A927: "e8a4e71d00",
    0x030822CB: "488d8f28030000",
    0x030822D2: "e875ecffff",
    0x0308233A: "4438bfc0050000",
    0x03082343: "488d8fa8040000",
    0x0308234D: "ff9080000000",
}
# Exact E8 rel32 edges. None imply a real-time Shift execution hit.
E8 = {
 0x02ECA999: 0x02F5F7C8, 0x02F448FC: 0x02F5F7C8,
 0x03265C69: 0x0326A3A0, 0x0326A3E3: 0x030D95E4,
 0x0326A423: 0x02F5F8DC, 0x0326A466: 0x02F5F8DC,
 0x0306BA23: 0x02DC2E04, 0x0306BA5B: 0x02F5F7C8,
 0x02F5F7D8: 0x0324C114, 0x02F5F7EE: 0x02D99F74,
 0x02F83BB8: 0x02F67178, 0x02F83BCD: 0x02F7A578,
 0x02F83BDD: 0x032528B4, 0x02F6B1C5: 0x02F67178,
 0x02F6B1DB: 0x02F79FF0,
 0x0306AD34: 0x02DB0A10, 0x0306AD48: 0x032498F8,
 0x0306AD8D: 0x02DB0A10, 0x0306A9A7: 0x02DB0A10,
 0x0306A9BB: 0x03249350, 0x0306A913: 0x02DB0A10,
 0x0306A927: 0x032490D0, 0x030822D2: 0x03080F4C,
}
VTABLE = {
 (0x03905E18,0x80): 0x008F4DD0,
 (0x03905E18,0x00): 0x02F63C30,
 (0x03905E18,0x08): 0x02F737D0,
 (0x03905E18,0x10): 0x02F83B24,
 (0x0390D4F8,0x368): 0x0306B9F0,
 (0x0390D4F8,0x568): 0x0306A8FC,
 (0x0390D4F8,0x580): 0x0306A990,
 (0x0390D4F8,0x5B0): 0x0306AD00,
}


def ordinary_b_flag(aux_flag_0f, formation_helper_nonzero):
    """Symbolic local truth-table ONLY for 0x0326A3A0's two branches."""
    return 0x07 if aux_flag_0f or formation_helper_nonzero else 0x0E


def receiver_uses_inline_slot(mode_helper_result, packet_plus50):
    """0x0306B9F0 static branch predicate, NOT a movement-timing model."""
    return mode_helper_result == 0 and (packet_plus50 & 0x20) == 0


def inline_query_bit10(initial_packet_flags):
    """Read-only expression for vt+0x80 of the just-constructed inline task."""
    return bool(initial_packet_flags & 0x10)


def time_gate_open(current_tick, task_start_tick):
    """Unsigned comparison from 0x02F6B18A/190; other task gates still apply."""
    return (current_tick & 0xffffffff) >= (task_start_tick & 0xffffffff)


class OriginalEXE:
    def __init__(self, path):
        self.file = open(path, 'rb')
        self.mm = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        self.sha = hashlib.sha256(self.mm).hexdigest()
        if self.sha != SHA:
            self.close()
            raise ValueError('SHA_MISMATCH: fail-closed')
        if self.mm[:2] != b'MZ': raise ValueError('INVALID_DOS')
        pe = struct.unpack_from('<I', self.mm, 0x3c)[0]
        if self.mm[pe:pe+4] != b'PE\0\0': raise ValueError('INVALID_PE')
        opt = pe + 24
        if struct.unpack_from('<H', self.mm, opt)[0] != 0x20b:
            raise ValueError('NOT_PE32_PLUS')
        self.base = struct.unpack_from('<Q', self.mm, opt+24)[0]
        if self.base != IMAGEBASE: raise ValueError('IMAGEBASE_DRIFT')
        num = struct.unpack_from('<H', self.mm, pe+6)[0]
        oh = struct.unpack_from('<H', self.mm, pe+20)[0]
        self.sections = []
        for i in range(num):
            off = opt + oh + 40*i
            name = self.mm[off:off+8].rstrip(b'\0').decode('ascii')
            vs, va, rs, rp = struct.unpack_from('<IIII', self.mm, off+8)
            self.sections.append((name, va, max(vs,rs),rp,rs))
        exception_rva, exception_size = struct.unpack_from('<II', self.mm, opt+112+3*8)
        if exception_size % 12: raise ValueError('INVALID_PDATA')
        off = self._offset(exception_rva, exception_size)
        self.pdata = [struct.unpack_from('<III',self.mm,off+j) for j in range(0,exception_size,12)]
        self.starts = [x[0] for x in self.pdata]

    def close(self): self.mm.close();self.file.close()

    def _offset(self,rva,n):
        for name,va,sz,rp,rs in self.sections:
            if va<=rva and rva+n<=va+rs:
                return rp+rva-va
        raise ValueError('RVA_NOT_FILE_BACKED:'+hex(rva))

    def read(self, rva,n):
        off=self._offset(rva,n)
        return self.mm[off:off+n]

    def section(self,rva):
        for name,va,sz,rp,rs in self.sections:
            if va<=rva<va+rs:return name
        return None

    def owner(self,rva):
        i=bisect.bisect_right(self.starts,rva)-1
        if i<0:return None
        begin,end,unwind=self.pdata[i]
        return (begin,end,unwind) if begin<=rva<end else None

    def starts_in(self,begin,end):
        with tempfile.NamedTemporaryFile() as f:
            f.write(self.read(begin,end-begin));f.flush()
            proc=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64',
                '-M','intel','--no-show-raw-insn',f'--adjust-vma=0x{begin:x}',f.name],
                capture_output=True,text=True,check=True)
        return {int(m.group(1),16) for line in proc.stdout.splitlines()
                if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+[a-zA-Z.]',line))}


def audit(exe):
    if not shutil.which('objdump'): raise ValueError('OBJDUMP_REQUIRED')
    b=OriginalEXE(exe)
    try:
        instructions={}
        for rva,hexx in PINS.items():
            raw=bytes.fromhex(hexx)
            if b.section(rva)!='.00cfg':raise ValueError('NON_EXECUTABLE_PIN:'+hex(rva))
            if b.read(rva,len(raw))!=raw:raise ValueError('OPCODE_DRIFT:'+hex(rva))
            owner=b.owner(rva)
            # The packet builder at 0x02F5F8DC is a valid leaf, not a pdata entry.
            if owner is None and 0x02F5F8DC<=rva<0x02F5F963:
                bounds=(0x02F5F8DC,0x02F5F963)
            elif owner is None and 0x008F4DD0<=rva<0x008F4DDD:
                bounds=(0x008F4DD0,0x008F4DDD)
            elif owner is None and 0x02D99F74<=rva<0x02D9A06C:
                bounds=(0x02D99F74,0x02D9A06C)
            elif owner is not None:bounds=owner[:2]
            else:raise ValueError('UNWIND_OWNER_UNRESOLVED:'+hex(rva))
            if bounds not in instructions:
                instructions[bounds]=b.starts_in(*bounds)
            if rva not in instructions[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(rva))
        for site,target in E8.items():
            raw=b.read(site,5)
            if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=target:
                raise ValueError('E8_TARGET_DRIFT:'+hex(site))
        for (table,slot),target in VTABLE.items():
            ptr=struct.unpack('<Q',b.read(table+slot,8))[0]
            if ptr!=IMAGEBASE+target:raise ValueError('VTABLE_DRIFT:'+hex(table)+':'+hex(slot))
        # Constructor actually installs the checked virtual table.
        lea=b.read(0x02F5F7DD,7)
        if lea[:3]!=bytes.fromhex('488d05') or \
           0x02F5F7DD+7+struct.unpack_from('<i',lea,3)[0]!=0x03905E18:
            raise ValueError('CTOR_VTABLE_LEA_DRIFT')
        if b.read(0x02F5F962,2)!=bytes.fromhex('c3cc'):
            raise ValueError('LEAF_BOUNDARY_DRIFT')
        return {
            'schema':'bsc.n1.b_member_packet_task_lifecycle.v1',
            'exe_sha256':b.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
            'verified_instruction_starts':len(PINS),
            'verified_direct_calls':len(E8),
            'verified_typed_vtable_slots':len(VTABLE),
            'verified_b_sender_flags':[ordinary_b_flag(False,False),ordinary_b_flag(True,False)],
            'typed_constructor_static_callers':[hex(x) for x in (0x02ECA999,0x02F448FC,0x0306BA5B)],
            'typed_holder_offsets':{'member_action_slot':'0x328',
                'member_inline_task':'0x4a8','member_task_slot':'0x490','member_task_active':'0x5c0'},
            'receiver_mode0_without_bit20_goes_inline_slot':True,
            'inline_task_update':{'vtable':'0x3905e18','slot':'0x10','target':'0x2f83b24'},
            'inline_task_plus80_query':'bit4 of task+0x90 copied packet flags; 0x07/0x0e -> 0 at installation, no future mutation excluded',
            'next_handoff':'task -> member +0x328 action variants; final motor goal still unknown',
            'runtime_shift_branch_observed':False,
            'same_unit_member_packet_kind_divergence_observed':False,
            'native_patch_authorized':False}
    finally: b.close()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out and args.exe.resolve()==args.out.resolve(): ap.error('EXE_OVERWRITE_FORBIDDEN')
    result=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('STATIC_PASS',result['verified_instruction_starts'],'opcode/starts',
          result['verified_direct_calls'],'E8',result['verified_typed_vtable_slots'],
          'typed slots; NO_GAMEPLAY_PATCH')
if __name__=='__main__':main()
