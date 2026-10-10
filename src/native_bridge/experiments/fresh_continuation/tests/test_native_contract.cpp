#undef NDEBUG
#include "bsc_continuation_patch.hpp"
#include <cassert>
#include <cstring>
#include <cstdio>
int main(){
 using namespace bsc;
 static_assert(kResumeRva-(kPatchRva+5u)==12u,"bad x64 branch");
 assert(resume_target(kPatchRva,kRmbStyleJump)==kResumeRva);
 assert(classify(kOriginalTransfer.data(),17)==ByteState::Original);
 assert(classify(kRmbStyleJump.data(),5)==ByteState::Patched);
 assert(classify(nullptr,5)==ByteState::Unknown);
 assert(classify(kOriginalTransfer.data(),4)==ByteState::Unknown);
 auto changed=kOriginalTransfer;changed[3]=0x90;
 assert(classify(changed.data(),changed.size())==ByteState::Unknown);
 struct S{int refs=1;bool transfer=false;bool pop=false;};
 auto execute=[](bool bypass,bool eligible){
  S s;
  if(eligible){if(!bypass){s.refs++;s.transfer=true;}s.pop=true;}
  return s;
 };
 const auto native=execute(false,true),experimental=execute(true,true);
 assert(native.refs==2&&native.transfer&&native.pop);
 assert(experimental.refs==1&&!experimental.transfer&&experimental.pop);
 assert(!execute(true,false).pop);
 std::puts("PASS: synthetic native handoff byte and refcount model");
}
