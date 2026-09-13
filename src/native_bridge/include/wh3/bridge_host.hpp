#pragma once
#include "wh3/identity_gate.hpp"
#include "wh3/packet_tracker.hpp"
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
 Id epoch=0;bool recording=false;std::uint64_t capture_errors=0;Error gate_fault=Error::Ok;
 bool exact_source=false,verified_issue=false,native_identity_adapter_connected=false;
 bool move_path_observed=false,attack_path_observed=false;
 bool physical_path_witnesses_ready=false,handler_calibration_ready=false,experimental_calibration_ready=false,experimental_issue_armed=false;
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
 const char* last_path_stage="NOT_STARTED";
};
struct IssueResult {Id id=0;const char* error=nullptr;explicit operator bool()const{return !error;}};
class BridgeHost {
public:
 explicit BridgeHost(MemoryReadFn,std::uintptr_t image_base=0x140000000ULL,MemoryWriteFn=nullptr,FrameActiveFn=nullptr,bool allow_unvalidated_issue=false);
 bool set_native_functions(NativeFunctions);
 bool set_adapter_functions(AdapterFunctions);
 NativeFunctions native_functions() const;
 Result<Id> begin(const std::string&);Error end(Id);HostStatus status() const;
 Result<Page> read(Id,Id,std::size_t);Error acknowledge(Id,Id);Result<Snapshot> unit_snapshot(Id) const;
 std::uint32_t order(Kind,void*,std::uint32_t,void*,std::uint8_t);
 void* allocate(void*,std::uint32_t);void halt(void*,std::uint32_t);
 const char* arm(bool explicit_ack);
 IssueResult begin_issue(Kind,bool,Id uid,Id revision,void* lua_state);
 IssueResult finish_issue(bool callback_succeeded);
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
 struct HandlerScope {BridgeHost* owner;HandlerScope* previous;Kind kind;std::shared_ptr<TrackedPacket> packet;};
 static thread_local HandlerScope* handler_current_;
 struct Control {bool active=false;std::thread::id thread;void* lua_state=nullptr;Issue issue{};Snapshot snapshot{};
   Kind kind=Kind::Move;bool queued=false;std::uintptr_t root=0;unsigned bindings=0,depth=0,published=0;
   bool attack_target_valid=false;std::uintptr_t attack_target_root=0;Id attack_target_uid=0;
   const char* error=nullptr;};
 struct Publication {std::thread::id thread;Kind kind;bool queued;std::uintptr_t root;Unit unit;bool metadata_valid;bool owned;Issue issue;Publication* previous;};
 struct ReaderWitness {std::thread::id thread;std::uintptr_t reader;FrameIdentity frame;std::shared_ptr<TrackedPacket> packet;};
 mutable std::recursive_mutex mutex_;
 IdentityGate gate_;NativeFunctions native_;AdapterFunctions adapter_;
 MemoryReadFn memory_;MemoryWriteFn write_;FrameActiveFn frame_active_;std::uintptr_t base_;
 std::string session_;Id epoch_=0;bool recording_=false,functions_locked_=false,adapter_connected_=false,armed_=false;
 std::map<Id,std::pair<Unit,std::uintptr_t>> units_;
 std::atomic<std::uint64_t> errors_{0};PacketTracker tracker_;Control control_;Publication* publication_=nullptr;
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
 bool allow_unvalidated_issue_=false;
 bool handler_move_seen_=false,handler_attack_seen_=false;
 bool accepted_move_seen_=false,accepted_attack_seen_=false;
 bool move_seen_=false,attack_seen_=false;const char* adapter_error_="NOT_STARTED";const char* last_path_stage_="NOT_STARTED";
 std::shared_ptr<TrackedPacket> pending_;
 bool get(std::uintptr_t,std::size_t,void*,std::size_t) const noexcept;
 bool put(std::uintptr_t,std::size_t,const void*,std::size_t) const noexcept;
 Unit track(Id,std::uintptr_t);void disarm(const char*) noexcept;
 bool decode_order(Order&,std::uintptr_t,Kind,void*,std::uint8_t);
 NativeOutcome outcome(const Scope&,std::uint32_t,Order&,bool& complete);
 std::shared_ptr<TrackedPacket> current_packet();
 std::shared_ptr<TrackedPacket> resolve_reader_packet(void* reader);
 bool single_recipient(void*,Kind,bool&,Unit&,std::uintptr_t&);
 bool adapter_ready() const noexcept;
 bool handler_calibration_ready() const noexcept;
 bool experimental_calibration_ready() const noexcept;
 bool issue_ready() const noexcept;
};
BridgeHost& host();std::uintptr_t platform_image_base() noexcept;
bool platform_read(std::uintptr_t,void*,std::size_t) noexcept;
bool platform_write(std::uintptr_t,const void*,std::size_t) noexcept;
bool platform_frame_active(const FrameIdentity&) noexcept;
FrameIdentity platform_caller_frame(void*) noexcept;
void* platform_lua_symbol(const char*) noexcept;const char* platform_start_observer();
bool platform_hooks_installed() noexcept;const char* platform_last_error() noexcept;
}
