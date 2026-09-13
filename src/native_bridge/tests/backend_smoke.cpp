// Exercises ONLY functions in this executable. Does not open or modify WH3.
// Ensures the actual dynamically loaded backend can create/queue/apply/remove
// detours and preserve several register/stack arguments and both return types.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstdint>

using Status = int;
using Simple = Status (WINAPI*)();
using Create = Status (WINAPI*)(void*, void*, void**);
using TargetOp = Status (WINAPI*)(void*);
using IntTarget = std::int64_t(*)(std::int64_t, std::int64_t, std::int64_t,
    std::int64_t, std::int64_t, std::int64_t, std::int64_t);
using FloatTarget = double(*)(double, double, double, double, double, double);
static IntTarget original_int = nullptr;
static FloatTarget original_float = nullptr;
static volatile LONG int_hits = 0, float_hits = 0;

__declspec(noinline) static std::int64_t int_target(std::int64_t a, std::int64_t b,
    std::int64_t c, std::int64_t d, std::int64_t e, std::int64_t f, std::int64_t g) {
    volatile std::int64_t result = a + 3*b + 5*c + 7*d + 11*e + 13*f + 17*g;
    return result;
}
__declspec(noinline) static double float_target(double a, double b, double c,
    double d, double e, double f) {
    volatile double result = a + 2*b + 4*c + 8*d + 16*e + 32*f;
    return result;
}
static std::int64_t int_observer(std::int64_t a, std::int64_t b, std::int64_t c,
    std::int64_t d, std::int64_t e, std::int64_t f, std::int64_t g) {
    InterlockedIncrement(&int_hits);
    return original_int(a,b,c,d,e,f,g);
}
static double float_observer(double a, double b, double c, double d, double e, double f) {
    InterlockedIncrement(&float_hits);
    return original_float(a,b,c,d,e,f);
}
static bool check(Status s, const char* name) {
    if (s == 0) return true;
    std::printf("FAIL %s status=%d\n", name, s);
    return false;
}
int wmain(int argc, wchar_t** argv) {
    if (argc != 2) { std::puts("Usage: observer_backend_smoke.exe <full backend DLL path>"); return 2; }
    HMODULE h = LoadLibraryExW(argv[1], nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!h) { std::printf("FAIL LoadLibraryExW error=%lu\n", GetLastError()); return 3; }
    auto init = reinterpret_cast<Simple>(GetProcAddress(h,"MH_Initialize"));
    auto uninit = reinterpret_cast<Simple>(GetProcAddress(h,"MH_Uninitialize"));
    auto create = reinterpret_cast<Create>(GetProcAddress(h,"MH_CreateHook"));
    auto queue = reinterpret_cast<TargetOp>(GetProcAddress(h,"MH_QueueEnableHook"));
    auto apply = reinterpret_cast<Simple>(GetProcAddress(h,"MH_ApplyQueued"));
    auto remove = reinterpret_cast<TargetOp>(GetProcAddress(h,"MH_RemoveHook"));
    if (!init || !uninit || !create || !queue || !apply || !remove) {
        std::puts("FAIL EXPORTS"); return 4;
    }
    if (!check(init(),"Initialize")) return 5;
    IntTarget volatile int_call = int_target;
    FloatTarget volatile float_call = float_target;
    const auto int_base = int_call(0x100000001LL,2,3,4,5,6,7);
    const auto float_base = float_call(1.5,2.5,3.5,4.5,5.5,6.5);
    void* t1 = reinterpret_cast<void*>(int_target);
    void* t2 = reinterpret_cast<void*>(float_target);
    if (!check(create(t1,reinterpret_cast<void*>(int_observer),reinterpret_cast<void**>(&original_int)),"CreateInt")
        || !original_int) return 6;
    if (!check(create(t2,reinterpret_cast<void*>(float_observer),reinterpret_cast<void**>(&original_float)),"CreateFloat")
        || !original_float) return 7;
    // CreateHook must not activate either detour.
    if (int_call(0x100000001LL,2,3,4,5,6,7)!=int_base || int_hits != 0
        || float_call(1.5,2.5,3.5,4.5,5.5,6.5)!=float_base || float_hits != 0) return 8;
    if (!check(queue(t1),"QueueInt") || !check(queue(t2),"QueueFloat") || !check(apply(),"ApplyQueued")) return 9;
    for (int i=0;i<1000;++i) {
        if (int_call(0x100000001LL,2,3,4,5,6,7)!=int_base
            || float_call(1.5,2.5,3.5,4.5,5.5,6.5)!=float_base) {
            std::puts("FAIL ARGUMENT_OR_RETURN_PRESERVATION"); return 10;
        }
    }
    if (int_hits!=1000 || float_hits!=1000) { std::puts("FAIL HIT_COUNTS"); return 11; }
    if (!check(remove(t1),"RemoveInt") || !check(remove(t2),"RemoveFloat")) return 12;
    if (int_call(0x100000001LL,2,3,4,5,6,7)!=int_base || int_hits!=1000
        || float_call(1.5,2.5,3.5,4.5,5.5,6.5)!=float_base || float_hits!=1000) return 13;
    if (!check(uninit(),"Uninitialize")) return 14;
    FreeLibrary(h);
    std::puts("PASS BACKEND_PRIVATE_PROCESS_SMOKE");
    return 0;
}
