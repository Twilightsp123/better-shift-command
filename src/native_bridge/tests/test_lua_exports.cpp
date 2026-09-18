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
void fake_block(std::uintptr_t base,std::size_t size){fake_mem[base]=std::vector<unsigned char>(size);}
template<class T> void fake_put(std::uintptr_t base,std::size_t off,const T& value){auto& b=fake_mem.at(base);CK(off+sizeof(T)<=b.size());std::memcpy(b.data()+off,&value,sizeof(T));}
void fake_entity(std::uintptr_t entity,std::uintptr_t component){
 fake_block(entity,0x200);fake_block(component,0x900);float x=1.0f,z=2.0f;std::uintptr_t c=component;std::uint32_t movement=1;
 fake_put(entity,0x88,x);fake_put(entity,0x90,z);fake_put(entity,0x18,c);fake_put(component,0x4a0,entity);fake_put(component,0x8b0,movement);fake_entities.insert(entity);
}
namespace wh3 {
std::uintptr_t platform_image_base() noexcept{return 0x140000000ULL;}
bool platform_write(std::uintptr_t,const void*,std::size_t) noexcept{return false;}
bool platform_entity_alive(std::uintptr_t entity,bool* alive) noexcept{if(!alive||!fake_entities.count(entity))return false;*alive=true;return true;}
bool platform_combat_group_query(std::uintptr_t,bool*,std::uintptr_t*) noexcept{return false;}
bool platform_frame_active(const FrameIdentity&) noexcept{return false;}
FrameIdentity platform_caller_frame(void*) noexcept{return {};}
bool platform_read(std::uintptr_t address,void* out,std::size_t size) noexcept{
 const auto w=reinterpret_cast<std::uintptr_t>(fake_wrapper);if(address>=w&&address+size<=w+sizeof(fake_wrapper)){std::memcpy(out,fake_wrapper+(address-w),size);return true;}
 for(const auto& kv:fake_mem){const auto base=kv.first;const auto& b=kv.second;if(address>=base&&address+size>=address&&address+size<=base+b.size()){std::memcpy(out,b.data()+(address-base),size);return true;}}
 if(address==0x103ea0&&size==4){Id uid=1001;std::memcpy(out,&uid,4);return true;}return false;
}
const char* platform_start_observer(){return "TEST_BACKEND_NOT_GAME";}
bool platform_hooks_installed() noexcept{return false;}
bool platform_evidence_build_verified() noexcept{return false;}
const char* platform_evidence_build_id() noexcept{return "TEST_UNAVAILABLE";}
std::uint64_t platform_tick_ms() noexcept{return 123456;}
const char* platform_last_error() noexcept{return "TEST_BACKEND_NOT_GAME";}
void* platform_lua_symbol(const char* key) noexcept{
#define MAP(k,f) if(std::strcmp(key,"lua_" k)==0)return ptr(f)
 MAP("settop",settop);MAP("pushvalue",pushvalue);MAP("pcall",protected_call);MAP("gettop",top);MAP("type",::type);MAP("tolstring",string);MAP("tonumber",number);
 MAP("toboolean",boolean);MAP("touserdata",userdata);MAP("pushnil",nil);MAP("pushnumber",pushnum);MAP("pushlstring",pushstr);
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
 int pass=0,fail=0;auto test=[&](const char* label,auto fn){try{fn();++pass;std::cout<<"PASS "<<label<<"\n";}catch(const std::exception& e){++fail;std::cout<<"FAIL "<<label<<": "<<e.what()<<"\n";}};
 test("actual Lua export creates full method table",[&]{CK(module->fields.size()==27);for(auto& x:module->fields)CK(x.second.tag==6&&x.second.fn);});
 test("version differs from installed baseline",[&]{auto r=call("version");CK(r.size()==1&&r[0].text=="1.0.15-r4-evidence-v3-validated-userdata-root");});
 test("R1 V2 capability is explicitly retired after RE07",[&]{
  auto r=call("r1_evidence_capabilities_v2");CK(r.size()==1&&r[0].table);auto fields=r[0].table->fields;CK(fields.at("schema").number==2);
  CK(!fields.at("game_build_verified").boolean&&!fields.at("execution_identity").boolean&&!fields.at("entity_snapshot").boolean&&!fields.at("combat_groups").boolean&&!fields.at("fresh_engagement").boolean);
  CK(fields.at("reason").text=="V2_RETIRED_USE_V3"&&fields.at("evidence_method").text=="RETIRED_RE07_STATE74_INVALID");
 });
 test("R1 V3 capabilities expose contact-pair model without state74 melee claim",[&]{
  auto r=call("r1_evidence_capabilities_v3");CK(r.size()==1&&r[0].table);auto f=r[0].table->fields;CK(f.at("schema").number==3);CK(!f.at("state74_runtime_melee").boolean);CK(!f.at("game_build_verified").boolean);CK(f.at("evidence_method").text=="R1_RAW_EVIDENCE_V3_CONTACT_PAIR");
 });
 test("R1 V2 readers validate arguments and then fail explicitly retired",[&]{
  auto bad_order=call("read_active_order_identity_v2",{n(1001)});CK(bad_order.size()==2&&bad_order[0].tag==0&&bad_order[1].text=="UNIT_UID_DECIMAL_STRING_REQUIRED");
  auto retired_order=call("read_active_order_identity_v2",{s("1001")});CK(retired_order.size()==2&&retired_order[0].tag==0&&retired_order[1].text=="V2_RETIRED_USE_V3");
  auto missing_ms=call("read_entity_snapshot_v2",{s("1001")});CK(missing_ms.size()==2&&missing_ms[0].tag==0&&missing_ms[1].text=="MODEL_MS_NUMBER_REQUIRED");
  auto retired_entity=call("read_entity_snapshot_v2",{s("1001"),n(100)});CK(retired_entity.size()==2&&retired_entity[0].tag==0&&retired_entity[1].text=="V2_RETIRED_USE_V3");
  auto bad_combat=call("read_combat_groups_v2",{n(1001)});CK(bad_combat.size()==2&&bad_combat[0].tag==0&&bad_combat[1].text=="UNIT_UID_DECIMAL_STRING_REQUIRED");
  auto retired_combat=call("read_combat_groups_v2",{s("1001")});CK(retired_combat.size()==2&&retired_combat[0].tag==0&&retired_combat[1].text=="V2_RETIRED_USE_V3");
  auto bad_contact=call("read_contact_events_v3",{n(0)});CK(bad_contact.size()==2&&bad_contact[0].tag==0&&bad_contact[1].text=="AFTER_SERIAL_DECIMAL_STRING_REQUIRED");
 });
 test("evidence root resolver follows Lua userdata -> CA wrapper -> BattleUnit +8",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t ca=0xC0000,root=0xD0000,arr=0xD1000,entity=0xD2000,component=0xD3000;fake_block(ca,0x20);fake_block(root,0x200);fake_block(arr,0x10);fake_entity(entity,component);
  std::uintptr_t p=ca;std::memcpy(fake_wrapper,&p,8);fake_put(ca,8,root);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,entity);
  auto r=call("bind_evidence_unit_v3",{s("1001"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==1&&r[0].boolean&&r[1].text==std::to_string(root));
 });
 test("evidence root resolver supports CA wrapper +16",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t ca=0xE0000,root=0xF0000,arr=0xF1000,entity=0xF2000,component=0xF3000;fake_block(ca,0x20);fake_block(root,0x200);fake_block(arr,0x10);fake_entity(entity,component);
  std::uintptr_t p=ca;std::memcpy(fake_wrapper,&p,8);fake_put(ca,16,root);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,entity);
  auto r=call("bind_evidence_unit_v3",{s("1002"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==1&&r[0].boolean&&r[1].text==std::to_string(root));
 });
 test("evidence root resolver rejects ambiguous valid candidates",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t r1=0x110000,r2=0x120000,a1=0x111000,a2=0x121000,e1=0x112000,e2=0x122000,c1=0x113000,c2=0x123000;for(auto x:{r1,r2})fake_block(x,0x200);fake_block(a1,0x10);fake_block(a2,0x10);fake_entity(e1,c1);fake_entity(e2,c2);
  std::memcpy(fake_wrapper+8,&r1,8);std::memcpy(fake_wrapper+16,&r2,8);wh3::Id one=1;fake_put(r1,0x114,one);fake_put(r1,0x118,a1);fake_put(a1,0,e1);fake_put(r2,0x114,one);fake_put(r2,0x118,a2);fake_put(a2,0,e2);
  auto r=call("bind_evidence_unit_v3",{s("3003"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="EVIDENCE_ROOT_AMBIGUOUS_OR_CONFLICT");
 });
 test("evidence root resolver rejects missing candidates without inventing a root",[&]{std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();auto r=call("bind_evidence_unit_v3",{s("4004"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="EVIDENCE_ROOT_NOT_FOUND");});
test("evidence root resolver rejects shallow container lookalike with unverified entity objects",[&]{
  std::memset(fake_wrapper,0,sizeof fake_wrapper);fake_mem.clear();fake_entities.clear();
  const std::uintptr_t root=0x130000,arr=0x131000,bogus=0x132000;fake_block(root,0x200);fake_block(arr,0x10);fake_block(bogus,0x20);std::memcpy(fake_wrapper+8,&root,8);wh3::Id one=1;fake_put(root,0x114,one);fake_put(root,0x118,arr);fake_put(arr,0,bogus);
  auto r=call("bind_evidence_unit_v3",{s("5005"),ud(fake_wrapper)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="EVIDENCE_ROOT_NOT_FOUND");
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
 test("V3 contact events export exact pair ownership and native tick",[&]{
  const std::uintptr_t rootA=0xA0000,arrA=0xA1000,entityA=0xA2000,rootB=0xB0000,arrB=0xB1000,entityB=0xB2000;
  fake_block(rootA,0x200);fake_block(arrA,0x20);fake_block(rootB,0x200);fake_block(arrB,0x20);
  wh3::Id one=1;fake_put(rootA,0x114,one);fake_put(rootA,0x118,arrA);fake_put(arrA,0,entityA);
  fake_put(rootB,0x114,one);fake_put(rootB,0x118,arrB);fake_put(arrB,0,entityB);
  auto& h=wh3::host();CK(h.bind_evidence_root(1001,rootA)==wh3::Error::Ok);CK(h.bind_evidence_root(2002,rootB)==wh3::Error::Ok);
  h.observe_contact_pair(entityA,entityB,120000);
  auto r=call("read_contact_events_v3",{s("0"),n(16)});CK(r.size()==2&&r[0].tag==5&&r[1].tag==5);
  auto ev=r[0].table->array.at(1).table->fields;CK(ev.at("uid_a").text=="1001"&&ev.at("uid_b").text=="2002");
  CK(ev.at("entity_a").text==std::to_string(entityA)&&ev.at("entity_b").text==std::to_string(entityB));CK(ev.at("tick_ms").text=="120000");
  CK(!ev.at("active_a").boolean&&!ev.at("active_b").boolean);
  auto meta=r[1].table->fields;CK(meta.at("count").number==1&&meta.at("next_after").text=="1"&&!meta.at("gap").boolean);
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
 std::cout<<"TOTAL "<<pass<<" PASS "<<fail<<" FAIL (float32 C API fixture, not Lua VM)\n";return fail?1:0;
}
