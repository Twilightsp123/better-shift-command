local H=assert(loadfile(assert(arg[1])))()
local pass,fail=0,0
local function T(name,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print("PASS "..name)else fail=fail+1;print("FAIL "..name.." :: "..tostring(e))end end
local function cohort()
 local c=H.new_cohort(7,"E4",4);H.cohort_mark(c,"E17",8000);H.cohort_mark(c,"E18",8100);return c
end
local function args(c)return {generation=7,block_id="E4",exit_action_id=4,exit_order_seq="137431",next_action_id=5,next_target_uid="1033",frozen_ms=8200,cohort=c}end
T("freeze deep-copies body cohort",function()local c=cohort();local r,ok=H.freeze(nil,args(c));assert(ok and H.contains(r,"E17"));c.members.E17=nil;c.members.E99=true;assert(H.contains(r,"E17") and not H.contains(r,"E99"))end)
T("frozen handoff cannot be overwritten by later poll",function()local c=cohort();local r=H.freeze(nil,args(c));local c2=H.new_cohort(7,"E4",4);H.cohort_mark(c2,"E99",9000);local a=args(c2);a.frozen_ms=9000;local r2,ok,why=H.freeze(r,a);assert(r2==r and ok==false and why=="ALREADY_FROZEN" and not H.contains(r2,"E99"))end)
T("generation mismatch invalidates record",function()local c=cohort();local r=H.freeze(nil,args(c));local ok,why=H.valid(r,{generation=8,block_id="E4",exit_action_id=4,next_action_id=5,next_target_uid="1033",now=8300});assert(not ok and why=="SCOPE_MISMATCH")end)
T("successor target mismatch invalidates record",function()local c=cohort();local r=H.freeze(nil,args(c));local ok,why=H.valid(r,{generation=7,block_id="E4",exit_action_id=4,next_action_id=5,next_target_uid="2040",now=8300});assert(not ok and why=="SUCCESSOR_MISMATCH")end)
T("exit order mismatch invalidates record",function()local c=cohort();local r=H.freeze(nil,args(c));local ok,why=H.valid(r,{generation=7,block_id="E4",exit_action_id=4,next_action_id=5,next_target_uid="1033",exit_order_seq="137432",now=8300});assert(not ok and why=="ORDER_MISMATCH")end)
T("stale handoff is rejected rather than reused",function()local c=cohort();local r=H.freeze(nil,args(c));local ok,why=H.valid(r,{generation=7,block_id="E4",exit_action_id=4,next_action_id=5,next_target_uid="1033",now=9301,max_age_ms=1000});assert(not ok and why=="STALE")end)
T("future freeze timestamp is rejected",function()local c=cohort();local r=H.freeze(nil,args(c));local ok,why=H.valid(r,{generation=7,block_id="E4",exit_action_id=4,next_action_id=5,next_target_uid="1033",now=8100});assert(not ok and why=="TIME_INVALID")end)
T("cohort scope must match handoff scope",function()local c=H.new_cohort(7,"E9",4);H.cohort_mark(c,"E17",8000);local ok=pcall(H.freeze,nil,args(c));assert(not ok)end)
T("cohort marks only entities progressing toward Exit",function()
 local c=H.new_cohort(7,"E4",4)
 local snap={schema=3,complete=true,entities={
  {entity="100",movement_state=1,motion_complete=true,x=0,z=0,vx=2,vz=0},
  {entity="101",movement_state=1,motion_complete=true,x=0,z=0,vx=-2,vz=0},
  {entity="102",movement_state=2,motion_complete=true,x=0,z=0,vx=2,vz=0},
  {entity="103",movement_state=1,motion_complete=false,x=0,z=0,vx=2,vz=0}}}
 local n,why=H.cohort_update_motion(c,snap,{x=10,z=0},1000)
 assert(why=="OK" and n==1 and H.cohort_has(c,"100") and not H.cohort_has(c,"101") and not H.cohort_has(c,"102") and not H.cohort_has(c,"103"))
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL")
os.exit(fail==0 and 0 or 1)
