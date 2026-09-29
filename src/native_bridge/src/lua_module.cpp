#include "wh3/lua51_abi.hpp"
#include "wh3/bridge_host.hpp"
#include <cstring>
#include <cmath>
#include <cstdio>
#include <mutex>
#include <string>
#include <stdexcept>
#include <limits>
namespace wh3::lua51 {
namespace {Api A;std::mutex mu;bool bound=false;}
Api& api(){return A;}
bool bind(){std::lock_guard<std::mutex> l(mu);if(bound)return true;Api next;
#define B(n) do{void* p=platform_lua_symbol("lua_" #n); if(!p)return false;static_assert(sizeof(next.n)==sizeof(p));std::memcpy(&next.n,&p,sizeof(p));}while(false)
 B(settop);B(pushvalue);B(pcall);B(gettop);B(type);B(tolstring);B(tonumber);B(toboolean);B(touserdata);B(pushnil);B(pushnumber);
 B(pushlstring);B(pushboolean);B(createtable);B(setfield);B(rawseti);B(pushcclosure);
 // lua_objlen is part of Lua 5.1, but keep it optional so an export-stripped host
 // cannot prevent the entire bridge from loading. Diagnostic discovery falls
 // back to the historical 24-byte seed window if it is unavailable.
 if(void* p=platform_lua_symbol("lua_objlen")){static_assert(sizeof(next.objlen)==sizeof(p));std::memcpy(&next.objlen,&p,sizeof p);}
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
[[maybe_unused]] static bool read_u64(lua_State* L,int i,std::uint64_t& out){
    if(A.type(L,i)!=4)return false;std::size_t n=0;const char* s=A.tolstring(L,i,&n);if(!s||n==0||n>20)return false;
    std::uint64_t v=0;for(std::size_t k=0;k<n;++k){if(s[k]<'0'||s[k]>'9')return false;const auto d=static_cast<unsigned>(s[k]-'0');if(v>(std::numeric_limits<std::uint64_t>::max()-d)/10)return false;v=v*10+d;}out=v;return true;
}
static void u64str(lua_State* L,const char* k,std::uint64_t v){fld(L,k,std::to_string(v));}
static int version(lua_State* L){str(L,kDiagnosticBridgeVersion);return 1;}
static int capabilities(lua_State* L){auto s=host().status();A.createtable(L,0,20);
    fld(L,"host_lua_number","float32");num(L,"host_lua_number_bytes",4);
    bit(L,"observer_hooks_installed",platform_hooks_installed());
    bit(L,"exact_source",s.exact_source);bit(L,"verified_issue",s.verified_issue);bit(L,"controller_connected",false);
    bit(L,"complete_command_batch",false);bit(L,"native_identity_adapter_connected",s.native_identity_adapter_connected);
    bit(L,"queued_from_native_entry",true);bit(L,"release_approved",s.native_issue_authorized);
    bit(L,"physical_path_witnesses_ready",s.physical_path_witnesses_ready);
    bit(L,"handler_calibration_ready",s.handler_calibration_ready);
    bit(L,"native_issue_authorized",s.native_issue_authorized);bit(L,"v3_issue_calibration_ready",s.v3_issue_calibration_ready);bit(L,"v3_issue_armed",s.v3_issue_armed);
    // Compatibility aliases; new controllers use the v3_* fields above.
    bit(L,"experimental_calibration_ready",s.experimental_calibration_ready);bit(L,"experimental_issue_armed",s.experimental_issue_armed);
    bit(L,"accepted_move_seen",s.accepted_move_seen);bit(L,"accepted_attack_seen",s.accepted_attack_seen);
    fld(L,"mapping_coverage","OBSERVED_COPY_PATHS_ONLY");
    bit(L,"smart_guard_capable",true);bit(L,"smart_guard_installed",s.smart_guard_installed);bit(L,"smart_guard_enabled",s.smart_guard_enabled);
    bit(L,"smart_guard_client_active",s.smart_guard_client_active);num(L,"active_clients",static_cast<float>(s.active_clients));
    bit(L,"identity_core_compiled",true);fld(L,"deployment_status",s.native_issue_authorized?"V3_RUNTIME_VERIFIED":"OBSERVER_NOT_VERIFIED");return 1;}
// R1 Evidence V3. Native exposes only build-locked facts; Lua owns R1 verdicts.
static int evidence_caps(lua_State* L){
 const bool build_ok=platform_hooks_installed();
 A.createtable(L,0,16);
 num(L,"schema",3);
 bit(L,"game_build_verified",build_ok);
 bit(L,"execution_identity",build_ok);
 bit(L,"entity_snapshot",false);
 bit(L,"combat_groups",false);
 bit(L,"contact_pairs",false);
 bit(L,"target_specific_physical_contact",false);
 bit(L,"physical_evidence_quarantined",true);
 bit(L,"state74_runtime_melee",false);
 fld(L,"build_id",platform_evidence_build_id());
 fld(L,"evidence_method","COREPATH_EXECUTION_IDENTITY_ONLY");
 fld(L,"reason",build_ok?"OK_COREPATH_PHYSICAL_QUARANTINED":"BUILD_NOT_VERIFIED");
 return 1;
}
static int evidence_caps_v2_retired(lua_State* L){A.createtable(L,0,10);num(L,"schema",2);bit(L,"game_build_verified",false);bit(L,"execution_identity",false);bit(L,"entity_snapshot",false);bit(L,"combat_groups",false);bit(L,"fresh_engagement",false);fld(L,"build_id",platform_evidence_build_id());fld(L,"evidence_method","RETIRED_RE07_STATE74_INVALID");fld(L,"reason","V2_RETIRED_USE_V3");return 1;}
static int bind_evidence_unit_v2_retired(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");if(A.type(L,2)!=7)return fail(L,"BATTLE_UNIT_USERDATA_REQUIRED");return fail(L,"V2_RETIRED_USE_V3");}
static int order_identity_read_v2_retired(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");return fail(L,"V2_RETIRED_USE_V3");}
static int entity_snapshot_read_v2_retired(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");if(A.gettop(L)<2||A.type(L,2)!=3)return fail(L,"MODEL_MS_NUMBER_REQUIRED");return fail(L,"V2_RETIRED_USE_V3");}
static int combat_snapshot_read_v2_retired(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");return fail(L,"V2_RETIRED_USE_V3");}
static int order_identity_read(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
 auto r=host().execution_identity(u.value);if(!r)return fail(L,name(r.error));const auto& e=r.value;
 A.createtable(L,0,16);num(L,"schema",3);fld(L,"epoch",format_id(host().status().epoch));fld(L,"unit_uid",format_id(e.unit.uid));
 fld(L,"unit_lifetime",format_id(e.unit.lifetime));bit(L,"complete",e.complete);bit(L,"active",e.active);bit(L,"known",e.known);
 if(e.active){fld(L,"active_engine_seq",format_id(e.active_engine_seq));fld(L,"kind",name(e.kind));}
 if(e.known){fld(L,"accepted_journal_serial",format_id(e.accepted_serial));if(e.kind==Kind::Attack){if(e.target_uid)fld(L,"target_uid",format_id(*e.target_uid));}
  else {optnum(L,"dest_x",e.dest_x);optnum(L,"dest_z",e.dest_z);}}
 return 1;}
static void ptr_id(lua_State* L,std::uintptr_t p){char b[32]{};std::snprintf(b,sizeof b,"%llu",static_cast<unsigned long long>(p));str(L,b);}
[[maybe_unused]] static const char* evidence_bind_error(Error e) noexcept{
 switch(e){case Error::Missing:return "EVIDENCE_ROOT_NOT_FOUND";case Error::BindingMismatch:return "EVIDENCE_ROOT_AMBIGUOUS_OR_CONFLICT";
  case Error::Capacity:return "ENTITY_OWNER_INDEX_BIND_FAILED";case Error::Invalid:return "EVIDENCE_USERDATA_INVALID";default:return name(e);}
}
static int bind_evidence_unit(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");return fail(L,"PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");}
static int diagnostic_command_root(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
 const auto r=host().observed_command_root(u.value);if(!r){A.pushboolean(L,0);str(L,"COMMAND_ROOT_NOT_OBSERVED");return 2;}A.pushboolean(L,1);ptr_id(L,r.value);return 2;}
static int diagnostic_bind_evidence(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
 if(A.type(L,2)!=7)return fail(L,"BATTLE_UNIT_USERDATA_REQUIRED");void* raw=A.touserdata(L,2);if(!raw)return fail(L,"BATTLE_UNIT_USERDATA_NULL");
 if(A.gettop(L)<3||A.type(L,3)!=3)return fail(L,"EXPECTED_MEN_NUMBER_REQUIRED");const float f=A.tonumber(L,3);
 if(!std::isfinite(f)||f<1||f>300||f!=std::floor(f))return fail(L,"EXPECTED_MEN_RANGE_1_TO_300");
 std::size_t user_size=A.objlen?A.objlen(L,2):32;if(user_size==0)user_size=32;if(user_size>256)user_size=256;
 const auto r=host().diagnostic_bind_evidence(u.value,reinterpret_cast<std::uintptr_t>(raw),user_size,static_cast<std::size_t>(f));
 A.createtable(L,0,10);bit(L,"passed",r.passed);if(r.passed)ptr_id(L,r.root),A.setfield(L,-2,"root");
 bit(L,"command_root_seen",r.command_root!=0);if(r.command_root)ptr_id(L,r.command_root),A.setfield(L,-2,"command_root");
 num(L,"userdata_size",static_cast<float>(r.userdata_size));num(L,"nodes_scanned",static_cast<float>(r.nodes_scanned));num(L,"candidate_count",static_cast<float>(r.candidate_count));fld(L,"method",r.method);fld(L,"reason",r.failure_reason);return 1;}
static int contact_owner_ready(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");A.pushboolean(L,0);return 1;}
static int entity_snapshot_read(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");return fail(L,"PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");}
static int combat_snapshot_read(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");return fail(L,"PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");}
static int contact_events_read(lua_State* L){return fail(L,"PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8");}
static int numbers(lua_State* L){A.pushnumber(L,16777215.0f);A.pushnumber(L,1.5f);return 2;}
static int ids(lua_State* L){str(L,"4294967295");str(L,"16777217");return 2;}
static int status(lua_State* L){auto s=host().status();A.createtable(L,0,8);
    fld(L,"version",kDiagnosticBridgeVersion);fld(L,"epoch",format_id(s.epoch));bit(L,"recording",s.recording);
    fld(L,"capture_errors",std::to_string(s.capture_errors));fld(L,"fatal_errors",std::to_string(s.fatal_errors));fld(L,"gate_fault",name(s.gate_fault));
    fld(L,"last_recoverable_uid",format_id(s.last_recoverable_uid));fld(L,"last_recoverable_error",s.last_recoverable_error);fld(L,"last_fatal_error",s.last_fatal_error);
    fld(L,"native_error",platform_last_error());fld(L,"adapter_error",s.adapter_error);
    bit(L,"move_path_observed",s.move_path_observed);bit(L,"attack_path_observed",s.attack_path_observed);
    bit(L,"verified_issue",s.verified_issue);bit(L,"exact_source",s.exact_source);
    bit(L,"physical_path_witnesses_ready",s.physical_path_witnesses_ready);bit(L,"handler_calibration_ready",s.handler_calibration_ready);
    bit(L,"native_issue_authorized",s.native_issue_authorized);bit(L,"v3_issue_calibration_ready",s.v3_issue_calibration_ready);bit(L,"v3_issue_armed",s.v3_issue_armed);
    bit(L,"experimental_calibration_ready",s.experimental_calibration_ready);bit(L,"experimental_issue_armed",s.experimental_issue_armed);
    bit(L,"accepted_move_seen",s.accepted_move_seen);bit(L,"accepted_attack_seen",s.accepted_attack_seen);
    fld(L,"pending_count",std::to_string(s.pending_count));fld(L,"pending_limit",std::to_string(s.pending_limit));
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
    fld(L,"last_path_stage",s.last_path_stage);
    bit(L,"smart_guard_installed",s.smart_guard_installed);bit(L,"smart_guard_enabled",s.smart_guard_enabled);
    num(L,"smart_guard_local_units",static_cast<float>(s.smart_guard_local_units));
    u64str(L,"smart_guard_intercepted",s.smart_guard_intercepted);
    u64str(L,"smart_guard_suppressed",s.smart_guard_suppressed);
    u64str(L,"smart_guard_duplicates",s.smart_guard_duplicates);
    u64str(L,"smart_guard_overflows",s.smart_guard_overflows);
    u64str(L,"smart_guard_drained",s.smart_guard_drained);
    u64str(L,"smart_guard_hook17_calls",s.smart_guard_hook17_calls);
    u64str(L,"smart_guard_target_pursue_seen",s.smart_guard_target_pursue_seen);
    u64str(L,"smart_guard_target_takeup_seen",s.smart_guard_target_takeup_seen);
    u64str(L,"smart_guard_unit_resolved",s.smart_guard_unit_resolved);
    u64str(L,"smart_guard_unit_resolve_failed",s.smart_guard_unit_resolve_failed);
    u64str(L,"smart_guard_active_probe_ok",s.smart_guard_active_probe_ok);
    u64str(L,"smart_guard_active_probe_failed",s.smart_guard_active_probe_failed);
    u64str(L,"smart_guard_active_attack_matched",s.smart_guard_active_attack_matched);
    u64str(L,"smart_guard_active_not_attack",s.smart_guard_active_not_attack);
    u64str(L,"smart_guard_local_rejected",s.smart_guard_local_rejected);
    u64str(L,"smart_guard_ranged_rejected",s.smart_guard_ranged_rejected);
    u64str(L,"smart_guard_guard_rejected",s.smart_guard_guard_rejected);
    u64str(L,"smart_guard_enqueue_ok",s.smart_guard_enqueue_ok);
    u64str(L,"smart_guard_enqueue_fail",s.smart_guard_enqueue_fail);
    num(L,"active_clients",static_cast<float>(s.active_clients));
    bit(L,"smart_guard_client_active",s.smart_guard_client_active);
    return 1;}
static int start(lua_State* L){
    if(A.type(L,1)!=1||!A.toboolean(L,1)){A.pushboolean(L,0);str(L,"EXPLICIT_OBSERVER_ACK_REQUIRED");return 2;}
    const char* e=platform_start_observer();A.pushboolean(L,e?0:1);if(e){str(L,e);return 2;}return 1;
}
static int stop_observer(lua_State* L){
    const char* e=platform_stop_observer();A.pushboolean(L,e?0:1);if(e){str(L,e);return 2;}return 1;
}
static int begin(lua_State* L){
    if(A.type(L,1)!=4)return fail(L,"SESSION_KEY_STRING_REQUIRED");
    std::size_t n=0;auto s=A.tolstring(L,1,&n);if(!s||!n||n>64)return fail(L,"SESSION_KEY_LENGTH_1_TO_64");
    auto r=host().begin(std::string(s,n));if(!r)return fail(L,name(r.error));str(L,format_id(r.value));return 1;
}
static int end(lua_State* L){auto e=read_id(L,1);if(!e)return fail(L,"EPOCH_DECIMAL_STRING_REQUIRED");
    auto r=host().end(e.value);if(r!=Error::Ok)return fail(L,name(r));A.pushboolean(L,1);return 1;}
static int acquire_client(lua_State* L){
    if(A.type(L,1)!=4)return fail(L,"CLIENT_NAME_STRING_REQUIRED");
    std::size_t n1=0;const char* s1=A.tolstring(L,1,&n1);
    if(!s1||n1==0)return fail(L,"CLIENT_NAME_STRING_REQUIRED");
    std::string client_name(s1,n1);
    std::string session_key;
    if(A.gettop(L)>=2&&A.type(L,2)==4){
        std::size_t n2=0;const char* s2=A.tolstring(L,2,&n2);
        if(s2&&n2>0)session_key.assign(s2,n2);
    }
    auto r=host().acquire_client(client_name,session_key);
    if(!r)return fail(L,name(r.error));
    str(L,r.value.first);
    str(L,format_id(r.value.second));
    return 2;
}
static int release_client(lua_State* L){
    if(A.type(L,1)!=4)return fail(L,"CLIENT_TOKEN_STRING_REQUIRED");
    std::size_t n=0;const char* s=A.tolstring(L,1,&n);
    if(!s||n==0)return fail(L,"CLIENT_TOKEN_STRING_REQUIRED");
    std::string token(s,n);
    auto err=host().release_client(token);
    if(err!=Error::Ok)return fail(L,name(err));
    A.pushboolean(L,1);
    return 1;
}
static int smart_guard_enable(lua_State* L){
    if(A.type(L,1)!=4)return fail(L,"CLIENT_TOKEN_STRING_REQUIRED");
    std::size_t n=0;const char* s=A.tolstring(L,1,&n);
    if(!s||n==0)return fail(L,"CLIENT_TOKEN_STRING_REQUIRED");
    std::string token(s,n);
    if(A.gettop(L)<2||A.type(L,2)!=1)return fail(L,"BOOLEAN_REQUIRED");
    bool enable=A.toboolean(L,2)!=0;
    auto r=host().smart_guard_enable(token,enable);
    if(!r){
        if(r.error==Error::Missing)return fail(L,"CLIENT_TOKEN_UNKNOWN");
        if(r.error==Error::BindingMismatch)return fail(L,"TRUE_GUARD_CLIENT_REQUIRED");
        return fail(L,name(r.error));
    }
    A.pushboolean(L,1);
    return 1;
}
static int epoch(lua_State* L){str(L,format_id(host().status().epoch));return 1;}
static int revision(lua_State* L){auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
    auto s=host().unit_snapshot(u.value);if(!s)return fail(L,name(s.error));str(L,format_id(s.value.revision));return 1;}
static int arm(lua_State* L){
 if(A.type(L,1)!=1)return fail(L,"BOOLEAN_ACK_REQUIRED");
 const char* e=host().arm(A.toboolean(L,1)!=0);if(e)return fail(L,e);A.pushboolean(L,1);return 1;
}
static int issue(lua_State* L){
 const int nargs=A.gettop(L);
 if((nargs!=5&&nargs!=8)||A.type(L,1)!=4||A.type(L,2)!=1||A.type(L,5)!=6)return fail(L,"EXPECTED_KIND_QUEUED_UID_REVISION_CALLBACK");
 std::size_t len=0;const char* raw=A.tolstring(L,1,&len);Kind kind;
 if(len==4&&std::memcmp(raw,"MOVE",4)==0)kind=Kind::Move;
 else if(len==6&&std::memcmp(raw,"ATTACK",6)==0)kind=Kind::Attack;
 else return fail(L,"SUPPORTED_KINDS_MOVE_ATTACK");
 auto uid=read_id(L,3),rev=read_id(L,4);if(!uid||!rev)return fail(L,"UID_REVISION_DECIMAL_STRING_REQUIRED");
 if(kind==Kind::Move&&nargs!=8)return fail(L,"EXPECTED_MOVE_DESTINATION_XYZ");
 std::optional<std::array<float,3>> move_destination;
 if(nargs==8){
  if(kind!=Kind::Move)return fail(L,"MOVE_DESTINATION_KIND_MISMATCH");
  std::array<float,3> d{};for(int i=0;i<3;++i){
   if(A.type(L,6+i)!=3)return fail(L,"MOVE_DESTINATION_NUMBER_REQUIRED");
   d[static_cast<std::size_t>(i)]=A.tonumber(L,6+i);
   if(!std::isfinite(d[static_cast<std::size_t>(i)]))return fail(L,"MOVE_DESTINATION_INVALID");}
  move_destination=d;
 }
 const bool queued=A.toboolean(L,2)!=0;
 A.pushvalue(L,5); // may raise BEFORE a token is active
 auto begin=host().begin_issue(kind,queued,uid.value,rev.value,L,move_destination);
 if(!begin){A.settop(L,nargs);return fail(L,begin.error);}
 int code=0;
 try{code=A.pcall(L,0,0,0);}catch(...){host().finish_issue(false);throw;}
 auto finish=host().finish_issue(code==0);A.settop(L,nargs);
 if(!finish)return fail(L,finish.error);
 str(L,format_id(finish.id));str(L,"PENDING_NATIVE_ACCEPTANCE");return 2;
}
static int cancel_pending(lua_State* L){auto i=read_id(L,1);if(!i)return fail(L,"ISSUE_ID_DECIMAL_STRING_REQUIRED");
 auto r=host().cancel_pending_issue(i.value);if(r!=Error::Ok)return fail(L,name(r));A.pushboolean(L,1);return 1;}
static int ack(lua_State* L){auto e=read_id(L,1),c=read_id(L,2);if(!e||!c)return fail(L,"DECIMAL_STRING_REQUIRED");
    auto r=host().acknowledge(e.value,c.value);if(r!=Error::Ok)return fail(L,name(r));A.pushboolean(L,1);return 1;}
static void event(lua_State* L,const Event& e){
 A.createtable(L,0,30);fld(L,"epoch",format_id(e.epoch));fld(L,"serial",format_id(e.serial));
 fld(L,"command_id",format_id(e.command_id));fld(L,"script_issue_id",format_id(e.script_issue_id));
 fld(L,"unit_uid",format_id(e.order.recipient.uid));
 fld(L,"unit_lifetime",format_id(e.order.recipient.lifetime));
 fld(L,"flags_valid_mask","0"); // native legacy bit layout is not fabricated
fld(L,"unit_revision",format_id(e.revision));
 fld(L,"status",name(e.status));fld(L,"source",name(e.source));fld(L,"order_type",name(e.order.kind));
 bit(L,"engine_seq_valid",e.engine_seq.has_value());fld(L,"engine_seq",format_id(e.engine_seq.value_or(0)));
 if(e.order.queued)bit(L,"is_queued",*e.order.queued);
 const auto& input=e.order.input;
 bit(L,"input_sampled",input.sampled);
 fld(L,"input_stage",input.sampled?"NATIVE_ORDER_ENTRY":"UNAVAILABLE");
 if(input.sampled){
  bit(L,"input_foreground",input.foreground);
  fld(L,"input_tick_ms",std::to_string(input.tick_ms));
  fld(L,"input_thread_id",std::to_string(input.thread_id));
  if(input.foreground){
   bit(L,"input_shift",input.shift);bit(L,"input_left_shift",input.left_shift);bit(L,"input_right_shift",input.right_shift);
   bit(L,"input_ctrl",input.ctrl);bit(L,"input_alt",input.alt);
  }
 }
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
static int drain_smart_guard_cancels(lua_State* L){
 auto requests=host().drain_smart_guard_cancel_requests();
 A.createtable(L,static_cast<int>(requests.size()),0);
 int i=0;
 for(const auto& req:requests){
  A.createtable(L,0,3);
  fld(L,"unit_uid",format_id(req.unit_uid));
  fld(L,"engine_seq",format_id(req.engine_seq));
  const char* reason_str=req.reason==SmartGuardCancelReason::Pursue?"PURSUE":
                         (req.reason==SmartGuardCancelReason::TakeUpPositions?"TAKE_UP_POSITIONS":"UNKNOWN");
  fld(L,"reason",reason_str);
  A.rawseti(L,-2,++i);
 }
 return 1;
}
static int smart_guard_register_local(lua_State* L){
 auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
 const bool ok=host().smart_guard_register_local_unit(u.value);
 A.pushboolean(L,ok?1:0);
 return 1;
}
static int smart_guard_unregister_local(lua_State* L){
 auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
 const bool ok=host().smart_guard_unregister_local_unit(u.value);
 A.pushboolean(L,ok?1:0);
 return 1;
}
static int smart_guard_clear_local(lua_State* L){
 host().smart_guard_clear_local_units();
 A.pushboolean(L,1);
 return 1;
}
static int diag_probe_component(lua_State* L){
    auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
    auto r=host().evidence_root(u.value);
    if(!r)return fail(L,"UNIT_NOT_FOUND");
    auto res=platform_probe_component_chain(r.value,300);
    A.createtable(L,0,16);
    bit(L,"passed",res.passed);
    num(L,"slot_count",static_cast<float>(res.slot_count));
    num(L,"sampled_count",static_cast<float>(res.sampled_count));
    num(L,"entity_component_offset",static_cast<float>(res.entity_component_offset));
    num(L,"component_backref_offset",static_cast<float>(res.component_backref_offset));
    num(L,"movement_state_offset",static_cast<float>(res.movement_state_offset));
    num(L,"layout_pair_candidate_count",static_cast<float>(res.layout_pair_candidate_count));
    num(L,"layout_state_candidate_count",static_cast<float>(res.layout_state_candidate_count));
    fld(L,"layout_method",res.layout_method);
    A.createtable(L,static_cast<int>(res.layout_pair_reported),0);
    for(std::size_t i=0;i<res.layout_pair_reported&&i<res.layout_pairs.size();++i){
        A.createtable(L,0,2);
        num(L,"entity_component_offset",static_cast<float>(res.layout_pairs[i].entity_component_offset));
        num(L,"component_backref_offset",static_cast<float>(res.layout_pairs[i].component_backref_offset));
        A.rawseti(L,-2,static_cast<int>(i+1));
    }
    A.setfield(L,-2,"layout_pairs");
    A.createtable(L,static_cast<int>(res.layout_state_reported),0);
    for(std::size_t i=0;i<res.layout_state_reported&&i<res.layout_state_offsets.size();++i){
        A.pushnumber(L,static_cast<float>(res.layout_state_offsets[i]));A.rawseti(L,-2,static_cast<int>(i+1));
    }
    A.setfield(L,-2,"layout_state_offsets");
    fld(L,"reason",res.failure_reason);
    return 1;
}
static int diag_probe_alive(lua_State* L){
    auto u=read_id(L,1);if(!u)return fail(L,"UNIT_UID_DECIMAL_STRING_REQUIRED");
    if(A.gettop(L)<2||A.type(L,2)!=3)return fail(L,"LUA_MEN_ALIVE_NUMBER_REQUIRED");
    const float men_f=A.tonumber(L,2);
    if(!std::isfinite(men_f)||men_f<0.0f||men_f>300.0f||std::floor(men_f)!=men_f)return fail(L,"LUA_MEN_ALIVE_RANGE_0_TO_300");
    const std::uint32_t men=static_cast<std::uint32_t>(men_f);
    auto r=host().evidence_root(u.value);
    if(!r)return fail(L,"UNIT_NOT_FOUND");
    auto res=platform_probe_entity_alive(r.value,men);
    A.createtable(L,0,9);
    bit(L,"match",res.match);
    num(L,"slot_count",static_cast<float>(res.slot_count));
    num(L,"native_alive_count",static_cast<float>(res.native_alive_count));
    num(L,"lua_men_alive",static_cast<float>(res.lua_men_alive));
    fld(L,"phase",res.phase);
    bit(L,"deployment_passed",res.deployment_passed);
    bit(L,"casualty_passed",res.casualty_passed);
    bit(L,"gate_passed",res.gate_passed);
    fld(L,"reason",res.failure_reason);
    return 1;
}
static int diag_gate_status(lua_State* L){
    auto s=platform_diagnostic_gate_status();
    A.createtable(L,0,12);
    bit(L,"component_chain_gate",s.component_chain_gate);
    u64str(L,"component_gate_root",static_cast<std::uint64_t>(s.component_gate_root));
    num(L,"entity_component_offset",static_cast<float>(s.entity_component_offset));
    num(L,"component_backref_offset",static_cast<float>(s.component_backref_offset));
    num(L,"movement_state_offset",static_cast<float>(s.movement_state_offset));
    fld(L,"component_layout_method",s.component_layout_method);
    bit(L,"alive_deployment_passed",s.alive_deployment_passed);
    bit(L,"alive_casualty_passed",s.alive_casualty_passed);
    bit(L,"entity_alive_gate",s.entity_alive_gate);
    u64str(L,"alive_gate_root",static_cast<std::uint64_t>(s.alive_gate_root));
    fld(L,"build_id",s.build_id);
    fld(L,"bridge_version",s.bridge_version);
    return 1;
}
// Never allow a C++ exception to escape through the Lua C ABI. Native SEH/OOM
// longjmp from a Lua allocator is not falsely advertised as recoverable here.
template<int(*F)(lua_State*)> int boundary(lua_State* L){try{return F(L);}catch(...){return fail(L,"BRIDGE_CPP_EXCEPTION");}}
int open(lua_State* L){if(!bind())return 0;A.createtable(L,0,41);
#define REG(k,f) A.pushcclosure(L,boundary<f>,0);A.setfield(L,-2,k)
 REG("r1_evidence_capabilities_v3",evidence_caps);REG("bind_evidence_unit_v3",bind_evidence_unit);REG("diagnostic_command_root_v3",diagnostic_command_root);REG("diagnostic_bind_evidence_unit_v3",diagnostic_bind_evidence);REG("read_active_order_identity_v3",order_identity_read);REG("read_entity_snapshot_v3",entity_snapshot_read);REG("read_combat_groups_v3",combat_snapshot_read);REG("read_contact_events_v3",contact_events_read);REG("contact_owner_ready_v3",contact_owner_ready);
 REG("r1_evidence_capabilities_v2",evidence_caps_v2_retired);REG("bind_evidence_unit_v2",bind_evidence_unit_v2_retired);REG("read_active_order_identity_v2",order_identity_read_v2_retired);REG("read_entity_snapshot_v2",entity_snapshot_read_v2_retired);REG("read_combat_groups_v2",combat_snapshot_read_v2_retired);
 REG("version",version);REG("capabilities",capabilities);REG("number_abi_probe",numbers);
 REG("exact_id_probe",ids);REG("get_status",status);REG("start_observer",start);REG("stop_observer",stop_observer);
 REG("begin_battle",begin);REG("end_battle",end);REG("get_battle_epoch",epoch);
 REG("acquire_client",acquire_client);REG("release_client",release_client);REG("smart_guard_enable",smart_guard_enable);
 REG("get_unit_revision",revision);REG("arm_verified_issue",arm);REG("issue_verified_command",issue);REG("cancel_pending_issue",cancel_pending);
 REG("read_journal",journal);REG("acknowledge",ack);
 REG("drain_smart_guard_cancel_requests",drain_smart_guard_cancels);
 REG("diagnostic_probe_component_chain",diag_probe_component);
 REG("diagnostic_probe_entity_alive",diag_probe_alive);
 REG("diagnostic_gate_status",diag_gate_status);
 REG("smart_guard_register_local_unit",smart_guard_register_local);
 REG("smart_guard_unregister_local_unit",smart_guard_unregister_local);
 REG("smart_guard_clear_local_units",smart_guard_clear_local);
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
