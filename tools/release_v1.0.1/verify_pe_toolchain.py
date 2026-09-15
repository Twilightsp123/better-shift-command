from pathlib import Path
import argparse, struct, sys
ap=argparse.ArgumentParser()
ap.add_argument('dll', type=Path)
a=ap.parse_args()
b=a.dll.read_bytes()
if b[:2] != b'MZ':
    raise SystemExit('NOT_PE_MZ')
pe=struct.unpack_from('<I', b, 0x3c)[0]
if b[pe:pe+4] != b'PE\0\0':
    raise SystemExit('NOT_PE_SIGNATURE')
opt=pe+4+20
magic=struct.unpack_from('<H',b,opt)[0]
major=b[opt+2]; minor=b[opt+3]
machine=struct.unpack_from('<H',b,pe+4)[0]
print(f'PE_MACHINE=0x{machine:04x}')
print(f'PE_MAGIC=0x{magic:04x}')
print(f'LINKER_VERSION={major}.{minor:02d}')
if machine != 0x8664 or magic != 0x20b:
    raise SystemExit('NOT_AMD64_PE32PLUS')
# Runtime-validated v0.5.0 DLL was built with MSVC linker 14.29 (VS2019/v142).
if not (major == 14 and minor == 29):
    raise SystemExit(f'UNVALIDATED_LINKER_VERSION_{major}_{minor:02d}_EXPECTED_14_29')
print('TOOLCHAIN_MATCH=VS2019_V142_LINKER_14_29')
