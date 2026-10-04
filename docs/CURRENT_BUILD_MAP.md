# WH3 9.0.2 Build Map — CorePath build candidate

Target EXE SHA256: `fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785`

**Validation state:** static relocation/dataflow PASS; Windows v142/MASM build, Windows Native CTest, and WH3 runtime smoke are still pending. The last runtime-validated build remains WH3 9.0.1 / Bridge 1.0.17.

## Mandatory core hooks (16)

| Hook | RVA | Relocation evidence |
|---|---:|---|
| move | `0x030351AC` | exact guard + Move/Attack relationship |
| attack | `0x03033544` | exact unique |
| allocator | `0x02F53128` | exact unique |
| halt | `0x0301C5E0` | normalized unique; rel32 changed |
| lua_move | `0x02ED6404` | exact guard + Lua pair relationship |
| lua_attack | `0x02ED5C9C` | exact unique |
| publish_move | `0x01CAFDDC` | normalized + regional/global/call relationship |
| publish_attack | `0x02DF3410` | normalized + regional/global/call relationship |
| writer_begin | `0x01BCBE28` | exact unique |
| writer_finalize | `0x01BCF144` | exact unique |
| copy | `0x01BACFB4` | exact unique |
| stage | `0x01BAE7B8` | exact unique |
| move_handler | `0x02ECFCD0` | exact guard + handler-pair/call relationship |
| attack_handler | `0x02ECF79C` | exact unique |
| selection | `0x02F04F70` | exact unique |
| free | `0x00537420` | normalized unique; branch/RIP displacements changed |

All 16 candidate guards were independently re-read from the supplied 9.0.2 EXE and match byte-for-byte.

## Optional static sites

| Site | RVA | Runtime |
|---|---:|---|
| ContactPair | `0x030A4505` | staged disabled / physical research only |
| Smart Guard state transition | `0x030E319C` | staged disabled |

Both optional guards also match the 9.0.2 EXE, but they remain outside CorePath release authorization.

## Re-derived order identity

| Item | WH3 9.0.2 RVA | Evidence |
|---|---:|---|
| allocator | `0x02F53128` | top-level Move/Attack call |
| common base constructor | `0x0300B518` | called by both full Move and Attack constructors |
| Full Move constructor | `0x0300BDC0` | called after allocator by top-level Move |
| Simple/Intercept Move constructor | `0x0300BD64` | sibling constructor; not top-level outcome |
| Attack constructor | `0x0300B8C4` | called after allocator by top-level Attack |
| Full Move VTable | `0x03913618` | installed by Full Move constructor |
| Simple/Intercept Move VTable | `0x03910438` | sibling only; **not** top-level Move identity |
| Attack VTable | `0x03912988` | installed by Attack constructor |

The Move/Attack VTables were derived from current-EXE allocator→constructor→RIP-relative VTable stores. They were not obtained by adding a global RVA delta to the 9.0.1 values.

## Address source of truth

Addresses and exact guards live in:

- `native_maps/CURRENT`
- `native_maps/wh3_9.0.2_fec656f4.json`

`maintenance_tools/generate_native_header.py` renders `src/native_bridge/include/wh3/generated_native_map.hpp`. Runtime C++ consumes the generated header and no longer maintains a second manual RVA table.

Maintenance workflow: `docs/NATIVE_ADDRESS_MAINTENANCE_PIPELINE.md`.

## Previous runtime-validated map

WH3 9.0.1 / SHA `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297` is preserved as `native_maps/wh3_9.0.1_6c104a63.json` and remains the last map with completed Windows/runtime evidence until this 9.0.2 candidate passes those gates.
