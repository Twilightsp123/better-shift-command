#undef NDEBUG
#include "bsc_continuation_patch.hpp"
#include <cassert>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <sys/mman.h>
#include <unistd.h>
extern "C" void bsc_synthetic_transfer(void*,void*);
extern "C" unsigned char bsc_synthetic_patch_site[];
extern "C" unsigned char bsc_synthetic_resume[];
struct OldState{unsigned char unused[0x18];std::uint32_t refs=1;};
struct Slot{unsigned char unused[0x18]{};void** next_vtable=nullptr;};
static int calls=0;
extern "C" __attribute__((ms_abi)) void synthetic_transfer(void* slot,void* state){
 assert(slot&&state);++calls;
}
void patch(unsigned char* site,const std::uint8_t* p,size_t n){
 auto pagesz=static_cast<size_t>(sysconf(_SC_PAGESIZE));
 auto base=reinterpret_cast<std::uintptr_t>(site)&~(pagesz-1);
 assert(mprotect(reinterpret_cast<void*>(base),pagesz*2,PROT_READ|PROT_WRITE|PROT_EXEC)==0);
 std::memcpy(site,p,n);
 __builtin___clear_cache(reinterpret_cast<char*>(site),reinterpret_cast<char*>(site+n));
 assert(mprotect(reinterpret_cast<void*>(base),pagesz*2,PROT_READ|PROT_EXEC)==0);
}
int main(){
 using namespace bsc;
 auto* site=bsc_synthetic_patch_site;
 assert(bsc_synthetic_resume==site+17);
 assert(std::memcmp(site,kOriginalTransfer.data(),17)==0);
 void* vtable[12]{};vtable[9]=reinterpret_cast<void*>(synthetic_transfer);
 Slot slot{};slot.next_vtable=vtable;
 OldState state{};
 bsc_synthetic_transfer(&state,&slot);
 assert(state.refs==2&&calls==1);
 patch(site,kRmbStyleJump.data(),5);
 state.refs=1;
 bsc_synthetic_transfer(&state,&slot);
 assert(state.refs==1&&calls==1);
 patch(site,kOriginalEntry.data(),5);
 bsc_synthetic_transfer(&state,&slot);
 assert(state.refs==2&&calls==2);
 std::puts("PASS original instruction execution -> patch -> rollback (synthetic)");
}
