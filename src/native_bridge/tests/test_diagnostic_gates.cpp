#include "wh3/bridge_host.hpp"
#include <iostream>
#include <vector>
#include <map>
#include <cstring>
#include <cstdint>
#include <stdexcept>
#include <algorithm>

namespace {
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)

std::map<std::uintptr_t, std::vector<unsigned char>> g_mem;
std::map<std::uintptr_t, bool> g_entity_alive;

bool mock_mem_read(std::uintptr_t address, void* out, std::size_t size) noexcept {
    for (const auto& kv : g_mem) {
        const auto base = kv.first;
        const auto& b = kv.second;
        if (address >= base && address + size >= address && address + size <= base + b.size()) {
            std::memcpy(out, b.data() + (address - base), size);
            return true;
        }
    }
    return false;
}

void put_bytes(std::uintptr_t addr, const void* data, std::size_t size) {
    auto it = g_mem.lower_bound(addr);
    if (it != g_mem.end() && it->first <= addr && addr + size <= it->first + it->second.size()) {
        std::memcpy(it->second.data() + (addr - it->first), data, size);
        return;
    }
    auto& vec = g_mem[addr];
    vec.resize(size);
    std::memcpy(vec.data(), data, size);
}

template<class T> void put(std::uintptr_t addr, const T& val) {
    put_bytes(addr, &val, sizeof(T));
}

void setup_mock_unit(std::uintptr_t root, std::uintptr_t arr, std::size_t soldier_count, bool valid_backref = true, std::uint32_t state = 1) {
    put<std::uint32_t>(root + 0x114, static_cast<std::uint32_t>(soldier_count));
    put<std::uintptr_t>(root + 0x118, arr);
    for (std::size_t i = 0; i < soldier_count; ++i) {
        const std::uintptr_t entity = root + 0x1000 + i * 0x100;
        const std::uintptr_t comp = root + 0x5000 + i * 0x100;
        put<std::uintptr_t>(arr + i * 8, entity);
        put<std::uintptr_t>(entity + 0x18, comp);
        put<std::uintptr_t>(comp + 0x4A0, valid_backref ? entity : 0xDEADBEEFULL);
        put<std::uint32_t>(comp + 0x8B0, state);
        g_entity_alive[entity] = true;
    }
}
} // namespace

namespace wh3 {
static std::atomic<bool> g_component_gate{false};
static std::atomic<std::uintptr_t> g_component_gate_root{0};
static std::atomic<bool> g_alive_deployment{false};
static std::atomic<bool> g_alive_casualty{false};
static std::atomic<bool> g_alive_gate{false};
static std::atomic<std::uintptr_t> g_alive_gate_root{0};

std::uintptr_t platform_image_base() noexcept { return 0x140000000ULL; }
std::uintptr_t platform_image_size() noexcept { return 0x0DCC1000; }
bool platform_executable_address(std::uintptr_t) noexcept { return true; }
bool platform_read(std::uintptr_t p, void* out, std::size_t n) noexcept { return mock_mem_read(p, out, n); }
bool platform_write(std::uintptr_t, const void*, std::size_t) noexcept { return false; }
bool platform_combat_group_query(std::uintptr_t, bool*, std::uintptr_t*) noexcept { return false; }
bool platform_frame_active(const FrameIdentity&) noexcept { return false; }
FrameIdentity platform_caller_frame(void*) noexcept { return {}; }
void* platform_lua_symbol(const char*) noexcept { return nullptr; }
const char* platform_start_observer() { return "TEST_HARNESS"; }
bool platform_hooks_installed() noexcept { return true; }
const char* platform_last_error() noexcept { return "NONE"; }
bool platform_evidence_build_verified() noexcept { return true; }
const char* platform_evidence_build_id() noexcept { return "WH3_6C104A63AACC4D86_DIAGNOSTIC_RC7_COMPONENT_LAYOUT_SAFE_STOP"; }
std::uint64_t platform_tick_ms() noexcept { return 1000; }

void platform_reset_diagnostic_gates() noexcept {
    g_component_gate.store(false, std::memory_order_relaxed);
    g_component_gate_root.store(0, std::memory_order_relaxed);
    g_alive_deployment.store(false, std::memory_order_relaxed);
    g_alive_casualty.store(false, std::memory_order_relaxed);
    g_alive_gate.store(false, std::memory_order_relaxed);
    g_alive_gate_root.store(0, std::memory_order_relaxed);
}
static void reset_alive_gate() noexcept {
    g_alive_deployment.store(false, std::memory_order_relaxed);
    g_alive_casualty.store(false, std::memory_order_relaxed);
    g_alive_gate.store(false, std::memory_order_relaxed);
    g_alive_gate_root.store(0, std::memory_order_relaxed);
}

bool platform_component_chain_gate_passed() noexcept {
    return g_component_gate.load(std::memory_order_relaxed);
}

bool platform_entity_alive_gate_passed() noexcept {
    return g_alive_gate.load(std::memory_order_relaxed);
}

DiagnosticGateStatus platform_diagnostic_gate_status() noexcept {
    DiagnosticGateStatus s{};
    s.component_chain_gate = g_component_gate.load(std::memory_order_relaxed);
    s.component_gate_root = g_component_gate_root.load(std::memory_order_relaxed);
    s.alive_deployment_passed = g_alive_deployment.load(std::memory_order_relaxed);
    s.alive_casualty_passed = g_alive_casualty.load(std::memory_order_relaxed);
    s.entity_alive_gate = g_alive_gate.load(std::memory_order_relaxed);
    s.alive_gate_root = g_alive_gate_root.load(std::memory_order_relaxed);
    s.build_id = platform_evidence_build_id();
    s.bridge_version = kDiagnosticBridgeVersion;
    return s;
}

DiagnosticChainResult platform_probe_component_chain(std::uintptr_t root, std::size_t sample_limit) noexcept {
    DiagnosticChainResult r{};
    r.passed = false;
    platform_reset_diagnostic_gates();
    if (!root) { r.failure_reason = "NULL_ROOT"; return r; }
    if (root > UINTPTR_MAX - 0x118) { r.failure_reason = "ROOT_POINTER_OVERFLOW"; return r; }
    std::uint32_t slot_count = 0;
    if (!platform_read(root + 0x114, &slot_count, sizeof(slot_count))) { platform_reset_diagnostic_gates(); r.failure_reason = "COUNT_READ_FAILED"; return r; }
    r.slot_count = slot_count;
    if (slot_count < 1 || slot_count > 300) { platform_reset_diagnostic_gates(); r.failure_reason = "COUNT_OUT_OF_RANGE"; return r; }
    std::uintptr_t arr = 0;
    if (!platform_read(root + 0x118, &arr, sizeof(arr)) || !arr) { platform_reset_diagnostic_gates(); r.failure_reason = "NULL_SOLDIER_ARRAY"; return r; }
    const std::size_t limit = sample_limit > 0 ? sample_limit : static_cast<std::size_t>(slot_count);
    if (limit < slot_count) { platform_reset_diagnostic_gates(); r.failure_reason = "COMPONENT_SAMPLE_INCOMPLETE"; return r; }
    std::size_t sampled = 0;
    for (std::size_t i = 0; i < slot_count; ++i) {
        std::uintptr_t entity = 0;
        if (!platform_read(arr + i * 8, &entity, sizeof(entity))) { platform_reset_diagnostic_gates(); r.failure_reason = "ENTITY_SLOT_READ_FAILED"; return r; }
        if (!entity) { platform_reset_diagnostic_gates(); r.failure_reason = "NULL_ENTITY_IN_CHAIN"; return r; }
        std::uintptr_t comp = 0;
        if (!platform_read(entity + 0x18, &comp, sizeof(comp)) || !comp) { platform_reset_diagnostic_gates(); r.failure_reason = "NULL_MOVEMENT_COMPONENT"; return r; }
        std::uintptr_t backref = 0;
        if (!platform_read(comp + 0x4a0, &backref, sizeof(backref)) || backref != entity) { platform_reset_diagnostic_gates(); r.failure_reason = "MOVEMENT_BACKREF_MISMATCH"; return r; }
        std::uint32_t movement_state = 0xFFFFFFFF;
        if (!platform_read(comp + 0x8b0, &movement_state, sizeof(movement_state)) || movement_state > 2) { platform_reset_diagnostic_gates(); r.failure_reason = "INVALID_MOVEMENT_STATE"; return r; }
        ++sampled;
    }
    r.sampled_count = sampled;
    if (sampled != slot_count) { platform_reset_diagnostic_gates(); r.failure_reason = "COMPONENT_SAMPLE_INCOMPLETE"; return r; }
    r.passed = true;
    r.failure_reason = "NONE";
    g_component_gate_root.store(root, std::memory_order_relaxed);
    g_component_gate.store(true, std::memory_order_release);
    return r;
}


static bool call_entity_alive_virtual_internal(std::uintptr_t entity, bool* alive = nullptr) noexcept {
    auto it = g_entity_alive.find(entity);
    if (it == g_entity_alive.end()) return false;
    if (alive) *alive = it->second;
    return true;
}

bool platform_entity_alive(std::uintptr_t entity, bool* alive) noexcept {
    if (!alive) return false;
    if (!platform_component_chain_gate_passed() || !platform_entity_alive_gate_passed()) {
        *alive = false;
        return false;
    }
    bool val = false;
    if (!call_entity_alive_virtual_internal(entity, &val)) return false;
    *alive = val;
    return true;
}

DiagnosticAliveResult platform_probe_entity_alive(std::uintptr_t root, std::uint32_t lua_men_alive) noexcept {
    DiagnosticAliveResult r{};
    r.match = false;
    r.deployment_passed = g_alive_deployment.load(std::memory_order_relaxed);
    r.casualty_passed = g_alive_casualty.load(std::memory_order_relaxed);
    r.gate_passed = g_alive_gate.load(std::memory_order_relaxed);
    r.phase = "NONE";
    auto fail_alive = [&](const char* reason) -> DiagnosticAliveResult {
        reset_alive_gate();
        r.deployment_passed = false;
        r.casualty_passed = false;
        r.gate_passed = false;
        r.failure_reason = reason;
        return r;
    };
    auto fail_component = [&](const char* reason) -> DiagnosticAliveResult {
        platform_reset_diagnostic_gates();
        r.deployment_passed = false;
        r.casualty_passed = false;
        r.gate_passed = false;
        r.failure_reason = reason;
        return r;
    };
    if (!platform_component_chain_gate_passed()) { r.failure_reason = "COMPONENT_GATE_PREREQUISITE_FAILED"; return r; }
    if (!root) return fail_alive("NULL_ROOT");
    if (root > UINTPTR_MAX - 0x118) return fail_alive("ROOT_POINTER_OVERFLOW");
    const auto component_root = g_component_gate_root.load(std::memory_order_acquire);
    if (!component_root || root != component_root) return fail_alive("COMPONENT_ROOT_MISMATCH");
    std::uint32_t slot_count = 0;
    if (!platform_read(root + 0x114, &slot_count, sizeof(slot_count))) return fail_alive("COUNT_READ_FAILED");
    r.slot_count = slot_count;
    r.lua_men_alive = lua_men_alive;
    if (slot_count < 1 || slot_count > 300) return fail_alive("COUNT_OUT_OF_RANGE");
    if (lua_men_alive > slot_count) return fail_alive("LUA_MEN_EXCEEDS_SLOT_COUNT");
    std::uintptr_t arr = 0;
    if (!platform_read(root + 0x118, &arr, sizeof(arr)) || !arr) return fail_alive("NULL_SOLDIER_ARRAY");
    std::uint32_t native_alive = 0;
    for (std::size_t i = 0; i < slot_count; ++i) {
        std::uintptr_t entity = 0;
        if (!platform_read(arr + i * 8, &entity, sizeof(entity))) return fail_alive("ENTITY_SLOT_READ_FAILED");
        if (!entity) return fail_alive("NULL_ENTITY_SLOT");
        std::uintptr_t comp = 0, backref = 0;
        std::uint32_t movement_state = 0xFFFFFFFF;
        if (!platform_read(entity + 0x18, &comp, sizeof(comp)) || !comp) return fail_component("COMPONENT_CHAIN_CHANGED_NULL_COMPONENT");
        if (!platform_read(comp + 0x4a0, &backref, sizeof(backref)) || backref != entity) return fail_component("COMPONENT_CHAIN_CHANGED_BACKREF");
        if (!platform_read(comp + 0x8b0, &movement_state, sizeof(movement_state)) || movement_state > 2) return fail_component("COMPONENT_CHAIN_CHANGED_STATE");
        bool is_alive = false;
        if (!call_entity_alive_virtual_internal(entity, &is_alive)) return fail_alive("VIRTUAL_CALL_EXCEPTION_OR_INVALID");
        if (is_alive) ++native_alive;
    }
    r.native_alive_count = native_alive;
    r.match = native_alive == lua_men_alive;
    if (lua_men_alive == slot_count) {
        r.phase = "DEPLOYMENT";
        if (!r.match) return fail_alive("DEPLOYMENT_COUNT_MISMATCH");
        g_alive_gate_root.store(root, std::memory_order_relaxed);
        g_alive_deployment.store(true, std::memory_order_relaxed);
        g_alive_casualty.store(false, std::memory_order_relaxed);
        g_alive_gate.store(false, std::memory_order_relaxed);
        r.deployment_passed = true;
        r.casualty_passed = false;
        r.gate_passed = false;
        r.failure_reason = "NONE";
        return r;
    }
    r.phase = "CASUALTY";
    if (!g_alive_deployment.load(std::memory_order_relaxed)) return fail_alive("CASUALTY_BEFORE_DEPLOYMENT");
    if (root != g_alive_gate_root.load(std::memory_order_relaxed)) return fail_alive("ROOT_MISMATCH");
    if (!r.match) return fail_alive("CASUALTY_COUNT_MISMATCH");
    g_alive_casualty.store(true, std::memory_order_relaxed);
    g_alive_gate.store(true, std::memory_order_relaxed);
    r.deployment_passed = true;
    r.casualty_passed = true;
    r.gate_passed = true;
    r.failure_reason = "NONE";
    return r;
}

} // namespace wh3

int main() {
    using namespace wh3;
    int pass = 0, fail = 0;
    auto test = [&](const char* label, auto fn) {
        try {
            fn();
            ++pass;
            std::cout << "PASS " << label << "\n";
        } catch (const std::exception& e) {
            ++fail;
            std::cout << "FAIL " << label << ": " << e.what() << "\n";
        }
    };

    const std::uintptr_t kRootA = 0x100000ULL;
    const std::uintptr_t kArrA  = 0x200000ULL;
    const std::uintptr_t kRootB = 0x300000ULL;
    const std::uintptr_t kArrB  = 0x400000ULL;

    BridgeHost host(platform_read, platform_image_base(), nullptr, nullptr, true, platform_entity_alive, nullptr);

    test("A: new battle initializes with component=false, alive=false", [&] {
        platform_reset_diagnostic_gates();
        auto s = platform_diagnostic_gate_status();
        CK(!s.component_chain_gate);
        CK(s.component_gate_root == 0);
        CK(!s.alive_deployment_passed);
        CK(!s.alive_casualty_passed);
        CK(!s.entity_alive_gate);
        CK(!platform_component_chain_gate_passed());
        CK(!platform_entity_alive_gate_passed());
    });

    test("B: valid component chain passes gate (component=true)", [&] {
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 25, true, 1);
        auto r = platform_probe_component_chain(kRootA, 300);
        CK(r.passed);
        CK(r.slot_count == 25);
        CK(r.sampled_count == 25);
        CK(platform_component_chain_gate_passed());
        CK(platform_diagnostic_gate_status().component_gate_root == kRootA);
    });

    test("C: subsequent bad backref in component chain fails closed (component=false, alive=false)", [&] {
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 25, false, 1);
        auto r = platform_probe_component_chain(kRootA, 300);
        CK(!r.passed);
        CK(!platform_component_chain_gate_passed());
        CK(!platform_entity_alive_gate_passed());
    });

    test("D: alive deployment match only -> deployment=true, casualty=false, alive_gate=false", [&] {
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);

        auto alive_res = platform_probe_entity_alive(kRootA, 20);
        CK(alive_res.match);
        CK(alive_res.deployment_passed);
        CK(!alive_res.casualty_passed);
        CK(!alive_res.gate_passed);
        CK(!platform_entity_alive_gate_passed());
    });

    test("E: casualty probe before deployment fails -> alive_gate=false", [&] {
        platform_reset_diagnostic_gates();
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);

        auto alive_res = platform_probe_entity_alive(kRootA, 18);
        CK(!alive_res.deployment_passed);
        CK(!alive_res.casualty_passed);
        CK(!alive_res.gate_passed);
        CK(std::string(alive_res.failure_reason) == "CASUALTY_BEFORE_DEPLOYMENT");
        CK(!platform_entity_alive_gate_passed());
    });

    test("F: deployment root A, casualty root B -> ROOT_MISMATCH, alive_gate=false", [&] {
        platform_reset_diagnostic_gates();
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        setup_mock_unit(kRootB, kArrB, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);
        CK(platform_probe_entity_alive(kRootA, 20).deployment_passed);

        auto alive_res = platform_probe_entity_alive(kRootB, 18);
        CK(!alive_res.casualty_passed);
        CK(!alive_res.gate_passed);
        CK(std::string(alive_res.failure_reason) == "COMPONENT_ROOT_MISMATCH");
        CK(!platform_entity_alive_gate_passed());
    });

    test("G: same root A deployment match then casualty match -> alive=true", [&] {
        platform_reset_diagnostic_gates();
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);

        auto dep_res = platform_probe_entity_alive(kRootA, 20);
        CK(dep_res.deployment_passed);
        CK(!dep_res.gate_passed);

        const std::uintptr_t e18 = kRootA + 0x1000 + 18 * 0x100;
        const std::uintptr_t e19 = kRootA + 0x1000 + 19 * 0x100;
        g_entity_alive[e18] = false;
        g_entity_alive[e19] = false;

        auto cas_res = platform_probe_entity_alive(kRootA, 18);
        CK(cas_res.match);
        CK(cas_res.deployment_passed);
        CK(cas_res.casualty_passed);
        CK(cas_res.gate_passed);
        CK(platform_entity_alive_gate_passed());
    });

    test("H: native alive != Lua men alive -> alive=false", [&] {
        platform_reset_diagnostic_gates();
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);
        CK(platform_probe_entity_alive(kRootA, 20).deployment_passed);

        auto cas_res = platform_probe_entity_alive(kRootA, 17);
        CK(!cas_res.match);
        CK(!cas_res.gate_passed);
        CK(!platform_entity_alive_gate_passed());
    });

    test("H2: incomplete component sample fails closed", [&] {
        platform_reset_diagnostic_gates();
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 100, true, 1);
        auto r = platform_probe_component_chain(kRootA, 64);
        CK(!r.passed);
        CK(std::string(r.failure_reason) == "COMPONENT_SAMPLE_INCOMPLETE");
        CK(!platform_component_chain_gate_passed());
        CK(!platform_entity_alive_gate_passed());
    });

    test("H3: null entity slot fails alive gate closed", [&] {
        platform_reset_diagnostic_gates();
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);
        CK(platform_probe_entity_alive(kRootA, 20).deployment_passed);
        std::uintptr_t zero = 0;
        put<std::uintptr_t>(kArrA + 19 * 8, zero);
        auto r = platform_probe_entity_alive(kRootA, 19);
        CK(!r.gate_passed);
        CK(std::string(r.failure_reason) == "NULL_ENTITY_SLOT");
        CK(!platform_entity_alive_gate_passed());
    });

    test("H4: probing a new component root revokes previous alive proof and rebinds component identity", [&] {
        platform_reset_diagnostic_gates();
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        setup_mock_unit(kRootB, kArrB, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);
        CK(platform_probe_entity_alive(kRootA, 20).deployment_passed);
        auto s1 = platform_diagnostic_gate_status();
        CK(s1.component_gate_root == kRootA);
        CK(s1.alive_deployment_passed);
        CK(platform_probe_component_chain(kRootB, 300).passed);
        auto s2 = platform_diagnostic_gate_status();
        CK(s2.component_chain_gate);
        CK(s2.component_gate_root == kRootB);
        CK(!s2.alive_deployment_passed);
        CK(!s2.entity_alive_gate);
    });

    test("H5: component chain mutation before casualty revokes both gates before virtual use", [&] {
        platform_reset_diagnostic_gates();
        g_mem.clear(); g_entity_alive.clear();
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);
        CK(platform_probe_entity_alive(kRootA, 20).deployment_passed);
        const std::uintptr_t e0 = kRootA + 0x1000;
        const std::uintptr_t c0 = kRootA + 0x5000;
        put<std::uintptr_t>(c0 + 0x4a0, 0xDEADBEEFULL);
        g_entity_alive[kRootA + 0x1000 + 19 * 0x100] = false;
        auto r = platform_probe_entity_alive(kRootA, 19);
        CK(!r.gate_passed);
        CK(std::string(r.failure_reason) == "COMPONENT_CHAIN_CHANGED_BACKREF");
        CK(!platform_component_chain_gate_passed());
        CK(platform_diagnostic_gate_status().component_gate_root == 0);
        CK(!platform_entity_alive_gate_passed());
        (void)e0;
    });

    test("I: new begin_battle resets all gates to false", [&] {
        auto b = host.begin("SCENARIO_I");
        CK(b);
        auto s = platform_diagnostic_gate_status();
        CK(!s.component_chain_gate);
        CK(!s.entity_alive_gate);
        CK(!platform_component_chain_gate_passed());
        CK(!platform_entity_alive_gate_passed());
    });

    test("J: end_battle resets all gates to false", [&] {
        setup_mock_unit(kRootA, kArrA, 20, true, 1);
        CK(platform_probe_component_chain(kRootA, 300).passed);
        CK(platform_component_chain_gate_passed());

        auto e = host.end(host.status().epoch);
        CK(e == Error::Ok);
        auto s = platform_diagnostic_gate_status();
        CK(!s.component_chain_gate);
        CK(!s.entity_alive_gate);
        CK(!platform_component_chain_gate_passed());
        CK(!platform_entity_alive_gate_passed());
    });

    test("K: physical diagnostic gates do not veto core command arming", [&] {
        platform_reset_diagnostic_gates();
        host.begin("SCENARIO_K");
        const char* err = host.arm(true);
        CK(err != nullptr);
        CK(std::string(err) == "V3_CALIBRATION_NOT_READY");
        host.end(host.status().epoch);
    });

    std::cout << "TOTAL " << pass << " PASS " << fail << " FAIL (Diagnostic Gates Suite)\n";
    return fail ? 1 : 0;
}
