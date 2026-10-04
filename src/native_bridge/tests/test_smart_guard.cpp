// Offline synthetic test suite for Smart Guard Pre-Movement Cancel architecture.
// STRICTLY NO GAME PROCESS / NO RUNTIME WH3 / NO HOOK INJECTION.
#include "wh3/bridge_host.hpp"
#include "wh3/generated_native_map.hpp"
#include <iostream>
#include <vector>
#include <map>
#include <cstring>
#include <cstdint>
#include <stdexcept>

namespace {
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)

constexpr std::uintptr_t kBase = 0x140000000ULL;
constexpr std::uintptr_t kAttackOrderVtable = kBase + wh3::native_map::kAttackVTable;
constexpr std::uintptr_t kMoveOrderVtable = kBase + wh3::native_map::kFullMoveVTable;
constexpr std::uintptr_t kSubOrderVtableA = kBase + 0x037B10C8;
constexpr std::uintptr_t kSubOrderVtableB = kBase + 0x037B0DB0;
constexpr std::uintptr_t kPursueObj = kBase + 0x03BB70C8;
constexpr std::uintptr_t kPursueVtable = kBase + 0x037E9298;
constexpr std::uintptr_t kTakeUpObj = kBase + 0x03BB69D8;
constexpr std::uintptr_t kTakeUpVtable = kBase + 0x037E6318;
constexpr std::uintptr_t kFireStateObj = kBase + 0x03BB6848;
constexpr std::uintptr_t kFireStateVtable = kBase + 0x037E6750;

std::map<std::uintptr_t, std::vector<unsigned char>> g_mem;

bool mock_mem_read(std::uintptr_t address, void* out, std::size_t size) noexcept {
 for (const auto& kv : g_mem) {
  const auto base = kv.first;
  const auto& b = kv.second;
  if (address >= base && address + size >= address && address + size <= base + b.size()) {
   std::memcpy(out, b.data() + (address - base), size);
   return true;
  }
 }
 return false;
}

void put_bytes(std::uintptr_t addr, const void* data, std::size_t size) {
 auto it = g_mem.lower_bound(addr);
 if (it != g_mem.end() && it->first <= addr && addr + size <= it->first + it->second.size()) {
  std::memcpy(it->second.data() + (addr - it->first), data, size);
  return;
 }
 auto& vec = g_mem[addr];
 vec.resize(size);
 std::memcpy(vec.data(), data, size);
}

template<class T>
void put(std::uintptr_t addr, const T& val) {
 put_bytes(addr, &val, sizeof(T));
}

static bool g_trampoline_called = false;
static void* g_trampoline_target = nullptr;
static void* g_trampoline_order = nullptr;
static std::uint8_t g_trampoline_flag = 0;

void mock_trampoline(void* target, void* order, std::uint8_t flag) {
 g_trampoline_called = true;
 g_trampoline_target = target;
 g_trampoline_order = order;
 g_trampoline_flag = flag;
}

void reset_trampoline() {
 g_trampoline_called = false;
 g_trampoline_target = nullptr;
 g_trampoline_order = nullptr;
 g_trampoline_flag = 0;
}

void setup_mock_unit(std::uintptr_t unit_addr, wh3::Id uid, bool ranged, bool guard_on) {
 put<std::uint32_t>(unit_addr + 0x108, ranged ? 0x10U : 0x00U);
 put<std::uint32_t>(unit_addr + 0x3D1C, guard_on ? 0x01U : 0x00U);
 put<wh3::Id>(unit_addr + 0x3EA0, uid);
}

void setup_mock_order(std::uintptr_t order_addr, std::uintptr_t vtable, wh3::Id engine_seq, std::uintptr_t unit_addr) {
 put<std::uintptr_t>(order_addr + 0x00, vtable);
 put<wh3::Id>(order_addr + 0x08, engine_seq); // RC2 deliberately ignores this for ownership.
 put<std::uintptr_t>(order_addr + 0x18, unit_addr);
}

void setup_active_attack(std::uintptr_t unit_root, wh3::Id engine_seq) {
 constexpr std::uintptr_t kOrderCount=0x2f88, kOrderHead=0x2f8c, kOrderBase=0x288;
 constexpr std::uintptr_t kOrderVtable=0x18, kOrderId=0x20, kPayload=0x58;
 wh3::Id count=1, head=0;
 put<wh3::Id>(unit_root + kOrderCount, count);
 put<wh3::Id>(unit_root + kOrderHead, head);
 const auto slot=unit_root + kOrderBase;
 put<std::uintptr_t>(slot + kOrderVtable, kAttackOrderVtable);
 put<wh3::Id>(slot + kOrderId, engine_seq);
 const std::uintptr_t target_root=0x0BADF00DULL;
 put<std::uintptr_t>(slot + kPayload, target_root);
}

void setup_active_move(std::uintptr_t unit_root, wh3::Id engine_seq) {
 constexpr std::uintptr_t kOrderCount=0x2f88, kOrderHead=0x2f8c, kOrderBase=0x288;
 constexpr std::uintptr_t kOrderVtable=0x18, kOrderId=0x20, kPayload=0x58;
 wh3::Id count=1, head=0;
 put<wh3::Id>(unit_root + kOrderCount, count);
 put<wh3::Id>(unit_root + kOrderHead, head);
 const auto slot=unit_root + kOrderBase;
 put<std::uintptr_t>(slot + kOrderVtable, kMoveOrderVtable);
 put<wh3::Id>(slot + kOrderId, engine_seq);
 const float x=10.0f, y=0.0f, z=20.0f;
 put<float>(slot + kPayload, x);
 put<float>(slot + kPayload + 0x04, y);
 put<float>(slot + kPayload + 0x08, z);
 put<float>(slot + kPayload + 0x10, 999999.0f);
}

void setup_inactive_order(std::uintptr_t unit_root) {
 wh3::Id count=0, head=0;
 put<wh3::Id>(unit_root + 0x2f88, count);
 put<wh3::Id>(unit_root + 0x2f8c, head);
}

void setup_mock_state(std::uintptr_t state_addr, std::uintptr_t vtable) {
 put<std::uintptr_t>(state_addr, vtable);
}
} // namespace

int main() {
 int pass = 0, fail = 0;
 auto test = [&](const char* label, auto fn) {
  try {
   fn();
   ++pass;
   std::cout << "PASS " << label << "\n";
  } catch (const std::exception& e) {
   ++fail;
   std::cout << "FAIL " << label << ": " << e.what() << "\n";
  }
 };

 setup_mock_state(kPursueObj, kPursueVtable);
 setup_mock_state(kTakeUpObj, kTakeUpVtable);
 setup_mock_state(kFireStateObj, kFireStateVtable);

 wh3::BridgeHost host(mock_mem_read, kBase);
 host.set_state_transition_trampoline(mock_trampoline);
 host.set_smart_guard_installed(true);
 host.set_smart_guard_runtime_enabled(true);

 constexpr std::uintptr_t kUnit1 = 0x200000;
 constexpr std::uintptr_t kOrder1 = 0x300000;
 constexpr wh3::Id kUid1 = 1001;
 constexpr wh3::Id kSeq1 = 42;

 test("Smart Guard client inactive -> passes through to trampoline even if runtime enabled", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);
  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.empty());
 });

 auto tg_client = host.acquire_client("TRUE_GUARD", "test_battle");
 CK(tg_client);
 auto sgen = host.smart_guard_enable(tg_client.value.first, true);
 CK(sgen);

 test("Guard OFF -> transition passes through to trampoline", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, false); // Guard OFF
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);
  CK(g_trampoline_target == reinterpret_cast<void*>(kPursueObj));
  CK(g_trampoline_order == reinterpret_cast<void*>(kOrder1));
  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.empty());
 });

 test("Non-local player unit -> transition passes through to trampoline", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);
  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.empty());
 });

 test("Non-ranged unit -> transition passes through to trampoline", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, false, true); // Non-ranged
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);
  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.empty());
 });

 test("Sub-order context + top-level active MOVE -> transition passes through", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_move(kUnit1, 77);
  setup_mock_order(kOrder1, kSubOrderVtableA, 1234, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);
  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.empty());
  CK(host.status().smart_guard_active_not_attack > 0);
 });

 test("Sub-order context + top-level ATTACK -> PURSUE suppresses using active seq", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, 101);
  setup_mock_order(kOrder1, kSubOrderVtableA, 9999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(!g_trampoline_called);
  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.size() == 1);
  CK(drained[0].unit_uid == kUid1);
  CK(drained[0].engine_seq == 101);
  CK(drained[0].engine_seq != 9999);
  CK(drained[0].reason == wh3::SmartGuardCancelReason::Pursue);
 });

 test("Sub-order context + top-level ATTACK -> TAKE_UP suppresses using active seq", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, 202);
  setup_mock_order(kOrder1, kSubOrderVtableB, 8888, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kTakeUpObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(!g_trampoline_called);
  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.size() == 1);
  CK(drained[0].engine_seq == 202);
  CK(drained[0].reason == wh3::SmartGuardCancelReason::TakeUpPositions);
 });

 test("Attack + Guard + PURSUE -> queued with PURSUE reason, transition suppressed", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(!g_trampoline_called); // SUPPRESSED

  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.size() == 1);
  CK(drained[0].unit_uid == kUid1);
  CK(drained[0].engine_seq == kSeq1);
  CK(drained[0].reason == wh3::SmartGuardCancelReason::Pursue);
 });

 test("Attack + Guard + TAKE_UP_POSITIONS -> queued with TAKE_UP_POSITIONS reason, transition suppressed", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kTakeUpObj), reinterpret_cast<void*>(kOrder1), 0);
  CK(!g_trampoline_called); // SUPPRESSED

  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.size() == 1);
  CK(drained[0].unit_uid == kUid1);
  CK(drained[0].engine_seq == kSeq1);
  CK(drained[0].reason == wh3::SmartGuardCancelReason::TakeUpPositions);
 });

 test("Wrong target vtable (tampered memory) -> passes through to trampoline", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  setup_mock_state(kPursueObj, 0x12345678ULL);
  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);
  setup_mock_state(kPursueObj, kPursueVtable);
 });

 test("Duplicate same uid/seq -> one queue item, transition suppressed both times", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(!g_trampoline_called);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(!g_trampoline_called);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(!g_trampoline_called);

  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.size() == 1);
  CK(drained[0].unit_uid == kUid1);
  CK(drained[0].engine_seq == kSeq1);
 });

 test("Queue capacity limit (64 entries) overflow -> 65th entry fails open to trampoline", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();

  for (wh3::Id i = 1; i <= 64; ++i) {
   const std::uintptr_t u = 0x400000 + i * 0x4000;
   const std::uintptr_t o = 0x800000 + i * 0x100;
   host.smart_guard_register_local_unit(i);
   setup_mock_unit(u, i, true, true);
   setup_active_attack(u, i * 10);
   setup_mock_order(o, kSubOrderVtableA, 9000 + i, u);
   host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(o), 1);
   CK(!g_trampoline_called);
  }

  const std::uintptr_t u65 = 0x400000 + 65 * 0x4000;
  const std::uintptr_t o65 = 0x800000 + 65 * 0x100;
  host.smart_guard_register_local_unit(65);
  setup_mock_unit(u65, 65, true, true);
  setup_active_attack(u65, 650);
  setup_mock_order(o65, kSubOrderVtableA, 9065, u65);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(o65), 1);
  CK(g_trampoline_called);

  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.size() == 64);
 });

 test("Smart Guard runtime latch false -> passthrough", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.set_smart_guard_runtime_enabled(false);
  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);

  host.set_smart_guard_runtime_enabled(true);
 });

 test("Attack + Guard + PURSUE with top-level engine_seq zero -> suppressed and queued", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, 0);
  setup_mock_order(kOrder1, kSubOrderVtableA, 7777, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(!g_trampoline_called);
  auto drained = host.drain_smart_guard_cancel_requests();
  CK(drained.size() == 1);
  CK(drained[0].unit_uid == kUid1);
  CK(drained[0].engine_seq == 0);
  CK(drained[0].reason == wh3::SmartGuardCancelReason::Pursue);
 });

 test("Drain operation clears queue and updates counters", [&] {
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  auto d1 = host.drain_smart_guard_cancel_requests();
  CK(d1.size() == 1);

  auto d2 = host.drain_smart_guard_cancel_requests();
  CK(d2.empty());
 });

 test("Target matched but active-order probe incomplete -> fail open", [&] {
  reset_trampoline();
  host.smart_guard_clear_local_units();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  // Force an invalid active-order container regardless of previous test memory.
  put<wh3::Id>(kUnit1 + 0x2f88, 41); // > EvidenceProbe::kMaxOrders (40)
  put<wh3::Id>(kUnit1 + 0x2f8c, 0);
  setup_mock_order(kOrder1, kSubOrderVtableA, 31337, kUnit1);
  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);
  CK(host.drain_smart_guard_cancel_requests().empty());
  CK(host.status().smart_guard_active_probe_failed > 0);
 });

 test("Simulated Lua-side deferred cancel: same Attack seq -> halt executed", [&] {
  wh3::SmartGuardCancelRequest req{kUid1, 42, wh3::SmartGuardCancelReason::Pursue};
  bool guard_active = true;
  std::string active_kind = "ATTACK";
  wh3::Id active_seq = 42;
  bool halted = false;

  if (active_kind == "ATTACK" && active_seq == req.engine_seq && guard_active) {
   halted = true;
  }
  CK(halted);
 });

 test("Simulated Lua-side deferred cancel: player manual Move race -> DROP, no halt", [&] {
  wh3::SmartGuardCancelRequest req{kUid1, 42, wh3::SmartGuardCancelReason::Pursue};
  bool guard_active = true;
  std::string active_kind = "MOVE";
  wh3::Id active_seq = 43;
  bool halted = false;

  if (active_kind == "ATTACK" && active_seq == req.engine_seq && guard_active) {
   halted = true;
  }
  CK(!halted);
 });

 test("Simulated Lua-side deferred cancel: new Attack seq replaces old -> DROP, no halt", [&] {
  wh3::SmartGuardCancelRequest req{kUid1, 42, wh3::SmartGuardCancelReason::Pursue};
  bool guard_active = true;
  std::string active_kind = "ATTACK";
  wh3::Id active_seq = 45;
  bool halted = false;

  if (active_kind == "ATTACK" && active_seq == req.engine_seq && guard_active) {
   halted = true;
  }
  CK(!halted);
 });

 test("Simulated Lua-side deferred cancel: Guard turned OFF before poll -> DROP, no halt", [&] {
  wh3::SmartGuardCancelRequest req{kUid1, 42, wh3::SmartGuardCancelReason::Pursue};
  bool guard_active = false;
  std::string active_kind = "ATTACK";
  wh3::Id active_seq = 42;
  bool halted = false;

  if (active_kind == "ATTACK" && active_seq == req.engine_seq && guard_active) {
   halted = true;
  }
  CK(!halted);
 });

 test("Smart Guard client disable -> transition passes through and allowlist is cleared", [&] {
  reset_trampoline();
  host.smart_guard_register_local_unit(kUid1);
  setup_mock_unit(kUnit1, kUid1, true, true);
  setup_active_attack(kUnit1, kSeq1);
  setup_mock_order(kOrder1, kSubOrderVtableA, 999, kUnit1);

  auto dis = host.smart_guard_enable(tg_client.value.first, false);
  CK(dis);
  CK(!host.smart_guard_client_active());

  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);

  // Allowlist was cleared on disable
  host.smart_guard_enable(tg_client.value.first, true);
  reset_trampoline();
  host.state_transition(reinterpret_cast<void*>(kPursueObj), reinterpret_cast<void*>(kOrder1), 1);
  CK(g_trampoline_called);
 });

 std::cout << "TOTAL " << pass << " PASS " << fail << " FAIL (Smart Guard Offline Suite)\n";
 return fail ? 1 : 0;
}
