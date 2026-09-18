#include "wh3/bridge_host.hpp"
#include <cstring>
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <set>
namespace wh3 {
thread_local BridgeHost::Scope* BridgeHost::current_=nullptr;
thread_local BridgeHost::HandlerScope* BridgeHost::handler_current_=nullptr;
BridgeHost::BridgeHost(MemoryReadFn r,std::uintptr_t b,MemoryWriteFn w,FrameActiveFn f,bool authorized,EntityAliveFn alive,CombatGroupQueryFn group_query):memory_(r),write_(w),frame_active_(f),base_(b),evidence_probe_(r,alive,group_query,b),native_issue_authorized_(authorized){}
bool BridgeHost::set_native_functions(NativeFunctions n){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(functions_locked_||recording_||!n.move||!n.attack||!n.allocate||!n.halt)return false;native_=n;return true;}
bool BridgeHost::set_adapter_functions(AdapterFunctions n){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(functions_locked_||recording_||!n.lua_move||!n.lua_attack||!n.publish_move||!n.publish_attack||!n.begin_writer||!n.finalize||!n.copy||!n.stage||!n.move_handler||!n.attack_handler||!n.selection||!n.free_memory||!write_)return false;
 adapter_=n;adapter_connected_=true;return true;}
bool BridgeHost::authorize_validated_issue(bool authorized){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(recording_||control_.active||publication_)return false;
 native_issue_authorized_=authorized;
 if(!authorized){armed_=false;gate_.set_issue_enabled(false);adapter_error_="V3_NATIVE_ISSUE_NOT_AUTHORIZED";}
 else adapter_error_="V3_RUNTIME_AUTHORIZED_WAITING_FOR_ACCEPTED_CALIBRATION";
 return true;}
NativeFunctions BridgeHost::native_functions()const{std::lock_guard<std::recursive_mutex> l(mutex_);return native_;}
Result<Id> BridgeHost::begin(const std::string& s){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(s.empty()||s.size()>64||s.find('\0')!=std::string::npos||recording_)return {{},Error::Invalid};
 if(control_.active||publication_)return {{},Error::Reentrant};
 for(auto* q=current_;q;q=q->previous)if(q->owner==this)return {{},Error::Reentrant};
 auto r=gate_.begin_battle();if(!r)return r;epoch_=r.value;session_=s;units_.clear();evidence_roots_.clear();evidence_uid_by_root_.clear();tracker_.clear();contacts_.clear();readers_.clear();accepted_evidence_.clear();evidence_probe_.clear();
 control_={};pending_by_uid_.clear();errors_=0;fatal_errors_=0;mapped_=unmapped_=0;move_seen_=attack_seen_=armed_=false;
 last_recoverable_uid_=0;last_recoverable_error_="NONE";last_fatal_error_="NONE";
 publish_seen_=publish_parsed_=publish_unparsed_=0;writer_begin_seen_=writer_finalize_seen_=writer_committed_=0;
 copy_seen_=stage_seen_=selection_seen_=selection_resolved_=0;handler_seen_=handler_resolved_=handler_missed_=handler_token_bindings_=0;handler_move_seen_count_=handler_attack_seen_count_=0;native_packet_seen_=native_packet_mapped_=native_attack_token_bindings_=0;
 last_issue_bindings_=last_issue_published_=last_issue_depth_=0;last_issue_error_.clear();
 last_reader_data_=last_reader_a_=last_reader_b_=last_reader_cursor_=last_reader_end_=0;
 last_reader_lineage_bytes_=last_reader_lineage_fragments_=0;
 handler_move_seen_=handler_attack_seen_=false;accepted_move_seen_=accepted_attack_seen_=false;recording_=true;adapter_error_=native_issue_authorized_?"V3_WAITING_FOR_ACCEPTED_CALIBRATION":"V3_NATIVE_ISSUE_NOT_AUTHORIZED";last_path_stage_="WAIT_PUBLISH";return r;}
Error BridgeHost::end(Id e){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(control_.active||publication_)return Error::Reentrant;
 for(auto* q=current_;q;q=q->previous)if(q->owner==this)return Error::Reentrant;
 auto r=gate_.end_battle(e);if(r==Error::Ok){recording_=armed_=false;tracker_.clear();readers_.clear();pending_by_uid_.clear();accepted_evidence_.clear();evidence_roots_.clear();evidence_uid_by_root_.clear();contacts_.clear();evidence_probe_.clear();}return r;}
bool BridgeHost::adapter_ready()const noexcept{return recording_&&adapter_connected_&&move_seen_&&attack_seen_&&!tracker_.faulted()&&fatal_errors_.load()==0;}
bool BridgeHost::handler_calibration_ready()const noexcept{return recording_&&adapter_connected_&&handler_move_seen_&&handler_attack_seen_&&fatal_errors_.load()==0;}
bool BridgeHost::v3_issue_calibration_ready()const noexcept{return native_issue_authorized_&&recording_&&adapter_connected_&&handler_seen_>0&&(accepted_move_seen_||accepted_attack_seen_)&&fatal_errors_.load()==0&&gate_.fault()==Error::Ok&&!tracker_.faulted();}
bool BridgeHost::issue_ready()const noexcept{return v3_issue_calibration_ready();}
HostStatus BridgeHost::status()const{std::lock_guard<std::recursive_mutex> l(mutex_);HostStatus s;
 s.epoch=epoch_;s.recording=recording_;s.capture_errors=errors_.load();s.fatal_errors=fatal_errors_.load();s.gate_fault=gate_.fault();
 s.last_recoverable_uid=last_recoverable_uid_;
 s.pending_count=pending_by_uid_.size();s.pending_limit=pending_limit_;
 s.native_identity_adapter_connected=adapter_connected_;
 // Path samples establish only the exercised mapping, NOT exhaustive native
 // lifecycle coverage. Never advertise production proof from these samples.
 s.physical_path_witnesses_ready=adapter_ready();
 s.handler_calibration_ready=handler_calibration_ready();
 s.native_issue_authorized=native_issue_authorized_;
 s.v3_issue_calibration_ready=v3_issue_calibration_ready();
 s.v3_issue_armed=armed_&&gate_.issue_enabled()&&issue_ready();
 s.experimental_calibration_ready=s.v3_issue_calibration_ready;
 s.experimental_issue_armed=s.v3_issue_armed;
 s.exact_source=false;s.verified_issue=native_issue_authorized_;
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
 s.adapter_error=adapter_error_;s.last_recoverable_error=last_recoverable_error_;s.last_fatal_error=last_fatal_error_;s.last_path_stage=last_path_stage_;return s;}
Result<Page> BridgeHost::read(Id e,Id a,std::size_t n){std::lock_guard<std::recursive_mutex> l(mutex_);return gate_.read(e,a,n);}
Error BridgeHost::acknowledge(Id e,Id a){std::lock_guard<std::recursive_mutex> l(mutex_);return gate_.acknowledge(e,a);}
Result<Snapshot> BridgeHost::unit_snapshot(Id u)const{std::lock_guard<std::recursive_mutex> l(mutex_);auto i=units_.find(u);if(i==units_.end())return {{},Error::Missing};return gate_.snapshot(i->second.first);}
Result<ExecutionEvidence> BridgeHost::execution_identity(Id uid){
 std::lock_guard<std::recursive_mutex> l(mutex_);ExecutionEvidence out;
 auto it=units_.find(uid);if(it==units_.end())return {out,Error::Missing};
 auto snap=gate_.snapshot(it->second.first);if(!snap)return {out,snap.error};out.unit=snap.value.unit;
 const auto root=it->second.second;auto active=evidence_probe_.active_order(root);
 if(!active.complete)return {out,Error::Invalid};out.complete=true;out.active=active.active;if(!active.active)return {out,Error::Ok};
 out.active_engine_seq=active.engine_seq;out.kind=active.kind;
 auto ai=accepted_evidence_.find({root,active.engine_seq});if(ai==accepted_evidence_.end())return {out,Error::Ok};
 const auto& r=ai->second;if(r.unit!=out.unit||r.kind!=active.kind)return {out,Error::Ok};
 out.known=true;out.accepted_serial=r.serial;out.target_uid=r.target_uid;out.dest_x=r.x;out.dest_z=r.z;return {out,Error::Ok};
}
Error BridgeHost::bind_evidence_root(Id uid,std::uintptr_t root){
 std::lock_guard<std::recursive_mutex> l(mutex_);if(!uid||!root)return Error::Invalid;
 // Physical evidence roots are accepted only after the entity container proves that
 // this is a BattleUnit-like object. A bad candidate must never replace a good root
 // or publish a new EntityOwnerIndex generation.
 const auto idx=evidence_probe_.entity_index(root);if(!idx.complete)return Error::Invalid;
 auto rev=evidence_uid_by_root_.find(root);if(rev!=evidence_uid_by_root_.end()&&rev->second!=uid)return Error::BindingMismatch;
 auto it=evidence_roots_.find(uid);
 if(it!=evidence_roots_.end()&&it->second==root){
  if(!contacts_.owner_ready(uid)&&!contacts_.bind_entities(uid,idx.entities))return Error::Capacity;
  evidence_uid_by_root_[root]=uid;return Error::Ok;
 }
 // ContactTracker validates the entire replacement before publishing a new owner
 // generation, so a failed rebind leaves the old mapping authoritative.
 if(!contacts_.bind_entities(uid,idx.entities))return Error::BindingMismatch;
 if(it!=evidence_roots_.end()){
  evidence_probe_.reset(it->second);evidence_uid_by_root_.erase(it->second);it->second=root;
 }else evidence_roots_.emplace(uid,root);
 evidence_uid_by_root_[root]=uid;return Error::Ok;
}
Result<std::uintptr_t> BridgeHost::evidence_root(Id uid) const{
 std::lock_guard<std::recursive_mutex> l(mutex_);auto it=evidence_roots_.find(uid);if(it==evidence_roots_.end()||!it->second)return {0,Error::Missing};return {it->second,Error::Ok};
}
bool BridgeHost::contact_owner_ready(Id uid) const{
 std::lock_guard<std::recursive_mutex> l(mutex_);return contacts_.owner_ready(uid);
}
Result<std::uintptr_t> BridgeHost::resolve_evidence_userdata(Id uid,std::uintptr_t userdata_block){
 std::lock_guard<std::recursive_mutex> l(mutex_);if(!uid||!userdata_block||!memory_)return {0,Error::Invalid};
 const auto plausible=[](std::uintptr_t p) noexcept{return p>=0x10000ULL&&p<=0x00007FFFFFFFFFFFULL;};
 std::vector<std::uintptr_t> level1,candidates,valid;
 auto add_unique=[](std::vector<std::uintptr_t>& v,std::uintptr_t p){if(!p)return;if(std::find(v.begin(),v.end(),p)==v.end())v.push_back(p);};
 // lua_touserdata() returns the Lua full-userdata payload address. CA interface
 // layouts are not assumed to equal that address: inspect the first three pointer
 // fields, then one additional wrapper indirection at +0x08/+0x10.
 for(const std::size_t off:{std::size_t(0),std::size_t(8),std::size_t(16)}){
  std::uintptr_t p=0;if(get(userdata_block,off,&p,sizeof p)&&plausible(p))add_unique(level1,p);
 }
 for(auto p:level1){
  add_unique(candidates,p);
  for(const std::size_t off:{std::size_t(8),std::size_t(16)}){
   std::uintptr_t q=0;if(get(p,off,&q,sizeof q)&&plausible(q))add_unique(candidates,q);
  }
 }
 for(auto p:candidates){const auto snap=evidence_probe_.entity_snapshot(p,0);evidence_probe_.reset(p);if(snap.complete)add_unique(valid,p);}
 if(valid.size()>1)return {0,Error::BindingMismatch};
 if(valid.empty()){
  // Preserve a previously proven physical root across a transient userdata read
  // failure, but only while that old root still validates structurally.
  auto old=evidence_roots_.find(uid);if(old!=evidence_roots_.end()&&evidence_probe_.entity_index(old->second).complete)return {old->second,Error::Ok};
  return {0,Error::Missing};
 }
 const auto e=bind_evidence_root(uid,valid.front());if(e!=Error::Ok)return {0,e};return {valid.front(),Error::Ok};
}
Result<EntitySnapshot> BridgeHost::entity_snapshot(Id uid,std::uint64_t model_ms){
 std::lock_guard<std::recursive_mutex> l(mutex_);EntitySnapshot out;auto it=evidence_roots_.find(uid);if(it==evidence_roots_.end())return {out,Error::Missing};
 out=evidence_probe_.entity_snapshot(it->second,model_ms);
 if(out.complete&&!contacts_.owner_ready(uid)){std::vector<std::uintptr_t> entities;entities.reserve(out.entities.size());for(const auto& e:out.entities)entities.push_back(e.entity);contacts_.bind_entities(uid,entities);}
 return {out,Error::Ok};
}
Result<CombatSnapshot> BridgeHost::combat_snapshot(Id uid){
 std::lock_guard<std::recursive_mutex> l(mutex_);CombatSnapshot out;auto it=evidence_roots_.find(uid);if(it==evidence_roots_.end())return {out,Error::Missing};
 out=evidence_probe_.combat_snapshot(it->second);if(!out.complete)return {out,Error::Ok};
 std::set<Id> targets;for(auto root:out.active_target_roots){auto ri=evidence_uid_by_root_.find(root);if(ri==evidence_uid_by_root_.end()){out.complete=false;out.probe_reason=CombatProbeReason::TargetUidRead;out.active_target_uids.clear();return {out,Error::Ok};}targets.insert(ri->second);}
 out.active_target_uids.assign(targets.begin(),targets.end());return {out,Error::Ok};
}
ContactPage BridgeHost::contact_events(std::uint64_t after,std::size_t max_count) const{return contacts_.read(after,max_count);}
void BridgeHost::observe_contact_pair(std::uintptr_t entity_a,std::uintptr_t entity_b,std::uint64_t tick_ms) noexcept{
 ContactOwnerView oa,ob;if(!contacts_.owner(entity_a,oa)||!contacts_.owner(entity_b,ob)||oa.uid==ob.uid)return;
 bool active_a=false,active_b=false;Id seq_a=0,seq_b=0;
 if(oa.command_root){const auto a=evidence_probe_.active_order(oa.command_root);active_a=a.complete&&a.active;if(active_a)seq_a=a.engine_seq;}
 if(ob.command_root){const auto b=evidence_probe_.active_order(ob.command_root);active_b=b.complete&&b.active;if(active_b)seq_b=b.engine_seq;}
 contacts_.record(entity_a,entity_b,active_a,seq_a,active_b,seq_b,tick_ms);
}
bool BridgeHost::get(std::uintptr_t p,std::size_t o,void* d,std::size_t n)const noexcept{return memory_&&p&&o<=UINTPTR_MAX-p&&n<=UINTPTR_MAX-(p+o)&&memory_(p+o,d,n);}
bool BridgeHost::put(std::uintptr_t p,std::size_t o,const void* d,std::size_t n)const noexcept{return write_&&p&&o<=UINTPTR_MAX-p&&n<=UINTPTR_MAX-(p+o)&&write_(p+o,d,n);}
bool BridgeHost::owned_in_flight()const noexcept{return control_.active||(publication_&&publication_->owned)||!pending_by_uid_.empty();}
void BridgeHost::note_capture(const char* reason,Id uid)noexcept{
 if(gate_.fault()!=Error::Ok||tracker_.faulted()||owned_in_flight()){disarm(reason);return;}
 ++errors_;last_recoverable_error_=reason;last_recoverable_uid_=uid;
}
void BridgeHost::disarm(const char* reason)noexcept{armed_=false;adapter_error_=reason;last_fatal_error_=reason;++fatal_errors_;try{gate_.set_issue_enabled(false);for(auto& kv:pending_by_uid_){kv.second->cancelled=true;gate_.cancel_issue(kv.second->issue);}}catch(...){} }
void BridgeHost::clear_command_evidence(std::uintptr_t root){
 for(auto i=accepted_evidence_.begin();i!=accepted_evidence_.end();){if(i->first.first==root)i=accepted_evidence_.erase(i);else ++i;}
}
void BridgeHost::clear_evidence_binding(Id uid){
 auto it=evidence_roots_.find(uid);if(it!=evidence_roots_.end()){evidence_probe_.reset(it->second);evidence_uid_by_root_.erase(it->second);evidence_roots_.erase(it);}
 contacts_.invalidate_entities(uid);
}
void BridgeHost::remember_accepted(const Order& o,std::uintptr_t root,const NativeOutcome& n,Id serial){
 if(!n.accepted||!n.engine_seq||!serial||!o.recipient.lifetime)return;AcceptedEvidence r;r.unit=o.recipient;r.root=root;r.kind=o.kind;r.engine_seq=*n.engine_seq;r.serial=serial;
 r.target_uid=o.target_uid;r.x=o.x;r.z=o.z;accepted_evidence_[{root,r.engine_seq}]=r;
}
Unit BridgeHost::track(Id uid,std::uintptr_t root){auto i=units_.find(uid);if(i!=units_.end()&&i->second.second==root){contacts_.bind_command_root(uid,root);return i->second.first;}
 if(i!=units_.end()){contacts_.bind_command_root(uid,0);clear_command_evidence(i->second.second);clear_evidence_binding(uid);gate_.retire_unit(i->second.first);units_.erase(i);}auto r=gate_.register_unit(uid,root);if(!r)throw std::runtime_error(name(r.error));units_.emplace(uid,std::make_pair(r.value,root));contacts_.bind_command_root(uid,root);return r.value;}
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
std::shared_ptr<TrackedPacket> BridgeHost::current_packet(bool* speculative_pending){
 if(speculative_pending)*speculative_pending=false;
 for(auto* h=handler_current_;h;h=h->previous)if(h->owner==this){if(speculative_pending)*speculative_pending=h->speculative_pending;return h->packet;}
 return {};
}
std::shared_ptr<TrackedPacket> BridgeHost::pending_candidate(const Order& o,std::uintptr_t root)const{
 auto it=pending_by_uid_.find(o.recipient.uid);if(it==pending_by_uid_.end())return {};
 const auto& p=it->second;
 if(!p||!p->owned||p->consumed||p->epoch!=epoch_||p->unit!=o.recipient||
    p->root!=root||p->kind!=o.kind||!o.queued||p->queued!=*o.queued)return {};
 if(o.kind==Kind::Attack){
  if(!p->attack_target_valid||o.target_root!=p->attack_target_root||o.target_uid!=p->attack_target_uid)return {};
 }else if(o.kind==Kind::Move&&p->move_destination){
  // Float32 Lua/native coordinates: compare with a bounded absolute tolerance.
  // This strengthens the build-verified V3 fallback but is not exact producer-source proof.
  if(!o.x||!o.y||!o.z)return {};
  const auto& d=*p->move_destination;
  if(std::fabs(*o.x-d[0])>0.05f||std::fabs(*o.y-d[1])>0.05f||std::fabs(*o.z-d[2])>0.05f)return {};
 }
 // Cancelled tokens MUST go through IdentityGate rejection, not fall through to native.
 return p;
}
void BridgeHost::retire_pending(const std::shared_ptr<TrackedPacket>& packet){
 auto it=pending_by_uid_.find(packet->unit.uid);
 if(it!=pending_by_uid_.end()&&it->second==packet)pending_by_uid_.erase(it);
}
std::uint32_t BridgeHost::order(Kind k,void* u,std::uint32_t a,void* payload,std::uint8_t q,InputSnapshot input){std::lock_guard<std::recursive_mutex> l(mutex_);functions_locked_=true;
 auto fn=k==Kind::Move?native_.move:native_.attack;if(!fn)throw std::logic_error("NATIVE_TRAMPOLINE_MISSING");
 for(auto* s=current_;s;s=s->previous)if(s->owner==this)s->nested_command=true;
 Scope f{this,current_,reinterpret_cast<std::uintptr_t>(u),epoch_,k,q};Order o;o.input=input;bool complete=false,capture_threw=false;
 if(recording_)try{complete=decode_order(o,f.root,k,payload,q);}catch(...){capture_threw=true;}
 bool speculative_pending=false;
 auto packet=recording_?current_packet(&speculative_pending):nullptr;
 if(capture_threw){if((packet&&packet->owned)||owned_in_flight())disarm("UNIT_OR_PAYLOAD_CAPTURE_FAILED");else note_capture("UNIT_OR_PAYLOAD_CAPTURE_FAILED",o.recipient.uid);}
 // Resolve the build-verified V3 recipient-token fallback ONLY at native entry, where recipient identity
 // is available. The handler is a scope witness, NOT an assignment to the first token.
 // A physical-lineage match, including a mismatched one, always takes precedence.
 if(recording_&&!packet&&native_issue_authorized_&&complete&&
    (speculative_pending||k==Kind::Attack)){
  packet=pending_candidate(o,f.root);
  if(packet){
   if(k==Kind::Attack)++native_attack_token_bindings_;else ++handler_token_bindings_;
   last_path_stage_=k==Kind::Attack?"ATTACK_NATIVE_PENDING_TOKEN":"MOVE_NATIVE_RECIPIENT_TOKEN";
  }else if(speculative_pending){++handler_missed_;last_path_stage_="HANDLER_PENDING_RECIPIENT_MISS";}
 }
 if(packet){++native_packet_seen_;if(last_path_stage_!=std::string("ATTACK_NATIVE_PENDING_TOKEN"))last_path_stage_="NATIVE_PACKET_PRESENT";}
 if(packet&&packet->owned&&packet->kind!=k){disarm("OWNED_KIND_MISMATCH");return 0;}
 std::uint32_t result=0;NativeOutcome n;
 auto original=[&](){current_=&f;try{result=fn(u,a,payload,q);}catch(...){current_=f.previous;disarm("NATIVE_EXCEPTION");throw;}current_=f.previous;n=outcome(f,result,o,complete);return n;};
 if(!recording_){original();return result;}
 if(packet&&packet->owned){
  if(!complete||packet->root!=f.root){disarm("OWNED_RECIPIENT_NOT_VERIFIED");return 0;}
  auto d=gate_.dispatch_owned(packet->key,o,original);packet->consumed=true;++mapped_;++native_packet_mapped_;last_path_stage_="OWNED_NATIVE_PACKET_MAPPED";
  if(d.native_outcome&&d.native_outcome->accepted){if(k==Kind::Move)accepted_move_seen_=true;else if(k==Kind::Attack)accepted_attack_seen_=true;remember_accepted(o,f.root,*d.native_outcome,d.serial);}
  retire_pending(packet);
  gate_.retire_stream(packet->stream);
  if(!d.native_called)return 0;
  if(!complete||d.status==Status::Indeterminate)disarm("OWNED_OUTCOME_INDETERMINATE");return result;
 }
 original();
 if(n.accepted){if(k==Kind::Move)accepted_move_seen_=true;else if(k==Kind::Attack)accepted_attack_seen_=true;
  if(v3_issue_calibration_ready()&&!armed_)adapter_error_="V3_ACCEPTED_KIND_CALIBRATION_READY";}
 try{
  if(!o.recipient.lifetime){Id uid=0;if(!get(f.root,0x3ea0,&uid,4)){note_capture("EXTERNAL_UID_UNREADABLE");return result;}o.recipient=track(uid,f.root);o.kind=k;o.queued=q!=0;}
  auto e=complete?gate_.observe_external(o,n):gate_.observe_external_partial(o,n);
  if(e&&n.accepted)remember_accepted(o,f.root,n,e.value.serial);
  if(!complete||!e){if(gate_.fault()==Error::Ok)note_capture("EXTERNAL_OUTCOME_PARTIAL",o.recipient.uid);else disarm("EXTERNAL_OUTCOME_PARTIAL");}
  if(packet&&packet->kind==k&&n.accepted){++mapped_;++native_packet_mapped_;last_path_stage_="EXTERNAL_NATIVE_PACKET_MAPPED";if(k==Kind::Move)move_seen_=true;else attack_seen_=true;}
  else {++unmapped_;last_path_stage_="NATIVE_UNMAPPED";}
 }catch(...){if(gate_.fault()==Error::Ok)note_capture("EXTERNAL_OBSERVER_EXCEPTION",o.recipient.uid);else disarm("EXTERNAL_OBSERVER_EXCEPTION");}
 return result;
}
void* BridgeHost::allocate(void* p,std::uint32_t q){std::lock_guard<std::recursive_mutex> l(mutex_);functions_locked_=true;
 if(!native_.allocate)throw std::logic_error("ALLOCATOR_TRAMPOLINE_MISSING");void* r=native_.allocate(p,q);
 auto* f=current_;if(f&&f->owner==this&&reinterpret_cast<std::uintptr_t>(p)==f->root+0x278){++f->allocations;f->slot=reinterpret_cast<std::uintptr_t>(r);f->queue_mismatch|=static_cast<std::uint8_t>(q)!=f->queued;}return r;}
void BridgeHost::halt(void* u,std::uint32_t flags){std::lock_guard<std::recursive_mutex> l(mutex_);functions_locked_=true;
 if(!native_.halt)throw std::logic_error("HALT_TRAMPOLINE_MISSING");native_.halt(u,flags);if(!recording_)return;
 try{Id uid=0;auto root=reinterpret_cast<std::uintptr_t>(u);if(!get(root,0x3ea0,&uid,4)){note_capture("HALT_UID_UNREADABLE");return;}
  Order o;o.kind=Kind::Halt;o.recipient=track(uid,root);o.halt_flags=static_cast<std::uint8_t>(flags);if(!gate_.observe_external(o,{true,{}})){if(gate_.fault()==Error::Ok)note_capture("HALT_RECORD_FAILED",uid);else disarm("HALT_RECORD_FAILED");}
 }catch(...){if(gate_.fault()==Error::Ok)note_capture("HALT_OBSERVER_EXCEPTION");else disarm("HALT_OBSERVER_EXCEPTION");}}
const char* BridgeHost::arm(bool ack){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(!ack){armed_=false;gate_.set_issue_enabled(false);return nullptr;}
 if(!native_issue_authorized_)return "V3_NATIVE_ISSUE_NOT_AUTHORIZED";
 if(!v3_issue_calibration_ready())return "V3_CALIBRATION_NOT_READY";
 if(gate_.set_issue_enabled(true)!=Error::Ok)return "GATE_FAULT";armed_=true;adapter_error_="ARMED_V3_VALIDATED_PER_KIND_CALIBRATION";return nullptr;}
IssueResult BridgeHost::begin_issue(Kind k,bool q,Id uid,Id rev,void* L,std::optional<std::array<float,3>> move_destination){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(!armed_||!issue_ready())return {0,"ADAPTER_NOT_READY"};
 if(native_issue_authorized_){
  if(k==Kind::Move&&!accepted_move_seen_)return {0,"MOVE_CALIBRATION_NOT_READY"};
  if(k==Kind::Attack&&!accepted_attack_seen_)return {0,"ATTACK_CALIBRATION_NOT_READY"};
 }
 if(control_.active||pending_by_uid_.count(uid))return {0,"ISSUE_ALREADY_PENDING"};
 if(pending_by_uid_.size()>=pending_limit_)return {0,"ISSUE_CAPACITY"};
 if(move_destination){if(k!=Kind::Move)return {0,"MOVE_DESTINATION_KIND_MISMATCH"};
  for(float v:*move_destination)if(!std::isfinite(v))return {0,"MOVE_DESTINATION_INVALID"};}
 auto it=units_.find(uid);if(it==units_.end())return {0,"UNIT_NOT_OBSERVED"};auto s=gate_.snapshot(it->second.first);
 if(!s||s.value.revision!=rev)return {0,"REJECTED_STALE"};auto issue=gate_.make_issue(k,q,{s.value});if(!issue)return {0,name(issue.error)};
 control_={};control_.active=true;control_.thread=std::this_thread::get_id();control_.lua_state=L;control_.issue=issue.value;
 control_.move_destination=move_destination;
 control_.snapshot=s.value;control_.kind=k;control_.queued=q;control_.root=it->second.second;return {issue.value.id,nullptr};}
Error BridgeHost::cancel_pending_issue(Id issue_id){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(!recording_)return Error::Inactive;
 for(auto it=pending_by_uid_.begin();it!=pending_by_uid_.end();++it){
  auto packet=it->second;if(!packet||packet->issue.id!=issue_id)continue;
  packet->cancelled=true;auto r=gate_.cancel_issue(packet->issue);
  if(r!=Error::Ok&&r!=Error::Missing)return r;
  pending_by_uid_.erase(it);return Error::Ok;
 }
 return Error::Missing;
}
IssueResult BridgeHost::finish_issue(bool ok){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(!control_.active||control_.thread!=std::this_thread::get_id())return {0,"NO_ACTIVE_ISSUE"};
 Id id=control_.issue.id;const char* error=control_.error;
 last_issue_bindings_=control_.bindings;last_issue_published_=control_.published;last_issue_depth_=control_.depth;
 if(!ok)error="LUA_CALLBACK_FAILED";
 else if(!error){
  const bool single_publish=control_.published==1;
  const bool binding_ok=native_issue_authorized_?control_.bindings<=1:control_.bindings==1;
  if(!single_publish||!binding_ok){
   last_issue_error_="ONE_NATIVE_COMMAND_REQUIRED bindings="+std::to_string(control_.bindings)+
     " published="+std::to_string(control_.published)+" depth="+std::to_string(control_.depth);
   error=last_issue_error_.c_str();
  }
 }
 if(error){gate_.cancel_issue(control_.issue);for(auto& kv:pending_by_uid_)if(kv.second->issue.id==id)kv.second->cancelled=true;}
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
 const bool owned=strict_owned||(native_issue_authorized_&&callback_scope);
 bool q=false;Unit unit{};std::uintptr_t root=0;bool parsed=false;
 if(recording_){++publish_seen_;last_path_stage_="PUBLISH_SEEN";try{parsed=single_recipient(cmd,k,q,unit,root);}catch(...){if(owned_in_flight())disarm("PUBLISH_CAPTURE_FAILED");else note_capture("PUBLISH_CAPTURE_FAILED");}}
 if(parsed){++publish_parsed_;last_path_stage_="PUBLISH_METADATA_PARSED";}else if(recording_){++publish_unparsed_;last_path_stage_="PUBLISH_UNPARSED_PHYSICAL_TRACKING";}
 if(owned){
  if(k!=control_.kind||control_.published){control_.error="PUBLISH_METADATA_MISMATCH";return 0;}
  if(parsed){if(q!=control_.queued||unit!=control_.snapshot.unit||root!=control_.root){control_.error="PUBLISH_METADATA_MISMATCH";return 0;}}
  else if(native_issue_authorized_){
   // Build-verified V3 callback-scope fallback. The Lua callback is synchronous,
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
  if(!get(b,0x5000,&start,4)||start>0x5000)note_capture("WRITER_CURSOR_INVALID");
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
   if(packet->owned){packet->move_destination=control_.move_destination;packet->expected_revision=control_.snapshot.revision;packet->attack_target_valid=control_.attack_target_valid;packet->attack_target_root=control_.attack_target_root;packet->attack_target_uid=control_.attack_target_uid;}
   if(packet->owned){auto stream=gate_.open_stream(b+start,end-start);if(!stream)throw std::runtime_error("stream capacity");packet->stream=stream.value;
    auto own=gate_.own_scope(packet->issue);auto key=gate_.commit_packet(packet->stream,0,end-start,packet->kind,packet->queued,{packet->unit});if(!key)throw std::runtime_error("metadata commit");packet->key=key.value;}
   if(!tracker_.put(b,b+start,end-start,packet))throw std::runtime_error("physical capacity");
   ++writer_committed_;last_path_stage_="WRITER_PACKET_COMMITTED";
  }catch(...){packet.reset();if(publication_&&publication_->owned)disarm("PROVENANCE_COMMIT_FAILED");else note_capture("PROVENANCE_COMMIT_FAILED",publication_?publication_->unit.uid:0);}
 }
 if(active&&publication_->owned&&!packet){std::uint8_t abort=1;if(!put(w,1,&abort,1))disarm("ABORT_FLAG_WRITE_FAILED_INDETERMINATE");control_.error="PACKET_NOT_COMMITTED";}
 if(packet&&packet->owned){
  if(pending_by_uid_.count(packet->unit.uid)||pending_by_uid_.size()>=pending_limit_){
   packet->cancelled=true;gate_.cancel_issue(packet->issue);disarm("PENDING_TOKEN_COLLISION");
   std::uint8_t abort=1;if(!put(w,1,&abort,1))disarm("ABORT_FLAG_WRITE_FAILED_INDETERMINATE");
   control_.error="PENDING_TOKEN_COLLISION";
  }else pending_by_uid_.emplace(packet->unit.uid,packet);
 }
 adapter_.finalize(writer);
}
void BridgeHost::copy_buffer(void* dest,void* source){std::lock_guard<std::recursive_mutex> l(mutex_);auto d=reinterpret_cast<std::uintptr_t>(dest),s=reinterpret_cast<std::uintptr_t>(source);Id n=0;std::uintptr_t old=0;
 if(recording_){++copy_seen_;last_path_stage_="BUFFER_COPY";get(d,8,&old,8);}
 bool good=get(s,0x5000,&n,4)&&n<=0x5000;adapter_.copy(dest,source);
 if(recording_&&good&&n){
  std::uintptr_t p=0;if(!get(d,8,&p,8)){note_capture("COPY_DEST_UNREADABLE");return;}
  // Reallocation retires the old allocation. In-place copies are invalidated only
  // for the exact copied range by PacketTracker::copy(), never wholesale first.
  if(old&&old!=p)tracker_.release(old);
  if(!tracker_.copy(p,p,s,n))note_capture("COPY_MAPPING_FAILED");
 }
}
std::uint32_t BridgeHost::stage_buffer(void* dst,std::uint32_t a,void* source,float f){std::lock_guard<std::recursive_mutex> l(mutex_);auto d=reinterpret_cast<std::uintptr_t>(dst),s=reinterpret_cast<std::uintptr_t>(source);Id old=0,n=0;
 if(recording_){++stage_seen_;last_path_stage_="STAGE_COPY";}
 bool good=get(d,0x5024,&old,4)&&get(s,0x5000,&n,4)&&old==0&&n>0&&n<=0x5000;
 auto r=adapter_.stage(dst,a,source,f);
 if(recording_&&good&&(r&0xffU)){auto p=d+0x20;if(!tracker_.copy(d,p,s,n))note_capture("STAGE_COPY_MAPPING_FAILED");}return r;
}
void BridgeHost::packet_handler(Kind k,void* reader,void* context){
 NativePacketHandlerFn fn=k==Kind::Move?adapter_.move_handler:adapter_.attack_handler;std::shared_ptr<TrackedPacket> packet;bool speculative_pending=false;
 {std::lock_guard<std::recursive_mutex> l(mutex_);functions_locked_=true;
  if(recording_){++handler_seen_;if(k==Kind::Move){handler_move_seen_=true;++handler_move_seen_count_;}else if(k==Kind::Attack){handler_attack_seen_=true;++handler_attack_seen_count_;}
   last_path_stage_=k==Kind::Move?"MOVE_HANDLER_ENTER":"ATTACK_HANDLER_ENTER";packet=resolve_reader_packet(reader);
   if(packet&&packet->kind==k){++handler_resolved_;last_path_stage_=k==Kind::Move?"MOVE_HANDLER_PACKET_RESOLVED":"ATTACK_HANDLER_PACKET_RESOLVED";}
   else if(packet){if(packet->owned)disarm("HANDLER_KIND_MISMATCH");packet.reset();++handler_missed_;last_path_stage_="HANDLER_EXACT_MISS";}
   else if(native_issue_authorized_&&!pending_by_uid_.empty()){
    speculative_pending=true;last_path_stage_="HANDLER_WAIT_RECIPIENT_IDENTITY";
   } else {++handler_missed_;last_path_stage_="HANDLER_EXACT_MISS";}
   if(native_issue_authorized_&&v3_issue_calibration_ready()&&!armed_)adapter_error_="V3_ACCEPTED_KIND_CALIBRATION_READY";
  }
 }
 HandlerScope scope{this,handler_current_,k,packet,speculative_pending};handler_current_=&scope;
 try{fn(reader,context);}catch(...){handler_current_=scope.previous;std::lock_guard<std::recursive_mutex> l(mutex_);disarm("PACKET_HANDLER_EXCEPTION");throw;}
 handler_current_=scope.previous;
}
void* BridgeHost::selection(void* out,void* reader,FrameIdentity){std::lock_guard<std::recursive_mutex> l(mutex_);
 if(recording_){++selection_seen_;last_path_stage_="SELECTION_DIAGNOSTIC";auto packet=resolve_reader_packet(reader);if(packet)++selection_resolved_;}
 return adapter_.selection(out,reader);
}
void BridgeHost::release_memory(void* ptr){
 {std::lock_guard<std::recursive_mutex> l(mutex_);auto p=reinterpret_cast<std::uintptr_t>(ptr);if(recording_){tracker_.release(p);
  for(auto it=units_.begin();it!=units_.end();){if(it->second.second==p){const auto uid=it->first;contacts_.bind_command_root(uid,0);clear_command_evidence(p);clear_evidence_binding(uid);gate_.retire_unit(it->second.first);it=units_.erase(it);}else ++it;}}}
 // Do not keep our mutex locked while forwarding a process-wide allocator call.
 adapter_.free_memory(ptr);
}
BridgeHost& host(){static BridgeHost h(platform_read,platform_image_base(),platform_write,platform_frame_active,false,platform_entity_alive,platform_combat_group_query);return h;}
}
