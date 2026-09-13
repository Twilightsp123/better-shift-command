// Loads ONLY our built DLL into this standalone process. No Warhammer process.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstring>
int wmain(int argc,wchar_t** argv) {
 if(argc!=2){std::puts("Expected full path to candidate DLL");return 2;}
 HMODULE m=LoadLibraryExW(argv[1],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
 if(!m){std::printf("FAIL MODULE_LOAD Win32=%lu\n",GetLastError());return 3;}
 FARPROC raw=GetProcAddress(m,"luaopen_wh3_native_bridge");
 if(!raw){FreeLibrary(m);std::puts("FAIL LUA_EXPORT");return 4;}
 using Entry=int(*)(void*);Entry entry=nullptr;static_assert(sizeof entry==sizeof raw);std::memcpy(&entry,&raw,sizeof entry);
 // This executable exports no Lua runtime: the module must fail bind safely,
 // returning zero results BEFORE touching a lua_State or installing hooks.
 int results=entry(nullptr);
 if(results!=0){FreeLibrary(m);std::puts("FAIL NO_HOST_LUA_BIND");return 5;}
 FreeLibrary(m);
 std::puts("PASS MODULE_PRIVATE_PROCESS_LOAD_AND_MISSING_HOST_LUA");return 0;
}
