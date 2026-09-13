#include "wh3/bridge_host.hpp"
namespace wh3 {
std::uintptr_t platform_image_base() noexcept{return 0x140000000ULL;}
bool platform_write(std::uintptr_t,const void*,std::size_t) noexcept{return false;}
bool platform_frame_active(const FrameIdentity&) noexcept{return false;}
FrameIdentity platform_caller_frame(void*) noexcept{return {};}
bool platform_read(std::uintptr_t,void*,std::size_t) noexcept{return false;}
void* platform_lua_symbol(const char*) noexcept{return nullptr;}
const char* platform_start_observer(){return "WINDOWS_X64_REQUIRED";}
bool platform_hooks_installed() noexcept{return false;}
const char* platform_last_error() noexcept{return "NON_GAME_HOST";}
}
