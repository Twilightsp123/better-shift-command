#pragma once
#include "wh3/identity_gate.hpp"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace wh3 {

struct ContactOwnerView {
    Id uid=0;
    std::uintptr_t command_root=0;
    explicit operator bool() const noexcept { return uid!=0; }
};

struct ContactEvent {
    std::uint64_t serial=0;
    std::uint64_t tick_ms=0;
    Id uid_a=0,uid_b=0;
    std::uintptr_t entity_a=0,entity_b=0;
    bool active_a=false,active_b=false;
    Id active_engine_seq_a=0,active_engine_seq_b=0;
};

struct ContactPage {
    std::vector<ContactEvent> events;
    std::uint64_t next_after=0,newest=0,oldest=0,dropped=0;
    bool gap=false;
};

// Fixed-capacity, allocation-free writer used by the runtime collision hook.
// Binding and reads are low-frequency control-plane operations; contact writes are
// lock-free and never take BridgeHost::mutex_.
class ContactTracker {
public:
    static constexpr std::size_t owner_capacity=32768;
    static constexpr std::size_t unit_capacity=1024;
    static constexpr std::size_t ring_capacity=32768;
    static constexpr std::size_t debounce_capacity=8192;
    static constexpr std::uint64_t debounce_ms=75;

    ContactTracker() noexcept { clear(); }
    void clear() noexcept;
    bool bind_entities(Id uid,const std::vector<std::uintptr_t>& entities) noexcept;
    void invalidate_entities(Id uid) noexcept;
    void bind_command_root(Id uid,std::uintptr_t root) noexcept;
    bool owner(std::uintptr_t entity,ContactOwnerView& out) const noexcept;
    bool owner_ready(Id uid) const noexcept;
    void record(std::uintptr_t entity_a,std::uintptr_t entity_b,
                bool active_a,Id seq_a,bool active_b,Id seq_b,
                std::uint64_t tick_ms) noexcept;
    ContactPage read(std::uint64_t after,std::size_t max_count) const;

private:
    struct OwnerSlot {
        std::atomic<std::uintptr_t> entity{0};
        std::atomic<Id> uid{0};
        std::atomic<std::uint64_t> generation{0};
    };
    struct UnitSlot {
        std::atomic<Id> uid{0};
        std::atomic<std::uintptr_t> root{0};
        std::atomic<std::uint64_t> owner_generation{0};
    };
    struct DebounceSlot {
        std::atomic<std::uintptr_t> a{0},b{0};
        std::atomic<Id> seq_a{0},seq_b{0};
        std::atomic<std::uint8_t> active_mask{0};
        std::atomic<std::uint64_t> tick{0};
    };
    struct EventSlot {
        std::atomic<std::uint64_t> commit{0};
        std::atomic<std::uint64_t> tick_ms{0};
        std::atomic<Id> uid_a{0},uid_b{0};
        std::atomic<std::uintptr_t> entity_a{0},entity_b{0};
        std::atomic<Id> seq_a{0},seq_b{0};
        std::atomic<std::uint8_t> active_mask{0};
    };
    std::array<OwnerSlot,owner_capacity> owners_{};
    std::array<UnitSlot,unit_capacity> units_{};
    std::array<DebounceSlot,debounce_capacity> debounce_{};
    std::array<EventSlot,ring_capacity> ring_{};
    std::atomic<std::uint64_t> newest_{0};
    std::atomic<std::uint64_t> next_owner_generation_{0};

    static std::uint64_t mix(std::uint64_t x) noexcept;
    static std::size_t owner_bucket(std::uintptr_t entity) noexcept;
    static std::size_t unit_bucket(Id uid) noexcept;
    static std::size_t pair_bucket(std::uintptr_t a,std::uintptr_t b) noexcept;
    bool insert_owner(std::uintptr_t entity,Id uid,std::uint64_t generation) noexcept;
    UnitSlot* unit_slot(Id uid,bool create) noexcept;
    const UnitSlot* unit_slot(Id uid) const noexcept;
    std::uint64_t owner_generation(Id uid) const noexcept;
    std::uintptr_t command_root(Id uid) const noexcept;
};

} // namespace wh3
