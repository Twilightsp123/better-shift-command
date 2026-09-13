// Real recorded order fields replayed into production observe_external().
// Unit lifetime and geometry absent from the compact TSV use explicit fixture
// values; this is NOT an engine replay or independent payload verification.
#include "wh3/identity_gate.hpp"
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
using namespace wh3;
Id id(const std::string& s){auto r=parse_id(s);if(!r)throw std::runtime_error("bad id "+s);return r.value;}
int main(int argc,char** argv){
 try{
  if(argc!=2)throw std::runtime_error("usage: replay_1428 <runtime_1428.tsv>");
  std::ifstream in(argv[1]);if(!in)throw std::runtime_error("cannot open input");
  std::string line;std::getline(in,line);
  IdentityGate core;auto epoch=core.begin_battle();if(!epoch)throw std::runtime_error("begin failed");
  std::map<Id,Unit> units;unsigned n=0,moves=0,attacks=0,queued=0;
  while(std::getline(in,line)){
   if(line.empty())continue;
   std::istringstream row(line);std::vector<std::string> v;std::string field;
   while(std::getline(row,field,'\t'))v.push_back(field);
   if(v.size()!=9)throw std::runtime_error("bad field count");
   Id uid=id(v[2]);if(!units.count(uid)){auto r=core.register_unit(uid,std::uint64_t(uid)+1);if(!r)throw std::runtime_error("registration failed");units[uid]=r.value;}
   Order o;o.recipient=units.at(uid);o.queued=(v[5]=="true");o.kind=v[6]=="MOVE"?Kind::Move:Kind::Attack;
   if(o.kind==Kind::Move){o.x=0;o.y=0;o.z=0;++moves;}else{o.target_uid=id(v[8]);o.target_root=1;++attacks;}
   if(*o.queued)++queued;
   auto r=core.observe_external(o,{true,id(v[4])});if(!r)throw std::runtime_error(name(r.error));
   const auto& e=r.value;
   if(e.epoch!=id(v[0])||e.serial!=id(v[1])||e.revision!=id(v[3])||!e.engine_seq||*e.engine_seq!=id(v[4])||e.source!=Source::Unknown||v[7]!="UNKNOWN"||e.script_issue_id!=0||e.batch_total)
       throw std::runtime_error("record replay mismatch");
   ++n;
  }
  if(n!=14||moves!=12||attacks!=2||queued!=5||core.issue_enabled())throw std::runtime_error("baseline count mismatch");
  std::cout<<"PASS REAL_1428_REPLAY records="<<n<<" move="<<moves<<" attack="<<attacks<<" queued_true="<<queued<<" source=UNKNOWN verified_issue=false\n";
  std::cout<<"LIMITS: synthetic lifetime/root/geometry for reducer fixture, not native source attribution or game execution.\n";
  return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}
}
