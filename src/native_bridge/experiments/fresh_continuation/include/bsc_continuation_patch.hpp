#pragma once
#include <array>
#include <cstdint>
#include <cstddef>
namespace bsc {
constexpr std::uint32_t kPatchRva=0x0304459D, kResumeRva=0x030445AE;
constexpr const char* kExactGameSha256="518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a";
constexpr std::array<std::uint8_t,17> kOriginalTransfer={
0xFF,0x46,0x18,0x49,0x8D,0x4E,0x18,0x49,0x8B,0x46,0x18,0x48,0x8B,0xD6,0xFF,0x50,0x48};
constexpr std::array<std::uint8_t,5> kOriginalEntry={0xFF,0x46,0x18,0x49,0x8D};
constexpr std::array<std::uint8_t,5> kRmbStyleJump={0xE9,0x0C,0x00,0x00,0x00};
// Experimental. Skip original MOVE->MOVE previous state reference increase and
// virtual inheritance but retain CA native queue pop and new MOVE work.
enum class ByteState{Original,Patched,Unknown};
ByteState classify(const std::uint8_t*,std::size_t) noexcept;
std::uint32_t resume_target(std::uint32_t,const std::array<std::uint8_t,5>&) noexcept;
}
