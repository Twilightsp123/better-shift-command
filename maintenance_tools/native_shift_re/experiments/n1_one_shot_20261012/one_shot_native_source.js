'use strict';
// BSC N1 observation only. Exact-original EXE & PID are guarded by Python.
// Frida temporarily patches/restores hooked code; never changes game state.
const image = Process.getModuleByName('Warhammer3.exe');
const base = image.base;
const PINS = [
  [0x0306b9f0,'48895c2410'], // member common receiver, RCX=member RDX=packet
  [0x0306ba5b,'e8683defff'], // conditional defer dispatch
  [0x03284304,'488bc48850105553'], // post-ctor group sender function
  [0x02dd579c,'488bc448895810'], // original unit-group Tick: RCX=group, group+0x98 clock
  [0x03284b7b,'ff9068030000'], // post-ctor virtual send
  [0x03265d3f,'ff9068030000'], // B cache subtype send
  [0x030d550f,'ff9068030000'], // A native formation send
  [0x0304459d,'ff4618498d'], // known queued continuation (may not execute)
  [0x0304433c,'488bc44889580848'], // native queued-order manager entry
  [0x030323c8,'488bc44889581048'], // native group MOVE issuer (not RMB-only)
  [0x03115cbc,'4c8d89e0010000'], // native per-member motor goal read
  [0x03256209,'84c0'], // native directional predicate AL result
  [0x0311963a,'0f1187e0010000'], // original per-member motor goal write
  [0x03119660,'c787d80100000000803f'] // real post-write instruction boundary
];
const SOURCE_RET = {
  [0x03284b81]:'POSTCTOR_REWRITE',
  [0x03265d45]:'B_CACHE',
  [0x030d5515]:'A_DIRECT'
};
function hex(p,n) {try {return Array.from(new Uint8Array(p.readByteArray(n)))
    .map(b=>b.toString(16).padStart(2,'0')).join('');}catch(_){return null;}}
function ptr(p,o) {try {return p.add(o).readPointer();}catch(_){return null;}}
function u32(p,o) {try {return p.add(o).readU32();}catch(_){return null;}}
function flt(p,o){try {let v=p.add(o).readFloat();return Number.isFinite(v)?v:null;}catch(_){return null;}}
function addr(p) {return p===null?null:p.toString();}
function goalXYZ(raw){
  if(!raw || raw.length<24)return null;
  function field(off){
    const b=new Uint8Array(4);
    for(let j=0;j<4;j++)b[j]=parseInt(raw.slice((off+j)*2,(off+j+1)*2),16);
    const v=new DataView(b.buffer).getFloat32(0,true);
    return Number.isFinite(v)?v:null;
  }
  const x=field(0),z=field(8);
  return x===null||z===null?null:{x,z};
}
function turnCosine(oldraw,newraw,pos){
  const a=goalXYZ(oldraw),b=goalXYZ(newraw);
  if(!a||!b||pos.x===null||pos.z===null)return null;
  const ax=a.x-pos.x,az=a.z-pos.z,bx=b.x-pos.x,bz=b.z-pos.z;
  const am=Math.hypot(ax,az),bm=Math.hypot(bx,bz);
  if(am<3||bm<3)return null;
  return (ax*bx+az*bz)/am/bm;
}
for (const [site,raw] of PINS) {
  if (hex(base.add(site),raw.length/2)!==raw)
    throw Error('EXACT_OPCODE_GUARD_FAILED_'+site.toString(16));
}
const start=Date.now();let total=0,dropped=0,stopped=false;
const MAX=2400, RESERVED_FOR_TURNS=700, MAX_PER_ACTOR_SOURCE=3, MAX_ACTOR=200;
const hooks=[],senderRecent=new Map(),receiverFrames=new Map();
const taskFrames=new Map(),activeActors=new Map(),writeFrames=new Map();
const turningGroups=new Map(),cohortMembers=new Map(),senderTaskSamples=new Map();
const eventCounts={};const sourceCounts={};const actorSeen=new Set(),groupSeen=new Set();
function ms(){return Date.now()-start;}
function sendEvent(kind,fields,always=false){
  eventCounts[kind]=(eventCounts[kind]||0)+1;
  if(stopped && !always)return;
  const priority=(kind==='MOTOR_GOAL_REVERSAL' || kind==='GROUP_TICK_POSITION' ||
                  kind==='POST_TURN_POSITION');
  if(total>=MAX || (!priority && total>=MAX-RESERVED_FOR_TURNS)){
    dropped++;return;
  }
  send({type:'event',ev:kind,atMs:ms(),seq:++total,...fields});
}
function groupOf(member){
  const owner=ptr(member,0x58);
  return {unit:addr(owner),group:owner?addr(ptr(owner,0x440)):null};
}
function rememberMember(member, group){
  if(!group||!member||member.isNull())return;
  let members=cohortMembers.get(group);
  if(!members){if(cohortMembers.size>=64)return;
    members=new Map();cohortMembers.set(group,members);}
  const key=addr(member);
  if(members.has(key))return;
  if(members.size>=100)return;
  members.set(key,{ptr:member,ordinal:u32(member,0x60)});
}
function cohortSample(group, turn){
  const list=[...(cohortMembers.get(group)||new Map()).values()];
  // Sample across the formation (native actor ordinal), not only its front.
  list.sort((a,b)=>(a.ordinal??0)-(b.ordinal??0));
  if(list.length<=16)return list;
  const selected=[];
  for(let i=0;i<16;i++)selected.push(list[Math.floor(i*(list.length-1)/15)]);
  for(const key of turn.members){
    const entry=(cohortMembers.get(group)||new Map()).get(key);
    if(entry&&!selected.some(z=>addr(z.ptr)===key))selected.push(entry);
  }
  return selected.slice(0,22);
}
function state(member){
  const g=groupOf(member);
  const unit=ptr(member,0x58),grp=unit?ptr(unit,0x440):null;
  return {...g,groupTick:grp?u32(grp,0x98):null,
    member:addr(member),x:flt(member,0x88),z:flt(member,0x90),
    actorMode:u32(member,0x318),motor710:u32(member,0x710),
    goal24:hex(member.add(0x1e0),24)};
}
function push(map,tid,entry){let stk=map.get(tid);if(!stk){stk=[];map.set(tid,stk);}stk.push(entry);}
function pop(map,tid){const stk=map.get(tid);if(!stk||!stk.length)return;
  stk.pop();if(!stk.length)map.delete(tid);}
function top(map,tid){const stk=map.get(tid);return stk&&stk.length?stk[stk.length-1]:null;}
function signedRva(ret){if(!ret)return null;
  try {const r=ret.sub(base);if(ret.compare(base)>=0 && ret.compare(base.add(image.size))<0) return r.toUInt32();}
  catch(_){}return null;}
function sampled(member,source){
  const key=addr(member)+'|'+source;
  const record=activeActors.get(key)||{count:0,last:-1e9};
  record.count++;
  if(actorSeen.size<MAX_ACTOR) actorSeen.add(addr(member));
  const accept=record.count<=MAX_PER_ACTOR_SOURCE || ms()-record.last>4000;
  record.last=ms();activeActors.set(key,record);
  return accept;
}
function isTracked(member){const m=addr(member);
  for(const key of activeActors.keys())if(key.startsWith(m+'|'))return true;
  return false;
}
function isFocusMember(member){
  // Only log a stratified slice of high-frequency per-model calls; maintain
  // all member identities in cohortMembers so actual motor reversals can still
  // trigger group Tick tracking for the full formation.
  const ordinal=u32(member,0x60);
  return ordinal===null || ordinal<3 || ordinal%8===0;
}
function attach(site,fn){hooks.push(Interceptor.attach(base.add(site),fn));}
try {
  attach(0x03284304,{
    onEnter(args){
      const task=args[0];const parent=ptr(task,0x28);
      const grp=parent?ptr(parent,0x440):null;
      push(taskFrames,this.threadId,{task:addr(task),unit:addr(parent),group:addr(grp)});
      const key=addr(task),n=(senderTaskSamples.get(key)||0)+1;
      senderTaskSamples.set(key,n);
      if(n<=2 || n%24===0)sendEvent('POSTCTOR_SENDER_ENTER',{
        thread:this.threadId,task:key,taskCallCount:n,
        unit:addr(parent),group:addr(grp)});
    },onLeave(){pop(taskFrames,this.threadId);}
  });
  function nativeSend(kind,context,tid){
    const m=context.rcx,p=context.rdx,task=top(taskFrames,tid);
    sourceCounts[kind]=(sourceCounts[kind]||0)+1;
    const group=groupOf(m).group;
    rememberMember(m,group);
    // Evidence: native virtual callsite, not merely similar packet bytes.
    senderRecent.set(tid,{source:kind,member:addr(m),packet:addr(p),at:ms()});
    const meetsBudget=sampled(m,kind);
    if(meetsBudget && isFocusMember(m)){
      const st=state(m);if(st.group)groupSeen.add(st.group);
      sendEvent('NATIVE_MEMBER_SEND',{source:kind,thread:tid,
        packetPtr:addr(p),packet58:hex(p,0x58),...(task?{task}:{}),...st});
    }
  }
  function nativeSendHook(kind){return {onEnter(){nativeSend(kind,this.context,this.threadId);}};}
  attach(0x03284b7b,nativeSendHook('POSTCTOR_REWRITE'));
  attach(0x03265d3f,nativeSendHook('B_CACHE'));
  attach(0x030d550f,nativeSendHook('A_DIRECT'));
  attach(0x0306b9f0,{
    onEnter(args){
      const m=args[0],p=args[1];const rv=signedRva(this.returnAddress);
      const source=rv!==null && SOURCE_RET[rv]?SOURCE_RET[rv]:'OTHER_OR_UNKNOWN';
      const sendTop=senderRecent.get(this.threadId);
      const direct=!!sendTop && ms()-sendTop.at<250 &&
        sendTop.member===addr(m) && sendTop.packet===addr(p);
      const ctx={thread:this.threadId,member:addr(m),packet:addr(p),
        source,returnRva:rv===null?null:'0x'+rv.toString(16),
        explicitlyMatchedSender:direct&&sendTop.source===source};
      push(receiverFrames,this.threadId,ctx);
      sourceCounts['RECEIVER_'+source]=(sourceCounts['RECEIVER_'+source]||0)+1;
      if(sampled(m,'RECV_'+source) && isFocusMember(m))sendEvent('MEMBER_RECEIVER',{
          ...ctx,packet58:hex(p,0x58),...state(m)});
    },onLeave(){pop(receiverFrames,this.threadId);}
  });
  attach(0x0306ba5b,{onEnter(){
    const m=this.context.rdi,p=this.context.rbx;
    const r=top(receiverFrames,this.threadId);
    const matched=!!r&&r.member===addr(m)&&r.packet===addr(p);
    const src=matched?r.source:'UNMATCHED_RECEIVER';
    sourceCounts['DEFER_'+src]=(sourceCounts['DEFER_'+src]||0)+1;
    if(sampled(m,'DEFER_'+src)&&isFocusMember(m))sendEvent('DEFERRED_PACKET',{
      thread:this.threadId,source:src,receiverFrameMatched:matched,
      packet58:hex(p,0x58),...state(m)});
  }});
  // A per-group native Tick provides member positions on *every* group Tick,
  // not merely on infrequent subsequent goal packet deliveries.
  attach(0x02dd579c,{onEnter(args){
    const group=addr(args[0]),turn=turningGroups.get(group);
    if(!turn)return; // almost-free fast path for unrelated game units
    const tick=u32(args[0],0x98);
    if(tick===null||tick<turn.tick||tick-turn.tick>18 || tick===turn.prevTick)return;
    turn.prevTick=tick;
    for(const entry of cohortSample(group,turn)){
      const model=entry.ptr,at=state(model);
      if(at.x===null||at.z===null||at.group!==group)continue;
      sendEvent('GROUP_TICK_POSITION',{turnStartTick:turn.tick,
        triggerMember:turn.members.has(addr(model)),
        nativeActorOrdinal:entry.ordinal,...at});
    }
  }});
  attach(0x0304459d,{onEnter(){sendEvent('QUEUED_CONTINUATION',{thread:this.threadId});}});
  attach(0x0304433c,{onEnter(args){sendEvent('QUEUE_MANAGER_ENTRY',{
    thread:this.threadId,manager:addr(args[0])});}});
  attach(0x030323c8,{onEnter(args){sendEvent('NATIVE_MOVE_ISSUER',{
    thread:this.threadId,unitCandidate:addr(args[0])});}});
  attach(0x03115cbc,{onEnter(){
    const m=this.context.rcx;if(!isTracked(m))return;
    if(isFocusMember(m)&&sampled(m,'GOAL_READ'))sendEvent('GOAL_READ',state(m));
  }});
  attach(0x03256209,{onEnter(){
    const action=this.context.rbx,m=ptr(action,0x8);
    if(!m || !isTracked(m))return;
    if(isFocusMember(m)&&sampled(m,'DIRECTION_AL'))sendEvent('NATIVE_GOAL_DIRECTION',{
      predicateReturn:this.context.rax.toUInt32()&0xff,...state(m)});
  }});
  attach(0x0311963a,{onEnter(){
    const m=this.context.rdi;if(!isTracked(m))return;
    const oldraw=hex(m.add(0x1e0),24),newraw=hex(this.context.rdx,24);
    const pos=state(m),angle=turnCosine(oldraw,newraw,pos);
    rememberMember(m,pos.group);
    writeFrames.set(addr(m),{before:oldraw,at:ms()});
    if(angle!==null&&angle< -0.8&&pos.group&&Number.isInteger(pos.groupTick)){
      const prior=turningGroups.get(pos.group);
      if(!prior || pos.groupTick-prior.tick>18){
        turningGroups.set(pos.group,{tick:pos.groupTick,at:ms(),members:new Set(),lastTick:new Map(),prevTick:null});
      }
      turningGroups.get(pos.group).members.add(addr(m));
      sendEvent('MOTOR_GOAL_REVERSAL',{oldGoal24:oldraw,newGoal24:newraw,
        headingCosine:angle,...pos});
    }
    if(isFocusMember(m)&&sampled(m,'GOAL_WRITE_PRE'))sendEvent('GOAL_WRITE_PRE',{
      expected24:newraw,...pos});
  }});
  attach(0x03119660,{onEnter(){
    const m=this.context.rdi,prev=writeFrames.get(addr(m));if(!prev)return;
    const after=hex(m.add(0x1e0),24),pos=state(m);
    const turn=turningGroups.get(pos.group);
    const inWindow=turn&&pos.groupTick!==null&&
      pos.groupTick>=turn.tick&&pos.groupTick-turn.tick<=18;
    if(inWindow && (turn.members.has(addr(m))||turn.members.size<36) &&
      turn.lastTick.get(addr(m))!==pos.groupTick){
      turn.members.add(addr(m));turn.lastTick.set(addr(m),pos.groupTick);
      sendEvent('POST_TURN_POSITION',{turnStartTick:turn.tick,
        before24:prev.before,after24:after,
        changed:prev.before!==after,...pos});
    }else if(isFocusMember(m)&&sampled(m,'GOAL_WRITE_POST'))sendEvent('GOAL_WRITE_POST',{
      before24:prev.before,after24:after,changed:prev.before!==after,
      commitLatencyMs:ms()-prev.at,...pos});
    writeFrames.delete(addr(m));
  }});
}catch(e){for(const h of hooks.reverse()){try{h.detach();}catch(_){}}throw e;}
function shutdown(){if(stopped)return;stopped=true;
  let problems=[];for(let i=hooks.length-1;i>=0;i--){
    try{hooks[i].detach();}catch(e){problems.push(String(e));}}
  send({type:'summary',hookCount:hooks.length,eventsSaved:total,
    dropped,sourceCounts,eventCounts,distinctActors:actorSeen.size,
    distinctGroups:groupSeen.size,detachErrors:problems});
}
recv('stop',function(){shutdown();});
send({type:'ready',guardCount:PINS.length,hookCount:hooks.length,
 warning:'Only a source-matched event proves sender provenance; a Shift keypress and physical crowding are not inferred.'});
