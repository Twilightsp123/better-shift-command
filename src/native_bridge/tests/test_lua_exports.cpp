// A float32 Lua-C-API stack fixture. NOT a Lua VM or WH3 runtime test.
#include "wh3/lua51_abi.hpp"
#include "wh3/bridge_host.hpp"
#include <map>
#include <vector>
#include <memory>
#include <string>
#include <cstring>
#include <iostream>
#include <stdexcept>
using wh3::lua51::CFunction;
struct Table;
struct Value {int tag=0;std::string text;float number=0;bool boolean=false;CFunction fn=nullptr;std::shared_ptr<Table> table;};
struct Table {std::map<std::string,Value> fields;std::map<int,Value> array;};
struct lua_State {std::vector<Value> stack;};
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)
Value s(const std::string& v){Value x;x.tag=4;x.text=v;return x;}
Value n(float f){Value x;x.tag=3;x.number=f;return x;}
Value b(bool f){Value x;x.tag=1;x.boolean=f;return x;}
Value& at(lua_State* L,int i){int p=i>0?i-1:static_cast<int>(L->stack.size())+i;return L->stack.at(static_cast<std::size_t>(p));}
void settop(lua_State* L,int n){CK(n>=0);L->stack.resize(static_cast<std::size_t>(n));}
void pushvalue(lua_State* L,int n){auto v=at(L,n);L->stack.push_back(v);}
int protected_call(lua_State*,int,int,int){throw std::runtime_error("unexpected Lua callback before gate ready");}
int top(lua_State* L){return static_cast<int>(L->stack.size());}
int type(lua_State* L,int i){if(i>top(L)||i==0||i < -top(L))return -1;return at(L,i).tag;}
const char* string(lua_State* L,int i,std::size_t* len){auto& v=at(L,i);if(v.tag!=4)return nullptr;if(len)*len=v.text.size();return v.text.data();}
float number(lua_State* L,int i){return at(L,i).number;}
int boolean(lua_State* L,int i){return at(L,i).boolean?1:0;}
void nil(lua_State* L){L->stack.emplace_back();}
void pushnum(lua_State* L,float v){L->stack.push_back(n(v));}
void pushstr(lua_State* L,const char* p,std::size_t z){L->stack.push_back(s(std::string(p,z)));}
void pushbool(lua_State* L,int v){L->stack.push_back(b(v!=0));}
void table(lua_State* L,int,int){Value v;v.tag=5;v.table=std::make_shared<Table>();L->stack.push_back(v);}
void setfield(lua_State* L,int i,const char* key){auto t=at(L,i).table;CK(t);auto v=L->stack.back();L->stack.pop_back();t->fields[key]=v;}
void setarray(lua_State* L,int i,int index){auto t=at(L,i).table;CK(t);auto v=L->stack.back();L->stack.pop_back();t->array[index]=v;}
void closure(lua_State* L,CFunction fn,int up){CK(up==0);Value v;v.tag=6;v.fn=fn;L->stack.push_back(v);}
template<class F> void* ptr(F f){void* p=nullptr;static_assert(sizeof p==sizeof f);std::memcpy(&p,&f,sizeof p);return p;}
namespace wh3 {
std::uintptr_t platform_image_base() noexcept{return 0x140000000ULL;}
bool platform_write(std::uintptr_t,const void*,std::size_t) noexcept{return false;}
bool platform_frame_active(const FrameIdentity&) noexcept{return false;}
FrameIdentity platform_caller_frame(void*) noexcept{return {};}
bool platform_read(std::uintptr_t,void*,std::size_t) noexcept{return false;}
const char* platform_start_observer(){return "TEST_BACKEND_NOT_GAME";}
bool platform_hooks_installed() noexcept{return false;}
const char* platform_last_error() noexcept{return "TEST_BACKEND_NOT_GAME";}
void* platform_lua_symbol(const char* key) noexcept{
#define MAP(k,f) if(std::strcmp(key,"lua_" k)==0)return ptr(f)
 MAP("settop",settop);MAP("pushvalue",pushvalue);MAP("pcall",protected_call);MAP("gettop",top);MAP("type",::type);MAP("tolstring",string);MAP("tonumber",number);
 MAP("toboolean",boolean);MAP("pushnil",nil);MAP("pushnumber",pushnum);MAP("pushlstring",pushstr);
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
 test("actual Lua export creates full method table",[&]{CK(module->fields.size()==14);for(auto& x:module->fields)CK(x.second.tag==6&&x.second.fn);});
 test("version differs from installed baseline",[&]{auto r=call("version");CK(r.size()==1&&r[0].text=="0.5.0-attack-native-token");});
 test("float32 ABI number return values",[&]{auto r=call("number_abi_probe");CK(r.size()==2&&r[0].tag==3&&r[0].number==16777215.0f&&r[1].number==1.5f);});
 test("full u32 and float boundary IDs stay strings",[&]{auto r=call("exact_id_probe");CK(r[0].tag==4&&r[0].text=="4294967295"&&r[1].text=="16777217");});
 test("compiled core is not claimed connected",[&]{auto t=call("capabilities")[0].table;CK(t->fields.at("identity_core_compiled").boolean);for(auto key:{"verified_issue","exact_source","native_identity_adapter_connected","observer_hooks_installed"})CK(!t->fields.at(key).boolean);});
 test("observer requires explicit bool true",[&]{auto r=call("start_observer",{s("true")});CK(r.size()==2&&r[0].tag==1&&!r[0].boolean&&r[1].text=="EXPLICIT_OBSERVER_ACK_REQUIRED");});
 test("backend failure forwarded, not fake hooks=true",[&]{auto r=call("start_observer",{b(true)});CK(r.size()==2&&!r[0].boolean&&r[1].text=="TEST_BACKEND_NOT_GAME");});
 test("invalid session produces nil/error",[&]{auto r=call("begin_battle",{n(1)});CK(r.size()==2&&r[0].tag==0);});
 std::string epoch;
 test("begin returns one epoch string, not bool+epoch",[&]{auto r=call("begin_battle",{s("fixture")});CK(r.size()==1&&r[0].tag==4);epoch=r[0].text;});
 test("duplicate begin refuses reset",[&]{auto r=call("begin_battle",{s("fixture")});CK(r.size()==2&&r[0].tag==0);});
 test("journal returns array and metadata separately",[&]{auto r=call("read_journal",{s(epoch),s("0"),n(64)});CK(r.size()==2&&r[0].tag==5&&r[1].tag==5);CK(r[1].table->fields.at("next_after").text=="0");});
 test("numeric epoch is not silently rounded",[&]{auto r=call("read_journal",{n(1),s("0")});CK(r.size()==2&&r[0].tag==0);});
 test("noncanonical and overflowing cursor rejected",[&]{for(auto c:{"01","4294967296","-1","1.0"}){auto r=call("read_journal",{s(epoch),s(c)});CK(r[0].tag==0);}});
 test("page count integer range checked",[&]{for(float count:{0.0f,65.0f,1.5f})CK(call("read_journal",{s(epoch),s("0"),n(count)})[0].tag==0);});
 test("own issuer cannot be enabled from Lua",[&]{auto r=call("issue_verified_command",{b(true)});CK(r.size()==2&&r[0].tag==0&&r[1].text=="EXPECTED_KIND_QUEUED_UID_REVISION_CALLBACK");});
 test("arming never bypasses missing calibration",[&]{auto r=call("arm_verified_issue",{b(true)});CK(r[0].tag==0&&(r[1].text=="ADAPTER_NOT_READY"||r[1].text=="HANDLER_CALIBRATION_NOT_READY"||r[1].text=="EXPERIMENTAL_CALIBRATION_NOT_READY"));});
 test("journal metadata supports the v0.2.2 client shape",[&]{auto r=call("read_journal",{s(epoch),s("0")});auto t=r[1].table;CK(t->fields.at("overrun").tag==1&&t->fields.at("count").tag==3&&t->fields.at("error").text=="Ok"&&t->fields.at("journal_fault").text=="Ok");});
 test("end returns actual boolean success",[&]{auto r=call("end_battle",{s(epoch)});CK(r.size()==1&&r[0].tag==1&&r[0].boolean);});
 test("closed session reports recording false",[&]{auto r=call("get_status");CK(!r[0].table->fields.at("recording").boolean);});
 std::cout<<"TOTAL "<<pass<<" PASS "<<fail<<" FAIL (float32 C API fixture, not Lua VM)\n";return fail?1:0;
}
