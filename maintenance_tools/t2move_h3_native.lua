-- H3 native exact i+1 adoption uses the same route credit as BSC ISSUE.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print("PASS "..n)else fail=fail+1;print("FAIL "..n.." :: "..tostring(e))end end
local function v3(f,u)
 local r=f.evidence_record;if not r or r.unit_uid~=u then return nil,"NO_ORDER" end
 return {schema=3,epoch="1",unit_uid=u,unit_lifetime=r.unit_lifetime,complete=true,active=true,known=true,
    accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,kind=r.order_type,
    dest_x=r.dest_x,dest_z=r.dest_z,target_uid=r.target_uid}
end
local function base(px,pz)
 local f=F({cold_idle=true,debug_source=true,no_calibration=true,width=20,native_order_evidence_v3=v3})
 f:start();f.unit.idle=false;f.unit.moving=true
 local a=f:emit("MOVE",false,100,0)
 local b=f:emit("MOVE",true,px,pz)
 f.evidence_record=a
 for _,row in ipairs({{100,0},{200,30},{300,50},{400,70}}) do f:tick(row[1],row[2],0) end
 return f,b
end
local function e(f,name)
 local n=0;for _,s in ipairs(f.logs) do if s:find("] "..name.." uid=1001 ",1,true) then n=n+1 end end;return n
end
T("H3-N01 exact Native forward i+1 is adopted with owed waypoint debt",function()
 local f,b=base(200,0)
 assert(f:has("T2MOVE_D_SHADOW_CAPTURE"),"prepromotion D proof missing")
 f.evidence_record=b;f:tick(500,72,0)
 assert(e(f,"NATIVE_SUCCESSOR_ADOPTED")==1)
 assert(e(f,"TRANSITION_EDGE_COMMITTED")==1)
 assert(e(f,"ROUTE_OBLIGATION_TRANSFERRED")==1)
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"))
end)
T("H3-N02 Native 90-degree successor denied without unpaid route proof",function()
 local f,b=base(100,100)
 f.evidence_record=b;f:tick(500,72,0)
 assert(e(f,"NATIVE_SUCCESSOR_ADOPTED")==0)
 assert(e(f,"TRANSITION_EDGE_COMMITTED")==0)
 assert(f:has("H1_SHADOW_ADOPT") and f:has("frozen_verdict=BLOCKED"),
  "no prepromotion shadow witness for the denied Native corner")
end)
T("H3-N03 Native 180-degree successor denied without unpaid route proof",function()
 local f,b=base(0,0)
 f.evidence_record=b;f:tick(500,72,0)
 assert(e(f,"NATIVE_SUCCESSOR_ADOPTED")==0)
 assert(e(f,"TRANSITION_EDGE_COMMITTED")==0)
end)
T("H3-N04 native stale revision remains fail-closed",function()
 local f,b=base(200,0)
 f.revision["1001"]="999"
 f.evidence_record=b;f:tick(500,72,0)
 assert(e(f,"NATIVE_SUCCESSOR_ADOPTED")==0)
 assert(e(f,"TRANSITION_EDGE_COMMITTED")==0)
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; H3 Native fixture NOT WH3")
os.exit(fail==0 and 0 or 1)
