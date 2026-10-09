-- H7: exact Native queued Shift ATTACK terminal handoff (real shipped controller,
-- simulated CA). Reproducer: WH3 2026-10-09 12:53 uid1010 G13: exact ATTACK
-- 207500ms near 19.799m, blocked G11 arrival brake, rolled back to MOVE.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)
 local ok,e=pcall(fn)
 if ok then pass=pass+1;print("PASS "..n)
 else fail=fail+1;print("FAIL "..n.." :: "..tostring(e))end
end
local function n(f,tag)
 local total=0
 for _,s in ipairs(f.logs) do if s:find("] "..tag.." uid=1001 ",1,true) then total=total+1 end end
 return total
end
local function v3(f,u)
 local r=f.evidence_record
 if not r or r.unit_uid~=u then return nil,"NO_ORDER" end
 return {schema=3,epoch="1",unit_uid=u,unit_lifetime=r.unit_lifetime,
  complete=true,active=true,known=true,accepted_journal_serial=r.serial,
  active_engine_seq=r.engine_seq,kind=r.order_type,dest_x=r.dest_x,dest_z=r.dest_z,target_uid=r.target_uid}
end
local function setup(x)
 local f=F({cold_idle=true,debug_source=true,no_calibration=false,width=40,native_order_evidence_v3=v3})
 f:start();f.unit.idle=false;f.unit.moving=true
 local a=f:emit("MOVE",false,100,0)
 f.evidence_record=a
 f:tick(100,0,0)
 f:tick(200,10,0)
 f:tick(300,20,0)
 f:tick(400,x-6,0)
 local b=f:emit("ATTACK",true,nil,nil,"2001")
 f.evidence_record=a
 f:tick(500,x,0) -- freeze a fresh T2B decision before Native promotion
 return f,b
end
local function healthy(f)
 for _,s in ipairs(f.logs) do assert(not s:find("CONTROLLER_FAIL",1,true),s) end
end
T("H7AN01 exact i+1 Native ATTACK at close terminal may adopt without G11 deceleration",function()
 local f,b=setup(84)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0,"attack should not be proactively issued")
 f.evidence_record=b;f:tick(600,85,0)
 assert(n(f,"H7_NATIVE_ATTACK_TERMINAL_ADOPT_READY")==1,"terminal evidence missing")
 assert(n(f,"NATIVE_SUCCESSOR_ADOPTED")==1,"exact Native ATTACK was rolled back")
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==1)
 assert(f:has("reason=ATTACK_TERMINAL_HANDOFF"),"unrecorded attack transition semantics")
 assert(n(f,"NATIVE_SUCCESSOR_ROLLBACK")==0)
 healthy(f)
end)
T("H7AN02 far future Native attack cannot skip MOVE",function()
 local f,b=setup(35)
 f.evidence_record=b;f:tick(600,36,0)
 assert(n(f,"H7_NATIVE_ATTACK_TERMINAL_ADOPT_READY")==0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0)
 healthy(f)
end)
T("H7AN03 wrong target identity cannot adopt",function()
 local f,b=setup(84)
 b.target_uid="2002"
 f.evidence_record=b;f:tick(600,85,0)
 assert(n(f,"H7_NATIVE_ATTACK_TERMINAL_ADOPT_READY")==0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0)
 healthy(f)
end)
T("H7AN04 unarmed, non-executing queued attack never gains ISSUE permission",function()
 local f,b=setup(84)
 f:tick(600,85,0) -- Native active remains MOVE
 assert(n(f,"H7_NATIVE_ATTACK_TERMINAL_ADOPT_READY")==0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0)
 assert(n(f,"DISPATCH_ATTACK")==0)
 healthy(f)
end)
T("H7AN05 Native i+2 ATTACK cannot skip intermediate MOVE",function()
 local f=F({cold_idle=true,debug_source=true,no_calibration=false,width=40,native_order_evidence_v3=v3})
 f:start();f.unit.idle=false;f.unit.moving=true
 local a=f:emit("MOVE",false,100,0)
 f.evidence_record=a
 f:tick(100,0,0);f:tick(200,10,0);f:tick(300,20,0)
 f:emit("MOVE",true,130,0)
 local b=f:emit("ATTACK",true,nil,nil,"2001")
 f.evidence_record=a;f:tick(400,60,0)
 f.evidence_record=b;f:tick(500,80,0)
 assert(n(f,"H7_NATIVE_ATTACK_TERMINAL_ADOPT_READY")==0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0)
 healthy(f)
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; H7 SYNTHETIC ONLY / WH3 UNVERIFIED")
os.exit(fail==0 and 0 or 1)
