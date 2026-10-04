#pragma once
// GENERATED FILE. Edit native_maps/*.json, then regenerate.
#include <array>
#include <cstdint>

namespace wh3 {
namespace native_map {

struct GuardSpec {
    std::uintptr_t rva;
    const char* bytes;
};

inline constexpr char kExeSha256[] = "6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297";

inline constexpr std::array<GuardSpec, 16> kCoreGuards{{
    GuardSpec{0x030344D4, "488bc4488958104889701848897820554154415541564157488da888feffff48"},
    GuardSpec{0x03032854, "488bc448895808488968104889701857415641574883ec30498b18488bf1488b"},
    GuardSpec{0x02F5248C, "48895c240855488d6c24c04881ec40010000488bd984d2752083b9102d000000"},
    GuardSpec{0x0301B890, "48895c24084889742410574883ec20488bf18ada4881c188020000e88007f2ff"},
    GuardSpec{0x02ED5808, "488bc44889580848897018488978205541564157488d68d84881ec1001000048"},
    GuardSpec{0x02ED50A0, "48895c240848896c2410488974241857415641574881ecd0000000458af8488b"},
    GuardSpec{0x01CB1DC8, "48895c2418574883ec408b0524c53b02488bd9488d4c245089442450488bfae8"},
    GuardSpec{0x02DF28BC, "48895c2418574883ec408b0504b92701488bd9488d4c245089442450488bfae8"},
    GuardSpec{0x01BCE174, "48895c24084c8bda488bd94c89590833d2668911418b8300500000894110418b"},
    GuardSpec{0x01BD140C, "8039004c8bc9753180790100752b488b51088b4114440fb7820050000066442b"},
    GuardSpec{0x01BAF488, "488bc44889581048897018574883ec20488bfa4c8d40088b920050000033db88"},
    GuardSpec{0x01BB0C94, "48895c24084889742410574883ec20488bd98bf2488b4918498bf8e830330000"},
    GuardSpec{0x02ECF0E0, "48895c241048897c242055488d6c24a94881ec00010000488bfa488bd9488bd1"},
    GuardSpec{0x02ECEBAC, "488bc448895810555657488d68a84881ec40010000488bf20f2970d8488bd148"},
    GuardSpec{0x02F042D4, "40555356574157488d6c24c94881ecc00000004533ff4c8d456f488bda44897d"},
    GuardSpec{0x0052F770, "4883ec584885c90f8412010000f6054caaa30302"},
}};

inline constexpr std::array<const char*, 16> kHookNames{{
    "move",
    "attack",
    "allocator",
    "halt",
    "lua_move",
    "lua_attack",
    "publish_move",
    "publish_attack",
    "writer_begin",
    "writer_finalize",
    "copy",
    "stage",
    "move_handler",
    "attack_handler",
    "selection",
    "free",
}};

inline constexpr GuardSpec kContactPairGuard{0x030A3859, "488b47184885c07418488b88e8020000"};
inline constexpr GuardSpec kSmartGuardGuard{0x030E2524, "48895c24084889742410574883ec20488b02488bf1488bca418af8488bdaff90"};

inline constexpr std::uintptr_t kFullMoveVTable = 0x03910AA8;
inline constexpr std::uintptr_t kSimpleInterceptMoveVTable = 0x0390E248;
inline constexpr std::uintptr_t kAttackVTable = 0x03910228;

} // namespace native_map
} // namespace wh3
