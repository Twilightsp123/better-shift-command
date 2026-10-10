// BSC native x64 experiment. DLL NEVER installs a patch automatically.
// Explicit exported enable only; exact 241MiB EXE SHA, byte guard, all-thread
// suspension, private rollback. No Lua reissue, queue mutation, or state writes.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <bcrypt.h>
#include "bsc_continuation_patch.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>
namespace {
std::mutex mutex_;
bool enabled_=false;
bool game_sha256(std::string& out) {
 wchar_t path[32768]{};
 DWORD len=GetModuleFileNameW(nullptr,path,32768);
 if(!len||len>=32768)return false;
 HANDLE f=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
                      nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(f==INVALID_HANDLE_VALUE)return false;
 BCRYPT_ALG_HANDLE alg=nullptr;
 BCRYPT_HASH_HANDLE h=nullptr;
 bool ok=false;
 do{
  if(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)!=0)break;
  if(BCryptCreateHash(alg,&h,nullptr,0,nullptr,0,0)!=0)break;
  std::array<UCHAR,65536> buffer{};
  bool io=true;
  for(;;){
   DWORD n=0;
   if(!ReadFile(f,buffer.data(),static_cast<DWORD>(buffer.size()),&n,nullptr)){io=false;break;}
   if(!n)break;
   if(BCryptHashData(h,buffer.data(),n,0)!=0){io=false;break;}
  }
  if(!io)break;
  std::array<UCHAR,32> digest{};
  if(BCryptFinishHash(h,digest.data(),static_cast<ULONG>(digest.size()),0)!=0)break;
  static constexpr char hex[]="0123456789abcdef";
  out.clear();
  for(auto b:digest){out.push_back(hex[b>>4]);out.push_back(hex[b&15]);}
  ok=true;
 }while(false);
 if(h)BCryptDestroyHash(h);
 if(alg)BCryptCloseAlgorithmProvider(alg,0);
 CloseHandle(f);
 return ok;
}
struct SuspendAll {
 std::vector<HANDLE> handles;
 ~SuspendAll(){
  for(auto it=handles.rbegin();it!=handles.rend();++it){ResumeThread(*it);CloseHandle(*it);}
 }
 bool lock(std::uintptr_t target){
  HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
  if(snapshot==INVALID_HANDLE_VALUE)return false;
  // Reserve BEFORE suspending: avoid allocator locks held by paused threads.
  handles.reserve(4096);
  THREADENTRY32 t{};t.dwSize=sizeof(t);
  bool found=Thread32First(snapshot,&t)!=FALSE;
  DWORD pid=GetCurrentProcessId(),self=GetCurrentThreadId();
  for(;found;found=Thread32Next(snapshot,&t)!=FALSE){
   if(t.th32OwnerProcessID!=pid||t.th32ThreadID==self)continue;
   HANDLE th=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,
                        FALSE,t.th32ThreadID);
   if(!th){CloseHandle(snapshot);return false;}
   if(SuspendThread(th)==static_cast<DWORD>(-1)){
    CloseHandle(th);CloseHandle(snapshot);return false;
   }
   handles.push_back(th);
   CONTEXT ctx{};ctx.ContextFlags=CONTEXT_CONTROL;
   if(!GetThreadContext(th,&ctx)){CloseHandle(snapshot);return false;}
   const auto rip=static_cast<std::uintptr_t>(ctx.Rip);
   if(rip>=target&&rip<target+bsc::kOriginalTransfer.size()){
    CloseHandle(snapshot);return false;
   }
  }
  auto error=GetLastError();
  CloseHandle(snapshot);
  return error==ERROR_NO_MORE_FILES;
 }
};
bool write5(void* addr,const std::array<std::uint8_t,5>& bytes){
 DWORD old=0;
 if(!VirtualProtect(addr,5,PAGE_EXECUTE_READWRITE,&old))return false;
 std::memcpy(addr,bytes.data(),5);
 FlushInstructionCache(GetCurrentProcess(),addr,5);
 DWORD unused=0;
 if(!VirtualProtect(addr,5,old,&unused))return false;
 return std::memcmp(addr,bytes.data(),5)==0;
}
int apply(bool enable){
 std::lock_guard<std::mutex> g(mutex_);
 if(enable==enabled_)return enabled_?1:0;
 std::string sha;
 if(!game_sha256(sha)||sha!=bsc::kExactGameSha256)return -2;
 auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
 if(!base)return -3;
 auto* site=reinterpret_cast<std::uint8_t*>(base+bsc::kPatchRva);
 if(enable&&std::memcmp(site,bsc::kOriginalTransfer.data(),17)!=0)return -4;
 if(!enable&&bsc::classify(site,5)!=bsc::ByteState::Patched)return -4;
 SuspendAll threads;
 if(!threads.lock(reinterpret_cast<std::uintptr_t>(site)))return -5;
 if((enable&&std::memcmp(site,bsc::kOriginalTransfer.data(),17)!=0)||
    (!enable&&bsc::classify(site,5)!=bsc::ByteState::Patched))return -4;
 if(!write5(site,enable?bsc::kRmbStyleJump:bsc::kOriginalEntry))return -6;
 enabled_=enable;
 return enable?1:0;
}
}
extern "C" __declspec(dllexport) int BSC_EnableExperimentalRmbContinuation(int enabled){
 return apply(enabled!=0);
}
extern "C" __declspec(dllexport) int BSC_ExperimentalPatchStatus(){
 std::lock_guard<std::mutex> g(mutex_);
 return enabled_?1:0;
}
BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID){return TRUE;}
