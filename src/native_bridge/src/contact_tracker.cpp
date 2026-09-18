#include "wh3/contact_tracker.hpp"
#include <algorithm>
#include <limits>

namespace wh3 {

std::uint64_t ContactTracker::mix(std::uint64_t x) noexcept {
    x ^= x >> 30; x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27; x *= 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}
std::size_t ContactTracker::owner_bucket(std::uintptr_t entity) noexcept {
    return static_cast<std::size_t>(mix(static_cast<std::uint64_t>(entity)>>4))&(owner_capacity-1);
}
std::size_t ContactTracker::unit_bucket(Id uid) noexcept {
    return static_cast<std::size_t>(mix(uid))&(unit_capacity-1);
}
std::size_t ContactTracker::pair_bucket(std::uintptr_t a,std::uintptr_t b) noexcept {
    if(a>b)std::swap(a,b);
    const auto h=mix(static_cast<std::uint64_t>(a)>>4)^mix((static_cast<std::uint64_t>(b)>>4)+0x9e3779b97f4a7c15ULL);
    return static_cast<std::size_t>(h)&(debounce_capacity-1);
}
void ContactTracker::clear() noexcept {
    newest_.store(0,std::memory_order_relaxed);
    next_owner_generation_.store(0,std::memory_order_relaxed);
    for(auto& s:owners_){s.generation.store(0,std::memory_order_relaxed);s.uid.store(0,std::memory_order_relaxed);s.entity.store(0,std::memory_order_relaxed);}
    for(auto& s:units_){s.owner_generation.store(0,std::memory_order_relaxed);s.root.store(0,std::memory_order_relaxed);s.uid.store(0,std::memory_order_relaxed);}
    for(auto& s:debounce_){s.a.store(0,std::memory_order_relaxed);s.b.store(0,std::memory_order_relaxed);s.seq_a.store(0,std::memory_order_relaxed);s.seq_b.store(0,std::memory_order_relaxed);s.active_mask.store(0,std::memory_order_relaxed);s.tick.store(0,std::memory_order_relaxed);}
    for(auto& s:ring_){s.commit.store(0,std::memory_order_relaxed);s.tick_ms.store(0,std::memory_order_relaxed);s.uid_a.store(0,std::memory_order_relaxed);s.uid_b.store(0,std::memory_order_relaxed);s.entity_a.store(0,std::memory_order_relaxed);s.entity_b.store(0,std::memory_order_relaxed);s.seq_a.store(0,std::memory_order_relaxed);s.seq_b.store(0,std::memory_order_relaxed);s.active_mask.store(0,std::memory_order_relaxed);}
}
ContactTracker::UnitSlot* ContactTracker::unit_slot(Id uid,bool create) noexcept {
    if(!uid)return nullptr;
    const auto start=unit_bucket(uid);
    for(std::size_t n=0;n<unit_capacity;++n){
        auto& s=units_[(start+n)&(unit_capacity-1)];
        auto cur=s.uid.load(std::memory_order_acquire);
        if(cur==uid)return &s;
        if(cur==0){
            if(!create)return nullptr;
            Id zero=0;
            if(s.uid.compare_exchange_strong(zero,uid,std::memory_order_acq_rel,std::memory_order_acquire))return &s;
        }
    }
    return nullptr;
}
const ContactTracker::UnitSlot* ContactTracker::unit_slot(Id uid) const noexcept {
    if(!uid)return nullptr;
    const auto start=unit_bucket(uid);
    for(std::size_t n=0;n<unit_capacity;++n){
        const auto& s=units_[(start+n)&(unit_capacity-1)];
        const auto cur=s.uid.load(std::memory_order_acquire);
        if(cur==uid)return &s;
        if(cur==0)return nullptr;
    }
    return nullptr;
}
std::uint64_t ContactTracker::owner_generation(Id uid) const noexcept {
    const auto* s=unit_slot(uid);return s?s->owner_generation.load(std::memory_order_acquire):0;
}
bool ContactTracker::owner_ready(Id uid) const noexcept { return owner_generation(uid)!=0; }
bool ContactTracker::insert_owner(std::uintptr_t entity,Id uid,std::uint64_t generation) noexcept {
    if(!entity||!uid||!generation)return false;
    const auto start=owner_bucket(entity);
    for(std::size_t n=0;n<owner_capacity;++n){
        auto& s=owners_[(start+n)&(owner_capacity-1)];
        auto cur=s.entity.load(std::memory_order_acquire);
        if(cur==entity){
            const auto old_uid=s.uid.load(std::memory_order_acquire);
            const auto old_gen=s.generation.load(std::memory_order_acquire);
            if(old_uid&&old_uid!=uid&&old_gen&&owner_generation(old_uid)==old_gen)return false;
            s.generation.store(0,std::memory_order_release);
            s.uid.store(uid,std::memory_order_release);
            s.generation.store(generation,std::memory_order_release);
            return true;
        }
        if(cur==0){
            std::uintptr_t zero=0;
            if(s.entity.compare_exchange_strong(zero,entity,std::memory_order_acq_rel,std::memory_order_acquire)){
                s.uid.store(uid,std::memory_order_release);
                s.generation.store(generation,std::memory_order_release);
                return true;
            }
        }
    }
    return false;
}
bool ContactTracker::bind_entities(Id uid,const std::vector<std::uintptr_t>& entities) noexcept {
    if(!uid)return false;
    auto* us=unit_slot(uid,true);if(!us)return false;
    // Validate the whole replacement before publishing any new generation. This keeps
    // a failed rebind from partially invalidating the previous authoritative owner map.
    for(std::size_t i=0;i<entities.size();++i){
        const auto entity=entities[i];if(!entity)return false;
        for(std::size_t j=0;j<i;++j)if(entities[j]==entity)return false;
        const auto start=owner_bucket(entity);bool place=false;
        for(std::size_t n=0;n<owner_capacity;++n){
            const auto& slot=owners_[(start+n)&(owner_capacity-1)];
            const auto cur=slot.entity.load(std::memory_order_acquire);
            if(cur==entity){
                const auto old_uid=slot.uid.load(std::memory_order_acquire);
                const auto old_gen=slot.generation.load(std::memory_order_acquire);
                if(old_uid&&old_uid!=uid&&old_gen&&owner_generation(old_uid)==old_gen)return false;
                place=true;break;
            }
            if(cur==0){place=true;break;}
        }
        if(!place)return false;
    }
    const auto generation=next_owner_generation_.fetch_add(1,std::memory_order_acq_rel)+1;
    for(auto entity:entities)if(!insert_owner(entity,uid,generation))return false;
    us->owner_generation.store(generation,std::memory_order_release);
    return true;
}
void ContactTracker::invalidate_entities(Id uid) noexcept {
    auto* s=unit_slot(uid,false);if(s)s->owner_generation.store(0,std::memory_order_release);
}
void ContactTracker::bind_command_root(Id uid,std::uintptr_t root) noexcept {
    auto* s=unit_slot(uid,root!=0);if(s)s->root.store(root,std::memory_order_release);
}
std::uintptr_t ContactTracker::command_root(Id uid) const noexcept {
    const auto* s=unit_slot(uid);return s?s->root.load(std::memory_order_acquire):0;
}
bool ContactTracker::owner(std::uintptr_t entity,ContactOwnerView& out) const noexcept {
    out={};if(!entity)return false;const auto start=owner_bucket(entity);
    for(std::size_t n=0;n<owner_capacity;++n){
        const auto& s=owners_[(start+n)&(owner_capacity-1)];const auto cur=s.entity.load(std::memory_order_acquire);
        if(cur==entity){
            const auto uid=s.uid.load(std::memory_order_acquire);const auto gen=s.generation.load(std::memory_order_acquire);
            if(!uid||!gen||owner_generation(uid)!=gen)return false;
            out.uid=uid;out.command_root=command_root(uid);return true;
        }
        if(cur==0)return false;
    }return false;
}
void ContactTracker::record(std::uintptr_t entity_a,std::uintptr_t entity_b,bool active_a,Id seq_a,bool active_b,Id seq_b,std::uint64_t tick_ms) noexcept {
    if(!entity_a||!entity_b||entity_a==entity_b)return;
    ContactOwnerView oa,ob;if(!owner(entity_a,oa)||!owner(entity_b,ob)||oa.uid==ob.uid)return;
    std::uintptr_t da=entity_a,db=entity_b;Id dsa=seq_a,dsb=seq_b;bool daa=active_a,dab=active_b;
    if(da>db){std::swap(da,db);std::swap(dsa,dsb);std::swap(daa,dab);}
    auto& d=debounce_[pair_bucket(da,db)];
    const auto olda=d.a.load(std::memory_order_acquire),oldb=d.b.load(std::memory_order_acquire);
    const auto oldtick=d.tick.load(std::memory_order_acquire);const auto oldmask=d.active_mask.load(std::memory_order_acquire);
    const auto mask=static_cast<std::uint8_t>((daa?1:0)|(dab?2:0));
    if(olda==da&&oldb==db&&oldmask==mask&&d.seq_a.load(std::memory_order_acquire)==dsa&&d.seq_b.load(std::memory_order_acquire)==dsb&&tick_ms>=oldtick&&tick_ms-oldtick<debounce_ms)return;
    d.a.store(da,std::memory_order_release);d.b.store(db,std::memory_order_release);d.seq_a.store(dsa,std::memory_order_release);d.seq_b.store(dsb,std::memory_order_release);d.active_mask.store(mask,std::memory_order_release);d.tick.store(tick_ms,std::memory_order_release);
    const auto serial=newest_.fetch_add(1,std::memory_order_acq_rel)+1;auto& slot=ring_[static_cast<std::size_t>((serial-1)%ring_capacity)];
    slot.commit.store(0,std::memory_order_release);slot.tick_ms.store(tick_ms,std::memory_order_relaxed);slot.uid_a.store(oa.uid,std::memory_order_relaxed);slot.uid_b.store(ob.uid,std::memory_order_relaxed);slot.entity_a.store(entity_a,std::memory_order_relaxed);slot.entity_b.store(entity_b,std::memory_order_relaxed);slot.seq_a.store(seq_a,std::memory_order_relaxed);slot.seq_b.store(seq_b,std::memory_order_relaxed);slot.active_mask.store(static_cast<std::uint8_t>((active_a?1:0)|(active_b?2:0)),std::memory_order_relaxed);slot.commit.store(serial,std::memory_order_release);
}
ContactPage ContactTracker::read(std::uint64_t after,std::size_t max_count) const {
    ContactPage p;if(max_count<1)max_count=1;if(max_count>512)max_count=512;
    p.newest=newest_.load(std::memory_order_acquire);p.oldest=p.newest>=ring_capacity?p.newest-ring_capacity+1:(p.newest?1:0);
    std::uint64_t start=after+1;if(p.oldest&&start<p.oldest){p.gap=true;p.dropped=p.oldest-start;start=p.oldest;}
    for(std::uint64_t s=start;s<=p.newest&&p.events.size()<max_count;++s){
        const auto& slot=ring_[static_cast<std::size_t>((s-1)%ring_capacity)];
        const auto c1=slot.commit.load(std::memory_order_acquire);if(c1!=s)continue;
        ContactEvent e;e.serial=s;e.tick_ms=slot.tick_ms.load(std::memory_order_relaxed);e.uid_a=slot.uid_a.load(std::memory_order_relaxed);e.uid_b=slot.uid_b.load(std::memory_order_relaxed);e.entity_a=slot.entity_a.load(std::memory_order_relaxed);e.entity_b=slot.entity_b.load(std::memory_order_relaxed);e.active_engine_seq_a=slot.seq_a.load(std::memory_order_relaxed);e.active_engine_seq_b=slot.seq_b.load(std::memory_order_relaxed);const auto mask=slot.active_mask.load(std::memory_order_relaxed);e.active_a=(mask&1)!=0;e.active_b=(mask&2)!=0;
        const auto c2=slot.commit.load(std::memory_order_acquire);if(c2!=s)continue;p.events.push_back(e);p.next_after=s;
    }
    if(p.events.empty())p.next_after=after;return p;
}

} // namespace wh3
