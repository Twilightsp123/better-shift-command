// A float32 Lua-C-API stack fixture. NOT a Lua VM or WH3 runtime test.
#include "wh3/lua51_abi.hpp"
#include "wh3/bridge_host.hpp"
#include <map>
#include <set>
#include <vector>
#include <memory>
#include <string>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <limits>
#include <cstdint>
using wh3::lua51::CFunction;
struct Table;
struct Value {int tag=0;std::string text;float number=0;bool boolean=false;void* userdata=nullptr;CFunction fn=nullptr;std::shared_ptr<Table> table;};
struct Table {std::map<std::string,Value> fields;std::map<int,Value> array;};
struct lua_State {std::vector<Value> stack;};
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)
Value s(const std::string& v){Value x;x.tag=4;x.text=v;return x;}
Value n(float f){Value x;x.tag=3;x.number=f;return x;}
Value b(bool f){Value x;x.tag=1;x.boolean=f;return x;}
Value ud(void* p){Value x;x.tag=7;x.userdata=p;return x;}
Value& at(lua_State* L,int i){int p=i>0?i-1:static_cast<int>(L->stack.size())+i;return L->stack.at(static_cast<std::size_t>(p));}
void settop(lua_State* L,int n){CK(n>=0);L->stack.resize(static_cast<std::size_t>(n));}
void pushvalue(lua_State* L,int n){auto v=at(L,n);L->stack.push_back(v);}
int protected_call(lua_State*,int,int,int){throw std::runtime_error("unexpected Lua callback before gate ready");}
int top(lua_State* L){return static_cast<int>(L->stack.size());}
int type(lua_State* L,int i){if(i>top(L)||i==0||i < -top(L))return -1;return at(L,i).tag;}
const char* string(lua_State* L,int i,std::size_t* len){auto& v=at(L,i);if(v.tag!=4)return nullptr;if(len)*len=v.text.size();return v.text.data();}
float number(lua_State* L,int i){return at(L,i).number;}
int boolean(lua_State* L,int i){return at(L,i).boolean?1:0;}
void* userdata(lua_State* L,int i){return at(L,i).tag==7?at(L,i).userdata:nullptr;}
std::size_t objlen(lua_State* L,int i){return at(L,i).tag==7?32u:0u;}
void nil(lua_State* L){L->stack.emplace_back();}
void pushnum(lua_State* L,float v){L->stack.push_back(n(v));}
void pushstr(lua_State* L,const char* p,std::size_t z){L->stack.push_back(s(std::string(p,z)));}
void pushbool(lua_State* L,int v){L->stack.push_back(b(v!=0));}
void table(lua_State* L,int,int){Value v;v.tag=5;v.table=std::make_shared<Table>();L->stack.push_back(v);}
void setfield(lua_State* L,int i,const char* key){auto t=at(L,i).table;CK(t);auto v=L->stack.back();L->stack.pop_back();t->fields[key]=v;}
void setarray(lua_State* L,int i,int index){auto t=at(L,i).table;CK(t);auto v=L->stack.back();L->stack.pop_back();t->array[index]=v;}
void closure(lua_State* L,CFunction fn,int up){CK(up==0);Value v;v.tag=6;v.fn=fn;L->stack.push_back(v);}
template<class F> void* ptr(F f){void* p=nullptr;static_assert(sizeof p==sizeof f);std::memcpy(&p,&f,sizeof p);return p;}
alignas(8) unsigned char fake_wrapper[32]{};
std::map<std::uintptr_t,std::vector<unsigned char>> fake_mem;
std::set<std::uintptr_t> fake_entities;
std::size_t diag_component_sample_limit=0;
int fake_alive_calls=0;
bool fake_alive_allowed=true;
void fake_block(std::uintptr_t base,std::size_t size){fake_mem[base]=std::vector<unsigned char>(size);}
template<class T> void fake_put(std::uintptr_t base,std::size_t off,const T& value){auto& b=fake_mem.at(base);CK(off+sizeof(T)<=b.size());std::memcpy(b.data()+off,&value,sizeof(T));}
void fake_entity(std::uintptr_t entity,std::uintptr_t component){
 fake_block(entity,0x200);fake_block(component,0x900);float x=1.0f,z=2.0f;std::uintptr_t c=component;std::uint32_t movement=1;
 fake_put(entity,0x88,x);fake_put(entity,0x90,z);fake_put(entity,0x18,c);fake_put(component,0x4a0,entity);fake_put(component,0x8b0,movement);fake_entities.insert(entity);
}
namespace wh3 {
std::uintptr_t platform_image_base() noexcept{return 0x140000000ULL;}
bool platform_write(std::uintptr_t,const void*,std::size_t) noexcept{return false;}
bool platform_entity_alive(std::uintptr_t entity,bool* alive) noexcept{++fake_alive_calls;if(!fake_alive_allowed||!alive||!fake_entities.count(entity))return false;*alive=true;return true;}
bool platform_combat_group_query(std::uintptr_t,bool*,std::uintptr_t*) noexcept{return false;}
bool platform_frame_active(const FrameIdentity&) noexcept{return false;}
FrameIdentity platform_caller_frame(void*) noexcept{return {};}
bool platform_read(std::uintptr_t address,void* out,std::size_t size) noexcept{
 const auto w=reinterpret_cast<std::uintptr_t>(fake_wrapper);if(address>=w&&address+size<=w+sizeof(fake_wrapper)){std::memcpy(out,fake_wrapper+(address-w),size);return true;}
 for(const auto& kv:fake_mem){const auto base=kv.first;const auto& b=kv.second;if(address>=base&&address+size>=address&&address+size<=base+b.size()){std::memcpy(out,b.data()+(address-base),size);return true;}}
 if(address==0x103ea0&&size==4){Id uid=1001;std::memcpy(out,&uid,4);return true;}return false;
}
const char* platform_start_observer(){return "TEST_BACKEND_NOT_GAME";}
const char* platform_stop_observer(){return nullptr;}
bool platform_hooks_installed() noexcept{return false;}
bool platform_evidence_build_verified() noexcept{return false;}
const char* platform_evidence_build_id() noexcept{return "TEST_UNAVAILABLE";}
std::uint64_t platform_tick_ms() noexcept{return 123456;}
std::uintptr_t platform_image_size() noexcept{return 0x0DCC1000;}
bool platform_executable_address(std::uintptr_t) noexcept{return true;}
void platform_reset_diagnostic_gates() noexcept{}
bool platform_component_chain_gate_passed() noexcept{return true;}
bool platform_entity_alive_gate_passed() noexcept{return true;}
DiagnosticGateStatus platform_diagnostic_gate_status() noexcept{
    DiagnosticGateStatus s{};
    s.component_chain_gate = true;
    s.component_gate_root = 0;
    s.entity_component_offset = 0x18;
    s.component_backref_offset = 0x4a0;
    s.movement_state_offset = 0x8b0;
    s.component_layout_method = "LEGACY_EXACT";
    s.alive_deployment_passed = true;
    s.alive_casualty_passed = true;
    s.entity_alive_gate = true;
    s.alive_gate_root = 0;
    s.build_id = "TEST_UNAVAILABLE";
    s.bridge_version = wh3::kDiagnosticBridgeVersion;
    return s;
}
const char* platform_last_error() noexcept{return "NONE";}
DiagnosticChainResult platform_probe_component_chain(std::uintptr_t, std::size_t sample_limit) noexcept{
    diag_component_sample_limit=sample_limit;
    DiagnosticChainResult r{};
    r.passed = true;
    r.slot_count = 10;
    r.sampled_count = 10;
    r.entity_component_offset = 0x18;
    r.component_backref_offset = 0x4a0;
    r.movement_state_offset = 0x8b0;
    r.layout_method = "LEGACY_EXACT";
    r.failure_reason = "NONE";
    return r;
}
DiagnosticAliveResult platform_probe_entity_alive(std::uintptr_t, std::uint32_t lua_men_alive) noexcept{
    DiagnosticAliveResult r{};
    r.match = true;
    r.slot_count = 10;
    r.native_alive_count = lua_men_alive;
    r.lua_men_alive = lua_men_alive;
    r.deployment_passed = true;
    r.casualty_passed = true;
    r.gate_passed = true;
    r.phase = "DEPLOYMENT";
    r.failure_reason = "NONE";
    return r;
}
void* platform_lua_symbol(const char* key) noexcept{
#define MAP(k,f) if(std::strcmp(key,"lua_" k)==0)return ptr(f)
 MAP("settop",settop);MAP("pushvalue",pushvalue);MAP("pcall",protected_call);MAP("gettop",top);MAP("type",::type);MAP("tolstring",string);MAP("tonumber",number);
 MAP("toboolean",boolean);MAP("touserdata",userdata);MAP("objlen",objlen);MAP("pushnil",nil);MAP("pushnumber",pushnum);MAP("pushlstring",pushstr);
 MAP("pushboolean",pushbool);MAP("createtable",table);MAP("setfield",setfield);MAP("rawseti",setarray);MAP("pushcclosure",closure);
#undef MAP
 return nullptr;
}
}
extern "C" int luaopen_wh3_native_bridge(lua_State*);
int main(){lua_State L;CK(luaopen_wh3_native_bridge(&L)==1);auto module=L.stack.back().table;CK(module);
 auto call=[&](const char* key,std::vector<Value> in=std::vector<Value>{}){
  L.stack=in;int z=module->fields.at(key).fn(&L);CK(z>=0&&z<=top(&L));return std::vector<Value>(L.stack.end()-z,L.stack.end());
 };
 int pass=0,fail=0;auto test=[&](const char* label,auto fn){fake_alive_allowed=true;try{fn();++pass;std::cout<<"PASS "<<label<<"\n";}catch(const std::exception& e){fake_alive_allowed=true;++fail;std::cout<<"FAIL "<<label<<": "<<e.what()<<"\n";}};
 test("actual Lua export creates full method table",[&]{CK(module->fields.size()==40);for(auto& x:module->fields)CK(x.second.tag==6&&x.second.fn);});
 test("version matches diagnostic gated constant",[&]{auto r=call("version");CK(r.size()==1&&r[0].text==wh3::kDiagnosticBridgeVersion);});
 test("bridge version identity consistent",[&]{
  auto r_ver=call("version");
  auto r_stat=call("get_status");
  CK(r_ver.size()==1&&r_stat.size()==1&&r_stat[0].table);
  auto stat_ver=r_stat[0].table->fields.at("version").text;
  CK(r_ver[0].text==stat_ver);
  CK(stat_ver==wh3::kDiagnosticBridgeVersion);
 });
 test("diagnostic exports callable and return expected tables",[&]{CK(module->fields.count("diagnostic_bind_evidence_unit_v3")==1&&module->fields.count("diagnostic_command_root_v3")==1&&module->fields.count("stop_observer")==1);
  auto r1=call("diagnostic_gate_status");
  CK(r1.size()==1&&r1[0].table);
  CK(r1[0].table->fields.at("component_chain_gate").boolean);
  CK(r1[0].table->fields.at("entity_alive_gate").boolean);
  CK(r1[0].table->fields.at("bridge_version").text==wh3::kDiagnosticBridgeVersion);
 });
 test("R1 V2 capability is explicitly retired after RE07",[&]{
  auto r=call("r1_evidence_capabilities_v2");CK(r.size()==1&&r[0].table);auto fields=r[0].table->fields;CK(fields.at("schema").number==2);
  CK(!fields.at("game_build_verified").boolean&&!fields.at("execution_identity").boolean&&!fields.at("entity_snapshot").boolean&&!fields.at("combat_groups").boolean&&!fields.at("fresh_engagement").boolean);
  CK(fields.at("reason").text=="V2_RETIRED_USE_V3"&&fields.at("evidence_method").text=="RETIRED_RE07_STATE74_INVALID");
 });
 test("R1 V3 capabilities expose core execution identity and quarantine physical evidence",[&]{
  auto r=call("r1_evidence_capabilities_v3");CK(r.size()==1&&r[0].table);auto f=r[0].table->fields;CK(f.at("schema").number==3);CK(!f.at("state74_runtime_melee").boolean);CK(!f.at("game_build_verified").boolean);CK(f.at("evidence_method").text=="COREPATH_EXECUTION_IDENTITY_ONLY");CK(f.at("physical_evidence_quarantined").boolean);CK(!f.at("entity_snapshot").boolean&&!f.at("combat_groups").boolean&&!f.at("contact_pairs").boolean&&!f.at("target_specific_physical_contact").boolean);
 });
 test("R1 V2 readers validate arguments and then fail explicitly retired",[&]{
  auto bad_order=call("read_active_order_identity_v2",{n(1001)});CK(bad_order.size()==2&&bad_order[0].tag==0&&bad_order[1].text=="UNIT_UID_DECIMAL_STRING_REQUIRED");
  auto retired_order=call("read_active_order_identity_v2",{s("1001")});CK(retired_order.size()==2&&retired_order[0].tag==0&&retired_order[1].text=="V2_RETIRED_USE_V3");
  auto missing_ms=call("read_entity_snapshot_v2",{s("1001")});CK(missing_ms.size()==2&&missing_ms[0].tag==0&&missing_ms[1].text=="MODEL_MS_NUMBER_REQUIRED");
  auto retired_entity=call("read_entity_snapshot_v2",{s("1001"),n(100)});CK(retired_entity.size()==2&&retired_entity[0].tag==0&&retired_entity[1].text=="V2_RETIRED_USE_V3");
  auto bad_combat=call("read_combat_groups_v2",{n(1001)});CK(bad_combat.size()==2&&bad_combat[0].tag==0&&bad_combat[1].text=="UNIT_UID_DECIMAL_STRING_REQUIRED");
  auto retired_combat=call("read_combat_groups_v2",{s("1001")});CK(retired_combat.size()==2&&retired_combat[0].tag==0&&retired_combat[1].text=="V2_RETIRED_USE_V3");
  auto bad_contact=call("read_contact_events_v3",{n(0)});CK(bad_contact.size()==2&&bad_contact[0].tag==0&&bad_contact[1].text=="PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");
 });
 test("evidence root resolver follows Lua userdata -> CA wrapper -> BattleUnit +8",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t ca=0xC0000,root=0xD0000,arr=0xD1000,entity=0xD2000,component=0xD3000;fake_block(ca,0x20);fake_block(root,0x200);fake_block(arr,0x10);fake_entity(entity,component);
  std::uintptr_t p=ca;std::memcpy(fake_wrapper,&p,8);fake_put(ca,8,root);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,entity);
  auto r=call("bind_evidence_unit_v3",{s("1001"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");
 });
 test("evidence root resolver supports CA wrapper +16",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t ca=0xE0000,root=0xF0000,arr=0xF1000,entity=0xF2000,component=0xF3000;fake_block(ca,0x20);fake_block(root,0x200);fake_block(arr,0x10);fake_entity(entity,component);
  std::uintptr_t p=ca;std::memcpy(fake_wrapper,&p,8);fake_put(ca,16,root);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,entity);
  auto r=call("bind_evidence_unit_v3",{s("1002"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");
 });
 test("evidence root resolver is pre-gate-safe and never calls alive virtual",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();fake_alive_calls=0;fake_alive_allowed=false;
  const std::uintptr_t ca=0x1010000,root=0x1020000,arr=0x1021000,entity=0x1022000,component=0x1023000;fake_block(ca,0x20);fake_block(root,0x200);fake_block(arr,0x10);fake_entity(entity,component);
  std::uintptr_t p=ca;std::memcpy(fake_wrapper,&p,8);fake_put(ca,8,root);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,entity);
  auto r=call("bind_evidence_unit_v3",{s("1003"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");CK(fake_alive_calls==0);fake_alive_allowed=true;
 });
 test("evidence root resolver rejects ambiguous valid candidates",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t r1=0x110000,r2=0x120000,a1=0x111000,a2=0x121000,e1=0x112000,e2=0x122000,c1=0x113000,c2=0x123000;for(auto x:{r1,r2})fake_block(x,0x200);fake_block(a1,0x10);fake_block(a2,0x10);fake_entity(e1,c1);fake_entity(e2,c2);
  std::memcpy(fake_wrapper+8,&r1,8);std::memcpy(fake_wrapper+16,&r2,8);wh3::Id one=1;fake_put(r1,0x114,one);fake_put(r1,0x118,a1);fake_put(a1,0,e1);fake_put(r2,0x114,one);fake_put(r2,0x118,a2);fake_put(a2,0,e2);
  auto r=call("bind_evidence_unit_v3",{s("3003"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");
 });
 test("evidence root resolver rejects missing candidates without inventing a root",[&]{std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();auto r=call("bind_evidence_unit_v3",{s("4004"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");});
test("evidence root resolver rejects shallow container lookalike with unverified entity objects",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t root=0x130000,arr=0x131000,bogus=0x132000;fake_block(root,0x200);fake_block(arr,0x10);fake_block(bogus,0x20);std::memcpy(fake_wrapper+8,&root,8);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,bogus);
  auto r=call("bind_evidence_unit_v3",{s("5005"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");
 });
 test("diagnostic resolver follows deeper userdata pointer graph and expected men",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t w1=0x160000,w2=0x161000,root=0x162000,arr=0x163000,entity=0x164000,component=0x165000;
  fake_block(w1,0x80);fake_block(w2,0x80);fake_block(root,0x200);fake_block(arr,0x10);fake_entity(entity,component);
  std::uintptr_t p1=w1;std::memcpy(fake_wrapper+24,&p1,8);fake_put(w1,0x30,w2);fake_put(w2,0x48,root);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,entity);
  auto r=call("diagnostic_bind_evidence_unit_v3",{s("6106"),ud(fake_wrapper),n(1)});CK(r.size()==1&&r[0].table);auto f=r[0].table->fields;
  CK(f.at("passed").boolean&&f.at("root").text==std::to_string(root)&&f.at("method").text=="USERDATA_GRAPH"&&f.at("candidate_count").number==1);
 });
 test("diagnostic command-root API reports missing without inventing a root",[&]{auto r=call("diagnostic_command_root_v3",{s("9999")});CK(r.size()==2&&r[0].tag==1&&!r[0].boolean&&r[1].text=="COMMAND_ROOT_NOT_OBSERVED");});
 test("diagnostic Lua API contract matches harness fields and arguments",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t ca=0x140000,root=0x150000,arr=0x151000,entity=0x152000,component=0x153000;
  fake_block(ca,0x20);fake_block(root,0x200);fake_block(arr,0x10);fake_entity(entity,component);
  std::uintptr_t pca=ca;std::memcpy(fake_wrapper,&pca,8);fake_put(ca,8,root);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,entity);
  auto bound=call("diagnostic_bind_evidence_unit_v3",{s("6006"),ud(fake_wrapper),n(1)});CK(bound.size()==1&&bound[0].table&&bound[0].table->fields.at("passed").boolean);
  auto comp=call("diagnostic_probe_component_chain",{s("6006")});CK(comp.size()==1&&comp[0].table);auto cf=comp[0].table->fields;
  CK(diag_component_sample_limit==300);
  for(auto key:{"passed","slot_count","sampled_count","reason"})CK(cf.count(key)==1);
  auto missing=call("diagnostic_probe_entity_alive",{s("6006")});CK(missing.size()==2&&missing[0].tag==0&&missing[1].text=="LUA_MEN_ALIVE_NUMBER_REQUIRED");
  for(float bad:{-1.0f,1.5f,301.0f,std::numeric_limits<float>::quiet_NaN()}){auto rr=call("diagnostic_probe_entity_alive",{s("6006"),n(bad)});CK(rr.size()==2&&rr[0].tag==0&&rr[1].text=="LUA_MEN_ALIVE_RANGE_0_TO_300");}
  auto alive=call("diagnostic_probe_entity_alive",{s("6006"),n(1)});CK(alive.size()==1&&alive[0].table);auto af=alive[0].table->fields;
  for(auto key:{"match","slot_count","native_alive_count","lua_men_alive","phase","deployment_passed","casualty_passed","gate_passed","reason"})CK(af.count(key)==1);
  auto gs=call("diagnostic_gate_status");CK(gs.size()==1&&gs[0].table);auto gf=gs[0].table->fields;
  for(auto key:{"component_chain_gate","component_gate_root","alive_deployment_passed","alive_casualty_passed","entity_alive_gate","alive_gate_root","build_id","bridge_version"})CK(gf.count(key)==1);
 });
 test("evidence root binder rejects non-userdata",[&]{auto r=call("bind_evidence_unit_v2",{s("1001"),s("no")});CK(r.size()==2&&r[0].tag==0&&r[1].text=="BATTLE_UNIT_USERDATA_REQUIRED");});
 test("float32 ABI number return values",[&]{auto r=call("number_abi_probe");CK(r.size()==2&&r[0].tag==3&&r[0].number==16777215.0f&&r[1].number==1.5f);});
 test("full u32 and float boundary IDs stay strings",[&]{auto r=call("exact_id_probe");CK(r[0].tag==4&&r[0].text=="4294967295"&&r[1].text=="16777217");});
 test("compiled core is not claimed connected",[&]{auto t=call("capabilities")[0].table;CK(t->fields.at("identity_core_compiled").boolean);for(auto key:{"verified_issue","exact_source","native_identity_adapter_connected","observer_hooks_installed"})CK(!t->fields.at(key).boolean);});
 test("observer requires explicit bool true",[&]{auto r=call("start_observer",{s("true")});CK(r.size()==2&&r[0].tag==1&&!r[0].boolean&&r[1].text=="EXPLICIT_OBSERVER_ACK_REQUIRED");});
 test("backend failure forwarded, not fake hooks=true",[&]{auto r=call("start_observer",{b(true)});CK(r.size()==2&&!r[0].boolean&&r[1].text=="TEST_BACKEND_NOT_GAME");});
 test("invalid session produces nil/error",[&]{auto r=call("begin_battle",{n(1)});CK(r.size()==2&&r[0].tag==0);});
 std::string epoch;
 test("begin returns one epoch string, not bool+epoch",[&]{auto r=call("begin_battle",{s("fixture")});CK(r.size()==1&&r[0].tag==4);epoch=r[0].text;});
 test("duplicate begin refuses reset",[&]{auto r=call("begin_battle",{s("fixture")});CK(r.size()==2&&r[0].tag==0);});
 test("V3 contact events are quarantined from production API",[&]{
  auto r=call("read_contact_events_v3",{s("0"),n(16)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");
 });
 test("journal returns array and metadata separately",[&]{auto r=call("read_journal",{s(epoch),s("0"),n(64)});CK(r.size()==2&&r[0].tag==5&&r[1].tag==5);CK(r[1].table->fields.at("next_after").text=="0");});
 test("numeric epoch is not silently rounded",[&]{auto r=call("read_journal",{n(1),s("0")});CK(r.size()==2&&r[0].tag==0);});
 test("noncanonical and overflowing cursor rejected",[&]{for(auto c:{"01","4294967296","-1","1.0"}){auto r=call("read_journal",{s(epoch),s(c)});CK(r[0].tag==0);}});
 test("page count integer range checked",[&]{for(float count:{0.0f,65.0f,1.5f})CK(call("read_journal",{s(epoch),s("0"),n(count)})[0].tag==0);});
 test("own issuer cannot be enabled from Lua",[&]{auto r=call("issue_verified_command",{b(true)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="EXPECTED_KIND_QUEUED_UID_REVISION_CALLBACK");});
 test("arming never bypasses missing calibration",[&]{auto r=call("arm_verified_issue",{b(true)});CK(r[0].tag==0&&(r[1].text=="V3_NATIVE_ISSUE_NOT_AUTHORIZED"||r[1].text=="V3_CALIBRATION_NOT_READY"||r[1].text=="ADAPTER_NOT_READY"));});
 test("journal metadata supports the v0.2.2 client shape",[&]{auto r=call("read_journal",{s(epoch),s("0")});auto t=r[1].table;CK(t->fields.at("overrun").tag==1&&t->fields.at("count").tag==3&&t->fields.at("error").text=="Ok"&&t->fields.at("journal_fault").text=="Ok");});
 test("pending cancel reports missing token",[&]{auto r=call("cancel_pending_issue",{s("1")});CK(r[0].tag==0&&r[1].text=="MISSING");});
 test("end returns actual boolean success",[&]{auto r=call("end_battle",{s(epoch)});CK(r.size()==1&&r[0].tag==1&&r[0].boolean);});
 test("closed session reports recording false",[&]{auto r=call("get_status");CK(!r[0].table->fields.at("recording").boolean);});
 test("RC6 public Move API requires coordinate metadata",[&]{Value cb;cb.tag=6;
  auto r=call("issue_verified_command",{s("MOVE"),b(false),s("1"),s("1"),cb});
  CK(r[0].tag==0&&r[1].text=="EXPECTED_MOVE_DESTINATION_XYZ");});
 test("RC6 coordinate metadata rejects NaN before callback",[&]{Value cb;cb.tag=6;
  auto r=call("issue_verified_command",{s("MOVE"),b(false),s("1"),s("1"),cb,n(std::numeric_limits<float>::quiet_NaN()),n(0),n(1)});
  CK(r[0].tag==0&&r[1].text=="MOVE_DESTINATION_INVALID");});
 test("RC6 coordinate metadata does not bypass native readiness",[&]{Value cb;cb.tag=6;
  auto r=call("issue_verified_command",{s("MOVE"),b(false),s("1"),s("1"),cb,n(1),n(0),n(2)});
  CK(r[0].tag==0&&r[1].text=="ADAPTER_NOT_READY");});
 test("RC6 Attack does not accept Move coordinate fields",[&]{Value cb;cb.tag=6;
  auto r=call("issue_verified_command",{s("ATTACK"),b(false),s("1"),s("1"),cb,n(1),n(0),n(2)});
  CK(r[0].tag==0&&r[1].text=="MOVE_DESTINATION_KIND_MISMATCH");});
 test("pending cancel requires exact decimal issue id",[&]{for(auto v:{"01","-1","1.0","4294967296"}){auto r=call("cancel_pending_issue",{s(v)});CK(r[0].tag==0);}});
 test("RC6 status exposes bounded pending slots",[&]{auto t=call("get_status")[0].table;
  CK(t->fields.at("pending_count").text=="0"&&t->fields.at("pending_limit").text=="32");});
 test("v1.0.3 journal exports key states and exact 64-bit sample time",[&]{
  auto& h=wh3::host();wh3::NativeFunctions fn{};
  fn.move=+[](void*,std::uint32_t,void*,std::uint8_t)->std::uint32_t{return 1;};
  fn.attack=fn.move;fn.allocate=+[](void*,std::uint32_t)->void*{return nullptr;};fn.halt=+[](void*,std::uint32_t){};
  CK(h.set_native_functions(fn));auto start=call("begin_battle",{s("input-fixture")});epoch=start.at(0).text;
  wh3::InputSnapshot input{};input.sampled=true;input.foreground=true;input.shift=true;input.right_shift=true;
  input.tick_ms=9007199254740993ULL;input.thread_id=42;
  h.order(wh3::Kind::Move,reinterpret_cast<void*>(0x100000),0,nullptr,0,input);
  auto rows=call("read_journal",{s(epoch),s("0")}).at(0).table;
  auto fields=rows->array.at(1).table->fields;
  CK(fields.at("input_sampled").boolean&&fields.at("input_shift").boolean&&fields.at("input_right_shift").boolean);
  CK(!fields.at("is_queued").boolean&&fields.at("source").text=="UNKNOWN");
  CK(fields.at("input_tick_ms").tag==4&&fields.at("input_tick_ms").text=="9007199254740993");
  CK(fields.at("input_stage").text=="NATIVE_ORDER_ENTRY"&&fields.at("input_thread_id").text=="42");
 });
 test("v1.0.3 background samples omit all key-down claims",[&]{
  wh3::InputSnapshot input{};input.sampled=true;input.foreground=false;input.shift=true;
  wh3::host().order(wh3::Kind::Move,reinterpret_cast<void*>(0x100000),0,nullptr,1,input);
  auto fields=call("read_journal",{s(epoch),s("0")}).at(0).table->array.at(2).table->fields;
  CK(fields.at("input_sampled").boolean&&!fields.at("input_foreground").boolean);
  CK(fields.count("input_shift")==0&&fields.count("input_left_shift")==0&&fields.count("input_right_shift")==0);
 });
 test("v1.0.3 unsampled defaults export an explicit unavailable stage",[&]{
  wh3::host().order(wh3::Kind::Move,reinterpret_cast<void*>(0x100000),0,nullptr,0);
  auto fields=call("read_journal",{s(epoch),s("0")}).at(0).table->array.at(3).table->fields;
  CK(!fields.at("input_sampled").boolean&&fields.at("input_stage").text=="UNAVAILABLE"&&fields.count("input_shift")==0);
 });
 test("smart guard local unit registration and clearing export contract",[&]{
  auto reg_bad=call("smart_guard_register_local_unit",{n(1001)});CK(reg_bad.size()==2&&reg_bad[0].tag==0&&reg_bad[1].text=="UNIT_UID_DECIMAL_STRING_REQUIRED");
  auto reg_ok=call("smart_guard_register_local_unit",{s("1001")});CK(reg_ok.size()==1&&reg_ok[0].tag==1&&reg_ok[0].boolean);
  auto unreg_bad=call("smart_guard_unregister_local_unit",{n(1001)});CK(unreg_bad.size()==2&&unreg_bad[0].tag==0&&unreg_bad[1].text=="UNIT_UID_DECIMAL_STRING_REQUIRED");
  auto unreg_ok=call("smart_guard_unregister_local_unit",{s("1001")});CK(unreg_ok.size()==1&&unreg_ok[0].tag==1&&unreg_ok[0].boolean);
  auto clear_ok=call("smart_guard_clear_local_units");CK(clear_ok.size()==1&&clear_ok[0].tag==1&&clear_ok[0].boolean);
 });
 test("smart guard drain returns empty array when no cancel requests queued",[&]{
  auto r=call("drain_smart_guard_cancel_requests");CK(r.size()==1&&r[0].tag==5&&r[0].table->array.empty());
 });
 test("multi-client acquire and release lifecycle",[&]{
  auto bad_ac=call("acquire_client",{n(1)});CK(bad_ac.size()==2&&bad_ac[0].tag==0&&bad_ac[1].text=="CLIENT_NAME_STRING_REQUIRED");
  auto ac1=call("acquire_client",{s("BETTER_SHIFT"),s("test_bs")});
  CK(ac1.size()==2&&ac1[0].tag==4&&ac1[1].tag==4);
  const std::string token1=ac1[0].text;
  const std::string epoch1=ac1[1].text;
  CK(!token1.empty()&&!epoch1.empty()&&epoch1!="0");
  auto ac2=call("acquire_client",{s("TRUE_GUARD"),s("test_tg")});
  CK(ac2.size()==2&&ac2[0].tag==4&&ac2[1].tag==4);
  const std::string token2=ac2[0].text;
  const std::string epoch2=ac2[1].text;
  CK(token2!=token1&&epoch2==epoch1);
  auto st=call("get_status")[0].table;
  CK(st->fields.at("active_clients").number==2.0f);
  auto bad_sg=call("smart_guard_enable",{s(token1),b(true)});
  CK(bad_sg.size()==2&&bad_sg[0].tag==0&&bad_sg[1].text=="TRUE_GUARD_CLIENT_REQUIRED");
  auto ok_sg=call("smart_guard_enable",{s(token2),b(true)});
  CK(ok_sg.size()==1&&ok_sg[0].boolean);
  auto st2=call("get_status")[0].table;
  CK(st2->fields.at("smart_guard_client_active").boolean);
  auto rel1=call("release_client",{s(token1)});
  CK(rel1.size()==1&&rel1[0].boolean);
  auto st3=call("get_status")[0].table;
  CK(st3->fields.at("active_clients").number==1.0f);
  CK(st3->fields.at("smart_guard_client_active").boolean);
  auto rel2=call("release_client",{s(token2)});
  CK(rel2.size()==1&&rel2[0].boolean);
  auto st4=call("get_status")[0].table;
  CK(st4->fields.at("active_clients").number==0.0f);
  CK(!st4->fields.at("smart_guard_client_active").boolean);
 });
 std::cout<<"TOTAL "<<pass<<" PASS "<<fail<<" FAIL (float32 C API fixture, not Lua VM)\n";return fail?1:0;
}
