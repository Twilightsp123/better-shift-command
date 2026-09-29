#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

namespace wh3 {

using ComponentLayoutReadFn = bool (*)(std::uintptr_t, void*, std::size_t) noexcept;

enum class ComponentLayoutMethod : unsigned {
    None = 0,
    LegacyExact = 1,
    DiscoveredPairLegacyState = 2,
    DiscoveredPairDiscoveredState = 3
};

struct ComponentLayoutPair {
    std::size_t entity_component_offset{0};
    std::size_t component_backref_offset{0};
};

struct ComponentLayoutScanResult {
    bool passed{false};
    std::size_t entity_component_offset{0};
    std::size_t component_backref_offset{0};
    std::size_t movement_state_offset{0};
    std::size_t pair_candidate_count{0};
    std::size_t state_candidate_count{0};
    std::size_t pair_reported{0};
    std::size_t state_reported{0};
    std::array<ComponentLayoutPair, 8> pairs{};
    std::array<std::size_t, 16> states{};
    ComponentLayoutMethod method{ComponentLayoutMethod::None};
    const char* failure_reason{"NONE"};
};

// Read-only, bounded discovery around a soldier Entity array. It never calls
// engine code. Exactly one Entity->component/backref pair is required. The
// historical movement-state offset is preferred only if it validates live;
// otherwise a narrow unique fallback candidate is required.
ComponentLayoutScanResult scan_component_layout(
    ComponentLayoutReadFn read,
    std::uintptr_t soldier_array,
    std::uint32_t slot_count) noexcept;

const char* component_layout_method_name(ComponentLayoutMethod method) noexcept;

} // namespace wh3
