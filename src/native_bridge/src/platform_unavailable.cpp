#include "wh3/bridge_host.hpp"
namespace wh3 {
std::uintptr_t platform_image_base() noexcept{return 0x140000000ULL;}
bool platform_write(std::uintptr_t,const void*,std::size_t) noexcept{return false;}
bool platform_entity_alive(std::uintptr_t,bool*) noexcept{return false;}
bool platform_combat_group_query(std::uintptr_t,bool*,std::uintptr_t*) noexcept{return false;}
bool platform_frame_active(const FrameIdentity&) noexcept{return false;}
FrameIdentity platform_caller_frame(void*) noexcept{return {};}
bool platform_read(std::uintptr_t,void*,std::size_t) noexcept{return false;}
void* platform_lua_symbol(const char*) noexcept{return nullptr;}
const char* platform_start_observer(){return "WINDOWS_X64_REQUIRED";}
const char* platform_stop_observer(){return nullptr;}
bool platform_hooks_installed() noexcept{return false;}
bool platform_evidence_build_verified() noexcept{return false;}
const char* platform_evidence_build_id() noexcept{return "UNAVAILABLE";}
std::uint64_t platform_tick_ms() noexcept{return 0;}
const char* platform_last_error() noexcept{return "NON_GAME_HOST";}
std::uintptr_t platform_image_size() noexcept{return 0x0DCC1000;}
bool platform_executable_address(std::uintptr_t) noexcept{return true;}
void platform_reset_diagnostic_gates() noexcept{}
bool platform_component_chain_gate_passed() noexcept{return true;}
bool platform_entity_alive_gate_passed() noexcept{return true;}
DiagnosticGateStatus platform_diagnostic_gate_status() noexcept{
    DiagnosticGateStatus s{};
    s.component_chain_gate = true;
    s.component_gate_root = 0;
    s.entity_component_offset = 0x18;
    s.component_backref_offset = 0x4a0;
    s.movement_state_offset = 0x8b0;
    s.component_layout_method = "LEGACY_EXACT";
    s.alive_deployment_passed = true;
    s.alive_casualty_passed = true;
    s.entity_alive_gate = true;
    s.alive_gate_root = 0;
    s.build_id = "UNAVAILABLE";
    s.bridge_version = kDiagnosticBridgeVersion;
    return s;
}
DiagnosticChainResult platform_probe_component_chain(std::uintptr_t, std::size_t) noexcept{
    DiagnosticChainResult r{};
    r.passed = true;
    r.slot_count = 10;
    r.sampled_count = 10;
    r.entity_component_offset = 0x18;
    r.component_backref_offset = 0x4a0;
    r.movement_state_offset = 0x8b0;
    r.layout_method = "LEGACY_EXACT";
    r.failure_reason = "NONE";
    return r;
}
DiagnosticAliveResult platform_probe_entity_alive(std::uintptr_t, std::uint32_t lua_men_alive) noexcept{
    DiagnosticAliveResult r{};
    r.match = true;
    r.slot_count = 10;
    r.native_alive_count = lua_men_alive;
    r.lua_men_alive = lua_men_alive;
    r.deployment_passed = true;
    r.casualty_passed = true;
    r.gate_passed = true;
    r.phase = "DEPLOYMENT";
    r.failure_reason = "NONE";
    return r;
}
}
