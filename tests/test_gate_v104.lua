-- FEG4 formation-aware matched-melee envelope tests; synthetic unit-level evidence only.
local G=assert(loadfile(assert(arg[1])))()
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function z(t,d,melee,bbox)
 return {now=t,ax=-d,az=0,tx=0,tz=0,melee=melee,target_match=true,target_known=true,target_alive=true,bbox_distance=bbox}
end
local function warm(g)
 -- establish non-melee freshness + approach while outside the normal near band
 for t=0,1000,100 do local d=70-15*(t/1000);G.update(g,z(t,d,false,0))end
end
T('FEG4 bounded matched-melee formation contact may qualify inside strong envelope',function()
 local g=G.new(0,40,40);warm(g);local r
 for t=1100,4000,100 do r=G.update(g,z(t,55,true,0))end
 assert(g.strong_far==60);assert(r.allow and g.opened)
end)
T('FEG4 matched-melee contact beyond strong envelope cannot qualify',function()
 local g=G.new(0,40,40);warm(g);local r
 for t=1100,7000,100 do r=G.update(g,z(t,65,true,0))end
 assert(g.strong_far==60);assert(not r.allow and not g.opened)
end)
T('FEG4 extended matched-melee path requires bounding-box overlap',function()
 local g=G.new(0,40,40);warm(g);local r
 for t=1100,7000,100 do r=G.update(g,z(t,55,true,5))end
 assert(not r.allow and not g.opened)
end)
print('ACTUAL_INTERPRETER='.._VERSION);print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
