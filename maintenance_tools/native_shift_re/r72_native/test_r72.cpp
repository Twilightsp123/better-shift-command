#include "r72_capture.hpp"
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <set>
#include <thread>
#include <vector>
#define CHECK(condition) do { if (!(condition)) { std::fprintf(stderr,"CHECK FAILED: %s (%s:%d)\n",#condition,__FILE__,__LINE__); std::abort(); } } while(false)
using namespace bsc_r72;

static Event make(std::uint32_t producer, std::uint32_t seq) {
  return Event{0xC0DE000000000000ULL|((std::uint64_t)producer<<32)|seq, 9,seq,producer,2,seq,seq^0xA5A5};
}
static void fifo_wraparound() {
  BoundedMpsc<8> q;
  Event out{};
  for(int round=0;round<1000;++round) {
    for(unsigned n=0;n<8;++n) CHECK(q.try_publish(make(1,8*round+n)));
    CHECK(!q.try_publish(make(1,999999)));
    for(unsigned n=0;n<8;++n) {
      CHECK(q.try_pop(out)); CHECK(out.tick_sequence==8u*round+n);
      CHECK(out.owner_epoch==9);CHECK(out.phase==2);
    }
    CHECK(!q.try_pop(out));
  }
  CHECK(q.dropped()==1000);
}
static void lifecycle_failclosed() {
  SyntheticSession<4> s;
  CHECK(!s.record(make(2,1)));
  CHECK(!s.arm(0));CHECK(s.arm(9));CHECK(!s.arm(9));
  CHECK(!s.record(Event{0,9,4,2,2,3,4}));
  CHECK(!s.record(Event{5,8,4,2,2,3,4}));
  CHECK(s.record(make(2,2)));
  s.request_stop();
  CHECK(!s.record(make(2,3)));
  CHECK(s.finish_stop());
  CHECK(s.state()==GateState::Stopped);
  CHECK(!s.arm(10));
  Event e{}; CHECK(s.try_pop(e));CHECK(e.tick_sequence==2);
  CHECK(!s.try_pop(e));
}
static void parallel_producers() {
  constexpr unsigned P=4, EACH=20000;
  SyntheticSession<1024> s;
  CHECK(s.arm(9));
  std::atomic<unsigned> completed{0};
  std::atomic<unsigned> accepted{0};
  std::thread consumer([&] {
    std::set<std::uint64_t> seen;
    Event e{};
    while(completed.load(std::memory_order_acquire)<P || s.active_writers()!=0) {
      if(s.try_pop(e)) {CHECK(e.owner_epoch==9); CHECK(e.phase==2);
        CHECK(e.x_bits==e.tick_sequence);CHECK(e.z_bits==(e.tick_sequence^0xA5A5));
        CHECK(seen.insert(e.member_token).second);
      } else std::this_thread::yield();
    }
    while(s.try_pop(e)) CHECK(seen.insert(e.member_token).second);
    CHECK(seen.size()==accepted.load(std::memory_order_acquire));
  });
  std::vector<std::thread> producers;
  for(unsigned p=0;p<P;++p)producers.emplace_back([&,p]{
    for(unsigned i=0;i<EACH;++i) {
      auto e=make(p,i);
      if(s.record(e))accepted.fetch_add(1,std::memory_order_relaxed);
    }
    completed.fetch_add(1,std::memory_order_release);
  });
  for(auto& p:producers) p.join();
  consumer.join();
  CHECK(accepted.load()+s.dropped()==P*EACH);
  s.request_stop();CHECK(s.finish_stop());
  std::printf("mpsc attempts=%u accepted=%u drop=%llu\n",P*EACH,accepted.load(),(unsigned long long)s.dropped());
}
int main(){
 static_assert(std::atomic<std::uint64_t>::is_always_lock_free,"requires 64-bit lockfree atomic");
 fifo_wraparound(); lifecycle_failclosed(); parallel_producers();
 std::puts("R72_SYNTHETIC_RING_PASS; NO_GAME_HOOK; NO_OBJECT_LIFETIME_PROOF");
}
