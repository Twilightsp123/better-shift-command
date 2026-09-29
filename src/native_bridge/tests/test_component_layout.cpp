#include "wh3/component_layout.hpp"
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>

using namespace wh3;
#define CK(x) do { if (!(x)) throw std::runtime_error(#x); } while(false)

namespace {
std::map<std::uintptr_t, std::vector<unsigned char>> mem;

void block(std::uintptr_t base, std::size_t n) { mem[base] = std::vector<unsigned char>(n); }

template<class T>
void put(std::uintptr_t base, std::size_t off, T value) {
    auto& b = mem.at(base);
    CK(off + sizeof(T) <= b.size());
    std::memcpy(b.data() + off, &value, sizeof(T));
}

bool rd(std::uintptr_t addr, void* out, std::size_t n) noexcept {
    for (const auto& kv : mem) {
        const auto base = kv.first;
        const auto& b = kv.second;
        if (addr >= base && addr + n >= addr && addr + n <= base + b.size()) {
            std::memcpy(out, b.data() + (addr - base), n);
            return true;
        }
    }
    return false;
}

struct Fixture {
    std::uintptr_t arr{0x200000};
    std::vector<std::uintptr_t> entities;
    std::vector<std::uintptr_t> components;
};

Fixture setup(std::size_t count, std::size_t entity_off, std::size_t back_off, std::size_t state_off, std::uint32_t state = 1) {
    mem.clear();
    Fixture f;
    block(f.arr, count * sizeof(std::uintptr_t));
    for (std::size_t i = 0; i < count; ++i) {
        const auto e = 0x400000 + i * 0x4000;
        const auto c = 0x800000 + i * 0x4000;
        block(e, 0x400);
        block(c, 0xC00);
        put<std::uintptr_t>(e, entity_off, c);
        put<std::uintptr_t>(c, back_off, e);
        put<std::uint32_t>(c, state_off, state);
        f.entities.push_back(e);
        f.components.push_back(c);
        put<std::uintptr_t>(f.arr, i * sizeof(std::uintptr_t), e);
    }
    return f;
}
}

int main() {
    int pass = 0, fail = 0;
    auto test = [&](const char* name, auto fn) {
        try { fn(); ++pass; std::cout << "PASS " << name << "\n"; }
        catch (const std::exception& e) { ++fail; std::cout << "FAIL " << name << ": " << e.what() << "\n"; }
    };

    test("discovers legacy pair with live legacy state", [] {
        auto f = setup(4, 0x18, 0x4A0, 0x8B0, 1);
        const auto r = scan_component_layout(rd, f.arr, 4);
        CK(r.passed);
        CK(r.pair_candidate_count == 1);
        CK(r.entity_component_offset == 0x18);
        CK(r.component_backref_offset == 0x4A0);
        CK(r.movement_state_offset == 0x8B0);
        CK(r.method == ComponentLayoutMethod::DiscoveredPairLegacyState);
    });

    test("discovers relocated entity/component pair without guessing root equality", [] {
        auto f = setup(4, 0x28, 0x4B8, 0x8B0, 2);
        const auto r = scan_component_layout(rd, f.arr, 4);
        CK(r.passed);
        CK(r.entity_component_offset == 0x28);
        CK(r.component_backref_offset == 0x4B8);
        CK(r.movement_state_offset == 0x8B0);
    });

    test("ambiguous component pairs fail closed", [] {
        auto f = setup(4, 0x18, 0x4A0, 0x8B0, 1);
        for (std::size_t i = 0; i < f.entities.size(); ++i) {
            const auto c2 = 0xC00000 + i * 0x4000;
            block(c2, 0xC00);
            put<std::uintptr_t>(f.entities[i], 0x28, c2);
            put<std::uintptr_t>(c2, 0x4B8, f.entities[i]);
            put<std::uint32_t>(c2, 0x8B0, 1);
        }
        const auto r = scan_component_layout(rd, f.arr, 4);
        CK(!r.passed);
        CK(r.pair_candidate_count == 2);
        CK(std::string(r.failure_reason) == "COMPONENT_LAYOUT_PAIR_AMBIGUOUS");
    });

    test("unique fallback state offset can be discovered", [] {
        auto f = setup(4, 0x28, 0x4B8, 0x8C4, 1);
        for (auto c : f.components) put<std::uint32_t>(c, 0x8B0, 9);
        const auto r = scan_component_layout(rd, f.arr, 4);
        CK(r.passed);
        CK(r.movement_state_offset == 0x8C4);
        CK(r.state_candidate_count == 1);
        CK(r.method == ComponentLayoutMethod::DiscoveredPairDiscoveredState);
    });

    test("zero-filled legacy state slot is not accepted as live evidence", [] {
        auto f = setup(4, 0x28, 0x4B8, 0x8C4, 2);
        for (auto c : f.components) put<std::uint32_t>(c, 0x8B0, 0);
        const auto r = scan_component_layout(rd, f.arr, 4);
        CK(r.passed);
        CK(r.movement_state_offset == 0x8C4);
        CK(r.state_candidate_count == 1);
        CK(r.method == ComponentLayoutMethod::DiscoveredPairDiscoveredState);
    });

    test("ambiguous fallback state offsets fail closed", [] {
        auto f = setup(4, 0x28, 0x4B8, 0x8C4, 1);
        for (auto c : f.components) {
            put<std::uint32_t>(c, 0x8B0, 9);
            put<std::uint32_t>(c, 0x900, 2);
        }
        const auto r = scan_component_layout(rd, f.arr, 4);
        CK(!r.passed);
        CK(r.state_candidate_count == 2);
        CK(std::string(r.failure_reason) == "MOVEMENT_STATE_CANDIDATE_AMBIGUOUS");
    });

    test("fewer than three entities does not establish layout", [] {
        auto f = setup(2, 0x18, 0x4A0, 0x8B0, 1);
        const auto r = scan_component_layout(rd, f.arr, 2);
        CK(!r.passed);
        CK(std::string(r.failure_reason) == "COMPONENT_LAYOUT_NEEDS_3_ENTITIES");
    });

    std::cout << "SUMMARY pass=" << pass << " fail=" << fail << "\n";
    return fail ? 1 : 0;
}
