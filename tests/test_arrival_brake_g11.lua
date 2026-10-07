local A=assert(loadfile(arg[1]))()
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function S(xs,ts)local r={};for i=1,#xs do r[i]={x=xs[i],z=0,ms=ts and ts[i] or (i-1)*100} end;return r end
local function eq(a,b,m)assert(a==b,m..' got='..tostring(a)..' expected='..tostring(b))end
T('G11-00 missing entry fails closed',function()local r=A.observe(S({0,1,2,3}),{x=10,z=0},nil,1);eq(r.ready,false,'ready');eq(r.reason,'ENTRY_NOT_ESTABLISHED','reason')end)
T('G11-01 cruise not braking',function()local r=A.observe(S({0,1,2,3}),{x=10,z=0},0,1);eq(r.deceleration_observed,false,'decel')end)
T('G11-02 far slowdown incoherent',function()local r=A.observe(S({0,1.2,2,2.4}),{x=10,z=0},0,0.5);eq(r.deceleration_observed,true,'decel');eq(r.issue_coherent,false,'issue');eq(r.adopt_coherent,false,'adopt')end)
T('G11-03 issue coherent',function()local r=A.observe(S({0,1.2,2,2.4}),{x=2.7,z=0},0,0.2);eq(r.issue_coherent,true,'issue');eq(r.adopt_coherent,true,'adopt')end)
T('G11-04 adopt-only coherence',function()local r=A.observe(S({0,1.2,2,2.4}),{x=2.9,z=0},0,0.1);eq(r.issue_coherent,false,'issue');eq(r.adopt_coherent,true,'adopt')end)
T('G11-05 irregular polling',function()local r=A.observe(S({0,1.2,2.8,4},{0,100,300,600}),{x=4.7,z=0},0,0.1);eq(r.poll_ms,300,'poll')end)
T('G11-06 moving away',function()local r=A.observe(S({0,-1,-2,-3}),{x=10,z=0},0,2);eq(r.reason,'NOT_APPROACHING','reason')end)
T('G11-07 issue subset adopt',function()for tol=0,20 do for wp=25,60 do local r=A.observe(S({0,1.2,2,2.4}),{x=wp/10,z=0},0,tol/10);assert(not r.issue_coherent or r.adopt_coherent) end end end)
T('G11-08 nonmonotonic ground speed rejected',function()
 local rows={{x=0,z=0,ms=0},{x=0.9608703779745623,z=-0.2769984056470753,ms=100},{x=1.8768651220240802,z=0.3320612210510489,ms=200},{x=2.5937891758509872,z=-0.2120158884145063,ms=300}}
 local r=A.observe(rows,{x=10,z=0},0,3);assert(r.deceleration_observed==false and r.reason=='NO_SUSTAINED_DECELERATION')
end)
T('G11-09 nonmonotonic radial approach rejected',function()
 local rows={{x=0,z=0,ms=0},{x=0.9249649214870566,z=1.0854208456828138,ms=100},{x=2.13221549166603,z=0.7199782502776719,ms=200},{x=2.674099215728847,z=1.314923149765245,ms=300}}
 local r=A.observe(rows,{x=10,z=0},0,3);assert(r.deceleration_observed==false and r.reason=='NO_SUSTAINED_DECELERATION')
end)
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
