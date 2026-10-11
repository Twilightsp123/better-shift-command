'use strict';
// Exact-original BSC N1 one-shot read-only DATA capture. Frida temporarily
// patches/restores CODE; launcher validates full SHA and PID image identity.
const base=Process.getModuleByName('Warhammer3.exe').base;
const CAP={events:18000,actors:96,ageMs:50000,goalSampleMs:15,fanoutAgeMs:500};
const PINS=[
 [0x0304459d,'ff4618'],[0x03265d3f,'ff9068030000'],
 [0x0306ba5b,'e8683defff'],[0x0306bbae,'e85d4ed4ff'],
 [0x03115cbc,'4c8d89e0010000'],[0x03256209,'84c0'],
 [0x0311963a,'0f1187e0010000'],[0x03119660,'c787d80100000000803f'],
 [0x03115cf4,'f3410f104a08'],
 [0x03281554,'488b4070']
];
function hx(p,n){try{return Array.from(new Uint8Array(p.readByteArray(n)))
 .map(x=>x.toString(16).padStart(2,'0')).join('');}catch(_){return null;}}
function readPtr(p,o){try{return p.add(o).readPointer();}catch(_){return null;}}
function readU32(p,o){try{return p.add(o).readU32();}catch(_){return null;}}
function readF32(p,o){try{const x=p.add(o).readFloat();return Number.isFinite(x)?x:null;}catch(_){return null;}}
function show(p){return p===null?null:p.toString();}
for(const [rva,expected] of PINS){
 const got=hx(base.add(rva),expected.length/2);
 if(got!==expected)throw Error('ORIGINAL_CODE_GUARD_FAIL '+rva.toString(16)+' '+got);
}
const t0=Date.now();let total=0,discarded=0,nextId=0;
const queue=[],packets=new Map(),actors=new Map(),postWrites=new Map();
const goalReadsByThread=new Map();
let readCount=0;
function now(){return Date.now()-t0;}
function emit(ev,v){if(total>=CAP.events){discarded++;return;}
 send({type:'event',ev,seq:++total,atMs:now(),...v});}
function memberState(m){
 const owner=readPtr(m,0x58),owner440=owner?readPtr(owner,0x440):null;
 let status=null;try{status=m.add(0x18f).readU8();}catch(_){}
 return {member:show(m),memberOwner:show(owner),owner440:show(owner440),
  clock:owner440?readU32(owner440,0x98):null,
  x:readF32(m,0x88),z:readF32(m,0x90),motorState:readU32(m,0x710),
  actorMode:readU32(m,0x318),flag188:readU32(m,0x188),status18f:status,
  actionVtbl:show(readPtr(m,0x330)),deferredVtbl:show(readPtr(m,0x4a8)),
  goal24:hx(m.add(0x1e0),24)};
}
function active(m){if(!m||m.isNull())return null;
 const s=actors.get(show(m));if(!s)return null;
 if(now()-s.at>CAP.ageMs){actors.delete(show(m));return null;}return s;
}
function init(m,kind,packet,source){
 if(!m||m.isNull())return;
 const key=show(m);if(!actors.has(key)&&actors.size>=CAP.actors)return;
 const s={id:++nextId,at:now(),lastGoalSample:-1e9,readSeen:false,
          wrote:false,prior:hx(m.add(0x1e0),24),kind,source};
 actors.set(key,s);
 emit(kind,{traceId:s.id,packetAddress:show(packet),
   packet58:packet?hx(packet,0x58):null,source,...memberState(m)});
}
const hooks=[];
function attach(rva,fn){hooks.push(Interceptor.attach(base.add(rva),{onEnter:fn}));}
try {
 attach(0x0304459d,function(){
   // 0x0304435E: RBX=controller; 0x03044421 loads [rbx] unit root.
   const ctl=this.context.rbx,root=readPtr(ctl,0);
   const group=root?readPtr(root,0x32f8):null;
   const e={at:now(),root:show(root),group:show(group),
     controller:show(ctl),thread:this.threadId,queueSlot:show(this.context.r14)};
   queue.push(e);if(queue.length>200)queue.shift();
   emit('QUEUED_CONTINUATION',e);
 });
 attach(0x03281554,function(){
   const node=this.context.rax,task=this.context.rbx;
   emit('B_ROUTE_CACHE_READ',{node:show(node),task:show(task),
    geom:show(readPtr(node,0x70)),nodeReady:readU32(node,8),thread:this.threadId});
 });
 attach(0x03265d3f,function(){
   // Native 0x03265D32..3F: r14=member, rdx=48+ byte packet, rsi=B group.
   const m=this.context.r14,packet=this.context.rdx;
   const e={at:now(),m:show(m),packet:show(packet),bytes:hx(packet,0x58),
    group:show(this.context.rsi),desc:show(this.context.r15),
    geom:show(readPtr(this.context.r15,0)),thread:this.threadId};
   packets.set(show(m),e);
   if(packets.size>CAP.actors*3)packets.clear();
   emit('B_MEMBER_FANOUT',{...e,...memberState(m)});
 });
 attach(0x0306ba5b,function(){
   const m=this.context.rdi,p=this.context.rbx,last=packets.get(show(m));
   const match=last&&now()-last.at<CAP.fanoutAgeMs&&last.thread===this.threadId&&
       (last.packet===show(p)||last.bytes===hx(p,0x58));
   const owner=readPtr(m,0x58);
   const q=queue.filter(z=>now()-z.at<10000&&
      (z.root===show(owner)||z.group===show(owner)||(match&&last&&z.group===last.group)));
   init(m,'B_DEFERRED_RECEIVE',p,{
     memberFanoutMatched:!!match,memberFanoutGroup:last?last.group:null,
     memberFanoutGeo:last?last.geom:null,queuedUnitIdentityMatches:!!match&&q.length>0,
     queuedIdentityMethod:q.length?'EXACT_POINTER_EQUALITY':'UNKNOWN',
     note:'Temporal proximity is NOT proof of same Shift order.'});
 });
 attach(0x0306bbae,function(){
   init(this.context.rdi,'DIRECT_ACTION_RESET',null,{
     memberFanoutMatched:false,queuedUnitIdentityMatches:false});
 });
 attach(0x03115cbc,function(){
   const m=this.context.rcx,s=active(m);if(!s)return;
   if(now()-s.lastGoalSample<CAP.goalSampleMs)return;
   s.lastGoalSample=now();s.lastReadThread=this.threadId;
   s.readSeen=true;readCount++;
   const v=memberState(m);
   goalReadsByThread.set(this.threadId,{at:now(),member:show(m),
      traceId:s.id,x:v.x,z:v.z,oldGoal:v.goal24,decoded:null});
   emit('GOAL_READ',{traceId:s.id,
     goalUnchangedSinceReceive:v.goal24===s.prior,
     writeSeenSinceReceive:s.wrote,...v});
 });
 // Exact native 0x03115CF4 instruction boundary:
 // R10 contains decoded goal XYZ, RCX the ushort heading LUT index,
 // RAX the runtime-populated GOAL heading LUT (not soldier facing).
 attach(0x03115cf4,function(){
   const d=goalReadsByThread.get(this.threadId);if(!d)return;
   if(now()-d.at>100){goalReadsByThread.delete(this.threadId);return;}
   const idx=this.context.rcx.toUInt32();if(idx>65535)return;
   const tx=readF32(this.context.r10,0),tz=readF32(this.context.r10,8);
   const gx=readF32(this.context.rax,idx*8);
   const gz=readF32(this.context.rax,idx*8+4);
   const dot=(tx===null||tz===null||gx===null||gz===null||
     d.x===null||d.z===null)?null:(tx-d.x)*gx+(tz-d.z)*gz;
   d.decoded={targetX:tx,targetZ:tz,goalHeadingX:gx,goalHeadingZ:gz,
     headingIndex:idx,dot,nearZero:dot===null||Math.abs(dot)<0.0001,
     nativeExpectedReturn:dot===null||Math.abs(dot)<0.0001?null:(dot<0?1:0)};
 });
 attach(0x03256209,function(){
   // 0x032561E4 loads member from [action+0x8]; AL was just returned by
   // 0x03115C94. 0x0325620B jumps to skip action if AL=0.
   const action=this.context.rbx,m=readPtr(action,8);if(!m)return;
   const s=active(m);if(!s)return;
   const v=memberState(m),al=this.context.rax.toUInt32()&0xff;
   const paired=goalReadsByThread.get(this.threadId);
   const validPair=!!paired&&paired.member===show(m)&&paired.traceId===s.id&&
     now()-paired.at<100&&paired.decoded!==null;
   emit('OLD_GOAL_DIRECTION_DECISION',{
     traceId:s.id,action:show(action),predicateReturn:al,branchIfFalse:al===0,
     pairToExactNativeGoalRead:validPair,
     decodedOldGoal:validPair?paired.decoded:null,
     decodedGoalMatchesNativeAL:validPair&&paired.decoded.nativeExpectedReturn!==null?
       paired.decoded.nativeExpectedReturn===al:null,
     readSeenSinceReceive:s.readSeen,
     lastGoalReadSameThread:s.lastReadThread===this.threadId,
     lastGoalReadWithin100ms:now()-s.lastGoalSample<100,
     goalUnchangedSinceReceive:v.goal24===s.prior,
     writeSeenSinceReceive:s.wrote,...v});
   if(validPair)goalReadsByThread.delete(this.threadId);
 });
 attach(0x0311963a,function(){
   const m=this.context.rdi,s=active(m);if(!s)return;
   postWrites.set(show(m),{traceId:s.id});
   s.wrote=true;
   emit('GOAL_COMMIT_PRE',{traceId:s.id,proposed24:hx(this.context.rdx,24),
    before24:hx(m.add(0x1e0),24),...memberState(m)});
 });
 attach(0x03119660,function(){
   // 0x0311965F is inside a MOVSD, never hook mid-instruction.
   // At 0x03119660 the 24-byte goal stores have completed.
   const m=this.context.rdi,s=active(m);if(!s)return;
   const pre=postWrites.get(show(m));if(!pre||pre.traceId!==s.id)return;
   const actual=hx(m.add(0x1e0),24);
   emit('GOAL_COMMIT_POST',{traceId:s.id,actual24:actual,
    goalDifferentFromReceive:actual!==s.prior,...memberState(m)});
   postWrites.delete(show(m));
 });
} catch(e){for(const h of hooks)h.detach();throw e;}
recv('stop',function(){for(const h of hooks)h.detach();
 emit('SUMMARY',{trackedActors:actors.size,droppedEvents:discarded,readCount});});
send({type:'ready',pins:PINS.length,base:base.toString(),
 warning:'Goal-direction decision is not proof of physical collision or a Shift bug.'});
