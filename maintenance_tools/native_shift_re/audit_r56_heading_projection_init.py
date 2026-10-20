#!/usr/bin/env python3
"""R56: read-only, SHA-gated provenance of WH3 heading lookup and route projection.

Static proof only. Does not attach to a game process, hook, or patch any code.
"""
from pathlib import Path
import argparse, json, math, struct, sys, subprocess, re, tempfile
from audit_r53_turn_heading import PE, EXPECTED_SHA

PIN_FILE=Path(__file__).with_name('r56_exact_pins.txt')
def pins():
    result={}
    for raw in PIN_FILE.read_text('utf-8').splitlines():
        line=raw.split('#',1)[0].split()
        if not line:continue
        if len(line)!=2:raise ValueError('INVALID_PIN_ROW')
        at=int(line[0],16)
        if at in result:raise ValueError('DUPLICATE_PIN')
        result[at]=bytes.fromhex(line[1])
    if len(result)!=47:raise ValueError('PIN_COUNT_DRIFT')
    return result

# Pin list is frozen directly from the SHA-identical user's EXE; any mismatch fails closed.
CALLS={0x00186474:0x006042E8,0x00604322:0x01120900,
       0x00604356:0x01185360,0x03017A79:0x030F1B3C,
       0x03017AA3:0x0301E890,0x03017AB6:0x0300D948}
TABLE=0x03E8F360
ANGLE_STEP=0x039228A0
HALF=0x0392211C
LOCAL_CONST_ONE=0x036B7830

def projected_point(x,z,extent,heading):
    """Synthetic trigonometric model; not a recovered WH3 runtime trajectory."""
    if not all(math.isfinite(v) for v in (x,z,extent,heading)):raise ValueError('NONFINITE')
    return (x-.5*extent*math.sin(heading),z-.5*extent*math.cos(heading))

def projected_jump(extent,h0,h1):
    a=projected_point(0,0,extent,h0);b=projected_point(0,0,extent,h1)
    return math.dist(a,b)

def leaf_instruction_starts(p,begin,end):
    with tempfile.NamedTemporaryFile() as f:
        f.write(p.read(begin,end-begin));f.flush()
        out=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel',
          '--no-show-raw-insn',f'--adjust-vma={hex(begin)}',f.name],capture_output=True,text=True,check=True).stdout
    return {int(m.group(1),16) for line in out.splitlines()
      if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(.+)$',line))}

def audit(exe):
    p=PE(Path(exe));checked={};pin_set=pins()
    leaves={}
    for lo,hi in ((0x01120900,0x01120943),(0x0301E890,0x0301E8AD)):
        leaves[(lo,hi)]=leaf_instruction_starts(p,lo,hi)
    for at,raw in pin_set.items():
        if p.read(at,len(raw))!=raw or not p.is_exec(at):raise ValueError(f'PIN_DRIFT:{at:08X}')
        fn=p.owner(at)
        if fn:
            if fn not in checked:checked[fn]=p.instructions(fn)
            if at not in checked[fn]:raise ValueError(f'MID_INSTRUCTION:{at:08X}')
        else:
            applicable=next((starts for (lo,hi),starts in leaves.items() if lo<=at<hi),None)
            if applicable is None or at not in applicable:raise ValueError(f'UNVERIFIED_LEAF_START:{at:08X}')
    for at,target in CALLS.items():
        b=p.read(at,5)
        if b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=target:
            raise ValueError(f'E8_TARGET:{at:08X}')
    def lea_target(at):
        b=p.read(at,7)
        if b[:2]!=b'\x48\x8d':raise ValueError('NOT_LEA')
        return at+7+struct.unpack_from('<i',b,3)[0]
    if lea_target(0x00604304)!=TABLE or lea_target(0x03102be6)!=TABLE:
        raise ValueError('TABLE_BINDING_CHANGED')
    # Verify the sampled zero-initialized table is generated at runtime, not const wave values.
    if p.read(TABLE,32)!=b'\0'*32:raise ValueError('TABLE_DISK_NOT_ZERO')
    scale=struct.unpack('<f',p.read(ANGLE_STEP,4))[0]
    if abs(scale-2*math.pi/65536)>1e-9:raise ValueError('STEP_NOT_RADIAN_RATIO')
    one=struct.unpack('<f',p.read(LOCAL_CONST_ONE,4))[0]
    half=struct.unpack('<f',p.read(HALF,4))[0]
    if one!=1. or half!=.5:raise ValueError('CONSTANT_DRIFT')
    if p.read(0x00604366,6)!=b'\x81\xff\x00\x00\x01\x00':raise ValueError('LUT_LENGTH_CHANGED')
    # Instruction-level data flow: route angle copied, old binding released, then new binding stored.
    for at,hexbytes in {0x03017a69:'440fb7cb',0x03017a79:'e8bea00d00',
                        0x03017aa3:'e8e86d0000',0x03017abb:'48898770020000'}.items():
        if p.read(at,len(bytes.fromhex(hexbytes)))!=bytes.fromhex(hexbytes):raise ValueError('COMMIT_ORDER_CHANGED')
    return dict(schema='bsc.r56.heading_lookup_projection.v1',exe_sha=EXPECTED_SHA,
        static_only=True,verified_pins=len(pin_set),verified_direct_e8=len(CALLS),
        constructor_caller='0x00186474 CALL 0x006042E8',
        lookup_init='0x006042E8',lookuptable_rva=hex(TABLE),
        lookup_producer='0x00604322 call packed angle/math routine, stores 2 floats to [table+i*8] and [table+i*8+4]',
        lookuptable_disk_zero=True,iterations=65536,angle_radians_per_step=scale,
        zero_angle_small_branch='0x0112092A through +0x42 yields packed 0 and 1 (xmm0:low two lanes)',
        converter_use='0x03102BE6 references same table; +0x3C-+0x40 times one-half gives position offset',
        extent_is_formation_layout=True,
        route_commit_stage='0x03017AA3 -> 0x0301E890 conditionally decrements [Root+0x1E8+0x18]+4 and clears [Root+0x1E8+0x80]; 0x03017ABB publishes Root+0x270 route',
        local_angular_interpolation_proven=False,
        runtime_shift_leg_discontinuity_measured=False,root_cause_proven=False,
        gameplay_patch_authorized=False)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--out',type=Path)
    a=ap.parse_args()
    if a.out and a.out.resolve()==a.exe.resolve():ap.error('REFUSE_EXE_OVERWRITE')
    result=audit(a.exe)
    if a.out:a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('PASS',result['verified_pins'],'pins',result['verified_direct_e8'],'E8; READ ONLY')
