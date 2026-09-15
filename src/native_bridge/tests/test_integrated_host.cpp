// Executes the actual production BridgeHost entry methods, with explicitly
// synthetic native callbacks and a frame-activation oracle. It is not WH3.
#include "wh3/bridge_host.hpp"
#include <iostream>
#include <cstring>
#include <vector>
#include <map>
#include <stdexcept>
using namespace wh3;
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)
namespace {
std::map<std::uintptr_t,std::vector<unsigned char>> memory;
constexpr std::uintptr_t U=0x100000,T=0x200000,T2=0x210000,P=0x300000,C=0x400000,A=0x500000,W=0x600000,B=0x700000,V=0x800000,D=0x900000,R=0xa00000,ST=0xb00000;
BridgeHost* h=nullptr;Kind current=Kind::Move;bool queued=false,frame=false;bool call_selection=true,release_in_handler=false;int native_calls=0;Id seq=0;bool reject_publish=false;void* L=reinterpret_cast<void*>(0x1111);
bool rd(std::uintptr_t p,void* out,std::size_t n)noexcept{for(auto& kv:memory)if(p>=kv.first&&p-kv.first<=kv.second.size()&&n<=kv.second.size()-(p-kv.first)){std::memcpy(out,kv.second.data()+p-kv.first,n);return true;}return false;}
bool wr(std::uintptr_t p,const void* in,std::size_t n)noexcept{for(auto& kv:memory)if(p>=kv.first&&p-kv.first<=kv.second.size()&&n<=kv.second.size()-(p-kv.first)){std::memcpy(kv.second.data()+p-kv.first,in,n);return true;}return false;}
template<class Q>void set(std::uintptr_t a,Q q){CK(wr(a,&q,sizeof q));}
template<class Q>Q get(std::uintptr_t a){Q q{};CK(rd(a,&q,sizeof q));return q;}
bool active(const FrameIdentity& f)noexcept{return frame&&f.function==1&&f.establisher==2&&f.return_pc==3;}
void* allocator(void*,std::uint32_t){return reinterpret_cast<void*>(U+0x288);}
std::uint32_t native_order(void* unit,std::uint32_t,void* p,std::uint8_t q){++native_calls;auto u=reinterpret_cast<std::uintptr_t>(unit);CK(u==U);h->allocate(reinterpret_cast<void*>(U+0x278),q);
 set(U+0x288+0x18,std::uint64_t(0x140000000ULL+(current==Kind::Move?0x37b31c8:0x37b2540)));set(U+0x288+0x20,seq++);
 if(current==Kind::Move){float xyz[3];CK(rd(reinterpret_cast<std::uintptr_t>(p),xyz,12));CK(wr(U+0x288+0x58,xyz,12));}
 else{std::uintptr_t target=0;CK(rd(reinterpret_cast<std::uintptr_t>(p),&target,8));set(U+0x288+0x58,std::uint64_t(target));}return 1;}
void halt(void*,std::uint32_t){++native_calls;}
void* begin_writer(void*,void* b,void*,std::uint32_t){auto buf=reinterpret_cast<std::uintptr_t>(b);set(W,std::uint16_t(0));set(W+8,buf);auto start=get<Id>(buf+0x5000);set(W+0x10,start);set(W+0x14,start);set(buf+0x5000,start+7);return reinterpret_cast<void*>(W);}
void finalize(void*){auto buf=get<std::uintptr_t>(W+8);auto start=get<Id>(W+0x10);if(get<std::uint16_t>(W))set(buf+0x5000,start);else set(buf+start,std::uint16_t(get<Id>(buf+0x5000)-start));}
std::uint32_t publisher(void*,void*){h->writer_begin(reinterpret_cast<void*>(W),reinterpret_cast<void*>(B),nullptr,0);set(B+0x5000,get<Id>(B+0x5000)+20);if(reject_publish)set(W+1,std::uint8_t(1));h->writer_finalize(reinterpret_cast<void*>(W));return get<std::uint16_t>(W)?0:1;}
void copy(void* dst,void* source){auto n=get<Id>(reinterpret_cast<std::uintptr_t>(source)+0x5000);std::vector<unsigned char> data(n);CK(rd(reinterpret_cast<std::uintptr_t>(source),data.data(),n));CK(wr(D,data.data(),n));set(reinterpret_cast<std::uintptr_t>(dst)+8,std::uintptr_t(D));}
std::uint32_t stage(void* dst,std::uint32_t,void* source,float){auto d=reinterpret_cast<std::uintptr_t>(dst),s=reinterpret_cast<std::uintptr_t>(source);auto n=get<Id>(s+0x5000);std::vector<unsigned char> data(n);CK(rd(s,data.data(),n));CK(wr(d+0x20,data.data(),n));set(d+0x5020,n);set(d+0x5024,Id(1));return 1;}
void* select(void* out,void*){return out;}
void free_memory(void*){}
void packet_common(Kind k,void* reader){
 if(call_selection)h->selection(nullptr,reader,{1,2,3});
 if(release_in_handler)h->release_memory(reinterpret_cast<void*>(D));
 h->order(k,reinterpret_cast<void*>(U),0,reinterpret_cast<void*>(P),queued?1:0);
}
void move_handler(void* reader,void*){packet_common(Kind::Move,reader);}
void attack_handler(void* reader,void*){packet_common(Kind::Attack,reader);}
int binding(void*,void* state,std::uint8_t q){CK(state==L);queued=q!=0;h->publish(current,nullptr,reinterpret_cast<void*>(C));return 0;}
void descriptor(){// Actual 0x142C68624 shared-selection layout: cmd+0x10=count, +0x14=capacity, +0x18=array.
 set(C+0x10,Id(1));set(C+0x14,Id(1));set(C+0x18,std::uintptr_t(A));set(A,std::uintptr_t(U));set(C+(current==Kind::Move?0xa8:0x99),std::uint8_t(queued));
 if(current==Kind::Move){set(P,1.5f);set(P+4,2.0f);set(P+8,3.5f);}else{set(P,std::uintptr_t(T));set(P+0x18,std::uint8_t(1));set(C+0x88,std::uintptr_t(T));}}
struct Fixture{BridgeHost host;Id epoch;
 Fixture(bool allow=true):host(rd,0x140000000ULL,wr,active,allow){memory.clear();for(auto a:{U,T,T2,P,C,A,W,B,V,D,R,ST})memory[a]=std::vector<unsigned char>(0x7000);h=&host;frame=false;call_selection=true;release_in_handler=false;current=Kind::Move;queued=false;native_calls=0;seq=0;reject_publish=false;
 set(U+0x3ea0,Id(1002));set(T+0x3ea0,Id(1008));set(T2+0x3ea0,Id(1009));set(V+8,std::uintptr_t(D));
 CK(host.set_native_functions({native_order,native_order,allocator,halt}));CK(host.set_adapter_functions({binding,binding,publisher,publisher,begin_writer,finalize,copy,stage,move_handler,attack_handler,select,free_memory}));auto e=host.begin("integrated_fixture");CK(e);epoch=e.value;}
 void publish_external(Kind k){current=k;queued=false;descriptor();set(B+0x5000,Id(0));host.publish(k,nullptr,reinterpret_cast<void*>(C));}
 void consume(bool through_stage=false,bool swapped_bounds=false,bool release_after_resolution=false,bool no_selection=false,bool detached_reader=false){
  auto n=get<Id>(B+0x5000);
  if(through_stage){set(ST+0x5024,Id(0));host.stage_buffer(reinterpret_cast<void*>(ST),0,reinterpret_cast<void*>(B),1.0f);host.copy_buffer(reinterpret_cast<void*>(V),reinterpret_cast<void*>(ST+0x20));}
  else host.copy_buffer(reinterpret_cast<void*>(V),reinterpret_cast<void*>(B));
  set(R+8,std::uint8_t(0));set(R+0x10,std::uintptr_t(detached_reader?R+0x1000:D));
  // The primitive reader proves only that (+0x18 + +0x1C) is the absolute end.
  // HandlerScope resolution accepts either structural orientation, but only if
  // exactly one tracked physical span matches the resulting interval.
  set(R+0x18,swapped_bounds?Id(0):n);set(R+0x1c,swapped_bounds?n:Id(0));set(R+0x20,Id(7));
  call_selection=!no_selection;release_in_handler=release_after_resolution;frame=true;
  host.packet_handler(current,reinterpret_cast<void*>(R),nullptr);
  frame=false;call_selection=true;release_in_handler=false;
 }
 void calibrate(){publish_external(Kind::Move);consume();publish_external(Kind::Attack);consume(true);CK(host.status().physical_path_witnesses_ready);CK(host.arm(true)==nullptr);}
 void calibrate_handlers_only(){publish_external(Kind::Move);consume(false,false,false,false,true);publish_external(Kind::Attack);consume(false,false,false,false,true);auto st=host.status();CK(!st.physical_path_witnesses_ready&&st.handler_calibration_ready);CK(host.arm(true)==nullptr);}
 void direct_external(Kind k){current=k;queued=false;descriptor();host.order(k,reinterpret_cast<void*>(U),0,reinterpret_cast<void*>(P),0);}
 void detached_handler(Kind k){current=k;queued=false;descriptor();set(R+8,std::uint8_t(0));set(R+0x10,std::uintptr_t(R+0x1000));set(R+0x18,Id(83));set(R+0x1c,Id(0));set(R+0x20,Id(7));frame=true;host.packet_handler(k,reinterpret_cast<void*>(R),nullptr);frame=false;}
 void calibrate_runtime_shape(){detached_handler(Kind::Move);direct_external(Kind::Attack);detached_handler(Kind::Move);auto st=host.status();CK(st.handler_seen==2&&st.handler_move_seen==2&&st.handler_attack_seen==0);CK(st.accepted_move_seen&&st.accepted_attack_seen&&st.experimental_calibration_ready&&!st.handler_calibration_ready&&!st.physical_path_witnesses_ready);CK(host.arm(true)==nullptr);}
 IssueResult issue(Kind k=Kind::Move){current=k;queued=false;descriptor();set(B+0x5000,Id(0));auto s=host.unit_snapshot(1002);CK(s);auto r=host.begin_issue(k,false,1002,s.value.revision,L);if(!r)return r;host.binding(k,nullptr,L,0);return host.finish_issue(true);}
 IssueResult issue_publish_only(Kind k=Kind::Move){current=k;queued=false;descriptor();set(B+0x5000,Id(0));auto s=host.unit_snapshot(1002);CK(s);auto r=host.begin_issue(k,false,1002,s.value.revision,L);if(!r)return r;host.publish(k,nullptr,reinterpret_cast<void*>(C));return host.finish_issue(true);}
 Page events(){auto p=host.read(epoch,0,64);CK(p);return p.value;}
};
}
int main(){int pass=0,fail=0;auto test=[&](const char* name,auto fn){try{fn();++pass;std::cout<<"PASS "<<name<<'\n';}catch(const std::exception& e){++fail;std::cout<<"FAIL "<<name<<" "<<e.what()<<'\n';}};
 test("uncalibrated issue refuses before callback",[]{Fixture f;auto r=f.host.begin_issue(Kind::Move,false,1002,0,L);CK(!r&&native_calls==0);});
 test("real command selection layout is parsed, legacy fabricated offsets ignored",[]{Fixture f;current=Kind::Move;queued=true;f.publish_external(Kind::Move);f.consume();auto st=f.host.status();CK(st.publish_parsed==1&&st.publish_unparsed==0&&st.move_path_observed);});
 test("reader field orientation is irrelevant when exact physical interval agrees",[]{Fixture f;current=Kind::Move;queued=false;f.publish_external(Kind::Move);f.consume(false,true);auto st=f.host.status();CK(st.handler_seen==1&&st.handler_resolved==1&&st.native_packet_mapped==1&&st.move_path_observed);});
 test("resolved handler witness survives backing-span reclamation until handler returns",[]{Fixture f;current=Kind::Move;queued=false;f.publish_external(Kind::Move);f.consume(false,false,true);auto st=f.host.status();CK(st.handler_resolved==1&&st.native_packet_seen==1&&st.native_packet_mapped==1&&st.move_path_observed);});
 test("selection parser is diagnostic only and may be absent",[]{Fixture f;current=Kind::Move;queued=false;f.publish_external(Kind::Move);f.consume(false,false,false,true);auto st=f.host.status();CK(st.selection_seen==0&&st.handler_resolved==1&&st.native_packet_seen==1&&st.native_packet_mapped==1&&st.move_path_observed);});
 test("later writer begin does not erase unrelated live packet span",[]{Fixture f;current=Kind::Move;queued=false;f.publish_external(Kind::Move);auto before=f.host.status().spans;CK(before==1);set(B+0x5000,Id(64));f.host.writer_begin(reinterpret_cast<void*>(W),reinterpret_cast<void*>(B),nullptr,0);CK(f.host.status().spans==before);});
 test("external physical calibration survives metadata parse failure without becoming owned",[]{Fixture f;current=Kind::Move;queued=false;descriptor();set(C+0x10,Id(2));set(B+0x5000,Id(0));f.host.publish(Kind::Move,nullptr,reinterpret_cast<void*>(C));f.consume();auto st=f.host.status();CK(st.publish_unparsed==1&&st.move_path_observed&&st.native_packet_mapped==1);auto e=f.events().events.back();CK(e.source==Source::Unknown);});
 test("two exact physical path witnesses arm only after explicit acknowledgement",[]{Fixture f;f.publish_external(Kind::Move);f.consume();CK(!f.host.status().physical_path_witnesses_ready);f.publish_external(Kind::Attack);f.consume(true);CK(f.host.status().physical_path_witnesses_ready&&!f.host.status().verified_issue);CK(f.host.arm(true)==nullptr);});
 test("default production policy cannot be armed by path samples alone",[]{Fixture f(false);f.publish_external(Kind::Move);f.consume();f.publish_external(Kind::Attack);f.consume();CK(std::string(f.host.arm(true))=="NATIVE_RELEASE_NOT_APPROVED");CK(!f.host.status().verified_issue&&!f.host.status().exact_source);});
 test("experimental accepted calibration arms with both accepted kinds plus any handler",[]{Fixture f;f.calibrate_runtime_shape();auto st=f.host.status();CK(st.experimental_issue_armed&&st.experimental_calibration_ready&&!st.physical_path_witnesses_ready&&!st.handler_calibration_ready&&st.handler_move_seen==2&&st.handler_attack_seen==0);});
 test("accepted Move alone arms Move but not Attack",[]{
  Fixture f;f.detached_handler(Kind::Move);auto st=f.host.status();
  CK(st.accepted_move_seen&&!st.accepted_attack_seen&&st.experimental_calibration_ready);CK(f.host.arm(true)==nullptr);
  auto snap=f.host.unit_snapshot(1002);CK(snap);
  auto a=f.host.begin_issue(Kind::Attack,false,1002,snap.value.revision,L);CK(!a&&std::string(a.error)=="ATTACK_CALIBRATION_NOT_READY");
  CK(f.issue(Kind::Move));
 });
 test("accepted Attack alone arms Attack but not Move",[]{
  Fixture f;f.detached_handler(Kind::Attack);auto st=f.host.status();
  CK(!st.accepted_move_seen&&st.accepted_attack_seen&&st.experimental_calibration_ready);CK(f.host.arm(true)==nullptr);
  auto snap=f.host.unit_snapshot(1002);CK(snap);
  auto m=f.host.begin_issue(Kind::Move,false,1002,snap.value.revision,L);CK(!m&&std::string(m.error)=="MOVE_CALIBRATION_NOT_READY");
  CK(f.issue(Kind::Attack));
 });
 test("accepted Move and Attack without any handler cannot arm",[]{Fixture f;f.direct_external(Kind::Move);f.direct_external(Kind::Attack);auto st=f.host.status();CK(st.accepted_move_seen&&st.accepted_attack_seen&&st.handler_seen==0&&!st.experimental_calibration_ready);CK(std::string(f.host.arm(true))=="EXPERIMENTAL_CALIBRATION_NOT_READY");});
 test("callback-scope publish succeeds experimentally without Lua binding hook",[]{Fixture f;f.calibrate_runtime_shape();auto i=f.issue_publish_only();CK(i);auto st=f.host.status();CK(st.last_issue_bindings==0&&st.last_issue_published==1&&st.last_issue_depth==0);f.consume(false,false,false,false,true);auto e=f.events().events.back();CK(e.source==Source::OurController&&e.script_issue_id==i.id);});
 test("callback-scope still rejects a second native publish",[]{Fixture f;f.calibrate_runtime_shape();current=Kind::Move;queued=false;descriptor();set(B+0x5000,Id(0));auto s=f.host.unit_snapshot(1002);CK(s);auto b=f.host.begin_issue(Kind::Move,false,1002,s.value.revision,L);CK(b);CK(f.host.publish(Kind::Move,nullptr,reinterpret_cast<void*>(C))!=0);CK(f.host.publish(Kind::Move,nullptr,reinterpret_cast<void*>(C))==0);auto fin=f.host.finish_issue(true);CK(!fin&&std::string(fin.error)=="PUBLISH_METADATA_MISMATCH");});
 test("pending controller token binds at handler when physical reader is detached",[]{Fixture f;f.calibrate_handlers_only();auto i=f.issue();CK(i);f.consume(false,false,false,false,true);auto e=f.events().events.back();auto st=f.host.status();CK(e.source==Source::OurController&&e.script_issue_id==i.id&&st.handler_token_bindings==1&&st.native_packet_mapped==1);});
 test("external command after fallback-consumed token stays UNKNOWN",[]{Fixture f;f.calibrate_handlers_only();auto i=f.issue();CK(i);f.consume(false,false,false,false,true);current=Kind::Move;queued=false;descriptor();f.host.order(Kind::Move,reinterpret_cast<void*>(U),0,reinterpret_cast<void*>(P),0);auto e=f.events().events.back();CK(e.source==Source::Unknown&&e.script_issue_id==0);});
 test("experimental owned attack binds at native entry when attack handler is bypassed",[]{Fixture f;f.calibrate_runtime_shape();auto i=f.issue(Kind::Attack);CK(i);current=Kind::Attack;queued=false;descriptor();f.host.order(Kind::Attack,reinterpret_cast<void*>(U),0,reinterpret_cast<void*>(P),0);auto e=f.events().events.back();auto st=f.host.status();CK(e.source==Source::OurController&&e.script_issue_id==i.id&&e.order.target_uid==1008&&st.native_attack_token_bindings==1);});
 test("different player attack stays UNKNOWN and makes pending controller attack stale",[]{Fixture f;f.calibrate_runtime_shape();auto i=f.issue(Kind::Attack);CK(i);current=Kind::Attack;queued=false;descriptor();set(P,std::uintptr_t(T2));f.host.order(Kind::Attack,reinterpret_cast<void*>(U),0,reinterpret_cast<void*>(P),0);auto external=f.events().events.back();CK(external.source==Source::Unknown&&external.order.target_uid==1009);set(P,std::uintptr_t(T));int before=native_calls;f.host.order(Kind::Attack,reinterpret_cast<void*>(U),0,reinterpret_cast<void*>(P),0);auto stale=f.events().events.back();CK(stale.source==Source::OurController&&stale.script_issue_id==i.id&&stale.status==Status::RejectedStale&&native_calls==before);});
 test("production build cannot arm from handler kinds alone",[]{Fixture f(false);f.publish_external(Kind::Move);f.consume(false,false,false,false,true);f.publish_external(Kind::Attack);f.consume(false,false,false,false,true);auto st=f.host.status();CK(st.handler_calibration_ready&&!st.physical_path_witnesses_ready);CK(std::string(f.host.arm(true))=="ADAPTER_NOT_READY");});
 test("owned move travels publish copy reader native gate",[]{Fixture f;f.calibrate();auto i=f.issue();CK(i&&native_calls==2);f.consume();auto e=f.events().events.back();CK(e.source==Source::OurController&&e.script_issue_id==i.id&&e.status==Status::Accepted&&native_calls==3);});
 test("queued owned move reads queued from real +0xA8 field",[]{Fixture f;f.calibrate();current=Kind::Move;queued=true;descriptor();set(B+0x5000,Id(0));auto snap=f.host.unit_snapshot(1002);CK(snap);auto b=f.host.begin_issue(Kind::Move,true,1002,snap.value.revision,L);CK(b);f.host.binding(Kind::Move,nullptr,L,1);auto fin=f.host.finish_issue(true);CK(fin);f.consume();auto e=f.events().events.back();CK(e.source==Source::OurController&&e.order.queued&&*e.order.queued);});
 test("owned attack uses same gate not guessed payload",[]{Fixture f;f.calibrate();auto i=f.issue(Kind::Attack);CK(i);f.consume();auto e=f.events().events.back();CK(e.source==Source::OurController&&e.order.target_uid==1008);});
 test("player accepted command invalidates stale revision before allocator",[]{Fixture f;f.calibrate();auto i=f.issue();CK(i);frame=false;f.host.order(Kind::Move,reinterpret_cast<void*>(U),0,reinterpret_cast<void*>(P),0);int before=native_calls;f.consume();auto e=f.events().events.back();CK(e.status==Status::RejectedStale&&native_calls==before);});
 test("callback error cancels queued owned packet",[]{Fixture f;f.calibrate();current=Kind::Move;descriptor();set(B+0x5000,Id(0));auto s=f.host.unit_snapshot(1002);CK(f.host.begin_issue(current,false,1002,s.value.revision,L));f.host.binding(current,nullptr,L,0);CK(!f.host.finish_issue(false));int before=native_calls;f.consume();CK(native_calls==before&&f.events().events.back().status==Status::RejectedCancelled);});
 test("single native command contract rejects wrong recipient before publishing",[]{Fixture f;f.calibrate();current=Kind::Move;descriptor();set(A,std::uintptr_t(T));auto s=f.host.unit_snapshot(1002);CK(f.host.begin_issue(current,false,1002,s.value.revision,L));f.host.binding(current,nullptr,L,0);CK(!f.host.finish_issue(true)&&native_calls==2);});
 test("publish rollback leaves no successful owned issue",[]{Fixture f;f.calibrate();reject_publish=true;auto r=f.issue();CK(!r&&get<Id>(B+0x5000)==0);});
 test("rejected stale public snapshot does not call native binding",[]{Fixture f;f.calibrate();auto r=f.host.begin_issue(Kind::Move,false,1002,0,L);CK(!r&&std::string(r.error)=="REJECTED_STALE"&&native_calls==2);});
 test("inactive reader frame never lends source to unrelated command",[]{Fixture f;f.calibrate();CK(f.issue());f.consume();int before=native_calls;frame=false;f.host.order(Kind::Move,reinterpret_cast<void*>(U),0,reinterpret_cast<void*>(P),0);CK(native_calls==before+1&&f.events().events.back().source==Source::Unknown);});
 test("halt increments revision without fabricated sequence",[]{Fixture f;f.calibrate();f.host.halt(reinterpret_cast<void*>(U),1);auto e=f.events().events.back();CK(e.order.kind==Kind::Halt&&e.source==Source::Unknown&&!e.engine_seq);});
 test("explicit disarm prevents further issuing",[]{Fixture f;f.calibrate();CK(f.host.arm(false)==nullptr);CK(!f.host.status().experimental_issue_armed);CK(!f.host.begin_issue(Kind::Move,false,1002,2,L));});
 test("battle end prevents any new issue",[]{Fixture f;f.calibrate();CK(f.host.end(f.epoch)==Error::Ok);CK(!f.host.begin_issue(Kind::Move,false,1002,2,L));});
 std::cout<<"TOTAL "<<pass<<" PASS "<<fail<<" FAIL (synthetic native memory and unwind oracle)\n";return fail?1:0;
}
