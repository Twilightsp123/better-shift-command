#include "wh3/identity_gate.hpp"
#include <algorithm>
#include <cmath>
#include <deque>
#include <map>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <tuple>
#include <utility>

namespace wh3 {
namespace {
struct Frame { IdentityGate* owner; Issue issue; bool external; std::thread::id thread; };
thread_local std::vector<Frame> scopes;
bool in_range(Id start, Id length, Id base, Id extent) noexcept {
    return length>0 && start>=base && std::uint64_t(start)+length<=std::uint64_t(base)+extent;
}
bool valid_order(const Order& o) noexcept {
    auto finite=[](std::optional<float> f){return !f || std::isfinite(*f);};
    if(!finite(o.x)||!finite(o.y)||!finite(o.z)) return false;
    switch(o.kind) {
    case Kind::Move:return o.queued.has_value()&&o.x&&o.y&&o.z;
    case Kind::Attack:return o.queued.has_value()&&o.target_uid&&o.target_root&&*o.target_root!=0;
    case Kind::Halt:return true; // no seq/queued fabricated
    }
    return false;
}
bool valid_outcome(Kind kind, NativeOutcome n) noexcept {
    return (n.accepted || !n.engine_seq) && (kind!=Kind::Halt || !n.engine_seq);
}
Status accepted_status(NativeOutcome n, Kind kind) noexcept {
    if(!n.accepted) return Status::NativeRejected;
    return n.engine_seq||kind==Kind::Halt ? Status::Accepted : Status::AcceptedNoSlot;
}
}
bool PacketKey::operator<(const PacketKey& b) const noexcept {
    return std::tie(epoch,generation,start,length)<std::tie(b.epoch,b.generation,b.start,b.length);
}
#define WH3_NAMES(F,T,...) const char* name(T v) noexcept {switch(v){ __VA_ARGS__ }return "INVALID";}
#define N(T,V,S) case T::V: return S;
WH3_NAMES(_,Kind,N(Kind,Move,"MOVE") N(Kind,Attack,"ATTACK") N(Kind,Halt,"HALT"))
WH3_NAMES(_,Source,N(Source,Unknown,"UNKNOWN") N(Source,OurController,"OUR_CONTROLLER"))
WH3_NAMES(_,Status,
 N(Status,Accepted,"ACCEPTED") N(Status,AcceptedNoSlot,"ACCEPTED_NO_SLOT")
 N(Status,NativeRejected,"NATIVE_REJECTED") N(Status,RejectedStale,"REJECTED_STALE")
 N(Status,RejectedDuplicate,"REJECTED_DUPLICATE") N(Status,RejectedCancelled,"REJECTED_CANCELLED")
 N(Status,RejectedUnbound,"REJECTED_UNBOUND") N(Status,RejectedMetadata,"REJECTED_METADATA")
 N(Status,RejectedUnitLifetime,"REJECTED_UNIT_LIFETIME") N(Status,RejectedDisabled,"REJECTED_DISABLED")
 N(Status,RejectedFault,"REJECTED_FAULT") N(Status,Indeterminate,"INDETERMINATE"))
WH3_NAMES(_,Error,N(Error,Ok,"OK") N(Error,Inactive,"INACTIVE") N(Error,Invalid,"INVALID")
 N(Error,Missing,"MISSING") N(Error,Capacity,"CAPACITY") N(Error,CounterExhausted,"COUNTER_EXHAUSTED")
 N(Error,Duplicate,"DUPLICATE") N(Error,BindingMismatch,"BINDING_MISMATCH") N(Error,ThreadScope,"THREAD_SCOPE")
 N(Error,Reentrant,"REENTRANT") N(Error,JournalGap,"JOURNAL_GAP") N(Error,NativeException,"NATIVE_EXCEPTION")
 N(Error,NativeOutcomeInvalid,"NATIVE_OUTCOME_INVALID"))
#undef N
#undef WH3_NAMES

struct IdentityGate::Impl {
    explicit Impl(Limits l):limits(l), journal(l.journal) {
        if(!l.journal||!l.units||!l.streams||!l.views||!l.issues||!l.packets||!l.recipients||l.recipients>UINT32_MAX||!l.max_counter)
            throw std::invalid_argument("all limits must be positive");
    }
    mutable std::recursive_mutex mu;
    Limits limits;
    bool active=false, enabled=false, native_busy=false;
    Error fault=Error::Ok;
    Id acknowledged=0, delivered=0;
    Id epoch=0, unit_counter=0, stream_counter=0, view_counter=0, issue_counter=0, command_counter=0, serial=0;
    struct U { Unit key; std::uint64_t root; Id revision=0; };
    struct S { Stream key; std::uint64_t storage; Id capacity; };
    struct V { View key; Stream stream; std::uint64_t storage; Id local,begin,length; };
    struct I { Issue key; Kind kind; bool queued,cancelled=false,bound=false; std::vector<Snapshot> recipients; };
    struct P { PacketKey key; Id command,issue; Source source; Kind kind; bool queued;
               std::vector<Snapshot> recipients; std::vector<bool> used; };
    std::map<Id,U> units;
    std::map<Id,S> streams;
    std::map<Id,V> views;
    std::map<Id,I> issues;
    std::map<PacketKey,P> packets;
    std::vector<Event> journal; // fully allocated before any native call
    std::size_t first=0,size=0;
    std::uint64_t dropped=0;
    void latch(Error e) { if(fault==Error::Ok) fault=e; enabled=false; }
    bool mutating_allowed() { if(native_busy){latch(Error::Reentrant);return false;} return true; }
    std::optional<Id> next(Id& counter) {
        if(counter==limits.max_counter){latch(Error::CounterExhausted);return {};}
        return ++counter;
    }
    U* unit(Unit u) { auto i=units.find(u.uid); return i!=units.end()&&i->second.key==u?&i->second:nullptr; }
    const U* unit(Unit u) const { auto i=units.find(u.uid); return i!=units.end()&&i->second.key==u?&i->second:nullptr; }
    // Event assignment only contains value types and optionals: no allocation.
    Id publish(Event& e) {
        auto n=next(serial); if(!n) return 0; e.epoch=epoch;e.serial=*n;
        if(size==journal.size()) {
            if(journal[first].serial>acknowledged)latch(Error::JournalGap);
            first=(first+1)%journal.size();--size;++dropped;
        }
        journal[(first+size)%journal.size()]=e;++size;return *n;
    }
    bool room_for_owned_commit(U& u) {
        if(serial>=limits.max_counter||u.revision>=limits.max_counter){latch(Error::CounterExhausted);return false;}
        // Do not invoke a native command which is known to overwrite unread
        // bounded journal storage; producer must size/drain/retire appropriately.
        if(size==journal.size()&&journal[first].serial>acknowledged){latch(Error::JournalGap);return false;} return true;
    }
};
IdentityGate::IdentityGate(Limits l):p_(new Impl(l)){}
IdentityGate::~IdentityGate()=default;
Result<Id> IdentityGate::begin_battle() {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return {{},Error::Reentrant};
    if(p.active)return {{},Error::Invalid};
    auto e=p.next(p.epoch);if(!e)return {{},Error::CounterExhausted};
    p.units.clear();p.streams.clear();p.views.clear();p.issues.clear();p.packets.clear();
    p.first=p.size=0;p.dropped=0;p.serial=0;p.acknowledged=0;p.delivered=0;p.fault=Error::Ok;p.enabled=false;p.active=true;
    return {*e,Error::Ok};
}
Error IdentityGate::end_battle(Id e) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return Error::Reentrant;
    if(!p.active||p.epoch!=e)return Error::Inactive;
    p.active=false;p.enabled=false;p.streams.clear();p.views.clear();p.issues.clear();p.packets.clear();return Error::Ok;
}
Result<Unit> IdentityGate::register_unit(Id uid,std::uint64_t root) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return {{},Error::Reentrant};
    if(!p.active)return {{},Error::Inactive};
    if(!root)return {{},Error::Invalid};
    if(p.units.count(uid))return {{},Error::Duplicate};
    if(p.units.size()>=p.limits.units){p.latch(Error::Capacity);return {{},Error::Capacity};}
    auto n=p.next(p.unit_counter);if(!n)return {{},Error::CounterExhausted};
    Unit u{uid,*n};p.units.emplace(uid,Impl::U{u,root,0});return {u,Error::Ok};
}
Error IdentityGate::retire_unit(Unit u) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return Error::Reentrant;
    if(!p.active)return Error::Inactive;
    if(!p.unit(u))return Error::Missing;
    p.units.erase(u.uid);return Error::Ok;
}
Result<Snapshot> IdentityGate::snapshot(Unit u) const {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.active)return {{},Error::Inactive};
    auto v=p.unit(u);if(!v)return {{},Error::Missing};return {{u,v->revision},Error::Ok};
}
Error IdentityGate::fault() const {std::lock_guard<std::recursive_mutex> g(p_->mu);return p_->fault;}
Error IdentityGate::set_issue_enabled(bool v) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return Error::Reentrant;
    if(!p.active)return Error::Inactive;
    if(v&&p.fault!=Error::Ok)return p.fault;
    p.enabled=v;return Error::Ok;
}
bool IdentityGate::issue_enabled() const {std::lock_guard<std::recursive_mutex> g(p_->mu);return p_->enabled;}
Result<Stream> IdentityGate::open_stream(std::uint64_t storage,Id capacity) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return {{},Error::Reentrant};
    if(!p.active)return {{},Error::Inactive};
    if(!storage||!capacity)return {{},Error::Invalid};
    if(p.streams.size()>=p.limits.streams){p.latch(Error::Capacity);return {{},Error::Capacity};}
    auto n=p.next(p.stream_counter);if(!n)return {{},Error::CounterExhausted};
    Stream s{p.epoch,*n};p.streams.emplace(*n,Impl::S{s,storage,capacity});return {s,Error::Ok};
}
Error IdentityGate::retire_stream(Stream s) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return Error::Reentrant;
    if(!p.active||s.epoch!=p.epoch)return Error::Inactive;
    if(!p.streams.erase(s.generation))return Error::Missing;
    for(auto i=p.views.begin();i!=p.views.end();) {if(i->second.stream.generation==s.generation)i=p.views.erase(i);else ++i;}
    for(auto i=p.packets.begin();i!=p.packets.end();) {
        if(i->first.generation==s.generation) {
            if(i->second.issue)p.issues.erase(i->second.issue);
            i=p.packets.erase(i);
        }else ++i;
    }return Error::Ok;
}
Result<View> IdentityGate::bind_view(Stream s,std::uint64_t storage,Id local,Id begin,Id length) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return {{},Error::Reentrant};
    if(!p.active||s.epoch!=p.epoch)return {{},Error::Inactive};
    auto i=p.streams.find(s.generation);if(i==p.streams.end())return {{},Error::Missing};
    if(!storage||!in_range(begin,length,0,i->second.capacity)||std::uint64_t(local)+length>std::uint64_t(UINT32_MAX)+1)return {{},Error::Invalid};
    if(p.views.size()>=p.limits.views){p.latch(Error::Capacity);return {{},Error::Capacity};}
    auto n=p.next(p.view_counter);if(!n)return {{},Error::CounterExhausted};
    View v{p.epoch,*n};p.views.emplace(*n,Impl::V{v,s,storage,local,begin,length});return {v,Error::Ok};
}
Error IdentityGate::retire_view(View v) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return Error::Reentrant;
    if(!p.active||v.epoch!=p.epoch)return Error::Inactive;
    return p.views.erase(v.id)?Error::Ok:Error::Missing;
}
Result<PacketKey> IdentityGate::resolve(View v,Id local,Id length) const {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.active||v.epoch!=p.epoch)return {{},Error::Inactive};
    auto i=p.views.find(v.id);if(i==p.views.end())return {{},Error::Missing};
    const auto& x=i->second;if(!in_range(local,length,x.local,x.length))return {{},Error::Invalid};
    PacketKey k{p.epoch,x.stream.generation,static_cast<Id>(std::uint64_t(x.begin)+local-x.local),length};
    if(!p.packets.count(k))return {{},Error::Missing};
    return {k,Error::Ok};
}
Result<Issue> IdentityGate::make_issue(Kind kind,bool queued,const std::vector<Snapshot>& rs) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return {{},Error::Reentrant};
    if(!p.active)return {{},Error::Inactive};
    if(!p.enabled)return {{},p.fault==Error::Ok?Error::Invalid:p.fault};
    if(rs.empty()||rs.size()>p.limits.recipients||kind==Kind::Halt)return {{},Error::Invalid};
    for(std::size_t i=0;i<rs.size();++i) {
        auto u=p.unit(rs[i].unit);if(!u||u->revision!=rs[i].revision)return {{},Error::BindingMismatch};
        for(std::size_t j=0;j<i;++j)if(rs[i].unit==rs[j].unit)return {{},Error::Duplicate};
    }
    if(p.issues.size()>=p.limits.issues){p.latch(Error::Capacity);return {{},Error::Capacity};}
    auto n=p.next(p.issue_counter);if(!n)return {{},Error::CounterExhausted};
    Issue k{p.epoch,*n};p.issues.emplace(*n,Impl::I{k,kind,queued,false,false,rs});return {k,Error::Ok};
}
Error IdentityGate::cancel_issue(Issue k) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return Error::Reentrant;
    if(!p.active||k.epoch!=p.epoch)return Error::Inactive;
    auto i=p.issues.find(k.id);if(i==p.issues.end())return Error::Missing;i->second.cancelled=true;return Error::Ok;
}
IdentityGate::ProducerScope::ProducerScope(IdentityGate& o,Issue k,bool external):owner_(&o),depth_(scopes.size()) {
    auto& p=*o.p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.active||(!external&&(k.epoch!=p.epoch||!p.issues.count(k.id))))throw std::invalid_argument("invalid producer scope");
    scopes.push_back({&o,k,external,std::this_thread::get_id()});
}
IdentityGate::ProducerScope::~ProducerScope() {
    if(scopes.size()!=depth_+1||scopes.back().owner!=owner_||scopes.back().thread!=std::this_thread::get_id()) {
        std::lock_guard<std::recursive_mutex> g(owner_->p_->mu);owner_->p_->latch(Error::ThreadScope);return;
    }scopes.pop_back();
}
IdentityGate::ProducerScope IdentityGate::own_scope(Issue k){return ProducerScope(*this,k,false);}
IdentityGate::ProducerScope IdentityGate::external_scope(){return ProducerScope(*this,{},true);}
Result<PacketKey> IdentityGate::commit_packet(Stream s,Id start,Id length,Kind kind,bool queued,const std::vector<Unit>& units) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.mutating_allowed())return {{},Error::Reentrant};
    if(!p.active||s.epoch!=p.epoch)return {{},Error::Inactive};
    auto si=p.streams.find(s.generation);if(si==p.streams.end())return {{},Error::Missing};
    if(!in_range(start,length,0,si->second.capacity)||units.empty()||units.size()>p.limits.recipients)return {{},Error::Invalid};
    // No overlapping identities within one immutable stream generation.
    for(const auto& kv:p.packets)if(kv.first.generation==s.generation&&
        std::uint64_t(start)<std::uint64_t(kv.first.start)+kv.first.length&&
        std::uint64_t(kv.first.start)<std::uint64_t(start)+length){p.latch(Error::BindingMismatch);return {{},Error::Duplicate};}
    Impl::I* issue=nullptr;
    if(!scopes.empty()&&scopes.back().owner==this&&!scopes.back().external) {
        auto k=scopes.back().issue;auto it=p.issues.find(k.id);
        if(k.epoch!=p.epoch||it==p.issues.end()) {p.latch(Error::ThreadScope);return {{},Error::ThreadScope};}
        issue=&it->second;
        if(issue->cancelled||issue->bound||issue->kind!=kind||issue->queued!=queued||issue->recipients.size()!=units.size()) {
            p.latch(Error::BindingMismatch);return {{},Error::BindingMismatch};
        }
    }
    std::vector<Snapshot> recipients;recipients.reserve(units.size());
    for(std::size_t i=0;i<units.size();++i) {
        auto u=p.unit(units[i]);if(!u)return {{},Error::Missing};
        for(std::size_t j=0;j<i;++j)if(units[j]==units[i])return {{},Error::Duplicate};
        if(issue) {
            auto it=std::find_if(issue->recipients.begin(),issue->recipients.end(),[&](Snapshot a){return a.unit==units[i];});
            if(it==issue->recipients.end()){p.latch(Error::BindingMismatch);return {{},Error::BindingMismatch};}
            recipients.push_back(*it);
        } else recipients.push_back({units[i],u->revision});
    }
    if(p.packets.size()>=p.limits.packets){p.latch(Error::Capacity);return {{},Error::Capacity};}
    if(issue&&(!p.enabled||p.fault!=Error::Ok))return {{},p.fault==Error::Ok?Error::Invalid:p.fault};
    auto c=p.next(p.command_counter);if(!c)return {{},Error::CounterExhausted};
    PacketKey k{p.epoch,s.generation,start,length};
    p.packets.emplace(k,Impl::P{k,*c,issue?issue->key.id:0,issue?Source::OurController:Source::Unknown,kind,queued,recipients,std::vector<bool>(units.size(),false)});
    if(issue)issue->bound=true;
    return {k,Error::Ok};
}
DispatchResult IdentityGate::dispatch_owned(const PacketKey& k,const Order& o,const std::function<NativeOutcome()>& original) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.active||k.epoch!=p.epoch)return {Status::RejectedUnbound,false,0,{}};
    if(p.native_busy){p.latch(Error::Reentrant);return {Status::RejectedFault,false,0,{}};}
    auto it=p.packets.find(k);if(it==p.packets.end())return {Status::RejectedUnbound,false,0,{}};
    auto& pkt=it->second;
    if(pkt.source!=Source::OurController)return {Status::RejectedUnbound,false,0,{}};
    Event e;e.command_id=pkt.command;e.script_issue_id=pkt.issue;e.source=pkt.source;e.order=o;
    auto r=std::find_if(pkt.recipients.begin(),pkt.recipients.end(),[&](Snapshot a){return a.unit==o.recipient;});
    auto reject=[&](Status status){e.status=status;return DispatchResult{status,false,p.publish(e),{}};};
    if(r==pkt.recipients.end())return reject(Status::RejectedUnitLifetime);
    const std::size_t n=static_cast<std::size_t>(r-pkt.recipients.begin());
    e.batch_index=static_cast<Id>(n);e.batch_total=static_cast<Id>(pkt.recipients.size());
    auto u=p.unit(o.recipient);if(u)e.revision=u->revision;
    if(pkt.used[n])return reject(Status::RejectedDuplicate);
    pkt.used[n]=true; // attempt consumed even on rejection; never replay a stale call
    if(!u)return reject(Status::RejectedUnitLifetime);
    if(!valid_order(o)||pkt.kind!=o.kind||o.queued!=std::optional<bool>(pkt.queued)||!original)return reject(Status::RejectedMetadata);
    if(pkt.source==Source::OurController) {
        auto ii=p.issues.find(pkt.issue);
        if(ii==p.issues.end()||ii->second.cancelled)return reject(Status::RejectedCancelled);
        if(p.fault!=Error::Ok)return reject(Status::RejectedFault);
        if(!p.enabled)return reject(Status::RejectedDisabled);
        if(u->revision!=r->revision)return reject(Status::RejectedStale);
        if(!p.room_for_owned_commit(*u))return reject(Status::RejectedFault);
    }
    p.native_busy=true;NativeOutcome outcome{};bool threw=false;
    try {outcome=original();}catch(...) {threw=true;p.latch(Error::NativeException);}
    p.native_busy=false;
    // Reentrant external acceptance may have changed revision: keep it, do not
    // claim the already-invoked command was safely rejected or rolled back.
    if(threw||p.fault!=Error::Ok||!valid_outcome(o.kind,outcome)) {
        if(!threw&&p.fault==Error::Ok)p.latch(Error::NativeOutcomeInvalid);
        e.status=Status::Indeterminate;e.revision=u->revision;
        return {e.status,true,p.publish(e),threw?std::optional<NativeOutcome>{}:std::optional<NativeOutcome>{outcome}};
    }
    e.order=o; e.status=accepted_status(outcome,o.kind);e.engine_seq=outcome.engine_seq;
    if(outcome.accepted) {
        auto rev=p.next(u->revision);if(!rev){e.status=Status::Indeterminate;e.engine_seq.reset();}
    }
    e.revision=u->revision;return {e.status,true,p.publish(e),outcome};
}
Result<Event> IdentityGate::observe_external(const Order& o,NativeOutcome n) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.active)return {{},Error::Inactive};
    if(p.native_busy)p.latch(Error::Reentrant);
    auto u=p.unit(o.recipient);if(!u){p.latch(Error::BindingMismatch);return {{},Error::Missing};}
    if(!valid_order(o)||!valid_outcome(o.kind,n)){p.latch(Error::NativeOutcomeInvalid);return {{},Error::NativeOutcomeInvalid};}
    auto c=p.next(p.command_counter);if(!c)return {{},Error::CounterExhausted};
    Event e;e.command_id=*c;e.source=Source::Unknown;e.order=o;e.engine_seq=n.engine_seq;e.status=accepted_status(n,o.kind);
    if(n.accepted&&!p.next(u->revision))return {{},Error::CounterExhausted};
    e.revision=u->revision;if(!p.publish(e))return {{},Error::CounterExhausted};
    return {e,Error::Ok};
}
Result<Event> IdentityGate::observe_external_partial(const Order& o,NativeOutcome n) {
    auto& p=*p_; std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.active)return {{},Error::Inactive};
    // External native input has already executed. Missing optional payload is an
    // observer-quality loss, not an IdentityGate invariant failure. Preserve the
    // accepted revision and publish the partial record so consumers can resync,
    // but do NOT latch a permanent gate fault. Owned-command paths never call
    // this function: BridgeHost escalates any partial capture while owned input
    // is in flight before reaching here.
    auto u=p.unit(o.recipient); if(!u)return {{},Error::Missing};
    if(!valid_outcome(o.kind,n))return {{},Error::NativeOutcomeInvalid};
    auto c=p.next(p.command_counter); if(!c)return {{},Error::CounterExhausted};
    Event e; e.command_id=*c; e.source=Source::Unknown; e.order=o;
    e.engine_seq=n.engine_seq; e.status=accepted_status(n,o.kind);
    if(n.accepted&&!p.next(u->revision))return {{},Error::CounterExhausted};
    e.revision=u->revision; if(!p.publish(e))return {{},Error::CounterExhausted};
    return {e,Error::Ok};
}
ExternalResult IdentityGate::dispatch_external(const Order& o,const std::function<NativeOutcome()>& original) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!original)throw std::invalid_argument("external original is required");
    const bool parent_busy=p.native_busy;
    if(parent_busy)p.latch(Error::Reentrant);
    p.native_busy=true;NativeOutcome outcome;
    try {outcome=original();} catch(...) {
        p.native_busy=parent_busy;p.latch(Error::NativeException);throw;
    }
    p.native_busy=parent_busy;
    auto e=observe_external(o,outcome);
    return {outcome,e.error,e?e.value.serial:0};
}
Result<Page> IdentityGate::read(Id epoch,Id after,std::size_t count) const {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(epoch!=p.epoch||epoch==0)return {{},Error::Inactive};
    if(count==0||count>64||after>p.serial)return {{},Error::Invalid};
    Page out;out.epoch=epoch;out.next_after=after;out.newest=p.serial;out.dropped=p.dropped;
    if(p.size) {
        out.oldest=p.journal[p.first].serial;
        out.gap=std::uint64_t(after)+1<out.oldest;
        for(std::size_t i=0;i<p.size&&out.events.size()<count;++i) {
            const auto& e=p.journal[(p.first+i)%p.journal.size()];
            if(e.serial>after){out.events.push_back(e);out.next_after=e.serial;}
        }
    }
    if(!out.gap&&after<=p.delivered&&out.next_after>p.delivered)p.delivered=out.next_after;
    out.error=out.gap?Error::JournalGap:Error::Ok;return {out,Error::Ok};
}
Result<Source> IdentityGate::packet_source(const PacketKey& k) const {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.active||k.epoch!=p.epoch)return {{},Error::Inactive};
    auto i=p.packets.find(k);if(i==p.packets.end())return {{},Error::Missing};
    return {i->second.source,Error::Ok};
}
Error IdentityGate::acknowledge(Id epoch,Id through) {
    auto& p=*p_;std::lock_guard<std::recursive_mutex> g(p.mu);
    if(!p.active||epoch!=p.epoch)return Error::Inactive;
    if(through<p.acknowledged||through>p.delivered)return Error::Invalid;
    p.acknowledged=through;return Error::Ok;
}
Result<Id> parse_id(const std::string& s) {
    if(s.empty()||s.size()>10||(s.size()>1&&s.front()=='0'))return {{},Error::Invalid};
    std::uint64_t n=0;
    for(char c:s){if(c<'0'||c>'9')return {{},Error::Invalid};n=n*10+static_cast<unsigned>(c-'0');if(n>UINT32_MAX)return {{},Error::Invalid};}
    return {static_cast<Id>(n),Error::Ok};
}
std::string format_id(Id v){return std::to_string(v);}
} // namespace wh3
