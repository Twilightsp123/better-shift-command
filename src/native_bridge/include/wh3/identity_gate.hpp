#pragma once
// New source component, NOT the ABI of the installed 0.1.1 DLL.
// Host adapter must supply proven stream/view lifetimes and serialized native entries.
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace wh3 {
using Id = std::uint32_t;
enum class Kind { Move, Attack, Halt };
enum class Source { Unknown, OurController };
enum class Status {
    Accepted, AcceptedNoSlot, NativeRejected, RejectedStale, RejectedDuplicate,
    RejectedCancelled, RejectedUnbound, RejectedMetadata, RejectedUnitLifetime,
    RejectedDisabled, RejectedFault, Indeterminate
};
enum class Error {
    Ok, Inactive, Invalid, Missing, Capacity, CounterExhausted, Duplicate,
    BindingMismatch, ThreadScope, Reentrant, JournalGap, NativeException,
    NativeOutcomeInvalid
};
const char* name(Kind) noexcept;
const char* name(Source) noexcept;
const char* name(Status) noexcept;
const char* name(Error) noexcept;

struct Unit {
    Id uid = 0;
    Id lifetime = 0; // Bridge-issued incarnation; NOT inferred from root address equality.
    bool operator==(const Unit& b) const noexcept { return uid==b.uid && lifetime==b.lifetime; }
    bool operator!=(const Unit& b) const noexcept { return !(*this==b); }
};
struct Snapshot { Unit unit; Id revision=0; };
struct Stream { Id epoch=0, generation=0; };
struct View { Id epoch=0, id=0; };
struct Issue { Id epoch=0, id=0; };
struct PacketKey {
    Id epoch=0, generation=0, start=0, length=0;
    bool operator==(const PacketKey& b) const noexcept {
        return epoch==b.epoch && generation==b.generation && start==b.start && length==b.length;
    }
    bool operator<(const PacketKey& b) const noexcept;
};
// Diagnostic metadata only. Never used in identity matching or queued decisions.
// Captured at native order entry, NOT at mouse-button message generation.
struct InputSnapshot {
    bool sampled=false,foreground=false,shift=false,left_shift=false,right_shift=false,ctrl=false,alt=false;
    std::uint64_t tick_ms=0;
    std::uint32_t thread_id=0;
};
struct Order {
    Unit recipient;
    Kind kind=Kind::Move;
    std::optional<bool> queued;
    std::optional<float> x,y,z;
    std::optional<Id> target_uid;
    std::optional<std::uint64_t> target_root; // opaque; never a float/Lua number
    std::optional<std::uint8_t> raw70,raw71,raw72,raw78;
    std::optional<Id> halt_flags;
    InputSnapshot input{};
};
struct NativeOutcome {
    bool accepted=false;
    std::optional<Id> engine_seq; // 0 is valid; missing is not 0.
};
struct Event {
    Id epoch=0, serial=0, command_id=0, script_issue_id=0, revision=0;
    Source source=Source::Unknown;
    Status status=Status::NativeRejected;
    Order order;
    std::optional<Id> engine_seq;
    std::optional<Id> batch_index,batch_total;
};
struct Page {
    std::vector<Event> events;
    Id epoch=0, next_after=0, newest=0, oldest=0;
    std::uint64_t dropped=0;
    bool gap=false;
    Error error=Error::Ok;
};
struct DispatchResult {
    Status status=Status::RejectedUnbound;
    bool native_called=false;
    Id serial=0;
    std::optional<NativeOutcome> native_outcome; // preserved even if bookkeeping faults
};
struct ExternalResult {
    NativeOutcome native_outcome;
    Error observer_error=Error::Ok;
    Id serial=0;
};
template<class T> struct Result {
    T value{};
    Error error=Error::Ok;
    explicit operator bool() const noexcept { return error==Error::Ok; }
};
struct Limits {
    std::size_t units=4096, streams=64, views=256, issues=4096, packets=4096;
    std::size_t journal=4096, recipients=128;
    Id max_counter=UINT32_MAX; // lower values exist for deterministic overflow tests
};

class IdentityGate {
public:
    explicit IdentityGate(Limits limits = {});
    ~IdentityGate();
    IdentityGate(const IdentityGate&)=delete;
    IdentityGate& operator=(const IdentityGate&)=delete;
    // Epoch and identity counters never wrap or reset within this object.
    Result<Id> begin_battle();
    Error end_battle(Id epoch);
    Result<Unit> register_unit(Id uid, std::uint64_t opaque_root);
    Error retire_unit(Unit);
    Result<Snapshot> snapshot(Unit) const;
    Error fault() const;

    // Only an integration adapter may arm this after independently proving ALL
    // native boundaries. Calling this function is not evidence of that proof.
    // Defaults false; this package ships NO adapter that calls it in WH3.
    Error set_issue_enabled(bool);
    bool issue_enabled() const;

    // Native buffer constructor/reset/swap events, not address/offset heuristics.
    Result<Stream> open_stream(std::uint64_t producer_storage, Id byte_capacity);
    Error retire_stream(Stream);
    // Explicit copy/view mapping: local_start + d -> stream_start + d.
    Result<View> bind_view(Stream, std::uint64_t consumer_storage,
                           Id local_start, Id stream_start, Id length);
    Error retire_view(View);
    Result<PacketKey> resolve(View, Id local_start, Id length) const;

    Result<Issue> make_issue(Kind, bool queued, const std::vector<Snapshot>&);
    Error cancel_issue(Issue);

    class ProducerScope {
    public:
        ProducerScope(const ProducerScope&)=delete;
        ProducerScope& operator=(const ProducerScope&)=delete;
        ProducerScope(ProducerScope&&)=delete;
        ~ProducerScope();
    private:
        friend class IdentityGate;
        ProducerScope(IdentityGate&, Issue, bool external);
        IdentityGate* owner_;
        std::size_t depth_;
    };
    // C++17 guaranteed elision; scope stays on its creating thread.
    ProducerScope own_scope(Issue);
    ProducerScope external_scope();

    // Must succeed before the adapter publishes an OWNED packet to the engine.
    // One issue -> one packet -> exact recipient fanout; failure is NOT permission
    // to publish an untracked owned packet. No eviction/timeout/rebinding.
    Result<PacketKey> commit_packet(Stream, Id start, Id length, Kind, bool queued,
                                   const std::vector<Unit>& recipients);

    Result<Source> packet_source(const PacketKey&) const;

    // OWNED branch ONLY; external native paths must continue unchanged and call
    // observe_external AFTER original execution, never use a rejection here to
    // suppress external commands.
    // Run ONLY at a verified safe per-unit entry BEFORE native queue side effects.
    // Original callback is synchronous. All relevant entry paths must share the
    // same host serialization; the internal mutex alone cannot impose that on WH3.
    DispatchResult dispatch_owned(const PacketKey&, const Order&,
                            const std::function<NativeOutcome()>& original);

    // Observer notification AFTER an unbound/external original call. Does not
    // suppress or issue anything. A reentrant notification latches a fault;
    // an already-called native operation is then INDETERMINATE, not rolled back.
    Result<Event> observe_external(const Order&, NativeOutcome);
    // Already-executed EXTERNAL native input whose optional payload could not
    // be read. Records observed fields and advances accepted revision without
    // latching a permanent gate fault. BridgeHost separately reports the lossy
    // capture so the Lua consumer yields/resynchronizes before issuing again.
    // Never use this for owned/controller commands.
    Result<Event> observe_external_partial(const Order&, NativeOutcome);
    // Preferred external entry wrapper: includes original mutation in the same
    // serialization region. Never rejects native input; even inactive/faulted
    // observation does not prevent original execution. Native exceptions rethrow.
    ExternalResult dispatch_external(const Order&,
                                     const std::function<NativeOutcome()>& original);

    Result<Page> read(Id epoch, Id after, std::size_t count) const;
    // Ack only a contiguously delivered cursor AFTER the consumer stores it.
    Error acknowledge(Id epoch, Id through);
    // Loss acknowledgement is not a reset; own issuing stays disabled until a
    // new battle. 1428 replay keeps native source UNKNOWN.
private:
    struct Impl;
    std::unique_ptr<Impl> p_;
};
// Strict codec for future Lua string bindings; never accepts numbers/hex/whitespace.
Result<Id> parse_id(const std::string& text);
std::string format_id(Id value);
} // namespace wh3
