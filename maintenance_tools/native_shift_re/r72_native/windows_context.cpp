// Windows x64 standalone ABI/SEH fixture. Never attached to WH3.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winnt.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include "r72_capture.hpp"
using bsc_r72::Event;
#define CHECK(x) do { if(!(x)) {std::fprintf(stderr, "R72_WIN_CHECK_FAILED %s:%d %s\n",__FILE__,__LINE__,#x);std::abort();} }while(0)
extern "C" int bsc_win64_roundtrip(const Event*, volatile std::uint32_t*);
extern "C" int bsc_win64_verify_sentinel(const Event*, volatile std::uint32_t*);
extern "C" void bsc_fixture_callback(const Event* e, volatile std::uint32_t* marker) {
    if(e->phase==0xBEEF) RaiseException(0xE0420072,0,0,nullptr);
    CHECK(e->member_token==0xAABBCCDD11223344ULL);
    CHECK(e->owner_epoch==17);
    *marker = e->tick_sequence + 1;
}
// __try region intentionally contains no C++ objects with destructors.
static void seh_unwind_check() {
    Event e{0xAABBCCDD11223344ULL,17,4,11,0xBEEF,0,0};
    volatile std::uint32_t marker=0;
    int caught=0;
    __try { bsc_win64_roundtrip(&e,&marker); }
    __except(GetExceptionCode()==0xE0420072 ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) { caught=1; }
    CHECK(caught==1);CHECK(marker==0);
}
int main() {
    DWORD64 base=0;
    auto unwind=RtlLookupFunctionEntry(reinterpret_cast<DWORD64>(&bsc_win64_roundtrip),&base,nullptr);
    CHECK(unwind!=nullptr);
    CHECK(unwind->EndAddress>unwind->BeginAddress);
    Event e{0xAABBCCDD11223344ULL,17,4,11,2,0,0};
    volatile std::uint32_t marker=0;
    CHECK(bsc_win64_roundtrip(&e,&marker)==1);
    CHECK(marker==5);
    marker=0;
    CHECK(bsc_win64_verify_sentinel(&e,&marker)==1);
    CHECK(marker==5);
    seh_unwind_check();
    std::puts("R72_WINDOWS_ABI_UNWIND_FIXTURE_PASS; NO_WH3_HOOK; NO_HOOK_UNWIND_PROOF");
    return 0;
}
