# N1 — WH3 9.0.3 original ring-order lifecycle: instruction-backed findings

**Status (2026-10-09): partial N1 native control-flow proof, no runtime patch authorized.**

## Exact executable provenance

- Input: user-provided Warhammer3.exe from Warhammer3.zip, 252,021,192 bytes.
- SHA256: \`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a\`
- PE32+ AMD64, preferred image base \`0x140000000\`.
- Game version **9.0.3 is user-supplied context**, not independently verified through an EXE version resource.
- Research method: read-only PE mapping, x64 exception-function ranges, LLVM instruction disassembly, E8 rel32 direct-call xrefs. 25/25 selected edges rechecked at decoded call instruction boundaries. No Ghidra database, game session, DLL or PACK in this audit.

## Verified: original order count/head mutation

**RVA \`0x02F4FD10\`**, exception-function range \`[0x02F4FD10, 0x02F4FD5B)\`. In relevant original callsites the RCX pointer is derived from \`UnitRoot + 0x288\`. Relevant machine instructions:

\`\`\`asm
0x02F4FD16  mov eax, dword ptr [rcx + 0x2D04]   ; root + 0x2F8C
0x02F4FD1F  lea rcx, [rax+rax*8]
0x02F4FD23  shl rcx, 5                           ; stride 0x120
0x02F4FD2E  add rcx, rbx
0x02F4FD31  mov qword ptr [rcx], rax            ; slot reset; semantics TBD
0x02F4FD34  call 0x02F3A0D4                     ; cleanup; semantics TBD
0x02F4FD39  inc dword ptr [rbx + 0x2D04]        ; head++
0x02F4FD3F  dec dword ptr [rbx + 0x2D00]        ; count--
0x02F4FD45  cmp dword ptr [rbx + 0x2D04], 0x28 ; ring capacity 40
0x02F4FD4E  and dword ptr [rbx + 0x2D04], 0     ; head wrap
\`\`\`

This is a **real ring-queue pop primitive**, not just a historical byte-match candidate. \`root+0x2F88\` = count and \`root+0x2F8C\` = head in this demonstrated call context. The writer addresses fields through a subobject; searching only literal \`0x2F8C\` misses it. **Do not call or hook this routine to force early progress**: it also touches original slot cleanup/virtual-object lifetime.

## Verified direct pop callers (E8 instruction boundaries)

| Caller start RVA | Actual callsite RVA | Initial classification |
|---|---|---|
| \`0x02F39F94\` | \`0x02F39FA9\` | loops on count until queue empty; clear/drain path |
| \`0x0303BB60\` | \`0x0303BBAC\` | conditional pop after other stack/state mutation |
| \`0x030433B0\` | \`0x03043406\` | state-dependent order processing; **completion-like candidate** |
| \`0x03043648\` | \`0x030436B3\` | unit update path and conditional pop |
| \`0x0304433C\` | \`0x030445B1\` | active/next-order virtual checks, potential handoff |

The terms *completion-like*, *unit update* and *handoff* are research classifications, **not verified gameplay semantics**.

## Partial engine graph (actual direct calls, not all transition conditions)

\`\`\`text
0x02DD6D08 (iterates several arrays of UnitRoot pointers)
  -> 0x03043648 (unit update / order processing candidate)
    -> 0x0304433C (active/successor order checking)
      -> 0x02F4FD10 (actual head++ / count-- / 40 wrap)
      -> 0x030433B0 (state-dependent slot processing)
        -> 0x03043424 (slot state/virtual method calls)
        -> 0x02F4FD10 (conditional pop)
    -> 0x02F4FD10 (another conditional pop path)
\`\`\`

The \`0x030433B0\` branch checks \`slot+0x118\`, \`slot+0x38\` after invoking \`0x03043424\`, but field meanings are **not proven**. The larger \`0x0304433C\` function calls several order-vtable methods (including slots \`+0x38\`, \`+0x40\`, \`+0x48\`, \`+0x98\`) and has an internal path calling candidate native MOVE issuer \`0x030323C8\`. This is important: **not every native MOVE issuance is a player Shift click**.

\`0x03030298\` is a separate virtual-check/dispatch path; it calls \`0x03041B28\`, which dispatches through slot virtual entry 0, and does not directly mutate OrderHead. It should not be labeled the generic completion function without more evidence.

## Evidence grades and blocking questions

| Question | State |
|---|---|
| Original native head/count writer and ring pop semantics | **STATIC INSTRUCTION-BACKED** for exact SHA |
| Original queue drain wrapper | **STATIC INSTRUCTION-BACKED** |
| Some update-stage callers and conditional order cleanup | **STATIC CALLGRAPH-BACKED**, semantic labels provisional |
| Exact MOVE completion condition / field semantics | **UNKNOWN** |
| Original MOVE terminal braking and desired speed update | **UNKNOWN** |
| Whether next MOVE retains locomotion state | **UNKNOWN** |
| Native queued MOVE->ATTACK target/activation timing | **UNKNOWN** |
| Game thread, object lifetime, safe inline-patch ABI | **UNKNOWN** |
| Runtime patch authorization | **NO** |

**Next static RE tasks:** inspect \`0x030433B0\` / \`0x03043424\` and active-order VTable dispatch; trace \`0x0304433C\` current-vs-successor identity; follow executing MOVE into speed/braking state; compare queued ATTACK vs normal RMB. Never write raw OrderHead or reintroduce shadow scheduling.

This evidence is specific to the file hash above. Existing 9.0.2 native maps remain historical only. The completed native behavior patch is **not** implemented or validated.
