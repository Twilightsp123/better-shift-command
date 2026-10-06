local H=assert(loadfile(arg[1]))()
local function die(s) print("FAIL "..s);os.exit(1) end
local function eq(a,b,s) if a~=b then die(s.." got="..tostring(a).." expected="..tostring(b)) end end
local function run(f) return H.evaluate(f) end
eq(H.VERSION,"T2B_ATTACK_HANDOFF_1","version")
local base={prior_clear=true,semantic_done=false,exit_route=false,arrival_braking=true,brake_boundary=true,
    path_error=2,waypoint_tolerance=3,remaining=20,sync_margin=1}
local d=run(base);eq(d.ready,true,"path safe ready");eq(d.route_mode,"ATTACK_PATH_SAFE","path safe mode");eq(d.current_credit,"ATTACK_TERMINAL_HANDOFF","path credit")
local x={};for k,v in pairs(base) do x[k]=v end;x.prior_clear=false;d=run(x);eq(d.ready,false,"debt block");eq(d.reason,"PRIOR_ROUTE_OBLIGATION_PENDING","debt reason")
x={};for k,v in pairs(base) do x[k]=v end;x.exit_route=true;d=run(x);eq(d.ready,false,"exit strict");eq(d.reason,"ATTACK_REQUIRES_ROUTE_COMPLETE","exit reason")
x={};for k,v in pairs(base) do x[k]=v end;x.semantic_done=true;x.exit_route=true;x.prior_clear=true;d=run(x);eq(d.ready,true,"complete route ready");eq(d.route_mode,"COMPLETE","complete mode")
x={};for k,v in pairs(base) do x[k]=v end;x.arrival_braking=false;d=run(x);eq(d.ready,false,"no braking");eq(d.reason,"ATTACK_ARRIVAL_BRAKE_NOT_OBSERVED","no braking reason")
x={};for k,v in pairs(base) do x[k]=v end;x.brake_boundary=false;d=run(x);eq(d.ready,false,"before boundary");eq(d.reason,"ATTACK_BEFORE_ARRIVAL_BRAKE_BOUNDARY","boundary reason")
x={};for k,v in pairs(base) do x[k]=v end;x.path_error=8;x.remaining=3.5;x.waypoint_tolerance=3;x.sync_margin=0.5;d=run(x)
eq(d.ready,true,"terminal ready");eq(d.route_mode,"ATTACK_TERMINAL_CORRIDOR","terminal mode");eq(d.terminal_limit,3.5,"terminal limit")
x.remaining=3.5001;d=run(x);eq(d.ready,false,"terminal far block");eq(d.reason,"ATTACK_TERMINAL_ROUTE_PROTECT","terminal far reason")
x={};for k,v in pairs(base) do x[k]=v end;x.path_error=8;x.remaining=3;x.sync_margin=-100;d=run(x);eq(d.ready,true,"negative sync clamps");eq(d.terminal_limit,3,"negative sync no widening")
print("PASS: T2B attack handoff uses semantic corridor + observed arrival-brake timing without tunable distance constants")
