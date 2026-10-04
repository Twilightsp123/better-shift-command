// Windows x64 backend. No DllMain hook work; no EXE-file writes; no external injector.
// Byte-locked integrated Windows backend. Build/run status lives in validation/result.json.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <intrin.h>
#include <bcrypt.h>
#include "wh3/bridge_host.hpp"
#include "wh3/component_layout.hpp"\n#include "wh3/generated_native_map.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <cstdio>
#include <limits>
#include <mutex>
#include <string>
#include <vector>
extern "C" void* g_wh3_contact_pair_trampoline = nullptr;
extern "C" void* g_wh3_state_transition_trampoline = nullptr;
extern "C" void wh3_contact_pair_detour_stub();
namespace wh3 {
namespace {
static std::atomic<bool> g_wh3_smart_guard_runtime_enabled{false};
std::mutex install_mu;
bool installed=false, attempted=false;
std::string error_storage="NOT_STARTED";
HMODULE backend=nullptr, resident=nullptr;
constexpr const char* exe_hash=native_map::kExeSha256;
using Guard=native_map::GuardSpec;
constexpr auto guards=native_map::kCoreGuards;
constexpr Guard contact_pair_guard=native_map::kContactPairGuard;
using Init=int(WINAPI*)();using Create=int(WINAPI*)(void*,void*,void**);
using Target=int(WINAPI*)(void*);using Apply=int(WINAPI*)();
struct MH {
 Init init=nullptr;Create create=nullptr;
 Target queue_enable=nullptr,queue_disable=nullptr,remove=nullptr;
 Apply apply=nullptr;
};
MH g_mh{};
std::array<void*,16> g_core_targets{};
void* g_smart_guard_target=nullptr;
bool g_hooks_created=false;
bool g_observer_stopped=false;
constexpr auto hook_names=native_map::kHookNames;
const char* mh_status_name(int s) noexcept {
 switch(s){
  case 0:return "MH_OK";case 1:return "MH_ERROR_ALREADY_INITIALIZED";case 2:return "MH_ERROR_NOT_INITIALIZED";
  case 3:return "MH_ERROR_ALREADY_CREATED";case 4:return "MH_ERROR_NOT_CREATED";case 5:return "MH_ERROR_ENABLED";
  case 6:return "MH_ERROR_DISABLED";case 7:return "MH_ERROR_NOT_EXECUTABLE";case 8:return "MH_ERROR_UNSUPPORTED_FUNCTION";
  case 9:return "MH_ERROR_MEMORY_ALLOC";case 10:return "MH_ERROR_MEMORY_PROTECT";case 11:return "MH_ERROR_MODULE_NOT_FOUND";
  case 12:return "MH_ERROR_FUNCTION_NOT_FOUND";default:return "MH_ERROR_UNKNOWN";
 }
}
std::string create_failure(std::size_t i,int status,bool null_tramp,bool retried){
 char buf[256]{};
 std::snprintf(buf,sizeof buf,"MINHOOK_CREATE_FAILED_hook=%s_idx=%zu_rva=0x%llx_status=%d_%s_tramp_null=%d_retry=%d",
  i<hook_names.size()?hook_names[i]:"unknown",i,static_cast<unsigned long long>(guards[i].rva),status,mh_status_name(status),null_tramp?1:0,retried?1:0);
 return std::string(buf);
}
template<class F> bool symbol(HMODULE m,const char* name,F& f){auto p=GetProcAddress(m,name);if(!p)return false;
 static_assert(sizeof f==sizeof p);std::memcpy(&f,&p,sizeof f);return true;}
std::wstring path(HMODULE m){std::vector<wchar_t> s(32768);DWORD n=GetModuleFileNameW(m,s.data(),static_cast<DWORD>(s.size()));
 if(n==0||n>=s.size())return {};return std::wstring(s.data(),n);}
struct Handle {HANDLE h=INVALID_HANDLE_VALUE;~Handle(){if(h!=INVALID_HANDLE_VALUE)CloseHandle(h);}};
struct Sha {std::vector<unsigned char> object;BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;
 ~Sha(){if(h)BCryptDestroyHash(h);if(a)BCryptCloseAlgorithmProvider(a,0);}};
bool hash_file(const std::wstring& p,std::string& out){
 Handle f;f.h=CreateFileW(p.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_FLAG_SEQUENTIAL_SCAN,nullptr);
 if(f.h==INVALID_HANDLE_VALUE)return false;Sha sha;DWORD n=0,size=0;
 if(BCryptOpenAlgorithmProvider(&sha.a,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
 if(BCryptGetProperty(sha.a,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof size,&n,0)<0||!size)return false;
 sha.object.resize(size);std::array<unsigned char,65536> buf{};std::array<unsigned char,32> digest{};
 if(BCryptCreateHash(sha.a,&sha.h,sha.object.data(),size,nullptr,0,0)<0)return false;
 for(;;){DWORD got=0;if(!ReadFile(f.h,buf.data(),static_cast<DWORD>(buf.size()),&got,nullptr))return false;
  if(!got)break;if(BCryptHashData(sha.h,buf.data(),got,0)<0)return false;}
 if(BCryptFinishHash(sha.h,digest.data(),static_cast<ULONG>(digest.size()),0)<0)return false;
 static constexpr char hex[]="0123456789abcdef";out.clear();for(auto b:digest){out+=hex[b>>4];out+=hex[b&15];}return true;
}
unsigned nibble(char c){return c>='0'&&c<='9'?static_cast<unsigned>(c-'0'):static_cast<unsigned>(c-'a'+10);}
bool guard_matches(const Guard& g,std::uintptr_t base){
 std::array<unsigned char,32> b{};const auto n=std::strlen(g.bytes)/2;
 if(n>b.size()||g.rva>UINTPTR_MAX-base||!platform_read(base+g.rva,b.data(),n))return false;
 for(std::size_t i=0;i<n;++i)if(b[i]!=(nibble(g.bytes[2*i])*16+nibble(g.bytes[2*i+1])))return false;
 return true;
}
InputSnapshot sample_input() noexcept {
 InputSnapshot s{};s.sampled=true;s.tick_ms=GetTickCount64();s.thread_id=GetCurrentThreadId();
 DWORD pid=0;const HWND fg=GetForegroundWindow();
 if(fg) GetWindowThreadProcessId(fg,&pid);
 s.foreground=pid!=0&&pid==GetCurrentProcessId();
 if(!s.foreground)return s; // unavailable, not "Shift was definitely released"
 s.left_shift=(GetAsyncKeyState(VK_LSHIFT)&0x8000)!=0;
 s.right_shift=(GetAsyncKeyState(VK_RSHIFT)&0x8000)!=0;
 s.shift=s.left_shift||s.right_shift;
 s.ctrl=(GetAsyncKeyState(VK_CONTROL)&0x8000)!=0;
 s.alt=(GetAsyncKeyState(VK_MENU)&0x8000)!=0;
 return s;
}
std::uint32_t move_hook(void* u,std::uint32_t a,void* p,std::uint8_t q){return host().order(Kind::Move,u,a,p,q,sample_input());}
std::uint32_t attack_hook(void* u,std::uint32_t a,void* p,std::uint8_t q){return host().order(Kind::Attack,u,a,p,q,sample_input());}
void* allocator_hook(void* c,std::uint32_t q){return host().allocate(c,q);}
void halt_hook(void* u,std::uint32_t a){host().halt(u,a);}

int lua_move_hook(void* u,void* L,std::uint8_t q){return host().binding(Kind::Move,u,L,q);}
int lua_attack_hook(void* u,void* L,std::uint8_t q){return host().binding(Kind::Attack,u,L,q);}
std::uint32_t publish_move_hook(void* q,void* c){return host().publish(Kind::Move,q,c);}
std::uint32_t publish_attack_hook(void* q,void* c){return host().publish(Kind::Attack,q,c);}
void* writer_begin_hook(void* w,void* b,void* t,std::uint32_t c){return host().writer_begin(w,b,t,c);}
void writer_finalize_hook(void* w){host().writer_finalize(w);}
void copy_hook(void* d,void* s){host().copy_buffer(d,s);}
std::uint32_t stage_hook(void* d,std::uint32_t a,void* s,float f){return host().stage_buffer(d,a,s,f);}
void move_handler_hook(void* r,void* c){host().packet_handler(Kind::Move,r,c);}
void attack_handler_hook(void* r,void* c){host().packet_handler(Kind::Attack,r,c);}
void* selection_hook(void* d,void* r){return host().selection(d,r,platform_caller_frame(_ReturnAddress()));}
void free_hook(void* p){host().release_memory(p);}
template<class F> void* pointer(F f){void* p=nullptr;static_assert(sizeof f==sizeof p);std::memcpy(&p,&f,sizeof p);return p;}
template<class F> F function(void* p){F f=nullptr;static_assert(sizeof f==sizeof p);std::memcpy(&f,&p,sizeof f);return f;}
void state_transition_hook(void* target,void* order,std::uint8_t flag){
 if(!g_wh3_smart_guard_runtime_enabled.load(std::memory_order_acquire)||!g_wh3_state_transition_trampoline){
  if(g_wh3_state_transition_trampoline){
   function<NativeTransitionFn>(g_wh3_state_transition_trampoline)(target,order,flag);
  }
  return;
 }
 host().state_transition(target,order,flag);
}
}
std::uintptr_t platform_image_base() noexcept{return reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));}
bool platform_read(std::uintptr_t p,void* dst,std::size_t n) noexcept{
 if(!p||!dst||n>UINTPTR_MAX-p)return false;SIZE_T got=0;
 return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(p),dst,n,&got)&&got==n;
}
bool platform_write(std::uintptr_t p,const void* src,std::size_t n) noexcept{
 if(!p||!src||n>UINTPTR_MAX-p)return false;SIZE_T got=0;
 return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),src,n,&got)&&got==n;
}
std::uintptr_t platform_image_size() noexcept{
 const auto base=platform_image_base();if(!base)return 0;
 IMAGE_DOS_HEADER dos{};
 if(!platform_read(base,&dos,sizeof dos)||dos.e_magic!=IMAGE_DOS_SIGNATURE||dos.e_lfanew<=0||dos.e_lfanew>0x1000)return 0;
 if(static_cast<std::uintptr_t>(dos.e_lfanew)>UINTPTR_MAX-base)return 0;
 IMAGE_NT_HEADERS64 nt{};
 if(!platform_read(base+static_cast<std::uintptr_t>(dos.e_lfanew),&nt,sizeof nt)||nt.Signature!=IMAGE_NT_SIGNATURE)return 0;
 if(nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_AMD64||nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR64_MAGIC)return 0;
 const std::uintptr_t size=nt.OptionalHeader.SizeOfImage;
 if(size<0x100000||size>0x40000000||size>UINTPTR_MAX-base)return 0;
 return size;
}
bool platform_executable_address(std::uintptr_t addr) noexcept{
 if(!addr)return false;
 MEMORY_BASIC_INFORMATION mbi{};
 if(VirtualQuery(reinterpret_cast<LPCVOID>(addr),&mbi,sizeof(mbi))!=sizeof(mbi))return false;
 if(mbi.State!=MEM_COMMIT||(mbi.Protect&PAGE_GUARD)||(mbi.Protect&PAGE_NOACCESS))return false;
 const DWORD p=(mbi.Protect&0xFF);
 return p==PAGE_EXECUTE||p==PAGE_EXECUTE_READ||p==PAGE_EXECUTE_READWRITE||p==PAGE_EXECUTE_WRITECOPY;
}

static std::atomic<bool> g_component_gate{false};
static std::atomic<std::uintptr_t> g_component_gate_root{0};
static std::atomic<std::size_t> g_entity_component_offset{0};
static std::atomic<std::size_t> g_component_backref_offset{0};
static std::atomic<std::size_t> g_movement_state_offset{0};
static std::atomic<unsigned> g_component_layout_method{static_cast<unsigned>(ComponentLayoutMethod::None)};
static std::atomic<bool> g_alive_deployment{false};
static std::atomic<bool> g_alive_casualty{false};
static std::atomic<bool> g_alive_gate{false};
static std::atomic<std::uintptr_t> g_alive_gate_root{0};
void platform_reset_diagnostic_gates() noexcept{
 g_component_gate.store(false,std::memory_order_relaxed);
 g_component_gate_root.store(0,std::memory_order_relaxed);
 g_entity_component_offset.store(0,std::memory_order_relaxed);
 g_component_backref_offset.store(0,std::memory_order_relaxed);
 g_movement_state_offset.store(0,std::memory_order_relaxed);
 g_component_layout_method.store(static_cast<unsigned>(ComponentLayoutMethod::None),std::memory_order_relaxed);
 g_alive_deployment.store(false,std::memory_order_relaxed);
 g_alive_casualty.store(false,std::memory_order_relaxed);
 g_alive_gate.store(false,std::memory_order_relaxed);
 g_alive_gate_root.store(0,std::memory_order_relaxed);
}
static void reset_alive_diagnostic_gate() noexcept{
 g_alive_deployment.store(false,std::memory_order_relaxed);
 g_alive_casualty.store(false,std::memory_order_relaxed);
 g_alive_gate.store(false,std::memory_order_relaxed);
 g_alive_gate_root.store(0,std::memory_order_relaxed);
}

bool platform_component_chain_gate_passed() noexcept{
 return g_component_gate.load(std::memory_order_acquire);
}

bool platform_entity_alive_gate_passed() noexcept{
 return g_alive_gate.load(std::memory_order_acquire);
}

DiagnosticGateStatus platform_diagnostic_gate_status() noexcept{
 DiagnosticGateStatus s{};
 s.component_chain_gate=g_component_gate.load(std::memory_order_relaxed);
 s.component_gate_root=g_component_gate_root.load(std::memory_order_relaxed);
 s.entity_component_offset=g_entity_component_offset.load(std::memory_order_relaxed);
 s.component_backref_offset=g_component_backref_offset.load(std::memory_order_relaxed);
 s.movement_state_offset=g_movement_state_offset.load(std::memory_order_relaxed);
 s.component_layout_method=component_layout_method_name(static_cast<ComponentLayoutMethod>(g_component_layout_method.load(std::memory_order_relaxed)));
 s.alive_deployment_passed=g_alive_deployment.load(std::memory_order_relaxed);
 s.alive_casualty_passed=g_alive_casualty.load(std::memory_order_relaxed);
 s.entity_alive_gate=g_alive_gate.load(std::memory_order_relaxed);
 s.alive_gate_root=g_alive_gate_root.load(std::memory_order_relaxed);
 s.build_id=platform_evidence_build_id();
 s.bridge_version=kDiagnosticBridgeVersion;
 return s;
}

static bool validate_component_layout(std::uintptr_t arr,std::uint32_t slot_count,std::size_t sample_limit,
 std::size_t entity_off,std::size_t back_off,std::size_t state_off,std::size_t& sampled,const char*& reason) noexcept{
 const std::size_t limit=sample_limit>0?sample_limit:static_cast<std::size_t>(slot_count);
 if(limit<slot_count){reason="COMPONENT_SAMPLE_INCOMPLETE";return false;}
 sampled=0;
 for(std::size_t i=0;i<slot_count;++i){
  if(arr>UINTPTR_MAX-i*sizeof(std::uintptr_t)){reason="SOLDIER_ARRAY_RANGE_OVERFLOW";return false;}
  std::uintptr_t entity=0;
  if(!platform_read(arr+i*sizeof(std::uintptr_t),&entity,sizeof entity)){reason="ENTITY_SLOT_READ_FAILED";return false;}
  if(!entity){reason="NULL_ENTITY_IN_CHAIN";return false;}
  if(entity>UINTPTR_MAX-entity_off){reason="ENTITY_POINTER_OVERFLOW";return false;}
  std::uintptr_t vt=0,alive_fn=0;
  const auto image_base=platform_image_base();const auto image_size=platform_image_size();
  if(!image_base||!image_size||!platform_read(entity,&vt,sizeof vt)||!vt||vt<image_base||vt>=image_base+image_size||
     vt>UINTPTR_MAX-0x630||!platform_read(vt+0x630,&alive_fn,sizeof alive_fn)||!alive_fn||alive_fn<image_base||alive_fn>=image_base+image_size||
     !platform_executable_address(alive_fn)){reason="ENTITY_VTABLE_OR_ALIVE_SLOT_INVALID";return false;}
  std::uintptr_t comp=0;
  if(!platform_read(entity+entity_off,&comp,sizeof comp)||!comp){reason="NULL_MOVEMENT_COMPONENT";return false;}
  const auto max_off=std::max(back_off,state_off);
  if(comp>UINTPTR_MAX-max_off){reason="COMPONENT_POINTER_OVERFLOW";return false;}
  std::uintptr_t backref=0;
  if(!platform_read(comp+back_off,&backref,sizeof backref)||backref!=entity){reason="MOVEMENT_BACKREF_MISMATCH";return false;}
  std::uint32_t movement_state=0xFFFFFFFFU;
  if(!platform_read(comp+state_off,&movement_state,sizeof movement_state)||movement_state>2){reason="INVALID_MOVEMENT_STATE";return false;}
  ++sampled;
 }
 if(sampled!=slot_count){reason="COMPONENT_SAMPLE_INCOMPLETE";return false;}
 reason="NONE";return true;
}

static void copy_layout_diagnostics(DiagnosticChainResult& r,const ComponentLayoutScanResult& d) noexcept{
 r.entity_component_offset=d.entity_component_offset;
 r.component_backref_offset=d.component_backref_offset;
 r.movement_state_offset=d.movement_state_offset;
 r.layout_pair_candidate_count=d.pair_candidate_count;
 r.layout_state_candidate_count=d.state_candidate_count;
 r.layout_pair_reported=d.pair_reported;
 r.layout_state_reported=d.state_reported;
 for(std::size_t i=0;i<r.layout_pairs.size()&&i<d.pairs.size();++i){
  r.layout_pairs[i]={d.pairs[i].entity_component_offset,d.pairs[i].component_backref_offset};
 }
 r.layout_state_offsets=d.states;
 r.layout_method=component_layout_method_name(d.method);
}

static bool call_entity_alive_virtual_internal(std::uintptr_t entity,bool* alive=nullptr) noexcept{
 if(!entity)return false;std::uintptr_t vt=0,fn=0;
 if(!platform_read(entity,&vt,sizeof vt)||!vt||vt>UINTPTR_MAX-0x630||!platform_read(vt+0x630,&fn,sizeof fn)||!fn)return false;
 const auto base=platform_image_base();const auto img_size=platform_image_size();
 if(!base||!img_size||fn<base||fn>=base+img_size)return false;
 if(!platform_executable_address(fn))return false;
 using F=bool(*)(void*);bool value=false;
 __try{value=function<F>(reinterpret_cast<void*>(fn))(reinterpret_cast<void*>(entity));}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
 if(alive)*alive=value;
 return true;
}

bool platform_entity_alive(std::uintptr_t entity,bool* alive) noexcept{
 if(!alive)return false;
 if(!platform_component_chain_gate_passed()||!platform_entity_alive_gate_passed()){
  *alive=false;
  return false;
 }
 bool val=false;
 if(!call_entity_alive_virtual_internal(entity,&val))return false;
 *alive=val;return true;
}

DiagnosticChainResult platform_probe_component_chain(std::uintptr_t root,std::size_t sample_limit) noexcept{
 DiagnosticChainResult r{};r.passed=false;
 // Every component-chain probe is a fresh proof. Revoke both gates first so a
 // later bad probe cannot leave a sticky PASS from another root/unit.
 platform_reset_diagnostic_gates();
 if(!root){r.failure_reason="NULL_ROOT";return r;}
 if(root>UINTPTR_MAX-0x118){r.failure_reason="ROOT_POINTER_OVERFLOW";return r;}
 std::uint32_t slot_count=0;
 if(!platform_read(root+0x114,&slot_count,sizeof slot_count)){r.failure_reason="COUNT_READ_FAILED";return r;}
 r.slot_count=slot_count;
 if(slot_count<1||slot_count>300){r.failure_reason="COUNT_OUT_OF_RANGE";return r;}
 std::uintptr_t arr=0;
 if(!platform_read(root+0x118,&arr,sizeof arr)||!arr){r.failure_reason="NULL_SOLDIER_ARRAY";return r;}
 if(slot_count>0&&arr>UINTPTR_MAX-(static_cast<std::uintptr_t>(slot_count)-1)*sizeof(std::uintptr_t)){r.failure_reason="SOLDIER_ARRAY_RANGE_OVERFLOW";return r;}
 std::size_t sampled=0;const char* legacy_reason="NONE";
 if(validate_component_layout(arr,slot_count,sample_limit,0x18,0x4a0,0x8b0,sampled,legacy_reason)){
  r.sampled_count=sampled;r.entity_component_offset=0x18;r.component_backref_offset=0x4a0;r.movement_state_offset=0x8b0;
  r.layout_method="LEGACY_EXACT";r.failure_reason="NONE";r.passed=true;
  g_component_gate_root.store(root,std::memory_order_relaxed);
  g_entity_component_offset.store(0x18,std::memory_order_relaxed);
  g_component_backref_offset.store(0x4a0,std::memory_order_relaxed);
  g_movement_state_offset.store(0x8b0,std::memory_order_relaxed);
  g_component_layout_method.store(static_cast<unsigned>(ComponentLayoutMethod::LegacyExact),std::memory_order_relaxed);
  g_component_gate.store(true,std::memory_order_release);return r;
 }
 const auto discovered=scan_component_layout(platform_read,arr,slot_count);copy_layout_diagnostics(r,discovered);
 if(!discovered.passed){r.failure_reason=discovered.failure_reason;return r;}
 sampled=0;const char* discovered_reason="NONE";
 if(!validate_component_layout(arr,slot_count,sample_limit,discovered.entity_component_offset,discovered.component_backref_offset,
     discovered.movement_state_offset,sampled,discovered_reason)){
  r.sampled_count=sampled;r.failure_reason=discovered_reason;return r;
 }
 r.sampled_count=sampled;r.passed=true;r.failure_reason="NONE";
 g_component_gate_root.store(root,std::memory_order_relaxed);
 g_entity_component_offset.store(discovered.entity_component_offset,std::memory_order_relaxed);
 g_component_backref_offset.store(discovered.component_backref_offset,std::memory_order_relaxed);
 g_movement_state_offset.store(discovered.movement_state_offset,std::memory_order_relaxed);
 g_component_layout_method.store(static_cast<unsigned>(discovered.method),std::memory_order_relaxed);
 g_component_gate.store(true,std::memory_order_release);return r;
}

DiagnosticAliveResult platform_probe_entity_alive(std::uintptr_t root,std::uint32_t lua_men_alive) noexcept{
 DiagnosticAliveResult r{};
 r.match=false;r.deployment_passed=g_alive_deployment.load(std::memory_order_relaxed);
 r.casualty_passed=g_alive_casualty.load(std::memory_order_relaxed);r.gate_passed=g_alive_gate.load(std::memory_order_relaxed);r.phase="NONE";
 auto fail_alive=[&](const char* reason)->DiagnosticAliveResult{
  reset_alive_diagnostic_gate();r.deployment_passed=false;r.casualty_passed=false;r.gate_passed=false;r.failure_reason=reason;return r;
 };
 auto fail_component=[&](const char* reason)->DiagnosticAliveResult{
  platform_reset_diagnostic_gates();r.deployment_passed=false;r.casualty_passed=false;r.gate_passed=false;r.failure_reason=reason;return r;
 };
 if(!platform_component_chain_gate_passed()){r.failure_reason="COMPONENT_GATE_PREREQUISITE_FAILED";return r;}
 if(!root)return fail_alive("NULL_ROOT");
 if(root>UINTPTR_MAX-0x118)return fail_alive("ROOT_POINTER_OVERFLOW");
 const auto component_root=g_component_gate_root.load(std::memory_order_acquire);
 if(!component_root||root!=component_root)return fail_alive("COMPONENT_ROOT_MISMATCH");
 std::uint32_t slot_count=0;
 if(!platform_read(root+0x114,&slot_count,sizeof slot_count))return fail_alive("COUNT_READ_FAILED");
 r.slot_count=slot_count;r.lua_men_alive=lua_men_alive;
 if(slot_count<1||slot_count>300)return fail_alive("COUNT_OUT_OF_RANGE");
 if(lua_men_alive>slot_count)return fail_alive("LUA_MEN_EXCEEDS_SLOT_COUNT");
 std::uintptr_t arr=0;
 if(!platform_read(root+0x118,&arr,sizeof arr)||!arr)return fail_alive("NULL_SOLDIER_ARRAY");
 if(slot_count>0&&arr>UINTPTR_MAX-(static_cast<std::uintptr_t>(slot_count)-1)*sizeof(std::uintptr_t))return fail_alive("SOLDIER_ARRAY_RANGE_OVERFLOW");
 std::uint32_t native_alive=0;
 for(std::size_t i=0;i<slot_count;++i){
  std::uintptr_t entity=0;
  if(!platform_read(arr+i*8,&entity,sizeof entity))return fail_alive("ENTITY_SLOT_READ_FAILED");
  if(!entity)return fail_alive("NULL_ENTITY_SLOT");
  // Revalidate the read-only component chain immediately before the first
  // untrusted Entity virtual call. The earlier gate proves the layout, but the
  // soldier array/entity pointers must not be allowed to change underneath it.
  const auto entity_off=g_entity_component_offset.load(std::memory_order_acquire);
  const auto back_off=g_component_backref_offset.load(std::memory_order_acquire);
  const auto state_off=g_movement_state_offset.load(std::memory_order_acquire);
  if(g_component_layout_method.load(std::memory_order_acquire)==static_cast<unsigned>(ComponentLayoutMethod::None))return fail_component("COMPONENT_LAYOUT_NOT_PUBLISHED");
  if(entity>UINTPTR_MAX-entity_off)return fail_component("ENTITY_POINTER_OVERFLOW");
  std::uintptr_t comp=0,backref=0;std::uint32_t movement_state=0xFFFFFFFFU;
  if(!platform_read(entity+entity_off,&comp,sizeof comp)||!comp)return fail_component("COMPONENT_CHAIN_CHANGED_NULL_COMPONENT");
  const auto max_component_off=std::max(back_off,state_off);
  if(comp>UINTPTR_MAX-max_component_off)return fail_component("COMPONENT_POINTER_OVERFLOW");
  if(!platform_read(comp+back_off,&backref,sizeof backref)||backref!=entity)return fail_component("COMPONENT_CHAIN_CHANGED_BACKREF");
  if(!platform_read(comp+state_off,&movement_state,sizeof movement_state)||movement_state>2)return fail_component("COMPONENT_CHAIN_CHANGED_STATE");
  bool is_alive=false;
  if(!call_entity_alive_virtual_internal(entity,&is_alive))return fail_alive("VIRTUAL_CALL_EXCEPTION_OR_INVALID");
  if(is_alive)++native_alive;
 }
 r.native_alive_count=native_alive;r.match=native_alive==lua_men_alive;
 if(lua_men_alive==slot_count){
  r.phase="DEPLOYMENT";
  if(!r.match)return fail_alive("DEPLOYMENT_COUNT_MISMATCH");
  g_alive_gate_root.store(root,std::memory_order_relaxed);g_alive_deployment.store(true,std::memory_order_relaxed);
  g_alive_casualty.store(false,std::memory_order_relaxed);g_alive_gate.store(false,std::memory_order_relaxed);
  r.deployment_passed=true;r.casualty_passed=false;r.gate_passed=false;r.failure_reason="NONE";return r;
 }
 r.phase="CASUALTY";
 if(!g_alive_deployment.load(std::memory_order_relaxed))return fail_alive("CASUALTY_BEFORE_DEPLOYMENT");
 if(root!=g_alive_gate_root.load(std::memory_order_relaxed))return fail_alive("ROOT_MISMATCH");
 if(!r.match)return fail_alive("CASUALTY_COUNT_MISMATCH");
 g_alive_casualty.store(true,std::memory_order_relaxed);g_alive_gate.store(true,std::memory_order_relaxed);
 r.deployment_passed=true;r.casualty_passed=true;r.gate_passed=true;r.failure_reason="NONE";return r;
}


bool platform_combat_group_query(std::uintptr_t group,bool* in_melee,std::uintptr_t* target_root) noexcept{
 if(!group||!in_melee||!target_root)return false;*in_melee=false;*target_root=0;std::uintptr_t vt=0,mf=0,tf=0;
 if(!platform_read(group,&vt,sizeof vt)||!vt||vt>UINTPTR_MAX-0xa8||!platform_read(vt+0x48,&mf,sizeof mf)||!mf||!platform_read(vt+0xa8,&tf,sizeof tf)||!tf)return false;
 const auto base=platform_image_base();const auto image_size=platform_image_size();
 if(!base||!image_size||mf<base||mf>=base+image_size||tf<base||tf>=base+image_size)return false;
 if(!platform_executable_address(mf)||!platform_executable_address(tf))return false;
 using MeleeFn=bool(*)(void*);using TargetFn=void*(*)(void*);bool melee=false;void* target=nullptr;
 __try{melee=function<MeleeFn>(reinterpret_cast<void*>(mf))(reinterpret_cast<void*>(group));if(melee)target=function<TargetFn>(reinterpret_cast<void*>(tf))(reinterpret_cast<void*>(group));}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
 *in_melee=melee;if(!melee)return true;if(!target)return false;
 const auto target_addr=reinterpret_cast<std::uintptr_t>(target);if(target_addr>UINTPTR_MAX-0x2e8)return false;
 std::uintptr_t root=0;if(!platform_read(target_addr+0x2e8,&root,sizeof root)||!root)return false;*target_root=root;return true;
}
namespace {
// Walk actual x64 unwind metadata. A frame identity is a dynamic activation,
// not a function-address guess or a marker left in TLS after a callback returned.
bool unwind_one(CONTEXT& c,FrameIdentity& frame) noexcept{
 const auto pc=c.Rip;const auto sp=c.Rsp;if(!pc||!sp)return false;
 DWORD64 image=0;PRUNTIME_FUNCTION f=RtlLookupFunctionEntry(pc,&image,nullptr);
 if(!f){std::uint64_t next=0;if(!platform_read(sp,&next,8))return false;c.Rip=next;c.Rsp+=8;frame={0,sp,next};return next!=0;}
 PVOID data=nullptr;DWORD64 establish=0;
 RtlVirtualUnwind(UNW_FLAG_NHANDLER,image,pc,f,&c,&data,&establish,nullptr);
 frame={static_cast<std::uintptr_t>(image+f->BeginAddress),static_cast<std::uintptr_t>(establish),static_cast<std::uintptr_t>(c.Rip)};
 return c.Rip!=0&&c.Rsp>sp;
}
}
FrameIdentity platform_caller_frame(void* return_address) noexcept{
 CONTEXT c{};RtlCaptureContext(&c);const auto target=reinterpret_cast<std::uintptr_t>(return_address);
 for(unsigned i=0;i<64&&c.Rip;++i){const bool at_caller=c.Rip==target;FrameIdentity f{};
  if(!unwind_one(c,f))return {};if(at_caller)return f;
 }return {};
}
bool platform_frame_active(const FrameIdentity& wanted) noexcept{
 if(!wanted)return false;CONTEXT c{};RtlCaptureContext(&c);
 for(unsigned i=0;i<64&&c.Rip;++i){FrameIdentity f{};if(!unwind_one(c,f))return false;
  if(f.function==wanted.function&&f.establisher==wanted.establisher&&f.return_pc==wanted.return_pc)return true;
 }return false;
}
void* platform_lua_symbol(const char* s) noexcept {auto p=GetProcAddress(GetModuleHandleW(nullptr),s);void* v=nullptr;
 static_assert(sizeof p==sizeof v);std::memcpy(&v,&p,sizeof v);return v;}
bool platform_hooks_installed() noexcept {std::lock_guard<std::mutex> l(install_mu);return installed;}
const char* platform_last_error() noexcept {std::lock_guard<std::mutex> l(install_mu);return error_storage.c_str();}
bool platform_evidence_build_verified() noexcept {std::lock_guard<std::mutex> l(install_mu);return installed;}
const char* platform_evidence_build_id() noexcept {return native_map::kMapId;}
std::uint64_t platform_tick_ms() noexcept{return GetTickCount64();}
extern "C" void wh3_contact_pair_observer(void* result_record) noexcept {
 if(!result_record)return;
 const auto r=reinterpret_cast<std::uintptr_t>(result_record);
 std::uintptr_t ctrl_a=0,ctrl_b=0,entity_a=0,entity_b=0;
 // RE08 proves ResultRecord+0x18/+0x10 are the two controllers at this exact
 // mid-function site. Do not trust the unclosed ctrl+0x2E8 owner claim: unit
 // ownership is resolved exclusively through ContactTracker's EntityOwnerIndex.
 if(!platform_read(r+0x18,&ctrl_a,sizeof ctrl_a)||!platform_read(r+0x10,&ctrl_b,sizeof ctrl_b)||
    !ctrl_a||!ctrl_b||ctrl_a==ctrl_b)return;
 if(!platform_read(ctrl_a+0x4a0,&entity_a,sizeof entity_a)||
    !platform_read(ctrl_b+0x4a0,&entity_b,sizeof entity_b)||
    !entity_a||!entity_b||entity_a==entity_b)return;
 host().observe_contact_pair(entity_a,entity_b,platform_tick_ms());
}
const char* platform_start_observer(){
 std::lock_guard<std::mutex> lock(install_mu);
 if(installed)return nullptr;
 if(attempted){
  if(g_observer_stopped)error_storage="OBSERVER_ALREADY_STOPPED_PROCESS_RESTART_REQUIRED";
  return error_storage.c_str();
 }
 attempted=true;g_observer_stopped=false;
 try{
  const auto base=platform_image_base();std::string sha;
  if(!hash_file(path(nullptr),sha)){error_storage="HOST_HASH_READ_FAILED";return error_storage.c_str();}
  if(sha!=exe_hash){error_storage="HOST_EXE_SHA256_MISMATCH";return error_storage.c_str();}
  for(const auto& g:guards){
   if(!guard_matches(g,base)){error_storage="HOOK_BYTES_MISMATCH";return error_storage.c_str();}
  }
  // Pin BEFORE any enabling. Never unload callbacks/trampolines mid-flight.
  HMODULE module=nullptr;
  if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
       reinterpret_cast<LPCWSTR>(&platform_start_observer),&module)){
   error_storage="MODULE_PIN_FAILED";return error_storage.c_str();
  }
  resident=module;auto p=path(module);const auto slash=p.find_last_of(L"\\/");
  if(slash==std::wstring::npos){error_storage="MODULE_PATH_FAILED";return error_storage.c_str();}
  p.resize(slash+1);p+=L"minhook.x64.dll";
  std::string backend_sha;
  if(!hash_file(p,backend_sha)||backend_sha!="df452eacdb076c35a80c795df920fd3c6f128faa3e0bccb0b7490e95f8659d54"){
   error_storage="MINHOOK_SHA256_MISMATCH";return error_storage.c_str();
  }
  backend=LoadLibraryExW(p.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
  if(!backend){error_storage="MINHOOK_BACKEND_MISSING";return error_storage.c_str();}
  g_mh={};
  if(!symbol(backend,"MH_Initialize",g_mh.init)||!symbol(backend,"MH_CreateHook",g_mh.create)||
     !symbol(backend,"MH_QueueEnableHook",g_mh.queue_enable)||!symbol(backend,"MH_QueueDisableHook",g_mh.queue_disable)||
     !symbol(backend,"MH_ApplyQueued",g_mh.apply)||!symbol(backend,"MH_RemoveHook",g_mh.remove)){
   error_storage="MINHOOK_EXPORT_MISSING";return error_storage.c_str();
  }
  // Do not take ownership of somebody else's already-initialized backend.
  const int init_status=g_mh.init();
  if(init_status!=0){
   char buf[160]{};
   std::snprintf(buf,sizeof buf,"MINHOOK_INITIALIZE_NOT_FRESH_status=%d_%s",init_status,mh_status_name(init_status));
   error_storage=buf;return error_storage.c_str();
  }
  g_core_targets.fill(nullptr);g_smart_guard_target=nullptr;g_hooks_created=false;
  std::array<void*,16> tramp{};
  const std::array<void*,16> detours={pointer(move_hook),pointer(attack_hook),pointer(allocator_hook),pointer(halt_hook),
   pointer(lua_move_hook),pointer(lua_attack_hook),pointer(publish_move_hook),pointer(publish_attack_hook),pointer(writer_begin_hook),pointer(writer_finalize_hook),
   pointer(copy_hook),pointer(stage_hook),pointer(move_handler_hook),pointer(attack_handler_hook),pointer(selection_hook),pointer(free_hook)};
  auto create_all=[&](bool retried)->int{
   std::size_t created=0;
   for(std::size_t i=0;i<g_core_targets.size();++i){
    g_core_targets[i]=reinterpret_cast<void*>(base+guards[i].rva);
    tramp[i]=nullptr;
    const int create_result=g_mh.create(g_core_targets[i],detours[i],&tramp[i]);
    if(create_result!=0||!tramp[i]){
     const bool null_tramp=!tramp[i];
     if(create_result==0)g_mh.remove(g_core_targets[i]);
     for(std::size_t j=0;j<created;++j)g_mh.remove(g_core_targets[j]);
     error_storage=create_failure(i,create_result,null_tramp,retried);
     return create_result==0?-1000:create_result;
    }
    ++created;
   }
   return 0;
  };
  int create_status=create_all(false);
  // Retry only MinHook failures that can reasonably be transient. Deterministic structural
  // failures remain fail-closed so an unsafe partial observer can never start.
  if(create_status==9||create_status==10||create_status==-1000){
   Sleep(50);
   create_status=create_all(true);
  }
  if(create_status!=0)return error_storage.c_str();
  g_hooks_created=true;
  g_wh3_contact_pair_trampoline=nullptr;
  NativeFunctions n{function<NativeOrderFn>(tramp[0]),function<NativeOrderFn>(tramp[1]),
                    function<NativeAllocatorFn>(tramp[2]),function<NativeHaltFn>(tramp[3])};
  AdapterFunctions a{function<NativeBindingFn>(tramp[4]),function<NativeBindingFn>(tramp[5]),function<NativePublishFn>(tramp[6]),function<NativePublishFn>(tramp[7]),
   function<NativeBeginWriterFn>(tramp[8]),function<NativeFinalizeFn>(tramp[9]),function<NativeCopyFn>(tramp[10]),function<NativeStageFn>(tramp[11]),
   function<NativePacketHandlerFn>(tramp[12]),function<NativePacketHandlerFn>(tramp[13]),
   function<NativeSelectionFn>(tramp[14]),function<NativeFreeFn>(tramp[15])};
  if(!host().set_native_functions(n)||!host().set_adapter_functions(a)){
   for(auto t:g_core_targets)if(t)g_mh.remove(t);g_hooks_created=false;
   error_storage="TRAMPOLINE_PUBLICATION_FAILED";return error_storage.c_str();
  }
  for(std::size_t i=0;i<g_core_targets.size();++i){
   const int q=g_mh.queue_enable(g_core_targets[i]);
   if(q!=0){
    for(auto old:g_core_targets)if(old)g_mh.remove(old);g_hooks_created=false;
    char buf[192]{};
    std::snprintf(buf,sizeof buf,"MINHOOK_QUEUE_FAILED_hook=%s_idx=%zu_rva=0x%llx_status=%d_%s",
     hook_names[i],i,static_cast<unsigned long long>(guards[i].rva),q,mh_status_name(q));
    error_storage=buf;return error_storage.c_str();
   }
  }
  const int apply_status=g_mh.apply();
  if(apply_status!=0){
   // Apply can partially succeed. Keep module/backend/trampolines resident;
   // never remove a trampoline while any game thread may be executing it.
   char buf[160]{};
   std::snprintf(buf,sizeof buf,"MINHOOK_PARTIAL_ENABLE_PROCESS_RESTART_REQUIRED_status=%d_%s",apply_status,mh_status_name(apply_status));
   error_storage=buf;return error_storage.c_str();
  }
  // Production V3 issuing is authorized only after all of these have succeeded:
  // exact host EXE SHA256, every mandatory guarded hook-site byte check, all 16 core trampoline
  // creations, queueing, and MinHook's final enable/apply step. No CMake switch can
  // bypass this runtime proof.
  if(!host().authorize_validated_issue(true)){
   error_storage="V3_NATIVE_ISSUE_AUTHORIZATION_FAILED_PROCESS_RESTART_REQUIRED";
   return error_storage.c_str();
  }
  installed=true;
  // RC8 physical-evidence quarantine. ContactPair remains statically mapped for
  // future research, but it is NOT created/enabled and is not part of core BSC
  // authorization. Entity/Component/Alive assumptions are likewise non-gating.
  constexpr bool g_wh3_physical_evidence_staged_disabled = true;
  (void)contact_pair_guard;
  if(g_wh3_physical_evidence_staged_disabled)g_wh3_contact_pair_trampoline=nullptr;

  // Phase B — Optional Smart Guard (independent optional hook).
  // If any Smart Guard-specific operation fails:
  // CORE BETTER SHIFT REMAINS ACTIVE; SMART GUARD DISABLED.
  constexpr Guard smart_guard_guard=native_map::kSmartGuardGuard;
  // Current 6c104 build: state-transition hook address/guard is revalidated, but
  // Smart Guard's internal state-object/vtable map is intentionally NOT part of
  // this core runtime-gate diagnostic. Keep optional behavior disabled.
  constexpr bool g_wh3_smart_guard_staged_disabled = true;
  if(g_wh3_smart_guard_staged_disabled){
   host().set_smart_guard_installed(false);
   host().set_smart_guard_runtime_enabled(false);
   error_storage="OK";
   return nullptr;
  }
  if(!guard_matches(smart_guard_guard,base)){
   host().set_smart_guard_installed(false);
   host().set_smart_guard_runtime_enabled(false);
   error_storage="SMART_GUARD_FAIL_DISABLED_BYTE_MISMATCH";
   return nullptr;
  }
  void* sg_target=reinterpret_cast<void*>(base+smart_guard_guard.rva);
  void* sg_tramp=nullptr;
  const int sg_create=g_mh.create(sg_target,pointer(state_transition_hook),&sg_tramp);
  if(sg_create!=0||!sg_tramp){
   host().set_smart_guard_installed(false);
   host().set_smart_guard_runtime_enabled(false);
   error_storage="SMART_GUARD_FAIL_DISABLED_CREATE_FAILED";
   return nullptr;
  }
  g_wh3_state_transition_trampoline=sg_tramp;
  g_smart_guard_target=sg_target;
  host().set_state_transition_trampoline(function<NativeTransitionFn>(sg_tramp));
  const int sg_queue=g_mh.queue_enable(sg_target);
  if(sg_queue!=0){
   g_mh.remove(sg_target);g_smart_guard_target=nullptr;
   g_wh3_state_transition_trampoline=nullptr;
   host().set_smart_guard_installed(false);
   host().set_smart_guard_runtime_enabled(false);
   error_storage="SMART_GUARD_FAIL_DISABLED_QUEUE_FAILED";
   return nullptr;
  }
  const int sg_apply=g_mh.apply();
  if(sg_apply!=0){
   host().set_smart_guard_installed(false);
   host().set_smart_guard_runtime_enabled(false);
   error_storage="SMART_GUARD_FAIL_DISABLED_APPLY_FAILED";
   return nullptr;
  }
  host().set_smart_guard_installed(true);
  host().set_smart_guard_runtime_enabled(true);
  g_wh3_smart_guard_runtime_enabled.store(true,std::memory_order_release);
  error_storage="OK";
  return nullptr;
 }catch(...){error_storage="OBSERVER_INSTALL_CPP_EXCEPTION";return error_storage.c_str();}
}

const char* platform_stop_observer(){
 std::lock_guard<std::mutex> lock(install_mu);
 try{
  // The bridge DLL is deliberately pinned for process lifetime. Safe stop only
  // restores every hooked target to its original entry bytes; trampolines, the
  // MinHook backend and this DLL remain resident. This avoids both teardown-time
  // interception and use-after-free of an in-flight trampoline.
  if(!attempted){error_storage="OK_NOT_STARTED";return nullptr;}
  if(g_observer_stopped){error_storage="OK_STOPPED";return nullptr;}
  if(!g_hooks_created){
   installed=false;g_observer_stopped=true;host().authorize_validated_issue(false);
   host().set_smart_guard_runtime_enabled(false);g_wh3_smart_guard_runtime_enabled.store(false,std::memory_order_release);
   platform_reset_diagnostic_gates();error_storage="OK_STOPPED_NO_HOOKS";return nullptr;
  }
  if(!g_mh.queue_disable||!g_mh.apply){error_storage="OBSERVER_DISABLE_BACKEND_NOT_READY_PROCESS_RESTART_REQUIRED";return error_storage.c_str();}
  // This MinHook backend must have been freshly initialized by us; therefore
  // MH_ALL_HOOKS (nullptr) refers only to hooks created by this bridge instance.
  const int queue_status=g_mh.queue_disable(nullptr);
  if(queue_status!=0&&queue_status!=6){
   char buf[176]{};
   std::snprintf(buf,sizeof buf,"MINHOOK_QUEUE_DISABLE_FAILED_status=%d_%s_PROCESS_RESTART_REQUIRED",queue_status,mh_status_name(queue_status));
   error_storage=buf;return error_storage.c_str();
  }
  const int apply_status=g_mh.apply();
  if(apply_status!=0){
   char buf[176]{};
   std::snprintf(buf,sizeof buf,"MINHOOK_DISABLE_APPLY_FAILED_status=%d_%s_PROCESS_RESTART_REQUIRED",apply_status,mh_status_name(apply_status));
   error_storage=buf;return error_storage.c_str();
  }
  installed=false;g_observer_stopped=true;
  host().authorize_validated_issue(false);
  host().set_smart_guard_runtime_enabled(false);host().set_smart_guard_installed(false);
  g_wh3_smart_guard_runtime_enabled.store(false,std::memory_order_release);
  platform_reset_diagnostic_gates();
  error_storage="OK_STOPPED";return nullptr;
 }catch(...){error_storage="OBSERVER_DISABLE_CPP_EXCEPTION_PROCESS_RESTART_REQUIRED";return error_storage.c_str();}
}
}
