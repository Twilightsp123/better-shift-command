#include "wh3/bridge_host.hpp"
#include <iostream>
#include <cstring>
#include <vector>
#include <stdexcept>
#include <limits>
using namespace wh3;
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)
namespace {
constexpr std::uintptr_t root=0x100000,target=0x200000,base=0x140000000ULL;
std::vector<unsigned char> unit(0x5000),enemy(0x5000);
BridgeHost* h=nullptr;
int calls=0,mode=0;Id seq=0;bool throwing=false;std::uint32_t argument=0,ret=1;void* payload=nullptr;
std::uint8_t queue=0;Kind kind=Kind::Move;
bool memory(std::uintptr_t p,void* o,std::size_t n) noexcept{
 for(auto item:{std::make_pair(root,&unit),std::make_pair(target,&enemy)})
  if(p>=item.first&&p-item.first<=item.second->size()&&n<=item.second->size()-(p-item.first)){
   std::memcpy(o,item.second->data()+(p-item.first),n);return true;}
 return false;
}
template<class T>void wr(std::size_t off,T v){std::memcpy(unit.data()+off,&v,sizeof v);}
void* alloc(void*,std::uint32_t){return reinterpret_cast<void*>(root+0x288);}
std::uint32_t execute(void* u,std::uint32_t a,void* p,std::uint8_t q){
 ++calls;argument=a;payload=p;queue=q;CK(reinterpret_cast<std::uintptr_t>(u)==root);
 if(mode==9){mode=0;h->order(kind,u,a,p,q);mode=9;}
 if(mode==8)CK(h->end(h->status().epoch)==Error::Reentrant);
 if(mode!=1){
  auto c=reinterpret_cast<void*>(root+(mode==5?0x300:0x278));
  void* s=h->allocate(c,mode==4?std::uint32_t(q)^1:q);CK(s==reinterpret_cast<void*>(root+0x288));
  if(mode==2)h->allocate(c,q);
  auto vt=base+(kind==Kind::Move?0x37b31c8:0x37b2540);if(mode==3)++vt;
  wr(0x288+0x18,std::uint64_t(vt));wr(0x288+0x20,seq);
  if(kind==Kind::Move){wr(0x288+0x58,mode==7?std::numeric_limits<float>::quiet_NaN():12.5f);wr(0x288+0x5c,2.0f);wr(0x288+0x60,-5.0f);}
  else{wr(0x288+0x58,std::uint64_t(mode==6?0xdeadbeef:target));unit[0x288+0x70]=1;unit[0x288+0x71]=2;unit[0x288+0x72]=3;unit[0x288+0x78]=4;}
 }
 if(throwing)throw std::runtime_error("native fixture threw");
 return ret;
}
void stop(void*,std::uint32_t f){++calls;argument=f;}
struct Fixture {BridgeHost host{memory};Id epoch=0;Fixture(){
 h=&host;std::fill(unit.begin(),unit.end(),0);std::fill(enemy.begin(),enemy.end(),0);
 Id uid=1002,tuid=1008;wr(0x3ea0,uid);std::memcpy(enemy.data()+0x3ea0,&tuid,4);
 mode=0;seq=0;calls=0;ret=1;throwing=false;kind=Kind::Move;
 CK(host.set_native_functions({execute,execute,alloc,stop}));auto r=host.begin("fixture");CK(r);epoch=r.value;
 }
 std::uint32_t send(bool q=false){return host.order(kind,reinterpret_cast<void*>(root),0xabcdef12,reinterpret_cast<void*>(0x1234),q?1:0);}
 Page page(){auto r=host.read(epoch,0,64);CK(r);return r.value;}
};
}
int main(){int passed=0,failed=0;auto test=[&](const char* n,auto f){try{f();++passed;std::cout<<"PASS "<<n<<"\n";}catch(const std::exception& e){++failed;std::cout<<"FAIL "<<n<<": "<<e.what()<<"\n";}};
 test("forwards all four parameters and full EAX",[]{Fixture f;ret=0x12345678;CK(f.send()==ret);CK(calls==1&&argument==0xabcdef12&&payload==reinterpret_cast<void*>(0x1234)&&queue==0);});
 test("seq zero and finite slot geometry",[]{Fixture f;f.send();auto e=f.page().events.at(0);CK(e.engine_seq&&*e.engine_seq==0&&e.order.x==12.5f&&e.order.z==-5.0f);});
 test("append/replace preserved without source invention",[]{Fixture f;f.send(true);seq=62;f.send(false);auto p=f.page();CK(p.events.size()==2&&*p.events[0].order.queued&&!*p.events[1].order.queued);CK(p.events[1].revision==2&&p.events[0].source==Source::Unknown);});
 test("attack pointer uid raw flags decoded",[]{Fixture f;kind=Kind::Attack;seq=1450;f.send(true);auto e=f.page().events.at(0);CK(e.order.target_uid==1008&&e.order.target_root==target&&e.order.raw78==4&&e.order.raw71==2);});
 test("native failure preserves return and has no phantom seq",[]{Fixture f;ret=0;CK(f.send()==0);auto e=f.page().events.at(0);CK(e.status==Status::NativeRejected&&!e.engine_seq&&e.revision==0);});
 test("accepted no slot explicit, advances revision",[]{Fixture f;mode=1;f.send();auto e=f.page().events.at(0);CK(e.status==Status::AcceptedNoSlot&&!e.engine_seq&&!e.order.x&&e.revision==1);CK(f.host.status().capture_errors==1);});
 for(int bad:{2,3,4,5})test(("invalid slot evidence mode "+std::to_string(bad)).c_str(),[bad]{Fixture f;mode=bad;f.send();auto e=f.page().events.at(0);CK(!e.engine_seq&&e.status==Status::AcceptedNoSlot&&calls==1);});
 test("unreadable target cannot be guessed",[]{Fixture f;mode=6;kind=Kind::Attack;f.send();auto e=f.page().events.at(0);CK(!e.order.target_uid&&!e.order.target_root&&e.engine_seq);CK(f.host.status().capture_errors==1);});
 test("NaN geometry not published as coordinates",[]{Fixture f;mode=7;f.send();auto e=f.page().events.at(0);CK(!e.order.x&&e.engine_seq);});
 test("Halt no sequence or queued bit fabricated",[]{Fixture f;f.host.halt(reinterpret_cast<void*>(root),0xa5);auto e=f.page().events.at(0);CK(calls==1&&argument==0xa5&&e.order.kind==Kind::Halt&&!e.engine_seq&&!e.order.queued&&e.revision==1);});
 test("stopped session still forwards native command",[]{Fixture f;CK(f.host.end(f.epoch)==Error::Ok);f.send();CK(calls==1&&f.page().events.empty());});
 test("exception is not retried, allocator scope restored",[]{Fixture f;throwing=true;try{f.send();CK(false);}catch(const std::runtime_error&){}CK(calls==1);throwing=false;f.send();CK(calls==2&&f.page().events.size()==1);});
 test("reentrant lifecycle refused while native runs",[]{Fixture f;mode=8;f.send();CK(f.host.status().recording&&calls==1);});
 test("journal acknowledge does not skip unseen records",[]{Fixture f;f.send();CK(f.host.acknowledge(f.epoch,1)==Error::Invalid);f.page();CK(f.host.acknowledge(f.epoch,1)==Error::Ok);});
 test("same payload never implies self token",[]{Fixture f;f.send();f.send();for(auto e:f.page().events)CK(e.source==Source::Unknown&&e.script_issue_id==0&&!e.batch_total);});
 test("actual host own API rejects without calling native",[]{Fixture f;CK(!f.host.begin_issue(Kind::Move,false,1002,0,nullptr));CK(calls==0&&!f.host.status().verified_issue);});
 test("AL zero with nonzero high EAX is still native rejection",[]{Fixture f;ret=0x12345600;f.send();CK(f.page().events.at(0).status==Status::NativeRejected);});
 test("second battle does not reuse epoch",[]{Fixture f;f.send();f.host.end(f.epoch);auto e=f.host.begin("second");CK(e&&e.value!=f.epoch);CK(!f.host.read(f.epoch,0,64));});
 test("reentrant command cannot lend inner slot to parent",[]{Fixture f;mode=9;f.send();auto p=f.page();CK(calls==2&&p.events.size()==2&&p.events[0].engine_seq&&!p.events[1].engine_seq);CK(f.host.status().capture_errors==1);});
 test("trampolines immutable after first native call",[]{Fixture f;f.send();CK(!f.host.set_native_functions({execute,execute,alloc,stop}));});
 test("empty and overlong session rejected",[]{BridgeHost x(memory);CK(!x.begin(""));CK(!x.begin(std::string(65,'x')));});
 std::cout<<"TOTAL "<<passed<<" PASS "<<failed<<" FAIL (synthetic native callbacks, not WH3)\n";return failed?1:0;
}
