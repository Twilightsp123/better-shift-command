#include "wh3/evidence_probe.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <set>

namespace wh3 {
namespace {
constexpr std::uintptr_t kOrderCount=0x2f88;
constexpr std::uintptr_t kOrderHead=0x2f8c;
constexpr std::uintptr_t kOrderBase=0x288;
constexpr std::uintptr_t kOrderStride=0x120;
constexpr std::uintptr_t kOrderVtable=0x18;
constexpr std::uintptr_t kOrderId=0x20;
constexpr std::uintptr_t kPayload=0x58;
constexpr std::uintptr_t kSoldierCount=0x114;
constexpr std::uintptr_t kSoldierArray=0x118;
constexpr std::uintptr_t kSquad=0x32f8;
constexpr std::uintptr_t kMeleeCount=0x34b8;
constexpr std::uintptr_t kEntityX=0x88;
constexpr std::uintptr_t kEntityZ=0x90;
constexpr std::uintptr_t kMovementComponent=0x18;
constexpr std::uintptr_t kComponentBackref=0x4a0;
constexpr std::uintptr_t kComponentMovementState=0x8b0;
constexpr std::uintptr_t kGroupCount=0x8c8;
constexpr std::uintptr_t kGroupBase=0x848;
constexpr std::uintptr_t kGroupStride=0x10;
constexpr Id kMaxEntities=300;
constexpr Id kMaxGroups=128;
constexpr Id kMaxOrders=40;
constexpr std::uintptr_t kMoveVtableRva=0x37b31c8;
constexpr std::uintptr_t kAttackVtableRva=0x37b2540;
constexpr std::uint64_t kMaxMotionGapMs=2000;
inline bool finite(float v){return std::isfinite(v);}
}

const char* name(EntityProbeReason r) noexcept {switch(r){
 case EntityProbeReason::None:return "OK";case EntityProbeReason::ContainerHeader:return "CONTAINER_HEADER";
 case EntityProbeReason::PointerRead:return "POINTER_READ";case EntityProbeReason::NullEntitySlot:return "NULL_ENTITY_SLOT";
 case EntityProbeReason::DuplicateEntity:return "DUPLICATE_ENTITY";case EntityProbeReason::AliveQuery:return "ALIVE_QUERY";
 case EntityProbeReason::EntityPosition:return "ENTITY_POSITION";case EntityProbeReason::MovementComponent:return "MOVEMENT_COMPONENT";
 case EntityProbeReason::MovementBackref:return "MOVEMENT_BACKREF";case EntityProbeReason::MovementState:return "MOVEMENT_STATE";
 case EntityProbeReason::ContainerChanged:return "CONTAINER_CHANGED";default:return "UNKNOWN";}}
const char* name(CombatProbeReason r) noexcept {switch(r){
 case CombatProbeReason::None:return "OK";case CombatProbeReason::ContactCountRead:return "CONTACT_COUNT_READ";
 case CombatProbeReason::SquadRead:return "SQUAD_READ";case CombatProbeReason::GroupCountRead:return "GROUP_COUNT_READ";
 case CombatProbeReason::GroupPointerRead:return "GROUP_POINTER_READ";case CombatProbeReason::GroupQuery:return "GROUP_QUERY";
 case CombatProbeReason::TargetRootRead:return "TARGET_ROOT_READ";case CombatProbeReason::TargetUidRead:return "TARGET_UID_READ";
 case CombatProbeReason::GroupChanged:return "GROUP_CHANGED";default:return "UNKNOWN";}}

bool EvidenceProbe::get(std::uintptr_t p,std::size_t off,void* out,std::size_t n)const noexcept{
 if(!read_||!p||off>UINTPTR_MAX-p)return false;return read_(p+off,out,n);
}

ActiveOrderView EvidenceProbe::active_order(std::uintptr_t root)const noexcept{
 ActiveOrderView out;
 for(unsigned attempt=0;attempt<2;++attempt){
  Id count1=0,head1=0;
  if(!get(root,kOrderCount,&count1,4)||!get(root,kOrderHead,&head1,4))return {};
  if(count1==0){
   Id count2=0,head2=0;if(!get(root,kOrderCount,&count2,4)||!get(root,kOrderHead,&head2,4))return {};
   if(count2==0&&head2==head1){out.complete=true;out.active=false;return out;}
   continue;
  }
  if(count1>kMaxOrders||head1>=kMaxOrders)return {};
  const auto slot=root+kOrderBase+std::uintptr_t(head1)*kOrderStride;
  std::uintptr_t vt1=0;Id seq1=0;std::uintptr_t target1=0;float x1=0,z1=0;
  if(!get(slot,kOrderVtable,&vt1,8)||!get(slot,kOrderId,&seq1,4))return {};
  Kind kind=Kind::Move;
  if(vt1==base_+kMoveVtableRva){kind=Kind::Move;if(!get(slot,kPayload,&x1,4)||!get(slot,kPayload+0x10,&z1,4)||!finite(x1)||!finite(z1))return {};}
  else if(vt1==base_+kAttackVtableRva){kind=Kind::Attack;if(!get(slot,kPayload,&target1,8)||!target1)return {};}
  else return {};
  Id count2=0,head2=0,seq2=0;std::uintptr_t vt2=0,target2=0;float x2=0,z2=0;
  if(!get(root,kOrderCount,&count2,4)||!get(root,kOrderHead,&head2,4)||count2!=count1||head2!=head1)continue;
  if(!get(slot,kOrderVtable,&vt2,8)||!get(slot,kOrderId,&seq2,4)||vt2!=vt1||seq2!=seq1)continue;
  if(kind==Kind::Move){if(!get(slot,kPayload,&x2,4)||!get(slot,kPayload+0x10,&z2,4)||x2!=x1||z2!=z1)continue;}
  else {if(!get(slot,kPayload,&target2,8)||target2!=target1)continue;}
  out.complete=true;out.active=true;out.engine_seq=seq1;out.kind=kind;
  if(kind==Kind::Move){out.dest_x=x1;out.dest_z=z1;}else out.target_root=target1;
  return out;
 }
 return {};
}

float EvidenceProbe::median(std::vector<float> v){
 if(v.empty())return 0;const auto n=v.size();std::nth_element(v.begin(),v.begin()+n/2,v.end());float m=v[n/2];
 if((n&1)==0){auto lo=std::max_element(v.begin(),v.begin()+n/2);m=(m+*lo)*0.5f;}return m;
}
std::pair<float,float> EvidenceProbe::robust_center(const std::vector<Pos>& p){
 std::vector<float> xs,zs;xs.reserve(p.size());zs.reserve(p.size());for(const auto& v:p){xs.push_back(v.x);zs.push_back(v.z);}return {median(xs),median(zs)};
}

bool EvidenceProbe::stable_entity_array(std::uintptr_t root,Id count,std::uintptr_t array,const std::vector<std::uintptr_t>& ptrs) const{
 Id count2=0;std::uintptr_t array2=0;
 if(!get(root,kSoldierCount,&count2,4)||!get(root,kSoldierArray,&array2,8)||count2!=count||array2!=array)return false;
 std::vector<std::uintptr_t> ptrs2(count);
 if(!read_||!read_(array,ptrs2.data(),ptrs2.size()*sizeof(std::uintptr_t)))return false;
 return ptrs2==ptrs;
}

EntityIndex EvidenceProbe::entity_index(std::uintptr_t root) const{
 EntityIndex out;Id count=0;std::uintptr_t array=0;
 if(!get(root,kSoldierCount,&count,4)||!get(root,kSoldierArray,&array,8)||!array||count<1||count>kMaxEntities){out.probe_reason=EntityProbeReason::ContainerHeader;return out;}
 std::vector<std::uintptr_t> ptrs(count);
 if(!read_||!read_(array,ptrs.data(),ptrs.size()*sizeof(std::uintptr_t))){out.probe_reason=EntityProbeReason::PointerRead;return out;}
 std::set<std::uintptr_t> unique;
 for(auto e:ptrs){if(!e){out.probe_reason=EntityProbeReason::NullEntitySlot;return out;}if(!unique.insert(e).second){out.probe_reason=EntityProbeReason::DuplicateEntity;return out;}}
 if(!stable_entity_array(root,count,array,ptrs)){out.probe_reason=EntityProbeReason::ContainerChanged;return out;}
 out.complete=true;out.probe_reason=EntityProbeReason::None;out.slot_count=count;out.array=array;out.entities=std::move(ptrs);return out;
}

EntitySnapshot EvidenceProbe::entity_snapshot(std::uintptr_t root,std::uint64_t model_ms){
 EntitySnapshot out;out.model_ms=model_ms;const auto index=entity_index(root);
 if(!index.complete){out.probe_reason=index.probe_reason;reset(root);return out;}
 if(!alive_){out.probe_reason=EntityProbeReason::AliveQuery;reset(root);return out;}
 std::vector<Pos> live;live.reserve(index.entities.size());out.entities.reserve(index.entities.size());out.slot_count=index.slot_count;
 auto previous_it=previous_.find(root);const Previous* previous=(previous_it==previous_.end()?nullptr:&previous_it->second);
 const bool prev_usable=previous&&previous->array==index.array&&previous->slot_count==index.slot_count&&model_ms>previous->model_ms&&(model_ms-previous->model_ms)<=kMaxMotionGapMs;
 std::vector<float> all_vx,all_vz;
 for(auto e:index.entities){
  bool alive=false;if(!alive_(e,&alive)){out.probe_reason=EntityProbeReason::AliveQuery;reset(root);return out;}
  if(!alive){++out.dead_count;continue;}
  float x=0,z=0;if(!get(e,kEntityX,&x,4)||!get(e,kEntityZ,&z,4)||!finite(x)||!finite(z)){out.probe_reason=EntityProbeReason::EntityPosition;reset(root);return out;}
  std::uintptr_t component=0;if(!get(e,kMovementComponent,&component,8)||!component){out.probe_reason=EntityProbeReason::MovementComponent;reset(root);return out;}
  std::uintptr_t backref=0;if(!get(component,kComponentBackref,&backref,8)||backref!=e){out.probe_reason=EntityProbeReason::MovementBackref;reset(root);return out;}
  std::uint32_t movement=0;if(!get(component,kComponentMovementState,&movement,4)||movement>2){out.probe_reason=EntityProbeReason::MovementState;reset(root);return out;}
  switch(movement){case 0:++out.movement_idle_count;break;case 1:++out.movement_pathing_count;break;case 2:++out.movement_halted_count;break;}
  EntityObservation obs;obs.entity=e;obs.x=x;obs.z=z;obs.movement_state=movement;
  if(prev_usable){auto old=previous->pos.find(e);if(old!=previous->pos.end()){
   const float dt=float(model_ms-previous->model_ms);obs.motion_complete=true;obs.vx=(x-old->second.x)*1000.0f/dt;obs.vz=(z-old->second.z)*1000.0f/dt;
   if(finite(obs.vx)&&finite(obs.vz)){all_vx.push_back(obs.vx);all_vz.push_back(obs.vz);}else {out.probe_reason=EntityProbeReason::EntityPosition;reset(root);return out;}
  }}
  out.entities.push_back(obs);live.push_back({e,x,z});
 }
 // Revalidate after all per-entity virtual calls/reads. Any membership change makes
 // the entire frame incomplete rather than mixing two physical populations.
 if(!stable_entity_array(root,index.slot_count,index.array,index.entities)){out.probe_reason=EntityProbeReason::ContainerChanged;reset(root);return out;}
 out.live_count=static_cast<Id>(live.size());
 if(!live.empty()){auto c=robust_center(live);out.median_x=c.first;out.median_z=c.second;}
 if(!all_vx.empty()){out.motion_complete=true;out.motion_matched_count=static_cast<Id>(all_vx.size());out.previous_model_ms=previous->model_ms;out.median_vx=median(all_vx);out.median_vz=median(all_vz);}
 Previous prev;prev.model_ms=model_ms;prev.array=index.array;prev.slot_count=index.slot_count;for(const auto& p:live)prev.pos.emplace(p.entity,p);previous_[root]=std::move(prev);
 out.complete=true;out.probe_reason=EntityProbeReason::None;return out;
}

CombatSnapshot EvidenceProbe::combat_snapshot(std::uintptr_t root) const{
 CombatSnapshot out;
 for(unsigned attempt=0;attempt<2;++attempt){
  Id coarse1=0;if(!get(root,kMeleeCount,&coarse1,4)){out.probe_reason=CombatProbeReason::ContactCountRead;return out;}
  std::uintptr_t squad1=0;if(!get(root,kSquad,&squad1,8)||!squad1){out.probe_reason=CombatProbeReason::SquadRead;return out;}
  Id count1=0;if(!get(squad1,kGroupCount,&count1,4)||count1>kMaxGroups){out.probe_reason=CombatProbeReason::GroupCountRead;return out;}
  std::vector<std::uintptr_t> groups(count1);
  for(Id i=0;i<count1;++i)if(!get(squad1,kGroupBase+std::uintptr_t(i)*kGroupStride,&groups[i],8)||!groups[i]){out.probe_reason=CombatProbeReason::GroupPointerRead;return out;}
  if(count1&&!group_query_){out.probe_reason=CombatProbeReason::GroupQuery;return out;}
  std::vector<std::pair<bool,std::uintptr_t>> q1(count1);
  for(Id i=0;i<count1;++i)if(!group_query_(groups[i],&q1[i].first,&q1[i].second)){out.probe_reason=CombatProbeReason::GroupQuery;return out;}
  Id coarse2=0,count2=0;std::uintptr_t squad2=0;
  if(!get(root,kMeleeCount,&coarse2,4)||!get(root,kSquad,&squad2,8)||!get(squad1,kGroupCount,&count2,4)){out.probe_reason=CombatProbeReason::GroupChanged;return out;}
  if(coarse2!=coarse1||squad2!=squad1||count2!=count1)continue;
  bool stable=true;
  for(Id i=0;i<count1;++i){std::uintptr_t g=0;if(!get(squad1,kGroupBase+std::uintptr_t(i)*kGroupStride,&g,8)||g!=groups[i]){stable=false;break;}}
  if(!stable)continue;
  for(Id i=0;i<count1;++i){bool melee=false;std::uintptr_t target=0;if(!group_query_(groups[i],&melee,&target)){out.probe_reason=CombatProbeReason::GroupQuery;return out;}if(melee!=q1[i].first||target!=q1[i].second){stable=false;break;}}
  if(!stable)continue;
  out.coarse_contact_count=coarse1;out.group_count=count1;
  for(const auto& q:q1){if(!q.first)continue;++out.active_melee_group_count;if(!q.second){out.probe_reason=CombatProbeReason::TargetRootRead;return out;}out.active_target_roots.push_back(q.second);}
  out.complete=true;out.probe_reason=CombatProbeReason::None;return out;
 }
 out.probe_reason=CombatProbeReason::GroupChanged;return out;
}

void EvidenceProbe::reset(std::uintptr_t root) noexcept{previous_.erase(root);}
void EvidenceProbe::clear() noexcept{previous_.clear();}
}
