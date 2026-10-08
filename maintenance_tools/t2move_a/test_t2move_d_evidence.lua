local D=assert(loadfile(assert(arg[1])))()
local pass=0
local function T(name,fn)local ok,e=pcall(fn);if not ok then print("FAIL "..name.." "..tostring(e));os.exit(1) end;pass=pass+1;print("PASS "..name) end
local function f(mode)
 local a={action_id="11",block_id="B1",block_kind="MOVE_ROUTE",type="MOVE",pos={x=100,z=0},runtime={semantic_done=false}}
 local g={remaining=46,leg=100,next_leg=70,progress=.54,route_min_progress=.2,threshold=42,stall=false,route_mode=mode or "PATH_SAFE",route_debt_mode="CLEAR",arrival_brake_ready=true,arrival_sync_margin=5,cut_error=.5,cut_safe_limit=1,cut_tolerance=4,corner_window=50,corner_window_base=50,corner_window_early=25}
 local s={block_state={B1={id="B1",kind="MOVE_ROUTE",route_debts={}}}}
 local sig=assert(D.route_debt_signature(s,a))
 local p={exact_current_execution=true,current_kind="MOVE",successor_kind="MOVE",gen=7,revision="12",unit_lifetime="1",current_action_id="11",successor_action_id="12",current_index=1,successor_index=2,now_ms=500,poll_ms=100,waypoint_x=100,waypoint_z=0,route_ok=true,issue_open=false,debt_signature=sig,geometry=g,motion_samples={{ms=400,x=49,z=0},{ms=500,x=54,z=0}}}
 local q={gen=7,revision="12",unit_lifetime="1",current_action_id="11",successor_action_id="12",current_index=1,successor_index=2,now_ms=600,observed_step_ms=100,exact_native_successor=true,debt_signature=sig}
 return p,q,s,a
end
T("D00 geometry complete",function()local p=f();local c=assert(D.capture(p));assert(c.geometry.cut_safe_limit==1 and c.geometry.stall==false and c.geometry.route_min_progress==.2)end)
T("D01 pure non-authoritative",function()local p=f();local c=assert(D.capture(p));assert(c.authoritative==false and D.authoritative==false)end)
T("D02 deterministic debt signature",function()
 local p,q,s,a=f();local aa={action_id="01",block_id="B1",type="MOVE",pos={x=20,z=3},runtime={semantic_done=false}}
 local bb={action_id="02",block_id="B1",type="MOVE",pos={x=30,z=4},runtime={semantic_done=false}}
 s.block_state.B1.route_debts={["02"]={action=bb,tolerance=3},["01"]={action=aa,tolerance=4}}
 local x=assert(D.route_debt_signature(s,a))
 s.block_state.B1.route_debts={["01"]={action=aa,tolerance=4},["02"]={action=bb,tolerance=3}}
 assert(x==D.route_debt_signature(s,a))
end)
T("D03 debt addition revokes old signature",function()
 local p,q,s,a=f();local c=assert(D.capture(p))
 s.block_state.B1.route_debts["09"]={action={action_id="09",block_id="B1",type="MOVE",pos={x=2,z=1}},tolerance=5}
 q.debt_signature=assert(D.route_debt_signature(s,a));assert(not D.revalidate(c,q))
end)
T("D04 tolerance changes signature",function()
 local p,q,s,a=f();s.block_state.B1.route_debts["09"]={action={action_id="09",block_id="B1",type="MOVE",pos={x=2,z=1}},tolerance=5}
 local sig=assert(D.route_debt_signature(s,a));s.block_state.B1.route_debts["09"].tolerance=6
 assert(sig~=D.route_debt_signature(s,a))
end)
T("D05 paid debt changes signature",function()
 local p,q,s,a=f();local debt={action_id="09",block_id="B1",type="MOVE",pos={x=2,z=1},runtime={semantic_done=false}}
 s.block_state.B1.route_debts["09"]={action=debt,tolerance=5};local sig=assert(D.route_debt_signature(s,a))
 debt.runtime.semantic_done=true;assert(sig~=D.route_debt_signature(s,a))
end)
T("D06 progress fields not part of debt identity",function()
 local p,q,s,a=f();s.block_state.B1.route_debts["09"]={action={action_id="09",block_id="B1",type="MOVE",pos={x=2,z=1}},tolerance=5,last_remaining=90}
 local sig=assert(D.route_debt_signature(s,a));s.block_state.B1.route_debts["09"].last_remaining=80
 assert(sig==D.route_debt_signature(s,a))
end)
T("D07 other block debt irrelevant",function()local p,q,s,a=f();s.block_state.B2={id="B2",route_debts={foo=true}};assert(p.debt_signature==D.route_debt_signature(s,a))end)
T("D08 wrong owner fails closed",function()
 local p,q,s,a=f();s.block_state.B1.route_debts["09"]={action={action_id="09",block_id="B2",type="MOVE",pos={x=2,z=1}},tolerance=5}
 assert(D.route_debt_signature(s,a)==nil)
end)
T("D09 capture requires exact current",function()local p=f();p.exact_current_execution=false;assert(not D.capture(p))end)
T("D10 capture never skips successor",function()local p=f();p.successor_index=3;assert(not D.capture(p))end)
T("D11 exact timestamp and real poll",function()local p=f();p.motion_samples[1].ms=399;assert(not D.capture(p))end)
T("D12 geometry must correspond to sample",function()local p=f();p.geometry.remaining=45;assert(not D.capture(p))end)
T("D13 frozen geometry",function()local p=f();local c=assert(D.capture(p));p.geometry.remaining=44;assert(c.geometry.remaining==46)end)
T("D14 evidence positive radial",function()
 local p=f();local c=assert(D.capture(p));assert(c.evidence.previous_remaining==51 and c.evidence.current_remaining==46 and c.evidence.ground_distance==5)
end)
T("D15 exact next read valid one poll",function()local p,q=f();assert(D.revalidate(assert(D.capture(p)),q))end)
T("D16 i+2 or mismatch refused",function()local p,q=f();local c=assert(D.capture(p));q.successor_index=3;assert(not D.revalidate(c,q));q.successor_index=2;q.unit_lifetime="2";assert(not D.revalidate(c,q))end)
T("D17 revision and route debt bound",function()local p,q=f();local c=assert(D.capture(p));q.revision="13";assert(not D.revalidate(c,q));q.revision="12";q.debt_signature="bad";assert(not D.revalidate(c,q))end)
T("D18 stale after one poll",function()local p,q=f();local c=assert(D.capture(p));q.now_ms=601;assert(not D.revalidate(c,q))end)
T("D19 common field mandatory",function()local p=f();p.geometry.threshold=nil;local c,why=D.capture(p);assert(not c and why=="MOVE_SNAPSHOT_MISSING_threshold")end)
T("D20 steering fields mandatory",function()local p=f("STEERING_CORNER");assert(D.capture(p));p.geometry.corner_window_early=nil;assert(not D.capture(p))end)
T("D21 SC3 hard debt excluded",function()local p=f();p.geometry.route_debt_mode="HARD";assert(not D.capture(p))end)
T("D22 soft debt proof fields",function()local p=f();p.geometry.route_debt_mode="SOFT_PRESERVED";assert(not D.capture(p));p.geometry.route_debt_count=1;p.geometry.route_debt_error=1;p.geometry.route_debt_limit=2;assert(D.capture(p))end)
print("TOTAL "..pass.." PASS 0 FAIL")
