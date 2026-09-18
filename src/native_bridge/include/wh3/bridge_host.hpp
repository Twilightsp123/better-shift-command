#pragma once
#include "wh3/identity_gate.hpp"
#include "wh3/packet_tracker.hpp"
#include "wh3/evidence_probe.hpp"
#include "wh3/contact_tracker.hpp"
#include <array>
#include <atomic>
#include <map>
#include <mutex>
#include <thread>
namespace wh3 {
using NativeOrderFn = std::uint32_t (*)(void*,std::uint32_t,void*,std::uint8_t);
using NativeAllocatorFn = void* (*)(void*,std::uint32_t);
using NativeHaltFn = void (*)(void*,std::uint32_t);
using NativeBindingFn = int (*)(void*,void*,std::uint8_t);
using NativePublishFn = std::uint32_t (*)(void*,void*);
using NativeBeginWriterFn = void* (*)(void*,void*,void*,std::uint32_t);
using NativeFinalizeFn = void (*)(void*);
using NativeCopyFn = void (*)(void*,void*);
using NativeStageFn = std::uint32_t (*)(void*,std::uint32_t,void*,float);
using NativeSelectionFn = void* (*)(void*,void*);
using NativePacketHandlerFn = void (*)(void*,void*);
using NativeFreeFn = void (*)(void*);
using MemoryReadFn = bool (*)(std::uintptr_t,void*,std::size_t) noexcept;
using MemoryWriteFn = bool (*)(std::uintptr_t,const void*,std::size_t) noexcept;
struct NativeFunctions {NativeOrderFn move=nullptr,attack=nullptr;NativeAllocatorFn allocate=nullptr;NativeHaltFn halt=nullptr;};
struct FrameIdentity {std::uintptr_t function=0,establisher=0,return_pc=0;explicit operator bool()const{return function&&establisher&&return_pc;}};
using FrameActiveFn = bool (*)(const FrameIdentity&) noexcept;
struct AdapterFunctions {
 NativeBindingFn lua_move=nullptr,lua_attack=nullptr;
 NativePublishFn publish_move=nullptr,publish_attack=nullptr;
 NativeBeginWriterFn begin_writer=nullptr;NativeFinalizeFn finalize=nullptr;
 NativeCopyFn copy=nullptr;NativeStageFn stage=nullptr;
 NativePacketHandlerFn move_handler=nullptr,attack_handler=nullptr;
 NativeSelectionFn selection=nullptr;NativeFreeFn free_memory=nullptr;
};
struct HostStatus {
 Id epoch=0;bool recording=false;std::uint64_t capture_errors=0,fatal_errors=0;Error gate_fault=Error::Ok;
 Id last_recoverable_uid=0;
 std::size_t pending_count=0,pending_limit=32;
 bool exact_source=false,verified_issue=false,native_identity_adapter_connected=false;
 bool move_path_observed=false,attack_path_observed=false;
 bool physical_path_witnesses_ready=false,handler_calibration_ready=false;
 bool native_issue_authorized=false,v3_issue_calibration_ready=false,v3_issue_armed=false;
 // Deprecated compatibility aliases for older Lua/test clients.
 bool experimental_calibration_ready=false,experimental_issue_armed=false;
 std::uint64_t spans=0,mapped_orders=0,unmapped_orders=0;
 std::uint64_t publish_seen=0,publish_parsed=0,publish_unparsed=0;
 std::uint64_t writer_begin_seen=0,writer_finalize_seen=0,writer_committed=0;
 std::uint64_t copy_seen=0,stage_seen=0,selection_seen=0,selection_resolved=0;
 std::uint64_t handler_seen=0,handler_resolved=0,handler_missed=0,handler_token_bindings=0;
 std::uint64_t handler_move_seen=0,handler_attack_seen=0;
 std::uint64_t native_packet_seen=0,native_packet_mapped=0,native_attack_token_bindings=0;
 std::uint64_t last_issue_bindings=0,last_issue_published=0,last_issue_depth=0;
 bool accepted_move_seen=false,accepted_attack_seen=false;
 std::uint64_t last_reader_data=0,last_reader_a=0,last_reader_b=0,last_reader_cursor=0,last_reader_end=0;
 std::uint64_t last_reader_lineage_bytes=0,last_reader_lineage_fragments=0;
 const char* adapter_error="NOT_STARTED";
 const char* last_recoverable_error="NONE";
 const char* last_fatal_error="NONE";
 const char* last_path_stage="NOT_STARTED";
};
struct IssueResult {Id id=0;const char* error=nullptr;explicit operator bool()const{return !error;}};
struct ExecutionEvidence {
 bool complete=false,active=false,known=false; Unit unit{}; Id accepted_serial=0,active_engine_seq=0; Kind kind=Kind::Move;
 std::optional<Id> target_uid; std::optional<float> dest_x,dest_z;
};

class BridgeHost {
public:
 explicit BridgeHost(MemoryReadFn,std::uintptr_t image_base=0x140000000ULL,MemoryWriteFn=nullptr,FrameActiveFn=nullptr,bool validated_issue_authorized_for_fixture=false,EntityAliveFn=nullptr,CombatGroupQueryFn=nullptr);
 bool set_native_functions(NativeFunctions);
 bool set_adapter_functions(AdapterFunctions);
 bool authorize_validated_issue(bool authorized=true);
 NativeFunctions native_functions() const;
 Result<Id> begin(const std::string&);Error end(Id);HostStatus status() const;
 Result<Page> read(Id,Id,std::size_t);Error acknowledge(Id,Id);Result<Snapshot> unit_snapshot(Id) const;
 Result<ExecutionEvidence> execution_identity(Id);
 Result<EntitySnapshot> entity_snapshot(Id,std::uint64_t model_ms);
 Result<CombatSnapshot> combat_snapshot(Id);
 Error bind_evidence_root(Id,std::uintptr_t);
 Result<std::uintptr_t> resolve_evidence_userdata(Id,std::uintptr_t userdata_block);
 Result<std::uintptr_t> evidence_root(Id) const;
 bool contact_owner_ready(Id) const;
 ContactPage contact_events(std::uint64_t after,std::size_t max_count) const;
 void observe_contact_pair(std::uintptr_t entity_a,std::uintptr_t entity_b,std::uint64_t tick_ms) noexcept;
 std::uint32_t order(Kind,void*,std::uint32_t,void*,std::uint8_t,InputSnapshot={});
 void* allocate(void*,std::uint32_t);void halt(void*,std::uint32_t);
 const char* arm(bool explicit_ack);
 IssueResult begin_issue(Kind,bool,Id uid,Id revision,void* lua_state,
     std::optional<std::array<float,3>> move_destination=std::nullopt);
 IssueResult finish_issue(bool callback_succeeded);
 Error cancel_pending_issue(Id issue_id);
 int binding(Kind,void*,void*,std::uint8_t);
 std::uint32_t publish(Kind,void*,void*);
 void* writer_begin(void*,void*,void*,std::uint32_t);
 void writer_finalize(void*);
 void copy_buffer(void*,void*);
 std::uint32_t stage_buffer(void*,std::uint32_t,void*,float);
 void packet_handler(Kind,void*,void*);
 void* selection(void*,void*,FrameIdentity);
 void release_memory(void*);
private:
 struct Scope {BridgeHost* owner;Scope* previous;std::uintptr_t root;Id epoch;Kind kind;std::uint8_t queued;
   unsigned allocations=0;std::uintptr_t slot=0;bool queue_mismatch=false,nested_command=false;};
 static thread_local Scope* current_;
 struct HandlerScope {BridgeHost* owner;HandlerScope* previous;Kind kind;std::shared_ptr<TrackedPacket> packet;bool speculative_pending=false;};
 static thread_local HandlerScope* handler_current_;
 struct Control {bool active=false;std::thread::id thread;void* lua_state=nullptr;Issue issue{};Snapshot snapshot{};
   Kind kind=Kind::Move;bool queued=false;std::uintptr_t root=0;unsigned bindings=0,depth=0,published=0;
   bool attack_target_valid=false;std::uintptr_t attack_target_root=0;Id attack_target_uid=0;
   std::optional<std::array<float,3>> move_destination;
   const char* error=nullptr;};
 struct Publication {std::thread::id thread;Kind kind;bool queued;std::uintptr_t root;Unit unit;bool metadata_valid;bool owned;Issue issue;Publication* previous;};
 struct ReaderWitness {std::thread::id thread;std::uintptr_t reader;FrameIdentity frame;std::shared_ptr<TrackedPacket> packet;};
 mutable std::recursive_mutex mutex_;
 IdentityGate gate_;NativeFunctions native_;AdapterFunctions adapter_;
 MemoryReadFn memory_;MemoryWriteFn write_;[[maybe_unused]] FrameActiveFn frame_active_;std::uintptr_t base_;
 EvidenceProbe evidence_probe_;
 ContactTracker contacts_;
 struct AcceptedEvidence {Unit unit{};std::uintptr_t root=0;Kind kind=Kind::Move;Id engine_seq=0,serial=0;std::optional<Id> target_uid;std::optional<float> x,z;};
 std::map<std::pair<std::uintptr_t,Id>,AcceptedEvidence> accepted_evidence_;
 std::string session_;Id epoch_=0;bool recording_=false,functions_locked_=false,adapter_connected_=false,armed_=false;
 std::map<Id,std::pair<Unit,std::uintptr_t>> units_;
 // command roots come from native order entry; evidence roots come from Lua battle_unit userdata.
 std::map<Id,std::uintptr_t> evidence_roots_;
 std::map<std::uintptr_t,Id> evidence_uid_by_root_;
 std::atomic<std::uint64_t> errors_{0},fatal_errors_{0};PacketTracker tracker_;Control control_;Publication* publication_=nullptr;
 std::vector<ReaderWitness> readers_;std::uint64_t packet_serial_=0,mapped_=0,unmapped_=0;
 std::uint64_t publish_seen_=0,publish_parsed_=0,publish_unparsed_=0;
 std::uint64_t writer_begin_seen_=0,writer_finalize_seen_=0,writer_committed_=0;
 std::uint64_t copy_seen_=0,stage_seen_=0,selection_seen_=0,selection_resolved_=0;
 std::uint64_t handler_seen_=0,handler_resolved_=0,handler_missed_=0,handler_token_bindings_=0;
 std::uint64_t handler_move_seen_count_=0,handler_attack_seen_count_=0;
 std::uint64_t native_packet_seen_=0,native_packet_mapped_=0,native_attack_token_bindings_=0;
 std::uint64_t last_issue_bindings_=0,last_issue_published_=0,last_issue_depth_=0;
 std::string last_issue_error_;
 std::uint64_t last_reader_data_=0,last_reader_a_=0,last_reader_b_=0,last_reader_cursor_=0,last_reader_end_=0;
 std::uint64_t last_reader_lineage_bytes_=0,last_reader_lineage_fragments_=0;
 bool native_issue_authorized_=false;
 bool handler_move_seen_=false,handler_attack_seen_=false;
 bool accepted_move_seen_=false,accepted_attack_seen_=false;
 bool move_seen_=false,attack_seen_=false;const char* adapter_error_="NOT_STARTED";
 Id last_recoverable_uid_=0;const char* last_recoverable_error_="NONE";const char* last_fatal_error_="NONE";
 const char* last_path_stage_="NOT_STARTED";
 static constexpr std::size_t pending_limit_=32;
 // Exact recipient key, never FIFO. Cancelled tokens retain their slot until consumed.
 std::map<Id,std::shared_ptr<TrackedPacket>> pending_by_uid_;
 void remember_accepted(const Order&,std::uintptr_t,const NativeOutcome&,Id serial);
 void clear_command_evidence(std::uintptr_t);
 void clear_evidence_binding(Id);
 std::shared_ptr<TrackedPacket> pending_candidate(const Order&,std::uintptr_t) const;
 void retire_pending(const std::shared_ptr<TrackedPacket>&);
 bool get(std::uintptr_t,std::size_t,void*,std::size_t) const noexcept;
 bool put(std::uintptr_t,std::size_t,const void*,std::size_t) const noexcept;
 Unit track(Id,std::uintptr_t);void note_capture(const char*,Id=0) noexcept;void disarm(const char*) noexcept;
 bool owned_in_flight() const noexcept;
 bool decode_order(Order&,std::uintptr_t,Kind,void*,std::uint8_t);
 NativeOutcome outcome(const Scope&,std::uint32_t,Order&,bool& complete);
 std::shared_ptr<TrackedPacket> current_packet(bool* speculative_pending=nullptr);
 std::shared_ptr<TrackedPacket> resolve_reader_packet(void* reader);
 bool single_recipient(void*,Kind,bool&,Unit&,std::uintptr_t&);
 bool adapter_ready() const noexcept;
 bool handler_calibration_ready() const noexcept;
 bool v3_issue_calibration_ready() const noexcept;
 bool issue_ready() const noexcept;
};
BridgeHost& host();std::uintptr_t platform_image_base() noexcept;
bool platform_read(std::uintptr_t,void*,std::size_t) noexcept;
bool platform_write(std::uintptr_t,const void*,std::size_t) noexcept;
bool platform_entity_alive(std::uintptr_t,bool*) noexcept;
bool platform_combat_group_query(std::uintptr_t,bool*,std::uintptr_t*) noexcept;
bool platform_frame_active(const FrameIdentity&) noexcept;
FrameIdentity platform_caller_frame(void*) noexcept;
void* platform_lua_symbol(const char*) noexcept;const char* platform_start_observer();
bool platform_hooks_installed() noexcept;const char* platform_last_error() noexcept;
bool platform_evidence_build_verified() noexcept;const char* platform_evidence_build_id() noexcept;
std::uint64_t platform_tick_ms() noexcept;
}
