#pragma once
#include "wh3/identity_gate.hpp"
#include <cstdint>
#include <array>
#include <memory>
#include <vector>
#include <utility>

namespace wh3 {
// Addresses are used only within a witnessed memory lifetime. No payload hashes,
// target comparisons or timing windows are used to attribute a packet.
struct TrackedPacket {
    std::uint64_t identity=0;
    Id epoch=0;
    Kind kind=Kind::Move;
    bool queued=false, owned=false, consumed=false, cancelled=false;
    Issue issue{};
    Stream stream{};
    PacketKey key{};
    Unit unit{};
    std::uintptr_t root=0;
    Id expected_revision=0;
    std::optional<std::array<float,3>> move_destination;
    bool attack_target_valid=false;
    std::uintptr_t attack_target_root=0;
    Id attack_target_uid=0;
};
struct PhysicalSpan {
    std::uintptr_t allocation=0, address=0;
    std::uint32_t length=0;
    std::uint32_t packet_offset=0;
    std::uint64_t storage_generation=0;
    std::shared_ptr<TrackedPacket> packet;
};
class PacketTracker {
public:
    explicit PacketTracker(std::size_t limit=4096):limit_(limit) {}
    // Every call denotes a witnessed NEW write/copy lifetime for this interval.
    // Labels are byte-range lineage fragments, not whole-packet-only spans.
    // Overwrites split surviving fragments; copies propagate the exact overlap.
    void invalidate(std::uintptr_t address,std::size_t length);
    void release(std::uintptr_t allocation);
    void clear();
    bool put(std::uintptr_t allocation,std::uintptr_t address,std::uint32_t length,
             const std::shared_ptr<TrackedPacket>& packet);
    bool copy(std::uintptr_t destination_allocation,std::uintptr_t destination,
              std::uintptr_t source,std::uint32_t length);
    // Resolve only when the exact reader interval is covered without gaps or
    // conflicting overlap by one packet lineage from packet byte 0 through N.
    // No payload/content/time/FIFO fallback exists.
    std::shared_ptr<TrackedPacket> resolve(std::uintptr_t payload,std::uintptr_t end,Id epoch) const;
    // Consumer reader invariant proven by 0x141B2479C: (+0x18 + +0x1C) is
    // the absolute packet end offset, and the packet handler starts with the
    // cursor immediately after the seven-byte BCQ header. This resolves the
    // exact physical interval without assuming which of +0x18/+0x1C is the
    // start versus length field.
    std::shared_ptr<TrackedPacket> resolve_reader(std::uintptr_t data,std::uint32_t cursor,
                                                  std::uint32_t end_offset,Id epoch) const;
    // At packet-handler entry the reader has already consumed a generic envelope,
    // so cursor-7 is not authoritative. The primitive reader proves only that
    // field18+field1c is the absolute packet end. Exactly one of the two fields
    // is the packet start offset for the exercised handlers. Try both structural
    // interpretations plus cursor-7; accept only one unique exact-span match.
    std::shared_ptr<TrackedPacket> resolve_reader_bounds(std::uintptr_t data,
        std::uint32_t field18,std::uint32_t field1c,std::uint32_t cursor,Id epoch) const;
    // Diagnostic only: union byte coverage/fragments from any lineage of this epoch.
    std::pair<std::uint32_t,std::uint32_t> coverage(std::uintptr_t start,std::uintptr_t end,Id epoch) const;
    std::size_t size() const noexcept {return spans_.size();}
    bool faulted() const noexcept {return fault_;}
    const std::vector<PhysicalSpan>& spans() const noexcept {return spans_;}
private:
    static bool valid(std::uintptr_t,std::size_t) noexcept;
    std::vector<PhysicalSpan> spans_;
    std::size_t limit_;
    std::uint64_t generation_=0;
    bool fault_=false;
};
}
