#undef NDEBUG
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cassert>
#include <cstdio>
extern "C" __declspec(dllimport) int BSC_EnableExperimentalRmbContinuation(int);
extern "C" __declspec(dllimport) int BSC_ExperimentalPatchStatus();
int main(){
 assert(BSC_ExperimentalPatchStatus()==0);
 assert(BSC_EnableExperimentalRmbContinuation(1)==-2);
 assert(BSC_ExperimentalPatchStatus()==0);
 assert(BSC_EnableExperimentalRmbContinuation(0)==0);
 std::puts("PASS Windows private process: wrong EXE rejected, no patch installed");
}
