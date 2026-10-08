-- BSC T2-MOVE-H1 pure route-obligation shadow model.
-- No Native bridge, dispatch, transaction, cursor, or gameplay permission authority.
-- A DEBT_PRESERVED verdict proves *geometric opportunity*, not actual CA movement.
local H={VERSION="T2MOVE_H1_ROUTE_OBLIGATION_SHADOW_1",authoritative=false}
local huge=math.huge or 1e300
local function finite(n)return type(n)=="number" and n==n and n<huge and n>-huge end
local function valid_point(p)return type(p)=="table" and finite(p.x) and finite(p.z) end
local function distance(a,b)local dx,dz=a.x-b.x,a.z-b.z;return math.sqrt(dx*dx+dz*dz) end
local function chord_error(p,a,b)
 local x,z=b.x-a.x,b.z-a.z
 local sq=x*x+z*z
 if sq<=0 then return distance(p,a) end
 local projection=((p.x-a.x)*x+(p.z-a.z)*z)/sq
 local t=math.max(0,math.min(1,projection))
 local dx,dz=p.x-(a.x+x*t),p.z-(a.z+z*t)
 return math.sqrt(dx*dx+dz*dz)
end
local function reply(state,reason,extra)
 local r={state=state,reason=reason,authoritative=false,
    route_credit=state=="SATISFIED" and "CURRENT_WAYPOINT_COMPLETE"
       or (state=="DEBT_PRESERVED" and "REGISTER_ROUTE_OBLIGATION" or "NONE"),
    permits_issue=false,permits_adopt=false,
    proof_scope="GEOMETRIC_NECESSARY_CONDITION_ONLY"}
 if extra then for k,v in pairs(extra) do r[k]=v end end
 return r
end
function H.evaluate(f)
 if type(f)~="table" or not valid_point(f.current_pos)
   or not valid_point(f.waypoint) or not valid_point(f.successor)
   or not finite(f.reach) or f.reach<0
   or type(f.semantic_done)~="boolean" then
    return reply("BLOCKED","H1_INPUT_NOT_PROVEN")
 end
 if f.prior_debts~=nil and type(f.prior_debts)~="table" then
    return reply("BLOCKED","H1_PRIOR_DEBTS_INVALID")
 end
 local prior_debt_count=0
 -- Never count an unverified/stale prior-debt record as paid.
 for _,d in pairs(f.prior_debts or {}) do
    if type(d)~="table" or type(d.semantic_done)~="boolean"
       or not valid_point(d.waypoint) or not finite(d.tolerance)
       or d.tolerance<0 then
        return reply("BLOCKED","H1_PRIOR_DEBT_UNPROVEN")
    end
    if not d.semantic_done then
       prior_debt_count=prior_debt_count+1
       if chord_error(d.waypoint,f.current_pos,f.successor)>d.tolerance then
          return reply("BLOCKED","H1_PRIOR_DEBT_CHORD_MISSED",
             {prior_debt_count=prior_debt_count})
       end
    end
 end
 local remaining=distance(f.current_pos,f.waypoint)
 local path_error=chord_error(f.waypoint,f.current_pos,f.successor)
 local metrics={remaining=remaining,chord_error=path_error,
   reach=f.reach,prior_debt_count=prior_debt_count}
 if f.semantic_done then
    return reply("SATISFIED","H1_CANONICAL_ALREADY_COMPLETE",metrics)
 end
 if remaining<=f.reach then
    return reply("SATISFIED","H1_WAYPOINT_REACHED",metrics)
 end
 if f.motion_fresh==true and valid_point(f.previous_pos)
    and chord_error(f.waypoint,f.previous_pos,f.current_pos)<=f.reach then
    return reply("SATISFIED","H1_WAYPOINT_PASSED_OBSERVED",metrics)
 end
 if path_error<=f.reach then
    return reply("DEBT_PRESERVED","H1_SUCCESSOR_CHORD_PRESERVES_WAYPOINT",metrics)
 end
 return reply("BLOCKED","H1_SUCCESSOR_CHORD_MISSES_WAYPOINT",metrics)
end
return H
