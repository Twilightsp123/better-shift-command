#pragma once
#include "wh3/identity_gate.hpp"
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace wh3 {
using EvidenceReadFn = bool (*)(std::uintptr_t,void*,std::size_t) noexcept;
using EntityAliveFn = bool (*)(std::uintptr_t,bool*) noexcept;
using CombatGroupQueryFn = bool (*)(std::uintptr_t,bool*,std::uintptr_t*) noexcept;

enum class EntityProbeReason {
    None, ContainerHeader, PointerRead, NullEntitySlot, DuplicateEntity,
    AliveQuery, EntityPosition, MovementComponent, MovementBackref,
    MovementState, ContainerChanged
};
const char* name(EntityProbeReason) noexcept;

enum class CombatProbeReason {
    None, ContactCountRead, SquadRead, GroupCountRead, GroupPointerRead, GroupQuery,
    TargetRootRead, TargetUidRead, GroupChanged
};
const char* name(CombatProbeReason) noexcept;

struct ActiveOrderView {
    bool complete=false;
    bool active=false;
    Id engine_seq=0;
    Kind kind=Kind::Move;
    std::uintptr_t target_root=0;
    std::optional<float> dest_x,dest_z;
};

struct EntityIndex {
    bool complete=false;
    EntityProbeReason probe_reason=EntityProbeReason::None;
    Id slot_count=0;
    std::uintptr_t array=0;
    std::vector<std::uintptr_t> entities;
};

struct EntityObservation {
    std::uintptr_t entity=0;
    float x=0,z=0;
    std::uint32_t movement_state=0; // +0x8B0 raw 0/1/2 fact only.
    bool motion_complete=false;
    float vx=0,vz=0;
};

// Evidence V3 raw physical facts. +0x74 is intentionally absent: RE07 proved it
// is an initialization-time collision-envelope tier, not a runtime melee state.
struct EntitySnapshot {
    bool complete=false;
    EntityProbeReason probe_reason=EntityProbeReason::None;
    Id slot_count=0;
    Id live_count=0;
    Id dead_count=0;
    Id movement_idle_count=0;
    Id movement_pathing_count=0;
    Id movement_halted_count=0;
    float median_x=0,median_z=0;
    bool motion_complete=false;
    Id motion_matched_count=0;
    std::uint64_t previous_model_ms=0;
    std::uint64_t model_ms=0;
    float median_vx=0,median_vz=0;
    std::vector<EntityObservation> entities;
};

struct CombatSnapshot {
    bool complete=false;
    CombatProbeReason probe_reason=CombatProbeReason::None;
    Id coarse_contact_count=0;
    Id group_count=0;
    Id active_melee_group_count=0;
    std::vector<std::uintptr_t> active_target_roots;
    std::vector<Id> active_target_uids;
};

class EvidenceProbe {
public:
    explicit EvidenceProbe(EvidenceReadFn read,EntityAliveFn alive=nullptr,CombatGroupQueryFn group_query=nullptr,
        std::uintptr_t image_base=0x140000000ULL):read_(read),alive_(alive),group_query_(group_query),base_(image_base){}
    ActiveOrderView active_order(std::uintptr_t root) const noexcept;
    EntityIndex entity_index(std::uintptr_t root) const;
    EntitySnapshot entity_snapshot(std::uintptr_t root,std::uint64_t model_ms);
    CombatSnapshot combat_snapshot(std::uintptr_t root) const;
    void reset(std::uintptr_t root) noexcept;
    void clear() noexcept;
private:
    struct Pos {std::uintptr_t entity=0;float x=0,z=0;};
    struct Previous {std::uint64_t model_ms=0;std::uintptr_t array=0;Id slot_count=0;std::map<std::uintptr_t,Pos> pos;};
    EvidenceReadFn read_;
    EntityAliveFn alive_;
    CombatGroupQueryFn group_query_;
    std::uintptr_t base_;
    std::map<std::uintptr_t,Previous> previous_;
    bool get(std::uintptr_t,std::size_t,void*,std::size_t) const noexcept;
    static float median(std::vector<float>);
    static std::pair<float,float> robust_center(const std::vector<Pos>&);
    bool stable_entity_array(std::uintptr_t root,Id count,std::uintptr_t array,const std::vector<std::uintptr_t>& ptrs) const;
};
}
