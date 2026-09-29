#include "wh3/component_layout.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace wh3 {
namespace {

bool plausible_runtime_pointer(std::uintptr_t p) noexcept {
    return p >= 0x10000ULL && p <= 0x00007FFFFFFFFFFFULL && (p % alignof(void*) == 0);
}

} // namespace

const char* component_layout_method_name(ComponentLayoutMethod method) noexcept {
    switch (method) {
        case ComponentLayoutMethod::LegacyExact: return "LEGACY_EXACT";
        case ComponentLayoutMethod::DiscoveredPairLegacyState: return "DISCOVERED_PAIR_LEGACY_STATE";
        case ComponentLayoutMethod::DiscoveredPairDiscoveredState: return "DISCOVERED_PAIR_DISCOVERED_STATE";
        default: return "NONE";
    }
}

ComponentLayoutScanResult scan_component_layout(
    ComponentLayoutReadFn read,
    std::uintptr_t arr,
    std::uint32_t slot_count) noexcept {
    ComponentLayoutScanResult d{};
    if (!read || !arr || slot_count < 1 || slot_count > 300) {
        d.failure_reason = "COMPONENT_LAYOUT_INVALID_ARGUMENT";
        return d;
    }
    const std::size_t sample_count = std::min<std::size_t>(slot_count, 4);
    if (sample_count < 3) {
        d.failure_reason = "COMPONENT_LAYOUT_NEEDS_3_ENTITIES";
        return d;
    }
    std::array<std::uintptr_t, 4> entities{};
    for (std::size_t i = 0; i < sample_count; ++i) {
        const auto stride = i * sizeof(std::uintptr_t);
        if (arr > UINTPTR_MAX - stride ||
            !read(arr + stride, &entities[i], sizeof(entities[i])) ||
            !plausible_runtime_pointer(entities[i])) {
            d.failure_reason = "COMPONENT_LAYOUT_ENTITY_READ_FAILED";
            return d;
        }
    }

    constexpr std::size_t kEntityScanEnd = 0x200;
    constexpr std::size_t kComponentScanEnd = 0xC00;
    for (std::size_t entity_off = 0; entity_off < kEntityScanEnd; entity_off += sizeof(std::uintptr_t)) {
        std::array<std::uintptr_t, 4> components{};
        bool components_ok = true;
        for (std::size_t i = 0; i < sample_count; ++i) {
            if (entities[i] > UINTPTR_MAX - entity_off ||
                !read(entities[i] + entity_off, &components[i], sizeof(components[i])) ||
                !plausible_runtime_pointer(components[i]) || components[i] == entities[i]) {
                components_ok = false;
                break;
            }
            for (std::size_t j = 0; j < i; ++j) {
                if (components[i] == components[j]) {
                    components_ok = false;
                    break;
                }
            }
            if (!components_ok) break;
        }
        if (!components_ok) continue;

        std::array<unsigned char, kComponentScanEnd> first_component{};
        if (!read(components[0], first_component.data(), first_component.size())) continue;
        for (std::size_t back_off = 0;
             back_off + sizeof(std::uintptr_t) <= first_component.size();
             back_off += sizeof(std::uintptr_t)) {
            std::uintptr_t p = 0;
            std::memcpy(&p, first_component.data() + back_off, sizeof(p));
            if (p != entities[0]) continue;
            bool all = true;
            for (std::size_t i = 1; i < sample_count; ++i) {
                std::uintptr_t back = 0;
                if (components[i] > UINTPTR_MAX - back_off ||
                    !read(components[i] + back_off, &back, sizeof(back)) || back != entities[i]) {
                    all = false;
                    break;
                }
            }
            if (!all) continue;
            if (d.pair_reported < d.pairs.size()) {
                d.pairs[d.pair_reported++] = {entity_off, back_off};
            }
            ++d.pair_candidate_count;
        }
    }

    if (d.pair_candidate_count == 0) {
        d.failure_reason = "COMPONENT_LAYOUT_PAIR_NOT_FOUND";
        return d;
    }
    if (d.pair_candidate_count != 1) {
        d.failure_reason = "COMPONENT_LAYOUT_PAIR_AMBIGUOUS";
        return d;
    }
    d.entity_component_offset = d.pairs[0].entity_component_offset;
    d.component_backref_offset = d.pairs[0].component_backref_offset;

    std::array<std::uintptr_t, 4> components{};
    for (std::size_t i = 0; i < sample_count; ++i) {
        if (!read(entities[i] + d.entity_component_offset, &components[i], sizeof(components[i])) ||
            !plausible_runtime_pointer(components[i])) {
            d.failure_reason = "COMPONENT_LAYOUT_COMPONENT_REREAD_FAILED";
            return d;
        }
    }

    auto state_valid = [&](std::size_t off, bool require_nonzero) noexcept {
        bool any_nonzero = false;
        for (std::size_t i = 0; i < sample_count; ++i) {
            std::uint32_t value = 0xFFFFFFFFU;
            if (components[i] > UINTPTR_MAX - off ||
                !read(components[i] + off, &value, sizeof(value)) || value > 2) {
                return false;
            }
            if (value != 0) any_nonzero = true;
        }
        return !require_nonzero || any_nonzero;
    };

    // A discovered pair does not make the historical state slot trustworthy.
    // Require live non-zero evidence before preferring +0x8B0; otherwise zero-filled
    // padding could masquerade as a valid 0..2 state field.
    if (state_valid(0x8B0, true)) {
        d.movement_state_offset = 0x8B0;
        d.state_candidate_count = 1;
        d.state_reported = 1;
        d.states[0] = 0x8B0;
        d.method = ComponentLayoutMethod::DiscoveredPairLegacyState;
        d.passed = true;
        d.failure_reason = "NONE";
        return d;
    }

    for (std::size_t off = 0x600; off <= 0xB00; off += sizeof(std::uint32_t)) {
        if (!state_valid(off, true)) continue;
        if (d.state_reported < d.states.size()) d.states[d.state_reported++] = off;
        ++d.state_candidate_count;
    }
    if (d.state_candidate_count == 0) {
        d.failure_reason = "MOVEMENT_STATE_CANDIDATE_NOT_FOUND";
        return d;
    }
    if (d.state_candidate_count != 1) {
        d.failure_reason = "MOVEMENT_STATE_CANDIDATE_AMBIGUOUS";
        return d;
    }
    d.movement_state_offset = d.states[0];
    d.method = ComponentLayoutMethod::DiscoveredPairDiscoveredState;
    d.passed = true;
    d.failure_reason = "NONE";
    return d;
}

} // namespace wh3
