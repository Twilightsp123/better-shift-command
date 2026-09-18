#include "wh3/bridge_host.hpp"
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>
using namespace wh3;
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)
namespace {
std::map<std::uintptr_t,std::vector<unsigned char>> mem;
BridgeHost* H=nullptr;
constexpr std::uintptr_t base=0x140000000ULL,cmd=0x100000,phys=0x200000,target_phys=0x300000,arr=0x400000,target_arr=0x410000,squad=0x500000,group=0x600000;
bool rd(std::uintptr_t a,void* o,std::size_t n) noexcept{auto it=mem.upper_bound(a);if(it==mem.begin())return false;--it;auto off=a-it->first;if(off>it->second.size()||n>it->second.size()-off)return false;std::memcpy(o,it->second.data()+off,n);return true;}
void block(std::uintptr_t a,std::size_t n){mem[a]=std::vector<unsigned char>(n);}
template<class T>void put(std::uintptr_t a,std::size_t o,T v){auto& b=mem.at(a);CK(o+sizeof(T)<=b.size());std::memcpy(b.data()+o,&v,sizeof v);}
bool alive(std::uintptr_t e,bool* out) noexcept{if(!out)return false;int hp=0;if(!rd(e+0xb1c,&hp,4))return false;*out=hp>0;return true;}
bool groupq(std::uintptr_t g,bool* melee,std::uintptr_t* target) noexcept{std::uint32_t m=0;std::uintptr_t t=0;if(!melee||!target||!rd(g+0x10,&m,4)||!rd(g+0x18,&t,8))return false;*melee=m!=0;*target=t;return true;}
void* alloc(void*,std::uint32_t){return reinterpret_cast<void*>(cmd+0x288);}
std::uint32_t move(void* u,std::uint32_t,void*,std::uint8_t q){CK(reinterpret_cast<std::uintptr_t>(u)==cmd);H->allocate(reinterpret_cast<void*>(cmd+0x278),q);put(cmd,0x2f88,std::uint32_t(1));put(cmd,0x2f8c,std::uint32_t(0));put(cmd,0x288+0x18,std::uint64_t(base+0x37b31c8));put(cmd,0x288+0x20,std::uint32_t(77));put(cmd,0x288+0x58,12.0f);put(cmd,0x288+0x5c,0.0f);put(cmd,0x288+0x60,-4.0f);return 1;}
void halt(void*,std::uint32_t){}
void setup(){mem.clear();block(cmd,0x5000);block(phys,0x5000);block(target_phys,0x5000);block(arr,3*8);block(target_arr,8);block(squad,0x1000);block(group,0x100);
 put(cmd,0x3ea0,std::uint32_t(1001));
 std::uintptr_t es[3];for(int i=0;i<3;++i){auto e=0x700000ULL+std::uintptr_t(i)*0x3000;auto c=e+0x1000;block(e,0xc00);block(c,0xc00);put(e,0xb1c,100);put(e,0x88,float(i));put(e,0x90,2.0f);put(e,0x18,c);put(c,0x4a0,e);put(c,0x74,std::uint32_t(i==0?4:1));put(c,0x8b0,std::uint32_t(1));es[i]=e;}std::memcpy(mem[arr].data(),es,sizeof es);put(phys,0x114,std::uint32_t(3));put(phys,0x118,arr);std::uintptr_t te=0x790000;block(te,0xc00);std::memcpy(mem[target_arr].data(),&te,8);put(target_phys,0x114,std::uint32_t(1));put(target_phys,0x118,target_arr);
 put(phys,0x32f8,squad);put(phys,0x34b8,std::uint32_t(1));put(squad,0x8c8,std::uint32_t(1));put(squad,0x848,group);put(group,0x10,std::uint32_t(1));put(group,0x18,target_phys);
}
}
int main(){try{setup();BridgeHost host(rd,base,nullptr,nullptr,false,alive,groupq);H=&host;CK(host.set_native_functions({move,move,alloc,halt}));auto ep=host.begin("dual-root");CK(ep);CK(host.bind_evidence_root(1001,phys)==Error::Ok);CK(host.bind_evidence_root(2002,target_phys)==Error::Ok);CK(host.contact_owner_ready(1001)&&host.contact_owner_ready(2002));CK(host.bind_evidence_root(1001,0xDEAD000)==Error::Invalid);auto sticky=host.evidence_root(1001);CK(sticky&&sticky.value==phys&&host.contact_owner_ready(1001));
 CK(host.order(Kind::Move,reinterpret_cast<void*>(cmd),0,nullptr,0)==1);auto id=host.execution_identity(1001);CK(id&&id.value.known&&id.value.active_engine_seq==77&&id.value.dest_x&&*id.value.dest_x==12.0f);
 auto es=host.entity_snapshot(1001,1000);CK(es&&es.value.complete&&es.value.slot_count==3&&es.value.live_count==3&&es.value.entities.size()==3);
 auto cs=host.combat_snapshot(1001);CK(cs&&cs.value.complete&&cs.value.active_target_uids.size()==1&&cs.value.active_target_uids[0]==2002);
 std::cout<<"PASS command root and Lua evidence root remain independent\n";return 0;}catch(const std::exception& e){std::cout<<"FAIL "<<e.what()<<"\n";return 1;}}
