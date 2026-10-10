# N1 — WH3 9.0.3: unit update → member-position aggregation → group coordinate processing

**2026-10-10; exact-file instruction analysis, NOT a demonstrated formation-fix site.**  
User-provided EXE: SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, AMD64, image base `0x140000000`; 9.0.3 label from user (VERSIONINFO independent check still open). Read-only LLVM x64 analysis. **23 instruction byte guards + 6 direct E8 calls PASS; 8 isolated synthetic tests PASS.** No Ghidra processing, in-game motion observation or runtime patch.

## New grounded call order

An original per-unit update path at **RVA 0x03043648** has these consecutively decoded calls:

```asm
0x0304371F  mov rcx,rbx                    ; same root
0x03043722  call 0x030421A4               ; member-position / unit aggregate
0x03043727  mov rcx,rbx                    ; same root
0x0304372A  call 0x0302AE0C               ; group/coordinate processing
0x0304372F  cmp dword ptr [rbx+0x184],esi  ; nonempty member-list check
...
0x03043769  lea rcx,[rbx+0x278]
0x03043770  call 0x0304433C               ; previously confirmed unit order processing
```

This gives an instruction-backed **ordering** of separate member aggregate and group coordinate updates before original queued-order processing **along this basic-block path**. It does NOT prove a causal group synchronization policy, that all paths/frames follow exactly the same sequence, or that any per-soldier waypoint promotion happens here.

## Native position-bearing member list (type not proven)

At `0x030421A4`:

```asm
0x030421EC  mov rdx,[rcx+0x188]         ; 8-byte pointer array candidate
0x030421F3  mov r8d,[rcx+0x184]        ; element count candidate
0x030421FA  lea rsi,[rdx+r8*8]
0x03042203  mov rcx,[rdx]              ; pointer to one member-like object
...
0x0304220C  movss xmm3,[rcx+0x88]      ; member X-like float
0x0304221F  movss xmm2,[rcx+0x90]      ; member Z-like float
...
0x0304222B  comiss xmm0,[r9+0xD0]    ; compare member-dependent value with group bounds
...
0x03042266  mov [rdi+0x3E9C],r10b    ; condition flag update
0x0304226D  add r11d,[rcx+0x704]      ; member-specific counter
0x03042274  mov [rdi+0x3C14],r11d     ; group aggregate write
...
0x030422C1  jne 0x03042203           ; next member
```

More of the function computes group-level aggregates and calls `0x03039D9C`, `0x03046DF4`, and other unit routines. **Crucial evidence limitation:** although the loop dereferences position-bearing member objects, the data structure `root+0x184/+0x188` is **not yet independently typed as a soldier model list**. It may be a subset/group list or another logical member array. A model-specific steering/arrival write is **not** present in these proven excerpts. Prior `root+0x114/+0x118` hints from old probes must not be silently conflated with this list.

## Native group position/coordinate construction path

`0x0302AE0C` reads the root's `+0x32F8` group pointer, extracts group `+0xB70`, calls `0x03034504` for a two-component coordinate value, then passes `root+0x3C38` plus the returned value into `0x0302A5C4`:

```asm
0x0302AE10  mov rax,[rcx+0x32F8]
0x0302AE1F  movzx r10d,word ptr [rax+0xB70]
0x0302AE27  call 0x03034504
0x0302AE32  lea rdx,[r11+0x3C38]
0x0302AE4C  call 0x0302A5C4
```

`0x03034504` itself loads `root+0x32F8` and accesses group subobject `+0xC10`, calls `0x0311D0CC` and writes the two selected coordinate components to its output. `0x0302A5C4` contains group-position geometric comparisons and handles group pointers, but **its real game-level meaning is not yet proven to be formation slots or soldiers' assigned destinations**.

## What this changes and what remains OPEN

**Advance relative to prior N1:** before we focused on UnitRoot queued commands and native route state; now we have exact, inspectable *unit update → position-bearing members → group coordinate computation* entry points for subsequent per-model provenance tracing. This is relevant to the user's real report of **intra-card model heading divergence and crowding**, unlike assumed vanilla unit-wide stopping.

**Not yet proved:** identity of each member as an individual soldier; the original model-specific target writer and reader; formation-slot and facing assignment; per-model arrival/turn predicate; any original grouping/coherence rule; causal link to jostling. Do not name `0x0302A5C4` a soldier waypoint scheduler, invent offsets/ABI, or install a Hook.

**Next N1 task:** follow actual writes to the position-bearing member objects, identify their formation-slot/desired-heading target producers and native turn/arrival consumers. Prioritize xrefs/callers of `0x0302A5C4` and `0x030421A4` alongside validated member-array producers; find the *first divergence* of targets or transition phase for members of one card. Compare original Shift and normal RMB without assuming that member objects carry independent high-level Shift queues.

## Reproducibility / boundaries

The read-only program `maintenance_tools/native_shift_re/audit_903_formation_entry.py` checks exact instruction bytes and real E8 target RVAs against the pinned SHA; unit tests exercise wrong-hash rejection, bounds, executability, relative call decoding and no input write. Report records `runtime_patch_authorized=false`. **STATIC** and **OFFLINE** only; no Win64 Hook or WH3 validation. 8/8 synthetic tests PASS locally.
