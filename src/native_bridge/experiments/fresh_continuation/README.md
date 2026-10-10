# BSC — RMB-style fresh native MOVE continuation (EXPERIMENT)

**Not a fixed BSC release.** This commits actual native WinX64 patch code, exact
EXE guards, a reversible 5-byte jump, a real x64 stolen-instruction test and
Windows private-process build/tests. DLL does not patch anything by default.

Target: user-owned EXE SHA256
\`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a\`.

## Why this is the RMB-versus-Shift experiment

Native ordinary nonqueued MOVE initializes \`MOVE+0xA0=null\` in its original
constructor \`0x030090E7\`. Native queued MOVE→MOVE can instead reach the special
handoff (only after native eligibility tests in \`0x0304433C\`), where
\`0x0304459D\` increments the prior shared-state refcount and
\`0x030445AB\` calls the next MOVE's +0x48 transfer virtual
(\`0x03040864\`). This copies old state into \`MOVE+0xA0\`.
Native queue pop follows at \`0x030445B1\`; regular processing follows.

The opt-in experimental patch changes just 5 bytes at RVA \`0x0304459D\`:
\`ff4618498d\` → \`e90c000000\` (jmp \`0x030445AE\`).
The old refcount increment and transfer call are **both bypassed**.
The original queue pop and next MOVE task still execute and next MOVE uses
the original engine's fresh initialization route; no second commander, Lua,
OrderHead mutation, synchronized pose/index, or reissued MOVE/ATTACK.

**IMPORTANT:** This does not establish better formation coherence, and it
may regress CA's intended progressive turn / original state reuse.
No user in-game testing is requested or appropriate until Windows private
tests and a vetted geometry/route-identity acceptance plan are completed.

## Guard and rollback

- Exact entire game EXE SHA check (never assume RVA stable across updates)
- 17 original machine bytes verified; only original or matching own-patch state accepted
- No patch during DllMain; explicit C ABI export only
- Other process threads suspended and their RIP checked for the 17-byte
  affected native span; failures abort; memory protection and icache restored
- \`BSC_EnableExperimentalRmbContinuation(1)\` opt-in enables; \`(...0)\`
  restores original bytes. Default: 0. Negative result means strict refusal
- No automatic DLL injection / PACK release. Windows loader integration pending

Build: \`cmake -S . -B build -A x64\` in MSVC environment, then
\`cmake --build build --config Release\` and
\`ctest --test-dir build -C Release --output-on-failure\`.
Native Windows binary and WH3 tests MUST be reported separately.

## Evidence gates

STATIC pinned EXE: previous SHA, 17 original transfer bytes and five
independent native instruction sites verified in offline source.
OFFLINE Linux: real 17-byte x64 code executes original→patched→restored
under a synthetic ABI-compatible stub; no WH3 gameplay physics tested.
WINDOWS: private MSVC job compiles and tries loading the DLL in a separate
non-WH3 process; SHA refusal is the expected success, not gameplay proof.
WH3: NOT RUN, pending explicit user-approved final one-off test.
