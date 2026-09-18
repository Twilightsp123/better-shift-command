#include "wh3/evidence_probe.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>
using namespace wh3;
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)
namespace {
std::map<std::uintptr_t,std::vector<unsigned char>> mem;
enum class Mode {Normal,MutateOrderAfterPayload,MutateGroupDuringQuery};
Mode mode=Mode::Normal;bool mutated=false;std::uintptr_t mutate_root=0,mutate_squad=0;

template<class T> void put(std::uintptr_t base,std::size_t off,const T& v){auto& b=mem.at(base);CK(off+sizeof(T)<=b.size());std::memcpy(b.data()+off,&v,sizeof(T));}
void block(std::uintptr_t a,std::size_t n){mem[a]=std::vector<unsigned char>(n);}
bool raw_rd(std::uintptr_t a,void* out,std::size_t n) noexcept{auto it=mem.upper_bound(a);if(it==mem.begin())return false;--it;const auto off=a-it->first;if(off>it->second.size()||n>it->second.size()-off)return false;std::memcpy(out,it->second.data()+off,n);return true;}
bool rd(std::uintptr_t a,void* out,std::size_t n) noexcept{
 if(!raw_rd(a,out,n))return false;
 if(mode==Mode::MutateOrderAfterPayload&&!mutated&&a==mutate_root+0x288+0x58){mutated=true;put(mutate_root,0x288+0x20,std::uint32_t(88));put(mutate_root,0x288+0x58,900.0f);}
 return true;
}
constexpr std::uintptr_t image=0x140000000ULL;
constexpr std::uintptr_t move_vt=image+0x37b31c8;
bool alive_cb(std::uintptr_t entity,bool* alive) noexcept{int hp=0;if(!alive||!raw_rd(entity+0xb1c,&hp,4))return false;*alive=hp>0;return true;}
bool group_cb(std::uintptr_t group,bool* melee,std::uintptr_t* target) noexcept{
 std::uint32_t m=0;std::uintptr_t t=0;if(!melee||!target||!raw_rd(group+0x10,&m,4)||!raw_rd(group+0x18,&t,8))return false;*melee=m!=0;*target=t;
 if(mode==Mode::MutateGroupDuringQuery&&!mutated){mutated=true;put(mutate_squad,0x8c8,std::uint32_t(0));}
 return true;
}
void reset_mode(){mode=Mode::Normal;mutated=false;mutate_root=mutate_squad=0;}
void setup_unit(std::uintptr_t root,std::uintptr_t arr,std::size_t count,float start_x,float z){
 block(root,0x5000);block(arr,count*8);std::vector<std::uintptr_t> ptrs;
 for(std::size_t i=0;i<count;++i){auto e=root+0x10000+i*0x2000;auto c=e+0x1000;block(e,0xc00);block(c,0xc00);int hp=100;float x=start_x+float(i)*0.1f;put(e,0xb1c,hp);put(e,0x88,x);put(e,0x90,z);put(e,0x18,c);put(c,0x4a0,e);std::uint32_t movement=1;put(c,0x8b0,movement);ptrs.push_back(e);}std::memcpy(mem[arr].data(),ptrs.data(),ptrs.size()*8);std::uint32_t c=static_cast<std::uint32_t>(count);put(root,0x114,c);put(root,0x118,arr);
}
std::uintptr_t entity_at(std::uintptr_t root,std::size_t i){std::uintptr_t arr=0,e=0;raw_rd(root+0x118,&arr,8);raw_rd(arr+i*8,&e,8);return e;}
void movement_state(std::uintptr_t root,std::size_t i,std::uint32_t state){auto e=entity_at(root,i);std::uintptr_t c=0;raw_rd(e+0x18,&c,8);put(c,0x8b0,state);}
void shift_entities(std::uintptr_t root,float dx,float dz,std::size_t first=0){std::uintptr_t arr=0;std::uint32_t count=0;raw_rd(root+0x118,&arr,8);raw_rd(root+0x114,&count,4);for(std::size_t i=first;i<count;++i){std::uintptr_t e=0;raw_rd(arr+i*8,&e,8);float x=0,z=0;raw_rd(e+0x88,&x,4);raw_rd(e+0x90,&z,4);x+=dx;z+=dz;put(e,0x88,x);put(e,0x90,z);}}
void set_move(std::uintptr_t root,std::uint32_t seq,float x,float z){std::uint32_t count=1,head=0;put(root,0x2f88,count);put(root,0x2f8c,head);put(root,0x288+0x18,move_vt);put(root,0x288+0x20,seq);put(root,0x288+0x58,x);put(root,0x288+0x68,z);}
std::uintptr_t setup_groups(std::uintptr_t root,const std::vector<std::pair<bool,std::uintptr_t>>& groups){auto squad=root+0x9000;block(squad,0x1200);put(root,0x32f8,squad);std::uint32_t n=static_cast<std::uint32_t>(groups.size());put(squad,0x8c8,n);std::uint32_t coarse=0;for(std::size_t i=0;i<groups.size();++i){auto g=root+0x600000+i*0x1000;block(g,0x100);std::uintptr_t target=groups[i].second;std::uint32_t melee=groups[i].first?1:0;put(g,0x10,melee);put(g,0x18,target);put(squad,0x848+i*0x10,g);if(melee)++coarse;}put(root,0x34b8,coarse);return squad;}
}
int main(){int pass=0,fail=0;auto test=[&](const char* n,auto f){try{mem.clear();reset_mode();f();++pass;std::cout<<"PASS "<<n<<"\n";}catch(const std::exception& e){++fail;std::cout<<"FAIL "<<n<<": "<<e.what()<<"\n";}};
 test("active head exposes exact stable order id",[]{auto root=0x100000ULL,arr=0x200000ULL;setup_unit(root,arr,10,0,0);set_move(root,77,100,0);EvidenceProbe p(rd,alive_cb,group_cb,image);auto a=p.active_order(root);CK(a.complete&&a.active&&a.engine_seq==77&&a.kind==Kind::Move&&a.dest_x&&*a.dest_x==100);});
 test("N01 active order replacement during read is incomplete",[]{auto root=0x2100000ULL,arr=0x2200000ULL;setup_unit(root,arr,3,0,0);set_move(root,77,100,0);mode=Mode::MutateOrderAfterPayload;mutate_root=root;EvidenceProbe p(rd,alive_cb,group_cb,image);auto a=p.active_order(root);CK(!a.complete||(a.active&&a.engine_seq==88&&a.dest_x&&*a.dest_x==900.0f));});
 test("dead retained pointers are skipped by authoritative alive callback",[]{auto root=0x300000ULL,arr=0x400000ULL;setup_unit(root,arr,6,0,0);auto dead=entity_at(root,4);int hp=0;put(dead,0xb1c,hp);EvidenceProbe p(rd,alive_cb,group_cb,image);auto s=p.entity_snapshot(root,1000);CK(s.complete&&s.slot_count==6&&s.live_count==5&&s.dead_count==1&&s.entities.size()==5);});
 test("null fixed deployment slot is structural invalidity",[]{auto root=0x500000ULL,arr=0x600000ULL;setup_unit(root,arr,6,0,0);std::uintptr_t nil=0;std::memcpy(mem[arr].data()+5*8,&nil,8);EvidenceProbe p(rd,alive_cb,group_cb,image);auto s=p.entity_snapshot(root,1000);CK(!s.complete&&s.probe_reason==EntityProbeReason::NullEntitySlot);});
 test("N03 duplicate Entity pointer is structural invalidity",[]{auto root=0x5100000ULL,arr=0x5200000ULL;setup_unit(root,arr,4,0,0);auto e=entity_at(root,0);std::memcpy(mem[arr].data()+3*8,&e,8);EvidenceProbe p(rd,alive_cb,group_cb,image);auto s=p.entity_snapshot(root,1000);CK(!s.complete&&s.probe_reason==EntityProbeReason::DuplicateEntity);});
 test("V3 ignores state74 and exposes only movement facts",[]{auto root=0x700000ULL,arr=0x800000ULL;setup_unit(root,arr,5,0,0);movement_state(root,0,2);movement_state(root,1,0);EvidenceProbe p(rd,alive_cb,group_cb,image);auto s=p.entity_snapshot(root,1000);CK(s.complete&&s.movement_halted_count==1&&s.movement_idle_count==1&&s.movement_pathing_count==3&&s.entities.size()==5);});
 test("bad movement component backpointer fails closed",[]{auto root=0x900000ULL,arr=0xa00000ULL;setup_unit(root,arr,3,0,0);auto e=entity_at(root,1);std::uintptr_t c=0;raw_rd(e+0x18,&c,8);std::uintptr_t wrong=0x1234;put(c,0x4a0,wrong);EvidenceProbe p(rd,alive_cb,group_cb,image);auto s=p.entity_snapshot(root,1000);CK(!s.complete&&s.probe_reason==EntityProbeReason::MovementBackref);});
 test("per entity and median motion are raw vector measurements",[]{auto root=0xb00000ULL,arr=0xc00000ULL;setup_unit(root,arr,5,0,0);EvidenceProbe p(rd,alive_cb,group_cb,image);auto a=p.entity_snapshot(root,1000);CK(a.complete&&!a.motion_complete);shift_entities(root,1.0f,-0.5f);auto b=p.entity_snapshot(root,1200);CK(b.complete&&b.motion_complete&&b.motion_matched_count==5&&b.entities[0].motion_complete);CK(b.median_vx>4.9f&&b.median_vx<5.1f&&b.median_vz<-2.4f&&b.median_vz>-2.6f);});
 test("combat snapshot enumerates every stable active melee target",[]{auto root=0xd00000ULL,arr=0xe00000ULL;setup_unit(root,arr,5,0,0);setup_groups(root,{{true,0xf00000},{false,0x1000000},{true,0x1100000},{true,0xf00000}});EvidenceProbe p(rd,alive_cb,group_cb,image);auto c=p.combat_snapshot(root);CK(c.complete&&c.group_count==4&&c.active_melee_group_count==3&&c.coarse_contact_count==3);CK(c.active_target_roots.size()==3&&c.active_target_roots[0]==0xf00000&&c.active_target_roots[1]==0x1100000&&c.active_target_roots[2]==0xf00000);});
 test("N02 combat group mutation during query is incomplete",[]{auto root=0x5300000ULL,arr=0x5400000ULL;setup_unit(root,arr,3,0,0);mutate_squad=setup_groups(root,{{true,0x5500000}});mode=Mode::MutateGroupDuringQuery;EvidenceProbe p(rd,alive_cb,group_cb,image);auto c=p.combat_snapshot(root);CK(!c.complete||(c.complete&&c.group_count==0&&c.active_target_roots.empty()));});
 test("zero combat groups is a complete clear fact",[]{auto root=0x1300000ULL,arr=0x1400000ULL;setup_unit(root,arr,1,0,0);setup_groups(root,{});EvidenceProbe p(rd,alive_cb,group_cb,image);auto c=p.combat_snapshot(root);CK(c.complete&&c.group_count==0&&c.active_melee_group_count==0&&c.active_target_roots.empty());});
 std::cout<<"TOTAL "<<pass<<" PASS "<<fail<<" FAIL\n";return fail?1:0;}
