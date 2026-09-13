#include "wh3/packet_tracker.hpp"
#include <iostream>
#include <stdexcept>
using namespace wh3;
#define CK(x) do{if(!(x))throw std::runtime_error(#x);}while(false)
int main(){int pass=0,fail=0;auto test=[&](const char* name,auto fn){try{fn();++pass;std::cout<<"PASS "<<name<<'\n';}catch(const std::exception& e){++fail;std::cout<<"FAIL "<<name<<" "<<e.what()<<'\n';}};
 auto packet=[](int id=1){auto p=std::make_shared<TrackedPacket>();p->identity=id;p->epoch=1;return p;};
 test("exact physical payload and end resolve",[&]{PacketTracker t;auto p=packet();CK(t.put(1000,1010,20,p));CK(t.resolve(1017,1030,1)==p);});
 test("same content is irrelevant to identity",[&]{PacketTracker t;auto a=packet(),b=packet(2);CK(t.put(1000,1000,20,a));CK(t.put(2000,2000,20,b));CK(t.resolve(2007,2020,1)==b);});
 test("offset-only containment does not resolve",[&]{PacketTracker t;auto p=packet();t.put(1000,1000,20,p);CK(!t.resolve(1008,1020,1));});
 test("packet end must match exactly",[&]{PacketTracker t;auto p=packet();t.put(1000,1000,20,p);CK(!t.resolve(1007,1021,1));});
 test("full copy preserves logical token",[&]{PacketTracker t;auto p=packet();t.put(1000,1010,20,p);t.copy(2000,2000,1000,40);CK(t.resolve(2017,2030,1)==p);});
 test("reader exact interval resolves without naming start-length fields",[&]{PacketTracker t;auto p=packet();CK(t.put(1000,1010,20,p));CK(t.resolve_reader(1000,17,30,1)==p);});
 test("reader cursor must be exactly seven bytes after packet start",[&]{PacketTracker t;auto p=packet();t.put(1000,1010,20,p);CK(!t.resolve_reader(1000,18,30,1));});
 test("reader end bound must match exact packet end",[&]{PacketTracker t;auto p=packet();t.put(1000,1010,20,p);CK(!t.resolve_reader(1000,17,31,1));});
 test("handler bounds resolve when field18 is start and field1c is length",[&]{PacketTracker t;auto p=packet();t.put(1000,1010,20,p);CK(t.resolve_reader_bounds(1000,10,20,99,1)==p);});
 test("handler bounds resolve when field1c is start and field18 is length",[&]{PacketTracker t;auto p=packet();t.put(1000,1010,20,p);CK(t.resolve_reader_bounds(1000,20,10,99,1)==p);});
 test("handler bounds duplicate structural candidates resolve same packet",[&]{PacketTracker t;auto p=packet();t.put(1000,1010,20,p);CK(t.resolve_reader_bounds(1000,10,20,17,1)==p);});
 test("partial packet copy does not manufacture identity",[&]{PacketTracker t;auto p=packet();t.put(1000,1010,20,p);t.copy(2000,2000,1000,25);CK(!t.resolve(2017,2030,1));});
 test("split copies reconstruct one exact packet lineage",[&]{PacketTracker t;auto p=packet();CK(t.put(1000,1000,20,p));CK(t.copy(2000,2000,1000,9));CK(t.copy(2000,2009,1009,11));CK(t.resolve(2007,2020,1)==p);});
 test("partial overlap copy propagates exact packet offsets",[&]{PacketTracker t;auto p=packet();CK(t.put(1000,1010,20,p));CK(t.copy(2000,2000,1005,15));CK(t.copy(2000,2015,1020,10));CK(t.resolve(2012,2025,1)==p);});
 test("gap in lineage never resolves",[&]{PacketTracker t;auto p=packet();CK(t.put(1000,1000,20,p));CK(t.copy(2000,2000,1000,9));CK(t.copy(2000,2010,1010,10));CK(!t.resolve(2007,2020,1));});
 test("mixed packet fragments never resolve as one packet",[&]{PacketTracker t;auto a=packet(),b=packet(2);CK(t.put(1000,1000,20,a));CK(t.put(3000,3000,20,b));CK(t.copy(2000,2000,1000,10));CK(t.copy(2000,2010,3010,10));CK(!t.resolve(2007,2020,1));});
 test("source overwrite does not invalidate immutable copied instance",[&]{PacketTracker t;auto p=packet();t.put(1000,1000,20,p);t.copy(2000,2000,1000,20);t.invalidate(1000,20);CK(t.resolve(2007,2020,1)==p);CK(!t.resolve(1007,1020,1));});
 test("destination overwrite removes old labels",[&]{PacketTracker t;auto p=packet();t.put(1000,1000,20,p);t.copy(1000,1000,3000,20);CK(!t.resolve(1007,1020,1));});
 test("deallocation invalidates a complete allocation lifetime",[&]{PacketTracker t;auto p=packet();t.put(1000,1010,20,p);t.release(1000);CK(!t.resolve(1017,1030,1));});
 test("address reuse obtains new generation",[&]{PacketTracker t;auto a=packet(),b=packet(2);t.put(1000,1000,20,a);auto g=t.spans()[0].storage_generation;t.release(1000);t.put(1000,1000,20,b);CK(t.spans()[0].storage_generation>g&&t.resolve(1007,1020,1)==b);});
 test("different battle never resolves",[&]{PacketTracker t;auto p=packet();t.put(1000,1000,20,p);CK(!t.resolve(1007,1020,2));});
 test("overlapping copy snapshots source before invalidation",[&]{PacketTracker t;auto p=packet();t.put(1000,1000,20,p);CK(t.copy(1000,1005,1000,20));CK(t.resolve(1012,1025,1)==p);});
 test("capacity fail closed",[&]{PacketTracker t(1);t.put(1000,1000,20,packet());CK(!t.put(2000,2000,20,packet(2)));CK(t.faulted());CK(!t.resolve(1007,1020,1));});
 test("pointer arithmetic overflow rejected",[&]{PacketTracker t;CK(!t.put(1,UINTPTR_MAX-3,20,packet()));});
 test("cancelled token remains a tombstone",[&]{PacketTracker t;auto p=packet();p->owned=true;t.put(1000,1000,20,p);p->cancelled=true;CK(t.resolve(1007,1020,1)->cancelled);});
 test("consumed token cannot masquerade as external on repeat read",[&]{PacketTracker t;auto p=packet();p->owned=true;t.put(1000,1000,20,p);p->consumed=true;CK(t.resolve(1007,1020,1)->owned&&t.resolve(1007,1020,1)->consumed);});
 test("coverage diagnostic reports union bytes and fragments without granting identity",[&]{PacketTracker t;auto p=packet();CK(t.put(1000,1000,20,p));CK(t.copy(2000,2000,1000,8));CK(t.copy(2000,2010,1010,10));auto c=t.coverage(2000,2020,1);CK(c.first==18&&c.second==2);CK(!t.resolve(2007,2020,1));});
 test("clear retires all labels",[&]{PacketTracker t;t.put(1000,1000,20,packet());t.clear();CK(t.size()==0);});
 std::cout<<"TOTAL "<<pass<<" PASS "<<fail<<" FAIL\n";return fail?1:0;
}
