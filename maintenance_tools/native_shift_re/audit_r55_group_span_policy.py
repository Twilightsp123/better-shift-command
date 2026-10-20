#!/usr/bin/env python3
"""BSC R55: SHA-guarded, READ-ONLY native Group span policy disambiguation.

Never hooks, writes the EXE, or infers a Shift-only runtime route from a static call.
This intentionally classifies a FORMATION-EXTENT policy, not curvature radius.
"""
from pathlib import Path
import argparse, json, math, struct
from audit_r53_turn_heading import PE, EXPECTED_SHA, BASE

HERE=Path(__file__).resolve().parent
PIN=HERE/'r55_group_span_exact_pins.txt'
# Each vtable is installed by a documented branch of 0x030CCDA4,
# at (Group+0xA30) and usually bound through (Group+0xB30).
# The two slots are called in order by 0x030D6A0C.
POLICY_TABLES={
 'square_floor':(0x039145F8,0x008F8190,0x008F8100),
 'square_ceil_spacing':(0x039144A8,0x008F8140,0x008F7080),
 'base_plus_one_step':(0x03914A30,0x030D6AA4,0x008F8110),
 'dynamic_bounded_linear':(0x039146B0,0x03065020,0x030D69F0),
 'table_dimensions_linear':(0x03914560,0x008F81B0,0x008F7080),
 'clamped_max13_linear':(0x03914978,0x030D6A94,0x008F7080),
 'scaled_2step_offset':(0x03914748,0x008F81C0,0x008F8120),
}
CALLS={0x030CCD97:0x030CCDA4,0x03017A4E:0x030D6A0C,
       0x030D6AAB:0x030E2ED0}
# For leaf methods, there is no PE unwind entry; vtable pointer is the
# instruction start; verify the first instruction and matching leaf RET.
LEAVES={
 0x008F8190:0x008F81A7,
 0x008F8100:0x008F810A,
 0x008F8140:0x008F8184,
 0x008F7080:0x008F7094,
 0x008F8110:0x008F811F,
 0x03065020:0x0306504D,
 0x030D69F0:0x030D6A08,
 0x008F81B0:0x008F81BF,
 0x030D6A94:0x030D6AA0,
 0x008F81C0:0x008F8205,
 0x008F8120:0x008F8133,
}
# Mathematically-sound examples of the precise recovered opcode fragments.
# These are SYNTHETIC examples, not actual game Group values.
def floor_square_dimension(n):
    if not isinstance(n,int) or n<0:raise ValueError('INVALID_COUNT')
    return math.floor(math.sqrt(n))
def ceil_square_dimension(n):
    if not isinstance(n,int) or n<0:raise ValueError('INVALID_COUNT')
    return math.ceil(math.sqrt(n))
def linear_span(dimension,offset,step):
    if not isinstance(dimension,int) or dimension<1 or not all(
      isinstance(x,(float,int)) and math.isfinite(x) for x in (offset,step)):
      raise ValueError('INVALID_SPAN_INPUT')
    return float(offset)+(dimension-1)*float(step)
def parse_pins():
    result={}
    for n,line in enumerate(PIN.read_text('utf-8').splitlines(),1):
        tok=line.split('#',1)[0].split()
        if not tok:continue
        if len(tok)!=2:raise ValueError(f'INVALID_PIN:{n}')
        at=int(tok[0],16)
        if at in result:raise ValueError('PIN_DUPLICATE')
        result[at]=bytes.fromhex(tok[1])
    if len(result)<40:raise ValueError('PIN_SET_TOO_SMALL')
    return result

def audit(exe):
    pe=PE(exe)  # SHA, PE x64 ImageBase and unwind via R53 helper
    pins=parse_pins()
    functions={};leaf_count=0
    for at,expected in pins.items():
        if pe.read(at,len(expected))!=expected or not pe.is_exec(at):
            raise ValueError(f'PIN_DRIFT:{at:08X}')
        owner=pe.owner(at)
        if owner is None:
            leaf=next(((lo,hi) for lo,hi in LEAVES.items() if lo<=at<=hi),None)
            if leaf is None:raise ValueError(f'UNEXPECTED_NO_UNWIND:{at:08X}')
            if pe.read(leaf[1],1)!=b'\xc3':raise ValueError('LEAF_RET_DRIFT')
            if at==leaf[0]:leaf_count+=1
        else:
            if owner not in functions:functions[owner]=pe.instructions(owner)
            if at not in functions[owner]:raise ValueError(f'MID_INSTRUCTION:{at:08X}')
    for site,target in CALLS.items():
        raw=pe.read(site,5)
        if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=target:
            raise ValueError(f'E8_TARGET_DRIFT:{site:08X}')
    # Real native grouped 'policy selection -> integer dimension -> float extent'.
    # Do not generalize these 7 vtables to all possible mode families.
    entries=[]
    for name,(table,m20,m28) in POLICY_TABLES.items():
        got20=struct.unpack('<Q',pe.read(table+0x20,8))[0]
        got28=struct.unpack('<Q',pe.read(table+0x28,8))[0]
        if (got20,got28)!=(BASE+m20,BASE+m28):
            raise ValueError(f'VTABLE_METHOD_DRIFT:{name}')
        for method in (m20,m28):
            if not pe.is_exec(method):raise ValueError('NON_EXEC_POLICY_METHOD')
        entries.append(dict(strategy=name,vtable=hex(table),method20=hex(m20),method28=hex(m28)))
    # Strong constructor/field identity checks.
    if pe.read(0x030C7D17,7)!=bytes.fromhex('4889ab300b0000'):
        raise ValueError('GROUP_INITIAL_NULL_DRIFT')
    for at,opcode in ((0x030CCF00,'48898b300b0000'),
                      (0x030CCFDA,'4c8993300b0000'),
                      (0x030CD1B9,'4889bb300b0000')):
        if pe.read(at,7)!=bytes.fromhex(opcode):raise ValueError('POLICY_BINDING_DRIFT')
    if pe.read(0x03017A47,7)!=bytes.fromhex('488b88300b0000'):
        raise ValueError('POLICY_CONSUMPTION_DRIFT')
    if pe.read(0x030D6A18,3)!=bytes.fromhex('ff5020') or \
       pe.read(0x030D6A2C,3)!=bytes.fromhex('49ffe0'):
        raise ValueError('POLICY_DOUBLE_DISPATCH_DRIFT')
    # The source geometry dimensions live in the unit root; not in a magic radius constant.
    for at,off in [(0x030CCD6B,0x1DC),(0x030CCD73,0x1D8),
                   (0x030CCD7B,0x1E4),(0x030CCD83,0x1E0)]:
        # All are MOVSS XMM,[RAX+imm32] for exact original SHA.
        raw=pe.read(at,8)
        if raw[-4:]!=struct.pack('<I',off):raise ValueError('ROOT_GEOMETRY_FIELD_DRIFT')
    return {
       'schema':'bsc.r55.group_extent_policy.v1',
       'proof':'EXACT_SHA_READONLY_PE_MACHINE_CODE',
       'exe_sha256':EXPECTED_SHA,
       'verified_pinned_instruction_sites':len(pins),
       'verified_direct_e8':len(CALLS),
       'verified_unwind_function_owners':len(functions),
       'verified_policy_vtable_pairs':len(entries),
       'group_policy_initial_null':'0x030C7D17 Group+0xB30=NULL',
       'group_policy_branch_initializer':'0x030CCDA4 chooses among multiple modes',
       'policy_embedded_storage':'Group+0xA30 (typical strategy instance)',
       'policy_runtime_binding':'Group+0xB30',
       'route_config_consumer':'0x03017A47 loads [Group+0xB30]',
       'two_stage_dispatch':'0x030D6A18 virtual+0x20 yields EAX dimension; +0x28 receives EDX=EAX and yields XMM0 extent',
       'unit_root_geometry_source':['Root+0x1D8','Root+0x1DC','Root+0x1E0','Root+0x1E4'],
       'sample_policies':entries,
       'interpretation':'formation-layout extent / arrangement dimension supported; not a radius or lookahead proof',
       'same_game_shift_policy_observed':False,
       'turn_radius_parameter_proven':False,
       'native_patch_authorized':False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    opts=ap.parse_args()
    if opts.out and opts.out.resolve()==opts.exe.resolve():ap.error('EXE_OVERWRITE_FORBIDDEN')
    out=audit(opts.exe)
    if opts.out:opts.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS',out['verified_pinned_instruction_sites'],'opcodes; 7 strategy tables; NO PATCH')
if __name__=='__main__':main()
