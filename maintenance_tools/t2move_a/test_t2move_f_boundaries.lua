-- T2-MOVE-F boundary regression: V3-only proof and live bridge revision.
-- Runs against real E/F controller in the isolated fixture. Never WH3 promotion.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(name,fn)
 local ok,err=pcall(fn)
 if ok then pass=pass+1;print("PASS "..name)
 else fail=fail+1;print("FAIL "..name.." :: "..tostring(err)) end
end
local function order(schema)
 return function(f,u)
  local r=f.evidence_record
  if not r or r.unit_uid~=u then return nil,"NO_ORDER" end
  return {schema=schema,epoch="1",unit_uid=u,unit_lifetime=r.unit_lifetime,
    complete=true,active=true,known=true,accepted_journal_serial=r.serial,
    active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,
    dest_x=r.dest_x,dest_z=r.dest_z}
 end
end
local function setup(opts)
 local f=F(opts)
 f:start();f.unit.idle=false;f.unit.moving=true
 local first=f:emit("MOVE",false,100,0)
 local second=f:emit("MOVE",true,200,0)
 f.evidence_record=first
 for _,p in ipairs({{100,0},{200,30},{300,50},{400,70}}) do
  f:tick(p[1],p[2],0)
 end
 assert(f:has("T2MOVE_D_SHADOW_CAPTURE"),"pre-promotion evidence absent")
 return f,first,second
end
local function healthy(f)
 for _,line in ipairs(f.logs) do assert(not line:find("CONTROLLER_FAIL",1,true),line) end
end
local function count_adoptions(f)
 local n=0
 for _,line in ipairs(f.logs) do
  if line:find("] NATIVE_SUCCESSOR_ADOPTED uid=",1,true) then n=n+1 end
 end
 return n
end
T("F-RISK-01 matching V2 future MOVE cannot consume V3-only proof",function()
 local f,_,nexta=setup({cold_idle=true,debug_source=true,no_calibration=true,
   width=20,disable_v3_evidence=true,native_order_evidence=order(2)})
 f.evidence_record=nexta;f:tick(500,72,0)
 assert(not f:has("NATIVE_SUCCESSOR_ADOPTED"),"V2 fallback authorized E MOVE")
 assert(not f:has("TRANSITION_EDGE_COMMITTED"),"V2 fallback committed")
 healthy(f)
end)
T("F-RISK-02 bridge live revision drift revokes cached MOVE proof",function()
 local f,_,nexta=setup({cold_idle=true,debug_source=true,no_calibration=true,
   width=20,native_order_evidence_v3=order(3)})
 f.revision["1001"]="999" -- Bridge revision changed; Journal has not yet delivered row.
 f.evidence_record=nexta;f:tick(500,72,0)
 assert(not f:has("NATIVE_SUCCESSOR_ADOPTED"),"stale live revision authorized E MOVE")
 assert(not f:has("TRANSITION_EDGE_COMMITTED"),"stale live revision got completion")
 healthy(f)
end)
T("F-RISK-03 normal V3 immediate MOVE remains adoptable",function()
 local f,_,nexta=setup({cold_idle=true,debug_source=true,no_calibration=true,
   width=20,native_order_evidence_v3=order(3)})
 f.evidence_record=nexta;f:tick(500,72,0)
 assert(f:has("NATIVE_SUCCESSOR_ADOPTED"),"legitimate V3 successor denied")
 assert(f:has("TRANSITION_EDGE_COMMITTED"),"legitimate V3 commit missing")
 healthy(f)
end)
T("F-RISK-04 changing SC3 debt completion invalidates frozen D proof",function()
 local f=F({cold_idle=true,debug_source=true,no_calibration=true,width=20,
   native_order_evidence_v3=order(3)})
 f:start();f.unit.idle=false;f.unit.moving=true
 local p1=f:emit("MOVE",false,100,0)
 local p2=f:emit("MOVE",true,105,0)
 local p3=f:emit("MOVE",true,200,0)
 f.evidence_record=p1
 for _,p in ipairs({{100,0},{200,30},{300,50},{400,70}}) do f:tick(p[1],p[2],0) end
 assert(f:has("T2MOVE_D_SHADOW_CAPTURE"),"no P1-to-P2 route proof")
 f.evidence_record=p2;f:tick(500,72,0)
 assert(count_adoptions(f)==1,"P1-to-P2 setup must adopt: "..table.concat(f.logs," | "))
 assert(f:has("ROUTE_OBLIGATION_TRANSFERRED"),"P1 debt must be registered")
 f:tick(600,85,0)
 assert(f:count("T2MOVE_D_SHADOW_CAPTURE")>=2,"no P2-to-P3 proof with P1 debt")
 f.evidence_record=p3;f:tick(700,102,0) -- crosses owed P1 at x=100.
 assert(count_adoptions(f)==1,"changed route debt consumed stale proof")
 assert(f:has("MOVE_D_REVALIDATE_debt_signature"),"debt signature must invalidate frozen cache")
 healthy(f)
end)
T("F-RISK-05 unavailable live revision denies MOVE without false credit",function()
 local f,_,nexta=setup({cold_idle=true,debug_source=true,no_calibration=true,
   width=20,native_order_evidence_v3=order(3)})
 f.cfg.revision_error=true
 f.evidence_record=nexta;f:tick(500,72,0)
 assert(not f:has("NATIVE_SUCCESSOR_ADOPTED"),"unavailable live revision authorized MOVE")
 assert(not f:has("TRANSITION_EDGE_COMMITTED"),"unavailable revision committed")
 assert(f.issued==0,"unavailable revision must not trigger unverified BSC issue")
 healthy(f)
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; ISOLATED F NOT WH3")
os.exit(fail==0 and 0 or 1)
