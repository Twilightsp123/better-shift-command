#!/usr/bin/env python3
"""H8 static obligations: classify actual Native/Lua ownership rather than assert restoration."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
ctl=(root/"source/better_shift_command.lua").read_text(encoding="utf-8")
templ=(root/"src/better_shift_command_selfcontained.template.lua").read_text(encoding="utf-8")
bridge=(root/"src/native_bridge/src/bridge_host.cpp").read_text(encoding="utf-8")
platform=(root/"src/native_bridge/src/platform_windows.cpp").read_text(encoding="utf-8")
assert "native_current_move_witness_ms=e.provider==\"V3\" and now or nil" in ctl
assert "ATTACK_NATIVE_MOVE_STALL_TERMINAL" in ctl and "ATTACK_NATIVE_MOVE_STALL_TERMINAL" in templ
assert "ATTACK_NATIVE_MOVE_STALL_TERMINAL" in (root/"source/t2b_attack_policy_v2.lua").read_text()
assert 'local issue_args={a.type,false,st.uid,rev,function()' in ctl
start=bridge.index("std::uint32_t BridgeHost::order(")
end=bridge.index("void* BridgeHost::allocate(",start)
section=bridge[start:end]
assert section.index("original();") < section.index("gate_.observe_external(o,n)") 
assert "attempted=true;g_observer_stopped=false" in platform
assert "if(attempted){" in platform
assert "MINHOOK_CREATE_FAILED" in platform
assert (root/"source/better_shift_command.lua").read_bytes()==(root/"src/better_shift_command.lua").read_bytes()
print("PASS H8 static source wiring: bounded stationary Native MOVE lane, mirrors, exact witness")
print("OPEN P2: Native original command executes before Lua observation; nonqueued rollback replaces native tail")
print("OPEN P0: MinHook first-create failure remains process-one-shot; no safe recovery proven")
