# N1 — 9.0.3 unit-root has distinct member collections (not yet soldier typed)

**Date:** 2026-10-10. **Scope:** intra-card soldier turn/arrival asynchrony and crowding, NOT native Shift stopping. **Evidence:** actual user EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, AMD64 image base `0x140000000`; game-version label supplied by user. No DLL, Hook, real WH3 test or gameplay-fix claim.

## 1. Two separate collections on the SAME root

Original instruction block beginning `0x0303D6AD` uses RDI for the same root while preparing distinct container operations:

| RVA | Original instruction | Meaning limited to data structure |
|---|---|---|
| `0x0303D6B3` | `mov ecx,[rdi+0x184]` | count A |
| `0x0303D6C4` | `mov rax,[rdi+0x188]` | pointer array A |
| `0x0303D6CF` | `lea rcx,[rdi+0x180]` | container subobject A |
| `0x0303D73D` | `mov ecx,[rdi+0x114]` | count B |
| `0x0303D74E` | `mov rax,[rdi+0x118]` | pointer array B |
| `0x0303D759` | `lea rcx,[rdi+0x110]` | container subobject B |

Both use original vector helper `0x0132BC08`, on **separate containers**. Former BSC files treated `+0x114/+0x118` as soldiers; that label is still a historical interpretation, not a proof that A or B corresponds to all render models.

## 2. Different consumers and nested child layer

- `0x030421A4` loops through A, reads element `+0x88/+0x90` position-like values plus `+0x704/+0x708` counters, and writes aggregates back to UnitRoot. It **does not** set a verified soldier's next waypoint/facing.
- `0x03043E34` loops B at `0x03043E65/6C`, loads each element at `0x03043E7F`, and conditionally invokes its virtual `+0x440` at `0x03043E99`.
- Within the same source region `0x03043FD2`, a **different** loop iterates A and invokes each member's virtual `+0x58` (`0x03043FE1`). A returned object is read at **`+0xBE4` count and `+0xBE8` pointer array** (`0x03043FF4/ED`), and its children are iterated (`0x03044003`). This is a **three-layer object walk**; target type still unknown.
- Unit updater `0x03043648` on the examined branch calls A's position aggregator `0x030421A4`, then group-coordinate processor `0x0302AE0C`, then native order stage `0x0304433C`, then auxiliary per-unit processing `0x03047628`. The latter traverses further arrays at root `+0x3274/+0x3278`, `+0x3294/+0x3298`, `+0x32B4/+0x32B8` with element virtual `+0x20` calls. **No formation-slot semantics proven.**

## 3. What the previous N1 hypothesis got wrong

It is unjustified to infer independent **per-soldier Shift command queues** simply from reading multiple positions. The unit-native order ring exists, but these arrays may include different grouping/child representations. The new evidence **disproves the implicit shortcut** “member-aggregate loop = model waypoint controller,” not any particular soldier movement architecture.

## 4. Concrete reverse-engineering tasks now justified

1. Resolve actual element vtable/constructor/RTTI for A and B separately; check whether individual elements alias, or represent subsets.
2. Resolve concrete implementations of A element virtual `+0x58` and type of the child-container `+0xBE4/+0xBE8`. Only then search their motion destination/facing writers.
3. Trace a single original queued MOVE unit target through native formation-slot assignment to specific models, per-model target update, steering and turn/arrival condition. Distinguish divergence due to per-model phase vs global group-target geometry vs avoidance.
4. No original braking-distance/OrderHead/state4/geometry flag patch until connected by exact dataflow to the **actual intra-card crowding**. Legacy Lua MOVE→ATTACK regression remains separate.

## 5. Reproducibility

A separately delivered read-only package `BSC_N1_903_member_layers_20261010.zip` contains independent `audit_member_layers.py`, 8 offline tests, SHA-gated JSON evidence, bounded actual LLVM disassembly and SHA256 manifest (no EXE). **23 exact instruction guards + 4 direct original E8 calls PASS, 8/8 local tests PASS**. No real 9.0.3 type labels, behavior, ABI, thread lifetime or candidate Hook is validated. **PATCH AUTHORIZED: FALSE.**

This evidence supersedes the speculative *type interpretation* of earlier N1 formation-entry notes, not their verified opcode bytes.
