local A=assert(loadfile(arg[1]))()
local function die(s) print("FAIL "..s);os.exit(1) end
local function eq(a,b,s) if a~=b then die(s.." got="..tostring(a).." expected="..tostring(b)) end end
local function near(a,b,e,s) if not a or math.abs(a-b)>e then die(s.." got="..tostring(a).." expected="..tostring(b)) end end
local function S(xs,ts)
  local r={};for i=1,#xs do r[i]={x=xs[i],z=0,ms=ts and ts[i] or (i-1)*100} end;return r
end
eq(A.VERSION,"ARRIVAL_BRAKE_G1","version")
local r=A.observe(S({0,1,2,3}),{x=10,z=0},nil)
eq(r.ready,false,"missing entry not ready");eq(r.reason,"ENTRY_NOT_ESTABLISHED","missing entry reason")
r=A.observe(S({0,1,2,3}),{x=10,z=0},0)
eq(r.ready,true,"constant ready");eq(r.braking,false,"constant not braking");eq(r.reason,"NO_SUSTAINED_DECELERATION","constant reason")
r=A.observe(S({0,1.2,2.0,2.4}),{x=10,z=0},0)
eq(r.braking,true,"decel braking");eq(r.boundary_crossed,false,"decel far boundary")
near(r.approach_speed,4,1e-9,"approach speed");near(r.ground_speed,4,1e-9,"ground speed")
near(r.approach_deceleration,40,1e-9,"approach decel");near(r.stopping_distance,0.2,1e-9,"stopping")
near(r.sync_margin,0.4,1e-9,"sync margin");near(r.preempt_distance,0.6,1e-9,"preempt")
r=A.observe(S({0,1.2,2.0,2.4}),{x=2.9,z=0},0)
eq(r.braking,true,"near braking");eq(r.boundary_crossed,true,"near boundary");eq(r.reason,"ARRIVAL_BRAKE_BOUNDARY_REACHED","near reason")
r=A.observe(S({0,1.2,2.8,4.0},{0,100,300,600}),{x=20,z=0},0)
eq(r.braking,true,"irregular braking");near(r.approach_speed,4,1e-9,"irregular speed");near(r.approach_deceleration,20,1e-9,"irregular decel")
near(r.sync_margin,1.2,1e-9,"irregular sync");near(r.stopping_distance,0.4,1e-9,"irregular stop")
r=A.observe(S({0,1.2,2.0,2.4}),{x=10,z=0},150)
eq(r.ready,false,"entry filter warmup");eq(r.reason,"WARMUP","entry filter reason")
r=A.observe(S({0,-1,-2,-3}),{x=10,z=0},0)
eq(r.braking,false,"away not braking");eq(r.reason,"NOT_APPROACHING","away reason")
print("PASS: ARRIVAL_BRAKE_G1 pure radial+ground deceleration observer")
