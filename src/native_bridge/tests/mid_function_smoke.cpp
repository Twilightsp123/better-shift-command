// Standalone mid-function hook smoke test driver.
// Exercises ONLY code within this test process. Does NOT touch WH3 or external processes.

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstddef>

using Status = int;
using Simple = Status (WINAPI*)();
using Create = Status (WINAPI*)(void*, void*, void**);
using TargetOp = Status (WINAPI*)(void*);

extern "C" std::int64_t target_function_mid_hook(std::int64_t a, std::int64_t b, std::int64_t test_rdi_val);
extern "C" void mid_hook_site_anchor();
extern "C" void test_mid_function_detour_stub();
extern "C" void* g_test_mid_function_trampoline = nullptr;

static volatile LONG g_observer_hits = 0;
static volatile std::uintptr_t g_last_observed_rdi = 0;

extern "C" void test_mid_function_observer(void* rdi_val) noexcept {
    InterlockedIncrement(&g_observer_hits);
    g_last_observed_rdi = reinterpret_cast<std::uintptr_t>(rdi_val);
}

static bool check(Status s, const char* name) {
    if (s == 0) return true;
    std::printf("FAIL %s status=%d\n", name, s);
    return false;
}

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) {
        std::puts("Usage: mid_function_smoke.exe <full path to minhook.x64.dll>");
        return 2;
    }

    HMODULE h = LoadLibraryExW(argv[1], nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!h) {
        std::printf("FAIL LoadLibraryExW error=%lu\n", GetLastError());
        return 3;
    }

    auto init = reinterpret_cast<Simple>(GetProcAddress(h, "MH_Initialize"));
    auto uninit = reinterpret_cast<Simple>(GetProcAddress(h, "MH_Uninitialize"));
    auto create = reinterpret_cast<Create>(GetProcAddress(h, "MH_CreateHook"));
    auto queue = reinterpret_cast<TargetOp>(GetProcAddress(h, "MH_QueueEnableHook"));
    auto apply = reinterpret_cast<Simple>(GetProcAddress(h, "MH_ApplyQueued"));
    auto remove = reinterpret_cast<TargetOp>(GetProcAddress(h, "MH_RemoveHook"));

    if (!init || !uninit || !create || !queue || !apply || !remove) {
        std::puts("FAIL EXPORTS");
        FreeLibrary(h);
        return 4;
    }

    if (!check(init(), "Initialize")) {
        FreeLibrary(h);
        return 5;
    }

    // 1. Establish baseline execution (unhooked)
    const std::int64_t test_a = 10;
    const std::int64_t test_b = 20;
    const std::int64_t test_rdi = 0x123456789ABCDEF0LL;
    const std::int64_t baseline_result = target_function_mid_hook(test_a, test_b, test_rdi);
    std::printf("Baseline result = 0x%llx\n", static_cast<unsigned long long>(baseline_result));

    void* hook_point = reinterpret_cast<void*>(mid_hook_site_anchor);
    void* func_entry = reinterpret_cast<void*>(target_function_mid_hook);
    std::ptrdiff_t hook_offset = reinterpret_cast<char*>(hook_point) - reinterpret_cast<char*>(func_entry);
    std::printf("Function entry = %p, Mid-function hook site = %p (offset = +0x%tx)\n",
        func_entry, hook_point, hook_offset);

    if (hook_offset <= 0) {
        std::puts("FAIL INVALID_MID_HOOK_OFFSET");
        uninit();
        FreeLibrary(h);
        return 6;
    }

    // 2. Create mid-function hook with MASM detour stub
    if (!check(create(hook_point, reinterpret_cast<void*>(test_mid_function_detour_stub),
                      reinterpret_cast<void**>(&g_test_mid_function_trampoline)), "CreateMidHook")
        || !g_test_mid_function_trampoline) {
        std::puts("FAIL TRAMPOLINE_NULL");
        uninit();
        FreeLibrary(h);
        return 7;
    }
    std::printf("Trampoline successfully allocated at %p\n", g_test_mid_function_trampoline);

    // Verify hook not active yet
    std::int64_t res_pre_enable = target_function_mid_hook(test_a, test_b, test_rdi);
    if (res_pre_enable != baseline_result || g_observer_hits != 0) {
        std::puts("FAIL HOOK_PREMATURELY_ACTIVE");
        remove(hook_point);
        uninit();
        FreeLibrary(h);
        return 8;
    }

    // 3. Queue and apply hook
    if (!check(queue(hook_point), "QueueMidHook") || !check(apply(), "ApplyQueued")) {
        remove(hook_point);
        uninit();
        FreeLibrary(h);
        return 9;
    }

    // 4. Test hooked execution over multiple iterations
    for (int i = 0; i < 500; ++i) {
        const std::int64_t rdi_arg = test_rdi + i;
        const std::int64_t expected = baseline_result + i;
        std::int64_t res = target_function_mid_hook(test_a, test_b, rdi_arg);
        if (res != expected) {
            std::printf("FAIL COMPUTATION_MISMATCH at iteration %d (got 0x%llx, expected 0x%llx)\n",
                i, static_cast<unsigned long long>(res), static_cast<unsigned long long>(expected));
            remove(hook_point);
            uninit();
            FreeLibrary(h);
            return 10;
        }
        if (g_last_observed_rdi != static_cast<std::uintptr_t>(rdi_arg)) {
            std::printf("FAIL RDI_CAPTURE_MISMATCH at iteration %d (got 0x%llx, expected 0x%llx)\n",
                i, static_cast<unsigned long long>(g_last_observed_rdi), static_cast<unsigned long long>(rdi_arg));
            remove(hook_point);
            uninit();
            FreeLibrary(h);
            return 11;
        }
    }

    if (g_observer_hits != 500) {
        std::printf("FAIL OBSERVER_HITS count=%ld\n", g_observer_hits);
        remove(hook_point);
        uninit();
        FreeLibrary(h);
        return 12;
    }

    // 5. Remove hook and verify clean detachment
    if (!check(remove(hook_point), "RemoveMidHook")) {
        uninit();
        FreeLibrary(h);
        return 13;
    }

    std::int64_t res_post_remove = target_function_mid_hook(test_a, test_b, test_rdi);
    if (res_post_remove != baseline_result || g_observer_hits != 500) {
        std::puts("FAIL POST_REMOVE_BEHAVIOR");
        uninit();
        FreeLibrary(h);
        return 14;
    }

    if (!check(uninit(), "Uninitialize")) {
        FreeLibrary(h);
        return 15;
    }

    FreeLibrary(h);
    std::puts("PASS MID_FUNCTION_HOOK_SMOKE");
    return 0;
}
