# WH3 9.0.1 Current Build Map — CorePath RC8

Locked EXE SHA256: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`

## Mandatory core hooks (16)

| Hook | RVA |
|---|---:|
| move | `0x030344D4` |
| attack | `0x03032854` |
| allocator | `0x02F5248C` |
| halt | `0x0301B890` |
| lua_move | `0x02ED5808` |
| lua_attack | `0x02ED50A0` |
| publish_move | `0x01CB1DC8` |
| publish_attack | `0x02DF28BC` |
| writer_begin | `0x01BCE174` |
| writer_finalize | `0x01BD140C` |
| copy | `0x01BAF488` |
| stage | `0x01BB0C94` |
| move_handler | `0x02ECF0E0` |
| attack_handler | `0x02ECEBAC` |
| selection | `0x02F042D4` |
| free | `0x0052F770` |

## Optional static sites

| Site | RVA | RC8 runtime |
|---|---:|---|
| ContactPair | `0x030A3859` | staged disabled / physical research only |
| Smart Guard state transition | `0x030E2524` | staged disabled |

Full Move VTable (top-level `Order::issue_move`): `0x03910AA8`  
Simple/Intercept Move VTable (internal sibling constructor, **not** the BSC top-level outcome type): `0x0390E248`  
Attack VTable: `0x03910228`

The exact byte guards live in `src/native_bridge/src/platform_windows.cpp` and are checked by `tools/prebuild_contract_check.py` and `tools/inspect_exe.py`. This document is descriptive; source + checker are authoritative.


## 2026-09-29 outcome dataflow correction

A direct current-EXE disassembly audit closed the top-level Move/Attack allocator→constructor→slot dataflow. The prior single “Move VTable = `0x0390E248`” entry was wrong: `0x0390E248` belongs to the sibling Simple/Intercept Move constructor `0x0300B038`, while the hooked player/top-level Move path `0x030344D4` calls Full Move constructor `0x0300B094`, which installs `0x03910AA8`. See `docs/static_audit_20260929/`.
