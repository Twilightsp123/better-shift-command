'use strict';
// Regression for the exact 2026-10-12 Windows Frida loader rejection:
// TypeError: cannot define variable 'ptr' at /script1.js:1.
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const original = fs.readFileSync(__dirname+'/one_shot_native_source.js','utf8');
function fridaGlobals(){
  const context = Object.create(null);
  for (const k of ['ptr','Process','Module','Interceptor','Script','Memory',
                   'Thread','NativePointer','send','recv','hexdump','rpc']) {
    Object.defineProperty(context,k,{value:()=>{},writable:false,
      configurable:false,enumerable:true});
  }
  return context;
}
assert.throws(()=>vm.runInNewContext("'use strict'; function ptr(p,o) {return null;}",
                                    fridaGlobals()),/ptr|already been declared/i);
// Our probe now lives in a function scope and never declares a global ptr.
assert(original.includes('(function bscN1AgentIsolatedScope(){'));
assert(original.includes('function readMemberPointer('));
assert(!/\bfunction\s+ptr\s*\(/.test(original));
assert(!/\bptr\s*\(/.test(original));
// Smoke the repaired Frida global script wrapper separately from game code.
vm.runInNewContext(original.slice(0,original.indexOf("'use strict';")) +
  "'use strict'; const ptrCheck = 17; }());",fridaGlobals());
console.log('FRIDA_GLOBALS_CONFLICT_REGRESSION_PASS: ptr builtin protected');
