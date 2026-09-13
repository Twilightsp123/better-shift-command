#include "wh3/bridge_host.hpp"
#include <cstring>
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>
namespace wh3 {
thread_local BridgeHost::Scope* BridgeHost::current_=nullptr;
thread_local BridgeHost::HandlerScope* BridgeHost::handler_current_=nullptr;
BridgeHost::BridgeHost(MemoryReadFn r,std::uintptr_t b,MemoryWriteFn w,FrameActiveFn f,bool allow):memory_(r),write_(w),frame_active_(f),base_(b),allow_unvalidated_issue_(allow){}
bool BridgeHost::set_native_functions(NativeFunctions n){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(functions_locked_||recording_||!n.move||!n.attack||!n.allocate||!n.halt)return false;native_=n;return true;}
bool BridgeHost::set_adapter_functions(AdapterFunctions n){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(functions_locked_||recording_||!n.lua_move||!n.lua_attack||!n.publish_move||!n.publish_attack||!n.begin_writer||!n.finalize||!n.copy||!n.stage||!n.move_handler||!n.attack_handler||!n.selection||!n.free_memory||!write_)return false;
 adapter_=n;adapter_connected_=true;return true;}
NativeFunctions BridgeHost::native_functions()const{std::lock_guard<std::recursive_mutex> l(mutex_);return native_;}
Result<Id> BridgeHost::begin(const std::string& s){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(s.empty()||s.size()>64||s.find('\0')!=std::string::npos||recording_)return {{},Error::Invalid};
 if(control_.active||publication_)return {{},Error::Reentrant};
 for(auto* q=current_;q;q=q->previous)if(q->owner==this)return {{},Error::Reentrant};
 auto r=gate_.begin_battle();if(!r)return r;epoch_=r.value;session_=s;units_.clear();tracker_.clear();readers_.clear();
 control_={};pending_.reset();errors_=0;mapped_=unmapped_=0;move_seen_=attack_seen_=armed_=false;
 publish_seen_=publish_parsed_=publish_unparsed_=0;writer_begin_seen_=writer_finalize_seen_=writer_committed_=0;
 copy_seen_=stage_seen_=selection_seen_=selection_resolved_=0;handler_seen_=handler_resolved_=handler_missed_=handler_token_bindings_=0;handler_move_seen_count_=handler_attack_seen_count_=0;native_packet_seen_=native_packet_mapped_=native_attack_token_bindings_=0;
 last_issue_bindings_=last_issue_published_=last_issue_depth_=0;last_issue_error_.clear();
 last_reader_data_=last_reader_a_=last_reader_b_=last_reader_cursor_=last_reader_end_=0;
 last_reader_lineage_bytes_=last_reader_lineage_fragments_=0;
 handler_move_seen_=handler_attack_seen_=false;accepted_move_seen_=accepted_attack_seen_=false;recording_=true;adapter_error_=allow_unvalidated_issue_?"WAITING_FOR_ACCEPTED_CALIBRATION":"WAITING_FOR_PHYSICAL_PATH_WITNESSES";last_path_stage_="WAIT_PUBLISH";return r;}
Error BridgeHost::end(Id e){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(control_.active||publication_)return Error::Reentrant;
 for(auto* q=current_;q;q=q->previous)if(q->owner==this)return Error::Reentrant;
 auto r=gate_.end_battle(e);if(r==Error::Ok){recording_=armed_=false;tracker_.clear();readers_.clear();pending_.reset();}return r;}
bool BridgeHost::adapter_ready()const noexcept{return recording_&&adapter_connected_&&move_seen_&&attack_seen_&&!tracker_.faulted()&&errors_.load()==0;}
bool BridgeHost::handler_calibration_ready()const noexcept{return recording_&&adapter_connected_&&handler_move_seen_&&handler_attack_seen_&&errors_.load()==0;}
bool BridgeHost::experimental_calibration_ready()const noexcept{return allow_unvalidated_issue_&&recording_&&adapter_connected_&&handler_seen_>0&&accepted_move_seen_&&accepted_attack_seen_&&errors_.load()==0&&gate_.fault()==Error::Ok;}
bool BridgeHost::issue_ready()const noexcept{return allow_unvalidated_issue_?experimental_calibration_ready():adapter_ready();}
HostStatus BridgeHost::status()const{std::lock_guard<std::recursive_mutex> l(mutex_);HostStatus s;
 s.epoch=epoch_;s.recording=recording_;s.capture_errors=errors_.load();s.gate_fault=gate_.fault();
 s.native_identity_adapter_connected=adapter_connected_;
 // Path samples establish only the exercised mapping, NOT exhaustive native
 // lifecycle coverage. Never advertise production proof from these samples.
 s.physical_path_witnesses_ready=adapter_ready();
 s.handler_calibration_ready=handler_calibration_ready();
 s.experimental_calibration_ready=experimental_calibration_ready();
 s.experimental_issue_armed=armed_&&gate_.issue_enabled()&&issue_ready();
 s.exact_source=false;s.verified_issue=false;
 s.move_path_observed=move_seen_;s.attack_path_observed=attack_seen_;s.spans=tracker_.size();s.mapped_orders=mapped_;s.unmapped_orders=unmapped_;
 s.publish_seen=publish_seen_;s.publish_parsed=publish_parsed_;s.publish_unparsed=publish_unparsed_;
 s.writer_begin_seen=writer_begin_seen_;s.writer_finalize_seen=writer_finalize_seen_;s.writer_committed=writer_committed_;
 s.copy_seen=copy_seen_;s.stage_seen=stage_seen_;s.selection_seen=selection_seen_;s.selection_resolved=selection_resolved_;
 s.handler_seen=handler_seen_;s.handler_resolved=handler_resolved_;s.handler_missed=handler_missed_;s.handler_token_bindings=handler_token_bindings_;
 s.handler_move_seen=handler_move_seen_count_;s.handler_attack_seen=handler_attack_seen_count_;
 s.native_packet_seen=native_packet_seen_;s.native_packet_mapped=native_packet_mapped_;s.native_attack_token_bindings=native_attack_token_bindings_;
 s.last_issue_bindings=last_issue_bindings_;s.last_issue_published=last_issue_published_;s.last_issue_depth=last_issue_depth_;
 s.accepted_move_seen=accepted_move_seen_;s.accepted_attack_seen=accepted_attack_seen_;
 s.last_reader_data=last_reader_data_;s.last_reader_a=last_reader_a_;s.last_reader_b=last_reader_b_;
 s.last_reader_cursor=last_reader_cursor_;s.last_reader_end=last_reader_end_;
 s.last_reader_lineage_bytes=last_reader_lineage_bytes_;s.last_reader_lineage_fragments=last_reader_lineage_fragments_;
 s.adapter_error=adapter_error_;s.last_path_stage=last_path_stage_;return s;}
Result<Page> BridgeHost::read(Id e,Id a,std::size_t n){std::lock_guard<std::recursive_mutex> l(mutex_);return gate_.read(e,a,n);}
Error BridgeHost::acknowledge(Id e,Id a){std::lock_guard<std::recursive_mutex> l(mutex_);return gate_.acknowledge(e,a);}
Result<Snapshot> BridgeHost::unit_snapshot(Id u)const{std::lock_guard<std::recursive_mutex> l(mutex_);auto i=units_.find(u);if(i==units_.end())return {{},Error::Missing};return gate_.snapshot(i->second.first);}
bool BridgeHost::get(std::uintptr_t p,std::size_t o,void* d,std::size_t n)const noexcept{return memory_&&p&&o<=UINTPTR_MAX-p&&n<=UINTPTR_MAX-(p+o)&&memory_(p+o,d,n);}
bool BridgeHost::put(std::uintptr_t p,std::size_t o,const void* d,std::size_t n)const noexcept{return write_&&p&&o<=UINTPTR_MAX-p&&n<=UINTPTR_MAX-(p+o)&&write_(p+o,d,n);}
void BridgeHost::disarm(const char* reason)noexcept{armed_=false;adapter_error_=reason;++errors_;try{gate_.set_issue_enabled(false);if(pending_){pending_->cancelled=true;gate_.cancel_issue(pending_->issue);}}catch(...){} }
Unit BridgeHost::track(Id uid,std::uintptr_t root){auto i=units_.find(uid);if(i!=units_.end()&&i->second.second==root)return i->second.first;
 if(i!=units_.end()){gate_.retire_unit(i->second.first);units_.erase(i);}auto r=gate_.register_unit(uid,root);if(!r)throw std::runtime_error(name(r.error));units_.emplace(uid,std::make_pair(r.value,root));return r.value;}
bool BridgeHost::decode_order(Order& o,std::uintptr_t root,Kind k,void* payload,std::uint8_t q){
 Id uid=0;if(!get(root,0x3ea0,&uid,4))return false;o.kind=k;o.recipient=track(uid,root);o.queued=q!=0;
 auto p=reinterpret_cast<std::uintptr_t>(payload);
 if(k==Kind::Move){float xyz[3]{};if(!get(p,0,xyz,12))return false;for(float x:xyz)if(!std::isfinite(x))return false;o.x=xyz[0];o.y=xyz[1];o.z=xyz[2];return true;}
 std::uintptr_t target=0;Id tu=0;if(!get(p,0,&target,8)||!get(target,0x3ea0,&tu,4))return false;o.target_root=target;o.target_uid=tu;
 std::uint8_t flags[3]{};if(get(p,0x18,flags,3)){o.raw70=flags[0];o.raw71=flags[1];o.raw72=flags[2];}return true;
}
NativeOutcome BridgeHost::outcome(const Scope& f,std::uint32_t result,Order& o,bool& complete){
 // WH3's bool result is AL. Preserve EAX for forwarding, but do not mistake
 // nonzero undefined high bits for accepted=true when AL is zero.
 NativeOutcome n{(result&0xffU)!=0,{}};if(!n.accepted)return n;
 if(f.allocations!=1||f.queue_mismatch||f.nested_command)return n;
 const auto first=f.root+0x288;
 if(f.slot<first||(f.slot-first)%0x120||(f.slot-first)/0x120>=40){complete=false;return n;}
 std::array<unsigned char,0x120> s{};if(!get(f.slot,0,s.data(),s.size())){complete=false;return n;}
 std::uint64_t vt=0;std::memcpy(&vt,s.data()+0x18,8);
 if(vt!=base_+(f.kind==Kind::Move?0x37b31c8:0x37b2540)){complete=false;return n;}
 Id seq=0;std::memcpy(&seq,s.data()+0x20,4);n.engine_seq=seq;
 if(f.kind==Kind::Move){float xyz[3];std::memcpy(xyz,s.data()+0x58,12);for(float x:xyz)if(!std::isfinite(x)){complete=false;return n;}o.x=xyz[0];o.y=xyz[1];o.z=xyz[2];}
 else{std::uintptr_t t=0;Id uid=0;std::memcpy(&t,s.data()+0x58,8);if(!get(t,0x3ea0,&uid,4)){complete=false;return n;}o.target_root=t;o.target_uid=uid;o.raw70=s[0x70];o.raw71=s[0x71];o.raw72=s[0x72];o.raw78=s[0x78];}
 complete=true;return n;
}
std::shared_ptr<TrackedPacket> BridgeHost::resolve_reader_packet(void* reader){
 auto r=reinterpret_cast<std::uintptr_t>(reader);std::uintptr_t data=0;Id a=0,b=0,cursor=0;std::uint8_t error=1;
 if(!r||!get(r,8,&error,1)||error||!get(r,0x10,&data,8)||!data||
    !get(r,0x18,&a,4)||!get(r,0x1c,&b,4)||!get(r,0x20,&cursor,4))return {};
 const std::uint64_t end64=std::uint64_t(a)+b;
 last_reader_data_=data;last_reader_a_=a;last_reader_b_=b;last_reader_cursor_=cursor;last_reader_end_=end64<=UINT32_MAX?end64:UINT64_MAX;
 last_reader_lineage_bytes_=last_reader_lineage_fragments_=0;
 if(end64>UINT32_MAX||data>UINTPTR_MAX-static_cast<std::uintptr_t>(end64))return {};
 const auto end=data+static_cast<std::uintptr_t>(end64);
 // Diagnostic only: report the best physical-lineage coverage among the exact
 // structural start candidates. This never participates in attribution.
 std::uintptr_t starts[3]{};std::size_t count=0;
 if(data<=UINTPTR_MAX-a)starts[count++]=data+a;
 if(data<=UINTPTR_MAX-b)starts[count++]=data+b;
 if(cursor>=7&&data<=UINTPTR_MAX-(cursor-7))starts[count++]=data+(cursor-7);
 for(std::size_t i=0;i<count;++i){if(starts[i]>=end)continue;auto c=tracker_.coverage(starts[i],end,epoch_);
  if(c.first>last_reader_lineage_bytes_||(c.first==last_reader_lineage_bytes_&&c.second>last_reader_lineage_fragments_)){last_reader_lineage_bytes_=c.first;last_reader_lineage_fragments_=c.second;}}
 return tracker_.resolve_reader_bounds(data,a,b,cursor,epoch_);
}
std::shared_ptr<TrackedPacket> BridgeHost::current_packet(){
 for(auto* h=handler_current_;h;h=h->previous)if(h->owner==this)return h->packet;
 return {};
}
std::uint32_t BridgeHost::order(Kind k,void* u,std::uint32_t a,void* payload,std::uint8_t q){std::lock_guard<std::recursive_mutex> l(mutex_);functions_locked_=true;
 auto fn=k==Kind::Move?native_.move:native_.attack;if(!fn)throw std::logic_error("NATIVE_TRAMPOLINE_MISSING");
 for(auto* s=current_;s;s=s->previous)if(s->owner==this)s->nested_command=true;
 Scope f{this,current_,reinterpret_cast<std::uintptr_t>(u),epoch_,k,q};Order o;bool complete=false;
 if(recording_)try{complete=decode_order(o,f.root,k,payload,q);}catch(...){disarm("UNIT_OR_PAYLOAD_CAPTURE_FAILED");}
 auto packet=recording_?current_packet():nullptr;
 if(recording_&&!packet&&allow_unvalidated_issue_&&k==Kind::Attack&&pending_&&pending_->owned&&!pending_->consumed&&!pending_->cancelled&&pending_->kind==Kind::Attack){
  // Experimental-only fallback for the real WH3 Attack path, which runtime shows
  // can bypass the packet-handler candidate used by the Move path. This is not
  // "first Attack wins": exact recipient root, queued bit and target root/UID
  // must match the published controller Attack. The IdentityGate then performs
  // the expected-revision stale check before native side effects. Production
  // builds never enter this path.
  const bool target_ok=complete&&pending_->attack_target_valid&&o.target_root==pending_->attack_target_root&&o.target_uid==pending_->attack_target_uid;
  if(target_ok&&pending_->root==f.root&&pending_->queued==(q!=0)){
   packet=pending_;++native_attack_token_bindings_;last_path_stage_="ATTACK_NATIVE_PENDING_TOKEN";
  }
 }
 if(packet){++native_packet_seen_;if(last_path_stage_!=std::string("ATTACK_NATIVE_PENDING_TOKEN"))last_path_stage_="NATIVE_PACKET_PRESENT";}
 if(packet&&packet->owned&&packet->kind!=k){disarm("OWNED_KIND_MISMATCH");return 0;}
 std::uint32_t result=0;NativeOutcome n;
 auto original=[&](){current_=&f;try{result=fn(u,a,payload,q);}catch(...){current_=f.previous;disarm("NATIVE_EXCEPTION");throw;}current_=f.previous;n=outcome(f,result,o,complete);return n;};
 if(!recording_){original();return result;}
 if(packet&&packet->owned){
  if(!complete||packet->root!=f.root){disarm("OWNED_RECIPIENT_NOT_VERIFIED");return 0;}
  auto d=gate_.dispatch_owned(packet->key,o,original);packet->consumed=true;++mapped_;++native_packet_mapped_;last_path_stage_="OWNED_NATIVE_PACKET_MAPPED";
  if(d.native_outcome&&d.native_outcome->accepted){if(k==Kind::Move)accepted_move_seen_=true;else if(k==Kind::Attack)accepted_attack_seen_=true;}
  if(pending_==packet)pending_.reset();
  gate_.retire_stream(packet->stream);
  if(!d.native_called)return 0;
  if(!complete||d.status==Status::Indeterminate)disarm("OWNED_OUTCOME_INDETERMINATE");return result;
 }
 original();
 if(n.accepted){if(k==Kind::Move)accepted_move_seen_=true;else if(k==Kind::Attack)accepted_attack_seen_=true;
  if(experimental_calibration_ready()&&!armed_)adapter_error_="ACCEPTED_CALIBRATION_READY_EXPERIMENTAL_ONLY";}
 try{
  if(!o.recipient.lifetime){Id uid=0;if(!get(f.root,0x3ea0,&uid,4)){disarm("EXTERNAL_UID_UNREADABLE");return result;}o.recipient=track(uid,f.root);o.kind=k;o.queued=q!=0;}
  auto e=complete?gate_.observe_external(o,n):gate_.observe_external_partial(o,n);
  if(!complete||!e)disarm("EXTERNAL_OUTCOME_PARTIAL");
  if(packet&&packet->kind==k&&n.accepted){++mapped_;++native_packet_mapped_;last_path_stage_="EXTERNAL_NATIVE_PACKET_MAPPED";if(k==Kind::Move)move_seen_=true;else attack_seen_=true;}
  else {++unmapped_;last_path_stage_="NATIVE_UNMAPPED";}
 }catch(...){disarm("EXTERNAL_OBSERVER_EXCEPTION");}
 return result;
}
void* BridgeHost::allocate(void* p,std::uint32_t q){std::lock_guard<std::recursive_mutex> l(mutex_);functions_locked_=true;
 if(!native_.allocate)throw std::logic_error("ALLOCATOR_TRAMPOLINE_MISSING");void* r=native_.allocate(p,q);
 auto* f=current_;if(f&&f->owner==this&&reinterpret_cast<std::uintptr_t>(p)==f->root+0x278){++f->allocations;f->slot=reinterpret_cast<std::uintptr_t>(r);f->queue_mismatch|=static_cast<std::uint8_t>(q)!=f->queued;}return r;}
void BridgeHost::halt(void* u,std::uint32_t flags){std::lock_guard<std::recursive_mutex> l(mutex_);functions_locked_=true;
 if(!native_.halt)throw std::logic_error("HALT_TRAMPOLINE_MISSING");native_.halt(u,flags);if(!recording_)return;
 try{Id uid=0;auto root=reinterpret_cast<std::uintptr_t>(u);if(!get(root,0x3ea0,&uid,4)){disarm("HALT_UID_UNREADABLE");return;}
  Order o;o.kind=Kind::Halt;o.recipient=track(uid,root);o.halt_flags=static_cast<std::uint8_t>(flags);if(!gate_.observe_external(o,{true,{}}))disarm("HALT_RECORD_FAILED");
 }catch(...){disarm("HALT_OBSERVER_EXCEPTION");}}
const char* BridgeHost::arm(bool ack){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(!ack){armed_=false;gate_.set_issue_enabled(false);return nullptr;}
 if(!allow_unvalidated_issue_){if(!adapter_ready())return "ADAPTER_NOT_READY";return "NATIVE_RELEASE_NOT_APPROVED";}
 if(!experimental_calibration_ready())return "EXPERIMENTAL_CALIBRATION_NOT_READY";
 if(gate_.set_issue_enabled(true)!=Error::Ok)return "GATE_FAULT";armed_=true;adapter_error_="ARMED_EXPERIMENTAL_ACCEPTED_CALIBRATION";return nullptr;}
IssueResult BridgeHost::begin_issue(Kind k,bool q,Id uid,Id rev,void* L){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(!armed_||!issue_ready())return {0,"ADAPTER_NOT_READY"};if(control_.active||pending_)return {0,"ISSUE_ALREADY_PENDING"};
 auto it=units_.find(uid);if(it==units_.end())return {0,"UNIT_NOT_OBSERVED"};auto s=gate_.snapshot(it->second.first);
 if(!s||s.value.revision!=rev)return {0,"REJECTED_STALE"};auto issue=gate_.make_issue(k,q,{s.value});if(!issue)return {0,name(issue.error)};
 control_={};control_.active=true;control_.thread=std::this_thread::get_id();control_.lua_state=L;control_.issue=issue.value;
 control_.snapshot=s.value;control_.kind=k;control_.queued=q;control_.root=it->second.second;return {issue.value.id,nullptr};}
IssueResult BridgeHost::finish_issue(bool ok){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(!control_.active||control_.thread!=std::this_thread::get_id())return {0,"NO_ACTIVE_ISSUE"};
 Id id=control_.issue.id;const char* error=control_.error;
 last_issue_bindings_=control_.bindings;last_issue_published_=control_.published;last_issue_depth_=control_.depth;
 if(!ok)error="LUA_CALLBACK_FAILED";
 else if(!error){
  const bool single_publish=control_.published==1;
  const bool binding_ok=allow_unvalidated_issue_?control_.bindings<=1:control_.bindings==1;
  if(!single_publish||!binding_ok){
   last_issue_error_="ONE_NATIVE_COMMAND_REQUIRED bindings="+std::to_string(control_.bindings)+
     " published="+std::to_string(control_.published)+" depth="+std::to_string(control_.depth);
   error=last_issue_error_.c_str();
  }
 }
 if(error){gate_.cancel_issue(control_.issue);if(pending_&&pending_->issue.id==id)pending_->cancelled=true;}
 control_={};return {id,error};}
int BridgeHost::binding(Kind k,void* uc,void* L,std::uint8_t q){
 NativeBindingFn fn=k==Kind::Move?adapter_.lua_move:adapter_.lua_attack;bool controlled=false;
 {std::lock_guard<std::recursive_mutex> lock(mutex_);if(control_.active&&control_.thread==std::this_thread::get_id()){
  controlled=true;++control_.bindings;++control_.depth;
  if(control_.bindings!=1||control_.depth!=1||k!=control_.kind||(q!=0)!=control_.queued||L!=control_.lua_state){control_.error="BINDING_METADATA_MISMATCH";--control_.depth;return 0;}
 }}
 // NO C++ lock or owning RAII object lives across this Lua binding. A host Lua
 // longjmp is contained by issue_verified_command's lua_pcall; finish_issue resets state.
 int r=fn(uc,L,q);
 if(controlled){std::lock_guard<std::recursive_mutex> lock(mutex_);if(control_.active&&control_.depth)--control_.depth;}return r;
}
bool BridgeHost::single_recipient(void* cmd,Kind k,bool& q,Unit& unit,std::uintptr_t& root){
 // The command-specific constructor places the shared selection subobject at cmd+0x08.
 // 0x142C68624 proves: sub+0x08=count, sub+0x0C=capacity, sub+0x10=array.
 // The previous v0.4.1 parser accidentally read +0x14/+0x24/+0x44 and therefore
 // rejected real one-unit packets before physical provenance could even be tracked.
 auto c=reinterpret_cast<std::uintptr_t>(cmd);std::uint32_t count=0,capacity=0;std::uintptr_t array=0;std::uint8_t queued=0;Id uid=0;
 if(!get(c,0x10,&count,4)||!get(c,0x14,&capacity,4)||count!=1||capacity<count||capacity>4096||
    !get(c,0x18,&array,8)||!array||!get(array,0,&root,8)||!root||!get(root,0x3ea0,&uid,4)||
    !get(c,k==Kind::Move?0xa8:0x99,&queued,1))return false;
 q=queued!=0;unit=track(uid,root);return true;
}
std::uint32_t BridgeHost::publish(Kind k,void* queue,void* cmd){std::lock_guard<std::recursive_mutex> lock(mutex_);
 auto fn=k==Kind::Move?adapter_.publish_move:adapter_.publish_attack;
 const bool callback_scope=control_.active&&control_.thread==std::this_thread::get_id();
 const bool strict_owned=callback_scope&&control_.depth==1;
 const bool owned=strict_owned||(allow_unvalidated_issue_&&callback_scope);
 bool q=false;Unit unit{};std::uintptr_t root=0;bool parsed=false;
 if(recording_){++publish_seen_;last_path_stage_="PUBLISH_SEEN";try{parsed=single_recipient(cmd,k,q,unit,root);}catch(...){disarm("PUBLISH_CAPTURE_FAILED");}}
 if(parsed){++publish_parsed_;last_path_stage_="PUBLISH_METADATA_PARSED";}else if(recording_){++publish_unparsed_;last_path_stage_="PUBLISH_UNPARSED_PHYSICAL_TRACKING";}
 if(owned){
  if(k!=control_.kind||control_.published){control_.error="PUBLISH_METADATA_MISMATCH";return 0;}
  if(parsed){if(q!=control_.queued||unit!=control_.snapshot.unit||root!=control_.root){control_.error="PUBLISH_METADATA_MISMATCH";return 0;}}
  else if(allow_unvalidated_issue_){
   // Experimental-only callback scope fallback. The Lua callback is synchronous,
   // same-thread, and permits exactly one publish. Descriptor parsing is known to
   // fail on this WH3 build, so carry the already-validated issue metadata forward.
   q=control_.queued;unit=control_.snapshot.unit;root=control_.root;
   last_path_stage_="PUBLISH_CALLBACK_TOKEN";
  } else {control_.error="PUBLISH_METADATA_MISMATCH";return 0;}
  if(k==Kind::Attack){
   // 0x142D6D2C0 stores the target BattleUnit root at command+0x88. Capture it
   // while the command object is synchronously alive so a later native Attack
   // without HandlerScope can still be matched on exact semantic identity.
   auto c=reinterpret_cast<std::uintptr_t>(cmd);std::uintptr_t target=0;Id target_uid=0;
   if(!get(c,0x88,&target,8)||!target||!get(target,0x3ea0,&target_uid,4)){control_.error="ATTACK_TARGET_CAPTURE_FAILED";return 0;}
   control_.attack_target_valid=true;control_.attack_target_root=target;control_.attack_target_uid=target_uid;
  }
  auto current=gate_.snapshot(unit);if(!current||current.value.revision!=control_.snapshot.revision){control_.error="REJECTED_STALE";return 0;}++control_.published;
 }
 Publication f{std::this_thread::get_id(),k,q,root,unit,parsed,owned,owned?control_.issue:Issue{},publication_};
 // External calibration does not need descriptor metadata to prove the byte path.
 // Keep the publication scope active even when metadata parsing fails; ONLY owned
 // commands require exact recipient/queued metadata before native publication.
 publication_=recording_?&f:nullptr;
 std::uint32_t r=0;try{r=fn(queue,cmd);}catch(...){publication_=f.previous;disarm("PUBLISH_EXCEPTION");throw;}publication_=f.previous;
 if(owned&&(r&0xffU)==0){control_.error="NATIVE_PUBLISH_REJECTED";gate_.cancel_issue(control_.issue);}return r;
}
void* BridgeHost::writer_begin(void* w,void* buffer,void* type,std::uint32_t channel){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(recording_){
  ++writer_begin_seen_;last_path_stage_="WRITER_BEGIN";
  // Do NOT invalidate cursor..0x5000 here. At begin we do not yet know the
  // packet's final byte range. v0.4.4 erased still-live labels merely because a
  // later writer started in the same arena. writer_finalize()->put() performs
  // exact [start,end) invalidation after the true packet length is known.
  Id start=0;auto b=reinterpret_cast<std::uintptr_t>(buffer);
  if(!get(b,0x5000,&start,4)||start>0x5000)disarm("WRITER_CURSOR_INVALID");
 }
 return adapter_.begin_writer(w,buffer,type,channel);
}
void BridgeHost::writer_finalize(void* writer){std::lock_guard<std::recursive_mutex> lock(mutex_);
 auto w=reinterpret_cast<std::uintptr_t>(writer);std::uintptr_t b=0;Id start=0,end=0;std::uint8_t flags[2]={1,1};std::shared_ptr<TrackedPacket> packet;
 if(recording_){++writer_finalize_seen_;last_path_stage_="WRITER_FINALIZE";}
 const bool active=recording_&&publication_&&publication_->thread==std::this_thread::get_id();
 bool readable=get(w,0,flags,2)&&get(w,8,&b,8)&&get(w,0x10,&start,4)&&get(b,0x5000,&end,4);
 if(active&&readable&&!flags[0]&&!flags[1]&&start<=end&&end<=0x5000&&end-start>=7){
  try{packet=std::make_shared<TrackedPacket>();packet->identity=++packet_serial_;packet->epoch=epoch_;packet->kind=publication_->kind;packet->queued=publication_->queued;
   packet->owned=publication_->owned;packet->issue=publication_->issue;packet->unit=publication_->unit;packet->root=publication_->root;
   if(packet->owned){packet->expected_revision=control_.snapshot.revision;packet->attack_target_valid=control_.attack_target_valid;packet->attack_target_root=control_.attack_target_root;packet->attack_target_uid=control_.attack_target_uid;}
   if(packet->owned){auto stream=gate_.open_stream(b+start,end-start);if(!stream)throw std::runtime_error("stream capacity");packet->stream=stream.value;
    auto own=gate_.own_scope(packet->issue);auto key=gate_.commit_packet(packet->stream,0,end-start,packet->kind,packet->queued,{packet->unit});if(!key)throw std::runtime_error("metadata commit");packet->key=key.value;}
   if(!tracker_.put(b,b+start,end-start,packet))throw std::runtime_error("physical capacity");
   ++writer_committed_;last_path_stage_="WRITER_PACKET_COMMITTED";
  }catch(...){packet.reset();disarm("PROVENANCE_COMMIT_FAILED");}
 }
 if(active&&publication_->owned&&!packet){std::uint8_t abort=1;if(!put(w,1,&abort,1))disarm("ABORT_FLAG_WRITE_FAILED_INDETERMINATE");control_.error="PACKET_NOT_COMMITTED";}
 adapter_.finalize(writer);
 if(packet&&packet->owned)pending_=packet;
}
void BridgeHost::copy_buffer(void* dest,void* source){std::lock_guard<std::recursive_mutex> l(mutex_);auto d=reinterpret_cast<std::uintptr_t>(dest),s=reinterpret_cast<std::uintptr_t>(source);Id n=0;std::uintptr_t old=0;
 if(recording_){++copy_seen_;last_path_stage_="BUFFER_COPY";get(d,8,&old,8);}
 bool good=get(s,0x5000,&n,4)&&n<=0x5000;adapter_.copy(dest,source);
 if(recording_&&good&&n){
  std::uintptr_t p=0;if(!get(d,8,&p,8)){disarm("COPY_DEST_UNREADABLE");return;}
  // Reallocation retires the old allocation. In-place copies are invalidated only
  // for the exact copied range by PacketTracker::copy(), never wholesale first.
  if(old&&old!=p)tracker_.release(old);
  if(!tracker_.copy(p,p,s,n))disarm("COPY_MAPPING_FAILED");
 }
}
std::uint32_t BridgeHost::stage_buffer(void* dst,std::uint32_t a,void* source,float f){std::lock_guard<std::recursive_mutex> l(mutex_);auto d=reinterpret_cast<std::uintptr_t>(dst),s=reinterpret_cast<std::uintptr_t>(source);Id old=0,n=0;
 if(recording_){++stage_seen_;last_path_stage_="STAGE_COPY";}
 bool good=get(d,0x5024,&old,4)&&get(s,0x5000,&n,4)&&old==0&&n>0&&n<=0x5000;
 auto r=adapter_.stage(dst,a,source,f);
 if(recording_&&good&&(r&0xffU)){auto p=d+0x20;if(!tracker_.copy(d,p,s,n))disarm("STAGE_COPY_MAPPING_FAILED");}return r;
}
void BridgeHost::packet_handler(Kind k,void* reader,void* context){
 NativePacketHandlerFn fn=k==Kind::Move?adapter_.move_handler:adapter_.attack_handler;std::shared_ptr<TrackedPacket> packet;
 {std::lock_guard<std::recursive_mutex> l(mutex_);functions_locked_=true;
  if(recording_){++handler_seen_;if(k==Kind::Move){handler_move_seen_=true;++handler_move_seen_count_;}else if(k==Kind::Attack){handler_attack_seen_=true;++handler_attack_seen_count_;}
   last_path_stage_=k==Kind::Move?"MOVE_HANDLER_ENTER":"ATTACK_HANDLER_ENTER";packet=resolve_reader_packet(reader);
   if(packet&&packet->kind==k){++handler_resolved_;last_path_stage_=k==Kind::Move?"MOVE_HANDLER_PACKET_RESOLVED":"ATTACK_HANDLER_PACKET_RESOLVED";}
   else if(packet){if(packet->owned)disarm("HANDLER_KIND_MISMATCH");packet.reset();++handler_missed_;last_path_stage_="HANDLER_EXACT_MISS";}
   else if(allow_unvalidated_issue_&&pending_&&pending_->owned&&!pending_->consumed&&!pending_->cancelled&&pending_->kind==k){
    // Experimental-validation-only fallback: one Bridge issue may be pending at a
    // time. The Handler kind binds that already-committed token to the synchronous
    // native call below. Native entry still verifies exact recipient root, queued
    // bit and expected revision before dispatch. This is NOT production exact-source
    // proof and is compiled out of release-approved builds.
    packet=pending_;++handler_token_bindings_;last_path_stage_=k==Kind::Move?"MOVE_HANDLER_PENDING_TOKEN":"ATTACK_HANDLER_PENDING_TOKEN";
   } else {++handler_missed_;last_path_stage_="HANDLER_EXACT_MISS";}
   if(allow_unvalidated_issue_&&experimental_calibration_ready()&&!armed_)adapter_error_="ACCEPTED_CALIBRATION_READY_EXPERIMENTAL_ONLY";
  }
 }
 HandlerScope scope{this,handler_current_,k,packet};handler_current_=&scope;
 try{fn(reader,context);}catch(...){handler_current_=scope.previous;std::lock_guard<std::recursive_mutex> l(mutex_);disarm("PACKET_HANDLER_EXCEPTION");throw;}
 handler_current_=scope.previous;
}
void* BridgeHost::selection(void* out,void* reader,FrameIdentity){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(recording_){++selection_seen_;last_path_stage_="SELECTION_DIAGNOSTIC";auto packet=resolve_reader_packet(reader);if(packet)++selection_resolved_;}
 return adapter_.selection(out,reader);
}
void BridgeHost::release_memory(void* ptr){
 {std::lock_guard<std::recursive_mutex> l(mutex_);auto p=reinterpret_cast<std::uintptr_t>(ptr);if(recording_){tracker_.release(p);
  for(auto it=units_.begin();it!=units_.end();){if(it->second.second==p){gate_.retire_unit(it->second.first);it=units_.erase(it);}else ++it;}}}
 // Do not keep our mutex locked while forwarding a process-wide allocator call.
 adapter_.free_memory(ptr);
}
#ifndef WH3_ALLOW_UNVALIDATED_NATIVE_ISSUE
#define WH3_ALLOW_UNVALIDATED_NATIVE_ISSUE 0
#endif
BridgeHost& host(){static BridgeHost h(platform_read,platform_image_base(),platform_write,platform_frame_active,WH3_ALLOW_UNVALIDATED_NATIVE_ISSUE!=0);return h;}
}
