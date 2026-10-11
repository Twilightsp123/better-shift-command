'use strict';
// Single-shot, read-only game DATA; Frida temporarily hooks/restores CODE.
// Python launcher independently validates full EXE SHA256 and PID image path.
const cfg={maxActors:96,maxEvents:16000,lifetimeMs:45000,sampleMs:30};
const base=Process.getModuleByName('Warhammer3.exe').base;
const pins=[
  [0x0306ba5b,'e8683defff'],[0x0306bbae,'e85d4ed4ff'],
  [0x03115cbc,'4c8d89e0010000'],[0x0311963a,'0f1187e0010000'],
  [0x03256204,'e88bfaebff'],[0x0304459d,'ff4618']
];
function bytes(p,n){try{return Array.from(new Uint8Array(p.readByteArray(n)))
  .map(x=>x.toString(16).padStart(2,'0')).join('');}catch(e){return null;}}
for(const [rva,hex] of pins){
 const got=bytes(base.add(rva),hex.length/2);
 if(got!==hex)throw Error('ORIGINAL_OPCODE_GUARD_FAILED '+rva.toString(16)+' '+got);
}
const map=new Map();let total=0,dropped=0,seq=0,queuedAt=-1e9;
const start=Date.now();
function safe(fn){try{return fn();}catch(e){return null;}}
function pointer(p,o){return safe(()=>p.add(o).readPointer());}
function word(p,o){return safe(()=>p.add(o).readU32());}
function f32(p,o){return safe(()=>p.add(o).readFloat());}
function snap(member,packet){
 const unit=pointer(member,0x58);
 const group=unit&&!unit.isNull()?pointer(unit,0x440):null;
 return {member:member.toString(),group:group?group.toString():null,
 groupTick:group&&!group.isNull()?word(group,0x98):null,
 x:f32(member,0x88),z:f32(member,0x90),state710:word(member,0x710),
 state318:word(member,0x318),flag108:word(member,0x108),
 flagB10:word(member,0xb10),
 actionVtbl:safe(()=>member.add(0x330).readPointer().toString()),
 deferredVtbl:safe(()=>member.add(0x4a8).readPointer().toString()),
 goalRaw:bytes(member.add(0x1e0),0x20),
 packetRaw:packet?bytes(packet,0x58):null};
}
function emit(ev,member,data){
 if(total>=cfg.maxEvents){dropped++;return;}
 total++;send({type:'event',ev,seq:total,ms:Date.now()-start,
 actor:member?member.toString():null,...data});
}
function receive(ev,member,packet){
 if(!member||member.isNull())return;
 const key=member.toString();
 if(!map.has(key)&&map.size>=cfg.maxActors)return;
 const t=Date.now();
 const s={id:++seq,t,old:bytes(member.add(0x1e0),0x20),lastRead:0,
          wrote:false,generation:0};
 map.set(key,s);
 emit(ev,member,{traceId:s.id,nearQueuedContinuation:(t-queuedAt)<2500,
   correlationWarning:'Time proximity is NOT queue/unit identity',
   ...snap(member,packet)});
}
function active(member){
 if(!member||member.isNull())return null;
 const s=map.get(member.toString());if(!s)return null;
 if(Date.now()-s.t>cfg.lifetimeMs){map.delete(member.toString());return null;}
 return s;
}
function read(member){
 const s=active(member);if(!s)return;
 const t=Date.now();if(t-s.lastRead<cfg.sampleMs)return;
 s.lastRead=t;
 emit('GOAL_READ',member,{traceId:s.id,
   goalEqualToAtReceive:bytes(member.add(0x1e0),0x20)===s.old,
   motorWriteSinceReceive:s.wrote,...snap(member,null)});
}
function write(member,proposal){
 const s=active(member);if(!s)return;
 const prior=bytes(member.add(0x1e0),0x20);
 s.generation++;s.wrote=true;
 emit('GOAL_WRITE_PRE',member,{traceId:s.id,generation:s.generation,
   unchangedUntilNow:prior===s.old,priorGoal:prior,
   proposedGoal:proposal,...snap(member,null)});
}
const hooks=[];
function hook(rva,fn){hooks.push(Interceptor.attach(base.add(rva),{onEnter:fn}));}
try{
 hook(0x0304459d,function(){queuedAt=Date.now();
   emit('QUEUED_CONTINUATION',null,{rsi:this.context.rsi.toString(),
                                     r14:this.context.r14.toString()});});
 hook(0x0306ba5b,function(){receive('B_DEFERRED_RECEIVE',this.context.rdi,this.context.rbx);});
 hook(0x0306bbae,function(){receive('DIRECT_ACTION_RESET',this.context.rdi,null);});
 hook(0x03115cbc,function(){read(this.context.rcx);});
 hook(0x03256204,function(){const member=this.context.rcx;const s=active(member);
    if(s)emit('ACTION_GOAL_CHECK',member,{traceId:s.id,
      action:this.context.rbx.toString(),...snap(member,null)});});
 hook(0x0311963a,function(){write(this.context.rdi,bytes(this.context.rdx,0x20));});
}catch(e){for(const h of hooks)h.detach();throw e;}
recv('stop',function(){
 for(const h of hooks)h.detach();
 send({type:'summary',events:total,dropped,trackedActors:map.size});
});
send({type:'ready',guards:pins.length,moduleBase:base.toString(),
  warning:'Read-before-write does not prove geometric route conflict or physical crowding.'});
