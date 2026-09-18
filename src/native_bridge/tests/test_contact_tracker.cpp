#include "wh3/contact_tracker.hpp"
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace wh3;
namespace {
int pass=0,fail=0;
#define CK(x) do{if(!(x))throw std::runtime_error(std::string("check failed: ")+#x);}while(0)
void test(const char* n,const std::function<void()>& f){try{f();++pass;std::cout<<"PASS "<<n<<"\n";}catch(const std::exception& e){++fail;std::cout<<"FAIL "<<n<<" :: "<<e.what()<<"\n";}}
}
int main(){
 test("owner index resolves uid and command root",[]{
  ContactTracker t; t.bind_command_root(1001,0xAAA0);CK(t.bind_entities(1001,{0x1000,0x1100}));
  ContactOwnerView o;CK(t.owner(0x1000,o));CK(o.uid==1001&&o.command_root==0xAAA0);
 });
 test("authoritative rebind invalidates stale entities",[]{
  ContactTracker t;t.bind_command_root(1001,0xAAA0);CK(t.bind_entities(1001,{0x1000,0x1100}));CK(t.bind_entities(1001,{0x1200}));
  ContactOwnerView o;CK(!t.owner(0x1000,o));CK(!t.owner(0x1100,o));CK(t.owner(0x1200,o)&&o.uid==1001);
 });
 test("cross-unit entity conflict is rejected without damaging prior map",[]{
  ContactTracker t;CK(t.bind_entities(1001,{0x1000,0x1100}));CK(t.bind_entities(2002,{0x2000}));
  CK(!t.bind_entities(1001,{0x1000,0x2000}));
  ContactOwnerView o;CK(t.owner(0x1000,o)&&o.uid==1001);CK(t.owner(0x1100,o)&&o.uid==1001);CK(t.owner(0x2000,o)&&o.uid==2002);
 });
 test("duplicate entity in one authoritative binding is rejected transactionally",[]{
  ContactTracker t;CK(t.bind_entities(1001,{0x1000,0x1100}));CK(!t.bind_entities(1001,{0x1200,0x1200}));
  ContactOwnerView o;CK(t.owner(0x1000,o)&&o.uid==1001);CK(!t.owner(0x1200,o));
 });
 test("invalidated owner generation cannot resolve and can be reassigned",[]{
  ContactTracker t;CK(t.bind_entities(1001,{0x1000}));t.invalidate_entities(1001);ContactOwnerView o;CK(!t.owner(0x1000,o));
  CK(t.bind_entities(2002,{0x1000}));CK(t.owner(0x1000,o)&&o.uid==2002&&o.command_root==0);
 });
 test("contact journal records exact cross-unit pair with order identities",[]{
  ContactTracker t;t.bind_command_root(1001,0xAAA0);t.bind_command_root(2002,0xBBB0);CK(t.bind_entities(1001,{0x1000,0x1100}));CK(t.bind_entities(2002,{0x2000}));
  t.record(0x1000,0x2000,true,77,true,88,1000);auto p=t.read(0,16);CK(p.events.size()==1);const auto& e=p.events[0];
  CK(e.uid_a==1001&&e.uid_b==2002&&e.entity_a==0x1000&&e.entity_b==0x2000&&e.active_a&&e.active_b&&e.active_engine_seq_a==77&&e.active_engine_seq_b==88&&e.tick_ms==1000);
 });
 test("same pair is debounced bidirectionally but heartbeats after window",[]{
  ContactTracker t;CK(t.bind_entities(1001,{0x1000}));CK(t.bind_entities(2002,{0x2000}));
  t.record(0x1000,0x2000,true,77,true,88,1000);t.record(0x2000,0x1000,true,88,true,77,1050);CK(t.read(0,16).events.size()==1);
  t.record(0x2000,0x1000,true,88,true,77,1075);auto p=t.read(0,16);CK(p.events.size()==2);CK(p.events[1].tick_ms==1075);
 });
 test("new active order identity bypasses debounce immediately",[]{
  ContactTracker t;CK(t.bind_entities(1001,{0x1000}));CK(t.bind_entities(2002,{0x2000}));
  t.record(0x1000,0x2000,true,77,true,88,1000);t.record(0x1000,0x2000,true,78,true,88,1010);auto p=t.read(0,16);CK(p.events.size()==2);CK(p.events[1].active_engine_seq_a==78);
 });
 test("same-unit and unknown-owner pairs never enter journal",[]{
  ContactTracker t;CK(t.bind_entities(1001,{0x1000,0x1100}));t.record(0x1000,0x1100,true,1,true,1,100);t.record(0x1000,0x9999,true,1,true,2,200);CK(t.read(0,16).events.empty());
 });
 test("stale owner generation cannot produce contact after rebind",[]{
  ContactTracker t;CK(t.bind_entities(1001,{0x1000}));CK(t.bind_entities(2002,{0x2000}));CK(t.bind_entities(1001,{0x1100}));
  t.record(0x1000,0x2000,true,1,true,2,100);CK(t.read(0,16).events.empty());t.record(0x1100,0x2000,true,1,true,2,200);CK(t.read(0,16).events.size()==1);
 });
 std::cout<<"TOTAL "<<pass<<" PASS "<<fail<<" FAIL\n";return fail?1:0;
}
