#pragma once
// R72: owned synthetic events only. Not a WH3 process hook.
#include <array>
#include <atomic>
#include <cstdint>
#include <type_traits>

namespace bsc_r72 {

struct Event {
  std::uint64_t member_token;   // externally assigned opaque generation ID, never a pointer
  std::uint32_t owner_epoch;
  std::uint32_t tick_sequence;
  std::uint32_t thread_tag;     // test tag, NOT a Windows TID guarantee
  std::uint32_t phase;
  std::uint32_t x_bits;
  std::uint32_t z_bits;
};
static_assert(std::is_trivially_copyable<Event>::value, "publication payload must be trivially copyable");
static_assert(sizeof(Event) == 32, "stable bounded event size");

template<std::size_t N> class BoundedMpsc {
  static_assert(N >= 2 && (N & (N - 1)) == 0, "capacity must be power of two");
  struct Slot {
    std::atomic<std::uint64_t> sequence;
    Event event{};
  };
  std::array<Slot,N> slots_{};
  alignas(64) std::atomic<std::uint64_t> head_{0};
  alignas(64) std::atomic<std::uint64_t> tail_{0};
  alignas(64) std::atomic<std::uint64_t> drops_{0};
 public:
  BoundedMpsc() noexcept {
    for(std::uint64_t i=0;i<N;++i) slots_[i].sequence.store(i,std::memory_order_relaxed);
  }
  BoundedMpsc(const BoundedMpsc&)=delete;
  BoundedMpsc& operator=(const BoundedMpsc&)=delete;
  // Bounded attempts. No heap allocations, no sleep, no locks, no dereference of game pointers.
  bool try_publish(const Event& e) noexcept {
    for(unsigned attempt=0;attempt<32;++attempt) {
      auto pos=head_.load(std::memory_order_relaxed);
      auto &slot=slots_[pos & (N-1)];
      const auto seq=slot.sequence.load(std::memory_order_acquire);
      if(seq==pos) {
        if(head_.compare_exchange_weak(pos,pos+1,std::memory_order_relaxed,std::memory_order_relaxed)) {
          slot.event=e;
          slot.sequence.store(pos+1,std::memory_order_release);
          return true;
        }
      } else if(seq<pos) {
        drops_.fetch_add(1,std::memory_order_relaxed);
        return false;
      }
    }
    drops_.fetch_add(1,std::memory_order_relaxed);
    return false;
  }
  // Exactly one consumer; only one thread may call try_pop at a time.
  bool try_pop(Event& out) noexcept {
    const auto pos=tail_.load(std::memory_order_relaxed);
    auto &slot=slots_[pos & (N-1)];
    if(slot.sequence.load(std::memory_order_acquire)!=pos+1) return false;
    out=slot.event;
    slot.sequence.store(pos+N,std::memory_order_release);
    tail_.store(pos+1,std::memory_order_release);
    return true;
  }
  std::uint64_t dropped() const noexcept {return drops_.load(std::memory_order_acquire);}
};

enum class GateState : std::uint32_t {Dormant,Armed,Stopping,Stopped};
template<std::size_t N> class SyntheticSession {
  BoundedMpsc<N> q_;
  std::atomic<GateState> state_{GateState::Dormant};
  std::atomic<std::uint32_t> active_{0};
  std::atomic<std::uint32_t> session_epoch_{0};
 public:
  bool arm(std::uint32_t epoch) noexcept {
    if(epoch==0 || state_.load(std::memory_order_acquire)!=GateState::Dormant) return false;
    session_epoch_.store(epoch,std::memory_order_release);
    auto prior=GateState::Dormant;
    return state_.compare_exchange_strong(prior,GateState::Armed,
                    std::memory_order_acq_rel,std::memory_order_acquire);
  }
  // Multi-producer. This carries only copied numeric values; no borrowed lifetime.
  bool record(const Event& e) noexcept {
    if(e.member_token==0 || e.owner_epoch!=session_epoch_.load(std::memory_order_acquire)) return false;
    if(state_.load(std::memory_order_acquire)!=GateState::Armed) return false;
    active_.fetch_add(1,std::memory_order_acq_rel);
    if(state_.load(std::memory_order_acquire)!=GateState::Armed) {
      active_.fetch_sub(1,std::memory_order_acq_rel);
      return false;
    }
    bool ok=q_.try_publish(e);
    active_.fetch_sub(1,std::memory_order_release);
    return ok;
  }
  // Controller-thread only. Caller must wait for active_writers=0 and join all producers
  // before destroy; this state check alone does NOT prove external native object lifetime.
  void request_stop() noexcept {
    auto prior=GateState::Armed;
    state_.compare_exchange_strong(prior,GateState::Stopping,
                    std::memory_order_acq_rel,std::memory_order_acquire);
  }
  bool finish_stop() noexcept {
    if(state_.load(std::memory_order_acquire)!=GateState::Stopping ||
       active_.load(std::memory_order_acquire)!=0) return false;
    state_.store(GateState::Stopped,std::memory_order_release);
    return true;
  }
  bool try_pop(Event& e) noexcept {return q_.try_pop(e);}
  std::uint64_t dropped() const noexcept {return q_.dropped();}
  GateState state() const noexcept {return state_.load(std::memory_order_acquire);}
  std::uint32_t active_writers() const noexcept {return active_.load(std::memory_order_acquire);}
};
}
