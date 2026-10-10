#include "bsc_continuation_patch.hpp"
#include <cstring>
namespace bsc {
ByteState classify(const std::uint8_t* p,std::size_t n) noexcept {
 if(!p||n<5)return ByteState::Unknown;
 if(std::memcmp(p,kOriginalEntry.data(),5)==0)return ByteState::Original;
 if(std::memcmp(p,kRmbStyleJump.data(),5)==0)return ByteState::Patched;
 return ByteState::Unknown;
}
std::uint32_t resume_target(std::uint32_t site,const std::array<std::uint8_t,5>& b) noexcept {
 if(b[0]!=0xE9)return 0;
 auto d=static_cast<std::uint32_t>(b[1])|static_cast<std::uint32_t>(b[2])<<8|
 static_cast<std::uint32_t>(b[3])<<16|static_cast<std::uint32_t>(b[4])<<24;
 return site+5u+d;
}
}
