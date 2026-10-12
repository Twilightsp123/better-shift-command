'use strict';
// Mock the documented Frida subset; no game is started or patched.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const script=fs.readFileSync(__dirname+'/one_shot_native_source.js','utf8');
const bytes=new Map();const ptrs=new Map();const words=new Map();const floats=new Map();
class Ptr {
  constructor(n){this.n=Number(n);}
  add(offset){return new Ptr(this.n+Number(offset));}
  sub(other){return new Ptr(this.n-Number(other instanceof Ptr?other.n:other));}
  toUInt32(){return this.n>>>0;}
  compare(other){const o=Number(other instanceof Ptr?other.n:other);return this.n===o?0:(this.n<o?-1:1);}
  isNull(){return this.n===0;}
  readByteArray(n){let arr=Buffer.alloc(n);for(let i=0;i<n;i++){
    if(bytes.has(this.n+i))arr[i]=bytes.get(this.n+i);
    else if(words.has(this.n+i))arr[i]=words.get(this.n+i)&255;
  }return new Uint8Array(arr);}
  readPointer(){const n=ptrs.get(this.n);if(n===undefined)throw Error('PTR_UNKNOWN:'+this.n.toString(16));return new Ptr(n);}
  readU32(){const n=words.get(this.n);if(n===undefined)throw Error('WORD_UNKNOWN');return n;}
  readFloat(){const n=floats.get(this.n);if(n===undefined)throw Error('FLOAT_UNKNOWN');return n;}
  toString(){return '0x'+this.n.toString(16);}
}
const base=0x140000000;
const pins=Array.from(script.matchAll(/\[0x([0-9a-f]+),'([0-9a-f]+)'\]/g),m=>[parseInt(m[1],16),m[2]]);
assert.strictEqual(pins.length,14);
for(const [site,str] of pins){const b=Buffer.from(str,'hex');for(let i=0;i<b.length;i++)bytes.set(base+site+i,b[i]);}
function run(overrides={}){
 const logs=[],hooks=new Map();let stop;
 const context={Process:{getModuleByName(){return {base:new Ptr(base),size:0x50000000};}},
   Interceptor:{attach(pointer,callbacks){assert(callbacks && typeof callbacks.onEnter==='function');
       const pos=pointer.n-base;hooks.set(pos,callbacks);return {detach(){hooks.delete(pos);}};}},
   recv(type,callback){if(type==='stop')stop=callback;},send(x){logs.push(x);},
   Date,Number,Map,Set,Uint8Array,Array,Error,Boolean,Object,Math,
   ...overrides};
 // Frida ships a non-configurable global `ptr`; a top-level helper called
 // `function ptr()` collides and prevents the agent from loading at all.
 // The previous Node mock omitted this built-in and falsely passed.
 Object.defineProperty(context,'ptr',{value:(n)=>new Ptr(n),
   writable:false,configurable:false,enumerable:true});
 vm.runInNewContext(script,context,{timeout:10000});
 return {logs,hooks,stop:()=>stop(),context};
}
function put32(n,val){words.set(n,val);const arr=Buffer.alloc(4);arr.writeUInt32LE(val);for(let i=0;i<4;i++)bytes.set(n+i,arr[i]);}
function putPtr(n,val){ptrs.set(n,val);const arr=Buffer.alloc(8);arr.writeBigUInt64LE(BigInt(val));for(let i=0;i<8;i++)bytes.set(n+i,arr[i]);}
function putBytes(n,buffer){for(let i=0;i<buffer.length;i++)bytes.set(n+i,buffer[i]);}
function fl(n,x){floats.set(n,x);const b=Buffer.alloc(4);b.writeFloatLE(x);putBytes(n,b);}
const member=0x10000000,packet=0x10020000,owner=0x20000000,group=0x20030000,task=0x20200000;
putPtr(member+0x58,owner);putPtr(owner+0x440,group);
put32(member+0x318,0);put32(member+0x710,4);fl(member+0x88,30);fl(member+0x90,40);
putPtr(task+0x28,owner);putBytes(packet+0x50,Buffer.from('02140e42ad45df41','hex'));
const run1=run();const {logs,hooks}=run1;
assert.strictEqual(hooks.size,14);assert.strictEqual(logs[0].type,'ready');
function hook(site,registers,ret){const obj=hooks.get(site);assert(obj,'HOOK_MISSING:'+site.toString(16));
  obj.onEnter.call({threadId:42,context:registers,returnAddress:new Ptr(ret||base+0x1)},[registers.rcx,registers.rdx]);
  return obj;}
hook(0x03284304,{rcx:new Ptr(task),rdx:new Ptr(0),rdi:new Ptr(0)});
hook(0x03284b7b,{rcx:new Ptr(member),rdx:new Ptr(packet)});
const recvHook=hook(0x0306b9f0,{rcx:new Ptr(member),rdx:new Ptr(packet)},base+0x03284b81);
hook(0x0306ba5b,{rdi:new Ptr(member),rbx:new Ptr(packet)});
recvHook.onLeave.call({threadId:42});
// Execute the original GOAL_WRITE_PRE and POST hook sequence with a full
// 180-degree motor target reversal, without any live game process.
put32(group+0x98,2000);
const oldGoal=Buffer.alloc(24),newGoal=Buffer.alloc(24);
oldGoal.writeFloatLE(35,0);oldGoal.writeFloatLE(50,8);
newGoal.writeFloatLE(25,0);newGoal.writeFloatLE(30,8);
putBytes(member+0x1e0,oldGoal);putBytes(packet,newGoal);
hook(0x0311963a,{rdi:new Ptr(member),rdx:new Ptr(packet)});
putBytes(member+0x1e0,newGoal);
hook(0x03119660,{rdi:new Ptr(member)});
assert(logs.some(l=>l.ev==='MOTOR_GOAL_REVERSAL'&&l.headingCosine<-0.8));
assert(logs.some(l=>l.ev==='POST_TURN_POSITION'&&l.turnStartTick===2000));
// Same actual group Tick stage reads a later member location, even if there is
// no further per-member goal write: distinguishes motor target from movement.
hook(0x02dd579c,{rcx:new Ptr(group)});
put32(group+0x98,2001);fl(member+0x90,40.42);
hook(0x02dd579c,{rcx:new Ptr(group)});
assert(logs.some(l=>l.ev==='GROUP_TICK_POSITION'&&l.groupTick===2001&&l.z===40.42));
run1.stop();
let recv=logs.find(l=>l.ev==='MEMBER_RECEIVER');
assert(recv);
assert.strictEqual(recv.returnRva,'0x3284b81');
assert.strictEqual(recv.source,'POSTCTOR_REWRITE');
assert.strictEqual(recv.explicitlyMatchedSender,true);
let def=logs.find(l=>l.ev==='DEFERRED_PACKET');assert(def);
assert.strictEqual(def.receiverFrameMatched,true);
let sum=logs.find(l=>l.type==='summary');assert(sum);assert.strictEqual(sum.detachErrors.length,0);
assert.strictEqual(hooks.size,0);
// Tampering even a single hook opcode must abort before modifying code.
const site=0x0306b9f0,was=bytes.get(base+site);bytes.set(base+site,0);
assert.throws(()=>run(),/EXACT_OPCODE_GUARD_FAILED/);bytes.set(base+site,was);
console.log('OFFLINE_FRIDA_MOCK_PASS: 14 opcode guards, source->receiver->reversal->groupTick motion, stop, wrong-byte refusal');
