-- Pure H1 proof contracts, independent of controller and WH3.
local H=assert(loadfile(assert(arg[1])))()
local passed,failed=0,0
local function P(x,z)return {x=x,z=z} end
local function case(name,fn)
 local ok,why=pcall(fn)
 if ok then passed=passed+1;print("PASS "..name)
 else failed=failed+1;print("FAIL "..name.." :: "..tostring(why)) end
end
local function proof(pos,waypoint,successor,reach,opts)
 opts=opts or {}
 return H.evaluate({current_pos=pos,waypoint=waypoint,successor=successor,
  reach=reach,semantic_done=opts.done==true,prior_debts=opts.debts,
  motion_fresh=opts.fresh,previous_pos=opts.previous})
end
local function expect(r,state,reason)
 assert(r.state==state,(r.state or "nil").." ~= "..state..":"..tostring(r.reason))
 assert(r.reason==reason,tostring(r.reason).." ~= "..reason)
 assert(r.authoritative==false and r.permits_issue==false and r.permits_adopt==false,
  "shadow cannot authorize gameplay")
end
case("H1-00 collinear forward transfer keeps waypoint debt",function()
 local r=proof(P(70,0),P(100,0),P(200,0),5)
 expect(r,"DEBT_PRESERVED","H1_SUCCESSOR_CHORD_PRESERVES_WAYPOINT")
 assert(r.route_credit=="REGISTER_ROUTE_OBLIGATION" and r.chord_error==0)
end)
case("H1-01 legacy 180-degree early U-turn is NOT waypoint complete",function()
 local r=proof(P(60,0),P(100,0),P(0,0),5)
 expect(r,"BLOCKED","H1_SUCCESSOR_CHORD_MISSES_WAYPOINT")
 assert(r.remaining==40 and r.route_credit=="NONE")
end)
case("H1-02 legacy 135-degree early turn does not prove route",function()
 expect(proof(P(70,0),P(100,0),P(30,70),5),
  "BLOCKED","H1_SUCCESSOR_CHORD_MISSES_WAYPOINT")
end)
case("H1-03 legacy 90-degree early corner is steering, not completion",function()
 local r=proof(P(60,0),P(100,0),P(100,100),5)
 expect(r,"BLOCKED","H1_SUCCESSOR_CHORD_MISSES_WAYPOINT")
 assert(r.chord_error>5)
end)
case("H1-04 legal corner near waypoint completes by observed reach",function()
 expect(proof(P(98,0),P(100,0),P(100,100),5),
  "SATISFIED","H1_WAYPOINT_REACHED")
end)
case("H1-05 motion-segment crossing supports completion only if fresh",function()
 local opt={previous=P(95,0),fresh=true}
 expect(proof(P(105,0),P(100,0),P(105,100),1,opt),
  "SATISFIED","H1_WAYPOINT_PASSED_OBSERVED")
 opt.fresh=false
 expect(proof(P(105,0),P(100,0),P(105,100),1,opt),
  "BLOCKED","H1_SUCCESSOR_CHORD_MISSES_WAYPOINT")
end)
case("H1-06 canonical semantic completion counts only with safe debts",function()
 expect(proof(P(60,0),P(100,0),P(0,0),5,{done=true}),
  "SATISFIED","H1_CANONICAL_ALREADY_COMPLETE")
end)
case("H1-07 two prior waypoint debts can remain geometrically payable",function()
 local debts={{waypoint=P(100,0),tolerance=5,semantic_done=false},
              {waypoint=P(105,0),tolerance=5,semantic_done=false}}
 local r=proof(P(94,0),P(110,0),P(200,0),5,{debts=debts})
 expect(r,"DEBT_PRESERVED","H1_SUCCESSOR_CHORD_PRESERVES_WAYPOINT")
 assert(r.prior_debt_count==2)
end)
case("H1-08 prior SC3 debt off successor chord vetoes even completed current",function()
 local debts={{waypoint=P(100,0),tolerance=5,semantic_done=false}}
 local r=proof(P(94,0),P(105,0),P(80,0),5,{done=true,debts=debts})
 expect(r,"BLOCKED","H1_PRIOR_DEBT_CHORD_MISSED")
end)
case("H1-09 dense short-leg reversal misses prior debt",function()
 local debts={{waypoint=P(100,0),tolerance=5,semantic_done=false}}
 expect(proof(P(94,0),P(105,0),P(80,0),5,{debts=debts}),
  "BLOCKED","H1_PRIOR_DEBT_CHORD_MISSED")
end)
case("H1-10 unknown debt record fails closed",function()
 local r=proof(P(70,0),P(100,0),P(200,0),5,
   {debts={{waypoint=P(80,0),semantic_done=false}}})
 expect(r,"BLOCKED","H1_PRIOR_DEBT_UNPROVEN")
end)
case("H1-11 missing route geometry cannot become credit",function()
 local r=H.evaluate({current_pos=P(70,0),waypoint=P(100,0),
     reach=5,semantic_done=false})
 expect(r,"BLOCKED","H1_INPUT_NOT_PROVEN")
end)
case("H1-12 successor target equal to current position cannot pay distant debt",function()
 expect(proof(P(60,0),P(100,0),P(60,0),5),
    "BLOCKED","H1_SUCCESSOR_CHORD_MISSES_WAYPOINT")
end)
case("H1-13 no cross-unit global state",function()
 local a=proof(P(70,0),P(100,0),P(200,0),5)
 local b=proof(P(70,0),P(100,0),P(0,0),5)
 assert(a.state=="DEBT_PRESERVED" and b.state=="BLOCKED")
 a.state="SATISFIED"
 local c=proof(P(70,0),P(100,0),P(200,0),5)
 assert(c.state=="DEBT_PRESERVED")
end)
print("TOTAL "..passed.." PASS "..failed.." FAIL; H1 PURE SHADOW ONLY")
os.exit(failed==0 and 0 or 1)
