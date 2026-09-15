#include "wh3/lua51_abi.hpp"
#include "wh3/bridge_host.hpp"
#include <cstring>
#include <cmath>
#include <cstdio>
#include <mutex>
#include <string>
#include <stdexcept>
namespace wh3::lua51 {
namespace {Api A;std::mutex mu;bool bound=false;}
Api& api(){return A;}
bool bind(){std::lock_guard<std::mutex> l(mu);if(bound)return true;Api next;
#define B(n) do{void* p=platform_lua_symbol("lua_" #n); if(!p)return false;static_assert(sizeof(next.n)==sizeof(p));std::memcpy(&next.n,&p,sizeof(p));}while(false)
 B(settop);B(pushvalue);B(pcall);B(gettop);B(type);B(tolstring);B(tonumber);B(toboolean);B(pushnil);B(pushnumber);
 B(pushlstring);B(pushboolean);B(createtable);B(setfield);B(rawseti);B(pushcclosure);
#undef B
 A=next;bound=true;return true;}
static void str(lua_State* L,const std::string& s){A.pushlstring(L,s.data(),s.size());}
static void fld(lua_State* L,const char* k,const std::string& s){str(L,s);A.setfield(L,-2,k);}
static void bit(lua_State* L,const char* k,bool v){A.pushboolean(L,v?1:0);A.setfield(L,-2,k);}
static void num(lua_State* L,const char* k,float v){A.pushnumber(L,v);A.setfield(L,-2,k);}
static void optid(lua_State* L,const char* k,std::optional<Id> v){if(v)fld(L,k,format_id(*v));}
static void optnum(lua_State* L,const char* k,std::optional<float> v){if(v)num(L,k,*v);}
static int fail(lua_State* L,const char* s){A.pushnil(L);str(L,s);return 2;}
static Result<Id> read_id(lua_State* L,int i){
    if(A.type(L,i)!=4)return {{},Error::Invalid};std::size_t n=0;const char* s=A.tolstring(L,i,&n);
    if(!s||n>10)return {{},Error::Invalid};return parse_id(std::string(s,n));
}
static int version(lua_State* L){str(L,"0.5.1-per-kind-calibration");return 1;}
static int capabilities(lua_State* L){auto s=host().status();A.createtable(L,0,18);
    fld(L,"host_lua_number","float32");num(L,"host_lua_number_bytes",4);
    bit(L,"observer_hooks_installed",platform_hooks_installed());
    bit(L,"exact_source",s.exact_source);bit(L,"verified_issue",s.verified_issue);bit(L,"controller_connected",false);
    bit(L,"complete_command_batch",false);bit(L,"native_identity_adapter_connected",s.native_identity_adapter_connected);
    bit(L,"queued_from_native_entry",true);bit(L,"release_approved",false);
    bit(L,"physical_path_witnesses_ready",s.physical_path_witnesses_ready);
    bit(L,"handler_calibration_ready",s.handler_calibration_ready);bit(L,"experimental_calibration_ready",s.experimental_calibration_ready);
    bit(L,"accepted_move_seen",s.accepted_move_seen);bit(L,"accepted_attack_seen",s.accepted_attack_seen);
    bit(L,"experimental_issue_armed",s.experimental_issue_armed);
    fld(L,"mapping_coverage","OBSERVED_COPY_PATHS_ONLY");
    bit(L,"identity_core_compiled",true);fld(L,"deployment_status","INTEGRATION_CANDIDATE");return 1;}
static int numbers(lua_State* L){A.pushnumber(L,16777215.0f);A.pushnumber(L,1.5f);return 2;}
static int ids(lua_State* L){str(L,"4294967295");str(L,"16777217");return 2;}
static int status(lua_State* L){auto s=host().status();A.createtable(L,0,8);
    fld(L,"version","0.5.1-per-kind-calibration");fld(L,"epoch",format_id(s.epoch));bit(L,"recording",s.recording);
    fld(L,"capture_errors",std::to_string(s.capture_errors));fld(L,"gate_fault",name(s.gate_fault));
    fld(L,"native_error",platform_last_error());fld(L,"adapter_error",s.adapter_error);
    bit(L,"move_path_observed",s.move_path_observed);bit(L,"attack_path_observed",s.attack_path_observed);
    bit(L,"verified_issue",s.verified_issue);bit(L,"exact_source",s.exact_source);
    bit(L,"physical_path_witnesses_ready",s.physical_path_witnesses_ready);bit(L,"handler_calibration_ready",s.handler_calibration_ready);bit(L,"experimental_calibration_ready",s.experimental_calibration_ready);bit(L,"experimental_issue_armed",s.experimental_issue_armed);
    bit(L,"accepted_move_seen",s.accepted_move_seen);bit(L,"accepted_attack_seen",s.accepted_attack_seen);
    fld(L,"physical_spans",std::to_string(s.spans));fld(L,"mapped_orders",std::to_string(s.mapped_orders));fld(L,"unmapped_orders",std::to_string(s.unmapped_orders));
    fld(L,"publish_seen",std::to_string(s.publish_seen));fld(L,"publish_parsed",std::to_string(s.publish_parsed));fld(L,"publish_unparsed",std::to_string(s.publish_unparsed));
    fld(L,"writer_begin_seen",std::to_string(s.writer_begin_seen));fld(L,"writer_finalize_seen",std::to_string(s.writer_finalize_seen));fld(L,"writer_committed",std::to_string(s.writer_committed));
    fld(L,"copy_seen",std::to_string(s.copy_seen));fld(L,"stage_seen",std::to_string(s.stage_seen));fld(L,"selection_seen",std::to_string(s.selection_seen));fld(L,"selection_resolved",std::to_string(s.selection_resolved));
    fld(L,"handler_seen",std::to_string(s.handler_seen));fld(L,"handler_resolved",std::to_string(s.handler_resolved));fld(L,"handler_missed",std::to_string(s.handler_missed));fld(L,"handler_token_bindings",std::to_string(s.handler_token_bindings));
    fld(L,"handler_move_seen",std::to_string(s.handler_move_seen));fld(L,"handler_attack_seen",std::to_string(s.handler_attack_seen));
    fld(L,"native_packet_seen",std::to_string(s.native_packet_seen));fld(L,"native_packet_mapped",std::to_string(s.native_packet_mapped));fld(L,"native_attack_token_bindings",std::to_string(s.native_attack_token_bindings));
    fld(L,"last_issue_bindings",std::to_string(s.last_issue_bindings));fld(L,"last_issue_published",std::to_string(s.last_issue_published));fld(L,"last_issue_depth",std::to_string(s.last_issue_depth));
    fld(L,"last_reader_data",std::to_string(s.last_reader_data));fld(L,"last_reader_a",std::to_string(s.last_reader_a));fld(L,"last_reader_b",std::to_string(s.last_reader_b));
    fld(L,"last_reader_cursor",std::to_string(s.last_reader_cursor));fld(L,"last_reader_end",std::to_string(s.last_reader_end));
    fld(L,"last_reader_lineage_bytes",std::to_string(s.last_reader_lineage_bytes));fld(L,"last_reader_lineage_fragments",std::to_string(s.last_reader_lineage_fragments));
    fld(L,"last_path_stage",s.last_path_stage);return 1;}
static int start(lua_State* L){
    if(A.type(L,1)!=1||!A.toboolean(L,1)){A.pushboolean(L,0);str(L,"EXPLICIT_OBSERVER_ACK_REQUIRED");return 2;}
    const char* e=platform_start_observer();A.pushboolean(L,e?0:1);if(e){str(L,e);return 2;}return 1;
}
static int begin(lua_State* L){
    if(A.type(L,1)!=4)return fail(L,"SESSION_KEY_STRING_REQUIRED");
    std::size_t n=0;auto s=A.tolstring(L,1,&n);if(!s||!n||n>64)return fail(L,"SESSION_KEY_LENGTH_1_TO_64");
    auto r=host().begin(std::string(s,n));if(!r)return fail(L,name(r.error));str(L,format_id(r.value));return 1;
}
static int end(lua_State* L){auto e=read_id(L,1);if(!e)return fail(L,"EPOCH_DECIMAL_STRING_REQUIRED");
    auto r=host().end(e.value);if(r!=Error::Ok)return fail(L,name(r));A.pushboolean(L,1);return 1;}
static int epoch(lua_State* L){str(L,format_id(host().status().epoch));return 1;}
static int revision(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
    auto s=host().unit_snapshot(u.value);if(!s)return fail(L,name(s.error));str(L,format_id(s.value.revision));return 1;}
static int arm(lua_State* L){
 if(A.type(L,1)!=1)return fail(L,"BOOLEAN_ACK_REQUIRED");
 const char* e=host().arm(A.toboolean(L,1)!=0);if(e)return fail(L,e);A.pushboolean(L,1);return 1;
}
static int issue(lua_State* L){
 if(A.gettop(L)!=5||A.type(L,1)!=4||A.type(L,2)!=1||A.type(L,5)!=6)return fail(L,"EXPECTED_KIND_QUEUED_UID_REVISION_CALLBACK");
 std::size_t len=0;const char* raw=A.tolstring(L,1,&len);Kind kind;
 if(len==4&&std::memcmp(raw,"MOVE",4)==0)kind=Kind::Move;
 else if(len==6&&std::memcmp(raw,"ATTACK",6)==0)kind=Kind::Attack;
 else return fail(L,"SUPPORTED_KINDS_MOVE_ATTACK");
 auto uid=read_id(L,3),rev=read_id(L,4);if(!uid||!rev)return fail(L,"UID_REVISION_DECIMAL_STRING_REQUIRED");
 const bool queued=A.toboolean(L,2)!=0;
 A.pushvalue(L,5); // may raise BEFORE a token is active
 auto begin=host().begin_issue(kind,queued,uid.value,rev.value,L);
 if(!begin){A.settop(L,5);return fail(L,begin.error);}
 int code=0;
 try{code=A.pcall(L,0,0,0);}catch(...){host().finish_issue(false);throw;}
 auto finish=host().finish_issue(code==0);A.settop(L,5);
 if(!finish)return fail(L,finish.error);
 str(L,format_id(finish.id));str(L,"PENDING_NATIVE_ACCEPTANCE");return 2;
}
static int ack(lua_State* L){auto e=read_id(L,1),c=read_id(L,2);if(!e||!c)return fail(L,"DECIMAL_STRING_REQUIRED");
    auto r=host().acknowledge(e.value,c.value);if(r!=Error::Ok)return fail(L,name(r));A.pushboolean(L,1);return 1;}
static void event(lua_State* L,const Event& e){
 A.createtable(L,0,30);fld(L,"epoch",format_id(e.epoch));fld(L,"serial",format_id(e.serial));
 fld(L,"command_id",format_id(e.command_id));fld(L,"script_issue_id",format_id(e.script_issue_id));
 fld(L,"unit_uid",format_id(e.order.recipient.uid));
 fld(L,"flags_valid_mask","0"); // native legacy bit layout is not fabricated
fld(L,"unit_revision",format_id(e.revision));
 fld(L,"status",name(e.status));fld(L,"source",name(e.source));fld(L,"order_type",name(e.order.kind));
 bit(L,"engine_seq_valid",e.engine_seq.has_value());fld(L,"engine_seq",format_id(e.engine_seq.value_or(0)));
 if(e.order.queued)bit(L,"is_queued",*e.order.queued);
 optnum(L,"dest_x",e.order.x);optnum(L,"dest_y",e.order.y);optnum(L,"dest_z",e.order.z);
 optid(L,"target_uid",e.order.target_uid);optid(L,"batch_index",e.batch_index);optid(L,"batch_total",e.batch_total);
 if(e.order.target_root){char s[19];std::snprintf(s,sizeof s,"0x%016llx",static_cast<unsigned long long>(*e.order.target_root));fld(L,"target_root",s);}
 if(e.order.raw70)num(L,"raw70",*e.order.raw70);if(e.order.raw71)num(L,"raw71",*e.order.raw71);
 if(e.order.raw72)num(L,"raw72",*e.order.raw72);if(e.order.raw78)num(L,"raw78",*e.order.raw78);
 optid(L,"halt_flags",e.order.halt_flags);
}
static int journal(lua_State* L){auto e=read_id(L,1),c=read_id(L,2);if(!e||!c)return fail(L,"EPOCH_CURSOR_DECIMAL_STRING_REQUIRED");
 std::size_t n=64;if(A.gettop(L)>=3){
    if(A.type(L,3)!=3)return fail(L,"COUNT_NUMBER_REQUIRED");float f=A.tonumber(L,3);
    if(!std::isfinite(f)||f<1||f>64||std::floor(f)!=f)return fail(L,"COUNT_RANGE_1_TO_64");n=static_cast<std::size_t>(f);
 }
 auto r=host().read(e.value,c.value,n);if(!r)return fail(L,name(r.error));const auto& p=r.value;
 A.createtable(L,static_cast<int>(p.events.size()),0);int i=0;
 for(const auto& item:p.events){event(L,item);A.rawseti(L,-2,++i);}
 A.createtable(L,0,8);fld(L,"epoch",format_id(p.epoch));fld(L,"next_after",format_id(p.next_after));
 fld(L,"newest_serial",format_id(p.newest));fld(L,"oldest_serial",format_id(p.oldest));
 fld(L,"dropped",std::to_string(p.dropped));bit(L,"gap",p.gap);bit(L,"complete",!p.gap);bit(L,"overrun",p.gap);num(L,"count",static_cast<float>(p.events.size()));
 fld(L,"error",p.gap?"Overrun":"Ok");fld(L,"journal_fault",host().status().gate_fault==Error::Ok?"Ok":name(host().status().gate_fault));return 2;
}
// Never allow a C++ exception to escape through the Lua C ABI. Native SEH/OOM
// longjmp from a Lua allocator is not falsely advertised as recoverable here.
template<int(*F)(lua_State*)> int boundary(lua_State* L){try{return F(L);}catch(...){return fail(L,"BRIDGE_CPP_EXCEPTION");}}
int open(lua_State* L){if(!bind())return 0;A.createtable(L,0,15);
#define REG(k,f) A.pushcclosure(L,boundary<f>,0);A.setfield(L,-2,k)
 REG("version",version);REG("capabilities",capabilities);REG("number_abi_probe",numbers);
 REG("exact_id_probe",ids);REG("get_status",status);REG("start_observer",start);
 REG("begin_battle",begin);REG("end_battle",end);REG("get_battle_epoch",epoch);
 REG("get_unit_revision",revision);REG("arm_verified_issue",arm);REG("issue_verified_command",issue);
 REG("read_journal",journal);REG("acknowledge",ack);
#undef REG
 return 1;}
} // namespace
#ifdef _WIN32
#define WH3_EXPORT __declspec(dllexport)
#else
#define WH3_EXPORT __attribute__((visibility("default")))
#endif
extern "C" WH3_EXPORT int luaopen_wh3_native_bridge(lua_State* L){
 try{return wh3::lua51::open(L);}catch(...){return 0;}
}
