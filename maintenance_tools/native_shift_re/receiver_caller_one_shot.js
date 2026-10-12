'use strict';
// Capture the original CALLER of the member receiver, not just a nearby
// Shift timer. Launcher must independently validate EXE SHA and PID path.
// Read-only game DATA; Frida temporarily alters/restores hooked code bytes.
const base=Process.getModuleByName('Warhammer3.exe').base;
const pins=[[0x0306b9f0,'48895c2410'],[0x0306ba5b,'e8683defff']];
function hexdump(p,n){try{return Array.from(new Uint8Array(p.readByteArray(n)))
  .map(x=>x.toString(16).padStart(2,'0')).join('')}catch(_){return null}}
for(const [rva,expected] of pins){
 if(hexdump(base.add(rva),expected.length/2)!==expected)
   throw Error('ORIGINAL_OPCODE_MISMATCH '+rva.toString(16));
}
function str(p){return p===null?null:p.toString()}
const pending=new Map(),hooks=[];let emitted=0,dropped=0;const max=200;
function emit(e){if(emitted>=max){dropped++;return}emitted++;send({type:'event',...e})}
hooks.push(Interceptor.attach(base.add(0x0306b9f0),{
 onEnter(args){
  const tid=this.threadId;let stack=pending.get(tid);
  if(!stack){stack=[];pending.set(tid,stack)}
  const ret=this.returnAddress;
  stack.push({thread:tid,member:str(args[0]),packet:str(args[1]),
    callerReturnVA:str(ret),callerReturnRva:ret.sub(base).toString(),
    preceding8Bytes:hexdump(ret.sub(8),8),actorVtbl:hexdump(args[0],8),
    packet58:hexdump(args[1],0x58)});
 },
 onLeave(){
  const stack=pending.get(this.threadId);
  if(stack&&stack.length)stack.pop();
  if(stack&&!stack.length)pending.delete(this.threadId);
 }
}));
hooks.push(Interceptor.attach(base.add(0x0306ba5b),{
 onEnter(){
  const stack=pending.get(this.threadId);
  const packet=stack&&stack.length?stack[stack.length-1]:null;
  emit({ev:'NATIVE_DEFERRED_RECEIVER_CALLER',timestampMs:Date.now(),
    matchedReceiverFrame:!!packet,caller:packet,
    packetFromRbx:hexdump(this.context.rbx,0x58),
    member:str(this.context.rdi)});
 }
}));
recv('stop',()=>{for(const h of hooks)h.detach();
 send({type:'summary',eventCount:emitted,dropped});});
send({type:'ready',guardCount:pins.length,maxEvents:max,
 note:'CALLER return address is not by itself evidence of queued Shift order.'});
