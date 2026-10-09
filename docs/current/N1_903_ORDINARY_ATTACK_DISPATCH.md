# N1 — WH3 9.0.3 original normal ATTACK activation differs from special MOVE transfer

**Exact-file static evidence; not gameplay proof or an executable patch.**
Target user-supplied EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; 9.0.3 label user-supplied.

## Two different native paths exist

The special state-transfer branch in original queue function `0x0304433C` calls current virtual `+0x40`, next `+0x38`, and permitted next `+0x48`; native ATTACK's successor `+0x38` explicitly returns false. This **does not mean native ATTACK cannot execute**.

The queue function's normal continuation calls original order state processor `0x030433B0` at **`0x030445D3`**. It resolves the actual current ring head and calls slot updater `0x03043424` at **`0x030433E3`**. Under original status/initialization guards, the updater dispatches that order object's virtual `+0x08` (work submission) and `+0x10` (completion/status):

```asm
0x0304343A lea rdi,[rcx+0x18]     ; active original order object
0x03043461 mov rax,[rdi]
0x0304346B call qword ptr [rax+0x08]
0x03043477 mov byte ptr [rbx+0x119],1
...
0x0304348B call qword ptr [rax+0x10]
```

As previously established from real ATTACK constructor `0x03008BC0`, ATTACK VTable at **`0x0390AC38`** has `+0x08 -> 0x03025788` and `+0x10 -> 0x03044258`.

The native ATTACK `+0x08` function at **`0x03025788`** is indeed a work-submitter: depending on game-native branches, it allocates auxiliary tasks from `0x02F2FFB0` at `0x030257E4` or `0x0302584B`, initializes them via **`0x02F2C6B0`** or **`0x02F2C534`**, and invokes a constructed task's virtual `+0x08` at `0x03025877`. These are original WH3 task operations, not BSC issuing a substitute ATTACK.

## What is and is not established

- **Proved:** the original engine has a *generic native current-order activation* route, which can dispatch this original ATTACK object once it becomes the current queue head and passes native guards.
- **Proved:** rejection by the special MOVE state-transfer eligibility does **not** imply the attack order is missing, destroyed or unable to activate.
- **Not proved:** at what frame/timing the predecessor MOVE completes; how quickly the next ATTACK's native guards pass; target validity, animation or line-of-sight constraints; whether the unit visibly stops in vanilla.
- **Not proved:** whether a narrow local MOVE handoff patch can safely fix this without altering target or refcount lifetime.

**Do not patch ATTACK VTable +0x38 to true.** Its receiver virtual +0x48 is a no-op and the specialized branch presumes a usable state adopter. Forcing eligibility would be a lifecycle violation.

## Reproducibility

Static local proof verified **10 exact instruction byte guards + 3 ATTACK VTable targets** on the exact SHA-matched PE. This is not runtime behavior evidence. Locally preserved `BSC_N1_903_normal_attack_dispatch.md` and `verify_903_normal_attack_dispatch.py` include further detail and reproducibility; combined archive includes source, tests and disassembly.

## Next hard research question

Trace original pending MOVE task collection emptiness **versus terminal speed/path behavior**, and ATTACK `0x03025788` target/activation rejection rules against non-Shift RMB. Do not add a Lua executor, force native queue-pop, or install a Hook until that causal distinction is proven.