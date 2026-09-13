#include "wh3/packet_tracker.hpp"
#include <algorithm>
#include <limits>
#include <tuple>
namespace wh3 {
bool PacketTracker::valid(std::uintptr_t a,std::size_t n) noexcept {return a&&n&&n<=UINTPTR_MAX-a;}

void PacketTracker::invalidate(std::uintptr_t a,std::size_t n) {
    if(!valid(a,n)){fault_=true;return;}
    const auto z=a+n;
    std::vector<PhysicalSpan> next;next.reserve(spans_.size()+4);
    for(const auto& s:spans_){
        const auto sb=s.address,se=s.address+s.length;
        if(z<=sb||se<=a){next.push_back(s);continue;}
        if(sb<a){auto left=s;left.length=static_cast<std::uint32_t>(a-sb);next.push_back(left);}
        if(z<se){auto right=s;const auto cut=static_cast<std::uint32_t>(z-sb);
            right.address=z;right.length=static_cast<std::uint32_t>(se-z);right.packet_offset+=cut;next.push_back(right);}
    }
    if(next.size()>limit_){fault_=true;spans_.clear();return;}
    spans_.swap(next);
}
void PacketTracker::release(std::uintptr_t a) {
    spans_.erase(std::remove_if(spans_.begin(),spans_.end(),[&](const PhysicalSpan& s){return s.allocation==a;}),spans_.end());
}
void PacketTracker::clear(){spans_.clear();fault_=false;}
bool PacketTracker::put(std::uintptr_t allocation,std::uintptr_t address,std::uint32_t n,const std::shared_ptr<TrackedPacket>& p){
    if(fault_||!valid(address,n)||!allocation||!p||n<7)return false;
    invalidate(address,n);if(fault_)return false;
    if(spans_.size()>=limit_||generation_==UINT64_MAX){fault_=true;return false;}
    spans_.push_back({allocation,address,n,0,++generation_,p});return true;
}
bool PacketTracker::copy(std::uintptr_t allocation,std::uintptr_t dst,std::uintptr_t src,std::uint32_t n){
    if(fault_||!allocation||!valid(src,n)||!valid(dst,n))return false;
    const auto src_end=src+n;std::vector<PhysicalSpan> selected;
    for(const auto& s:spans_){
        const auto sb=s.address,se=s.address+s.length;const auto lo=std::max(sb,src),hi=std::min(se,src_end);
        if(lo>=hi)continue;auto f=s;const auto delta=static_cast<std::uint32_t>(lo-sb);
        f.address=dst+(lo-src);f.length=static_cast<std::uint32_t>(hi-lo);f.packet_offset+=delta;f.allocation=allocation;selected.push_back(f);
    }
    invalidate(dst,n);if(fault_)return false;
    if(spans_.size()+selected.size()>limit_||generation_==UINT64_MAX){fault_=true;return false;}
    const auto gen=++generation_;for(auto& s:selected){s.storage_generation=gen;spans_.push_back(s);}return true;
}

static std::shared_ptr<TrackedPacket> resolve_exact_fragments(const std::vector<PhysicalSpan>& spans,std::uintptr_t start,std::uintptr_t end,Id e){
    if(start>=end)return {};
    struct Piece{std::uintptr_t lo,hi;std::uint32_t po;std::shared_ptr<TrackedPacket> p;};std::vector<Piece> v;
    for(const auto& s:spans){if(!s.packet||s.packet->epoch!=e)continue;const auto sb=s.address,se=s.address+s.length;
        const auto lo=std::max(sb,start),hi=std::min(se,end);if(lo>=hi)continue;
        v.push_back({lo,hi,static_cast<std::uint32_t>(s.packet_offset+(lo-sb)),s.packet});}
    if(v.empty())return {};
    std::sort(v.begin(),v.end(),[](const Piece&a,const Piece&b){return std::tie(a.lo,a.hi,a.po)<std::tie(b.lo,b.hi,b.po);});
    std::shared_ptr<TrackedPacket> packet;std::uintptr_t pos=start;std::uint32_t po=0;
    while(pos<end){const Piece* chosen=nullptr;
        for(const auto& x:v){if(x.lo>pos)break;if(x.lo<=pos&&pos<x.hi){const auto expected=static_cast<std::uint32_t>(x.po+(pos-x.lo));if(expected!=po)continue;
            if(!chosen)chosen=&x;else if(chosen->p!=x.p||chosen->hi!=x.hi||chosen->po!=x.po)return {};}}
        if(!chosen)return {};if(packet&&packet!=chosen->p)return {};packet=chosen->p;const auto advance=chosen->hi-pos;po+=static_cast<std::uint32_t>(advance);pos=chosen->hi;}
    if(!packet||po!=end-start)return {};return packet;
}

std::shared_ptr<TrackedPacket> PacketTracker::resolve(std::uintptr_t payload,std::uintptr_t end,Id e) const{
    if(fault_||payload>=end||payload<7)return {};return resolve_exact_fragments(spans_,payload-7,end,e);
}
std::shared_ptr<TrackedPacket> PacketTracker::resolve_reader(std::uintptr_t data,std::uint32_t cursor,std::uint32_t end_offset,Id e) const{
    if(fault_||!data||cursor<7||cursor>end_offset||data>UINTPTR_MAX-end_offset)return {};
    return resolve_exact_fragments(spans_,data+static_cast<std::uintptr_t>(cursor-7),data+static_cast<std::uintptr_t>(end_offset),e);
}
std::shared_ptr<TrackedPacket> PacketTracker::resolve_reader_bounds(std::uintptr_t data,std::uint32_t field18,std::uint32_t field1c,std::uint32_t cursor,Id e) const{
    if(fault_||!data)return {};const std::uint64_t end64=std::uint64_t(field18)+field1c;
    if(end64>UINT32_MAX||data>UINTPTR_MAX-static_cast<std::uintptr_t>(end64))return {};const auto end=data+static_cast<std::uintptr_t>(end64);
    std::uintptr_t starts[3]{};std::size_t count=0;if(data<=UINTPTR_MAX-field18)starts[count++]=data+field18;
    if(data<=UINTPTR_MAX-field1c)starts[count++]=data+field1c;if(cursor>=7&&data<=UINTPTR_MAX-(cursor-7))starts[count++]=data+(cursor-7);
    std::shared_ptr<TrackedPacket> result;for(std::size_t i=0;i<count;++i){const auto start=starts[i];if(start>=end)continue;auto p=resolve_exact_fragments(spans_,start,end,e);if(!p)continue;
        if(result&&result!=p)return {};result=p;}return result;
}
std::pair<std::uint32_t,std::uint32_t> PacketTracker::coverage(std::uintptr_t start,std::uintptr_t end,Id e) const{
    if(fault_||start>=end)return {0,0};struct I{std::uintptr_t a,b;};std::vector<I> v;std::uint32_t fr=0;
    for(const auto& s:spans_){if(!s.packet||s.packet->epoch!=e)continue;const auto a=std::max(start,s.address),b=std::min(end,s.address+s.length);if(a<b){v.push_back({a,b});++fr;}}
    if(v.empty())return {0,0};std::sort(v.begin(),v.end(),[](const I&x,const I&y){return x.a<y.a||(x.a==y.a&&x.b<y.b);});
    std::uintptr_t a=v[0].a,b=v[0].b;std::uint64_t bytes=0;for(std::size_t i=1;i<v.size();++i){if(v[i].a<=b)b=std::max(b,v[i].b);else{bytes+=b-a;a=v[i].a;b=v[i].b;}}bytes+=b-a;
    return {static_cast<std::uint32_t>(std::min<std::uint64_t>(bytes,UINT32_MAX)),fr};
}
}
