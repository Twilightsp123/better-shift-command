// Windows x64 backend. No DllMain hook work; no EXE-file writes; no external injector.
// Byte-locked integrated Windows backend. Build/run status lives in validation/result.json.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <intrin.h>
#include <bcrypt.h>
#include "wh3/bridge_host.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <mutex>
#include <string>
#include <vector>
namespace wh3 {
namespace {
std::mutex install_mu;
bool installed=false, attempted=false;
const char* error="NOT_STARTED";
HMODULE backend=nullptr, resident=nullptr;
constexpr const char* exe_hash="b7315fa718fd84e2e018e2c4df06600e9df0076156b474f148d9d558c939aa55";
struct Guard {std::uintptr_t rva;const char* bytes;};
constexpr Guard guards[]={
 {0x2ef9ff4,"488bc4488958104889701848897820554154415541564157488da888feffff48"},
 {0x2ef838c,"488bc448895808488968104889701857415641574883ec30498b18488bf1488b"},
 {0x2e18f54,"48895c240855488d6c24c04881ec40010000488bd984d2752083b9102d000000"},
 {0x2ee1478,"48895c24084889742410574883ec20488bf18ada4881c188020000e84816f2ff"},
 {0x2d9c620,"488bc44889580848897018488978205541564157488d68d84881ec1001000048"},
 {0x2d9beb8,"48895c240848896c2410488974241857415641574881ecd0000000458af8488b"},
 {0x1c8fd4c,"48895c2418574883ec408b0510cc2602488bd9488d4c245089442450488bfae8"},
 {0x2cba778,"48895c2418574883ec408b05b8202401488bd9488d4c245089442450488bfae8"},
 {0x1b432c4,"48895c24084c8bda488bd94c89590833d2668911418b8300500000894110418b"},
 {0x1b46624,"8039004c8bc9753180790100752b488b51088b4114440fb7820050000066442b"},
 {0x1b247fc,"488bc44889581048897018574883ec20488bfa4c8d40088b920050000033db88"},
 {0x1b2600c,"48895c24084889742410574883ec20488bd98bf2488b4918498bf8e858330000"},
 {0x2d95f8c,"48895c241048897c242055488d6c24a94881ec00010000488bfa488bd9488bd1"},
 {0x2d95a50,"488bc448895810555657488d68a84881ec40010000488bf20f2970d8488bd148"},
 {0x2dcaf24,"40555356574157488d6c24c94881ecc00000004533ff4c8d456f488bda44897d"},
 {0x4ec5c0,"4883ec584885c90f8412010000f605bc1a910302"}
};
using Init=int(WINAPI*)();using Create=int(WINAPI*)(void*,void*,void**);
using Target=int(WINAPI*)(void*);using Apply=int(WINAPI*)();
struct MH {Init init=nullptr;Create create=nullptr;Target queue=nullptr,remove=nullptr;Apply apply=nullptr;};
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
std::uint32_t move_hook(void* u,std::uint32_t a,void* p,std::uint8_t q){return host().order(Kind::Move,u,a,p,q);}
std::uint32_t attack_hook(void* u,std::uint32_t a,void* p,std::uint8_t q){return host().order(Kind::Attack,u,a,p,q);}
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
const char* platform_last_error() noexcept {std::lock_guard<std::mutex> l(install_mu);return error;}
const char* platform_start_observer(){
 std::lock_guard<std::mutex> lock(install_mu);if(installed)return nullptr;if(attempted)return error;
 attempted=true;
 try{
  const auto base=platform_image_base();std::string sha;
  if(!hash_file(path(nullptr),sha))return error="HOST_HASH_READ_FAILED";
  if(sha!=exe_hash)return error="HOST_EXE_SHA256_MISMATCH";
  for(const auto& g:guards)if(!guard_matches(g,base))return error="HOOK_BYTES_MISMATCH";
  // Pin BEFORE any enabling. Never unload callbacks/trampolines mid-flight.
  HMODULE module=nullptr;
  if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
       reinterpret_cast<LPCWSTR>(&platform_start_observer),&module))return error="MODULE_PIN_FAILED";
  resident=module;auto p=path(module);const auto slash=p.find_last_of(L"\\/");
  if(slash==std::wstring::npos)return error="MODULE_PATH_FAILED";
  p.resize(slash+1);p+=L"minhook.x64.dll";
  std::string backend_sha;
  if(!hash_file(p,backend_sha)||backend_sha!="e9c9fa622f5220b4dd5162b817b9295c53a7978a7bd0b656eac0d29a1106e8ea")return error="MINHOOK_SHA256_MISMATCH";
  backend=LoadLibraryExW(p.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
  if(!backend)return error="MINHOOK_BACKEND_MISSING";
  MH mh;
  if(!symbol(backend,"MH_Initialize",mh.init)||!symbol(backend,"MH_CreateHook",mh.create)||
     !symbol(backend,"MH_QueueEnableHook",mh.queue)||!symbol(backend,"MH_ApplyQueued",mh.apply)||
     !symbol(backend,"MH_RemoveHook",mh.remove))return error="MINHOOK_EXPORT_MISSING";
  // Do not take ownership of somebody else's already-initialized backend.
  if(mh.init()!=0)return error="MINHOOK_INITIALIZE_NOT_FRESH";
  std::array<void*,16> targets{},tramp{};
  const std::array<void*,16> detours={pointer(move_hook),pointer(attack_hook),pointer(allocator_hook),pointer(halt_hook),
   pointer(lua_move_hook),pointer(lua_attack_hook),pointer(publish_move_hook),pointer(publish_attack_hook),pointer(writer_begin_hook),pointer(writer_finalize_hook),
   pointer(copy_hook),pointer(stage_hook),pointer(move_handler_hook),pointer(attack_handler_hook),pointer(selection_hook),pointer(free_hook)};
  std::size_t created=0;
  for(std::size_t i=0;i<targets.size();++i){
   targets[i]=reinterpret_cast<void*>(base+guards[i].rva);
   const int create_result=mh.create(targets[i],detours[i],&tramp[i]);
   if(create_result!=0||!tramp[i]){
    if(create_result==0)mh.remove(targets[i]);
    for(std::size_t j=0;j<created;++j)mh.remove(targets[j]);return error="MINHOOK_CREATE_FAILED";
   }
   ++created;
  }
  NativeFunctions n{function<NativeOrderFn>(tramp[0]),function<NativeOrderFn>(tramp[1]),
                    function<NativeAllocatorFn>(tramp[2]),function<NativeHaltFn>(tramp[3])};
  AdapterFunctions a{function<NativeBindingFn>(tramp[4]),function<NativeBindingFn>(tramp[5]),function<NativePublishFn>(tramp[6]),function<NativePublishFn>(tramp[7]),
   function<NativeBeginWriterFn>(tramp[8]),function<NativeFinalizeFn>(tramp[9]),function<NativeCopyFn>(tramp[10]),function<NativeStageFn>(tramp[11]),
   function<NativePacketHandlerFn>(tramp[12]),function<NativePacketHandlerFn>(tramp[13]),
   function<NativeSelectionFn>(tramp[14]),function<NativeFreeFn>(tramp[15])};
  if(!host().set_native_functions(n)||!host().set_adapter_functions(a)){
   for(auto t:targets)mh.remove(t);return error="TRAMPOLINE_PUBLICATION_FAILED";
  }
  for(auto t:targets)if(mh.queue(t)!=0){
    for(auto old:targets)mh.remove(old);return error="MINHOOK_QUEUE_FAILED";
  }
  if(mh.apply()!=0){
   // Apply can partially succeed. Keep module/backend/trampolines resident;
   // never remove a trampoline while any game thread may be executing it.
   return error="MINHOOK_PARTIAL_ENABLE_PROCESS_RESTART_REQUIRED";
  }
  installed=true;error="OK";return nullptr;
 }catch(...){return error="OBSERVER_INSTALL_CPP_EXCEPTION";}
}
}
