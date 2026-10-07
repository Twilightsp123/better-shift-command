-- ARRIVAL_BRAKE_G1_1
local A={VERSION="ARRIVAL_BRAKE_G1_1"}
local HUGE=(type(math.huge)=="number" and math.huge) or 1e300
local function finite(n)return type(n)=="number" and n==n and n<HUGE and n>-HUGE end
local function point(p)return type(p)=="table" and finite(p.x) and finite(p.z) end
local function sample(s)return type(s)=="table" and finite(s.ms) and point(s) end
local function dist(a,b)local dx,dz=a.x-b.x,a.z-b.z;return math.sqrt(dx*dx+dz*dz) end
function A.observe(samples,waypoint,entered_ms,tol)
 local r={ready=false,deceleration_observed=false,issue_coherent=false,adopt_coherent=false,reason="WARMUP",sample_count=0}
 if type(samples)~="table" or not point(waypoint) then r.reason="INPUT_INVALID";return r end
 if not finite(entered_ms) then r.reason="ENTRY_NOT_ESTABLISHED";return r end
 if not finite(tol) or tol<0 then r.reason="WAYPOINT_TOLERANCE_INVALID";return r end
 local rows={};for i=1,#samples do local s=samples[i];if sample(s) and s.ms>=entered_ms then rows[#rows+1]=s end end
 r.sample_count=#rows;if #rows<4 then return r end
 local base=#rows-3;local rem,ground,approach,dt={},{},{},{}
 for j=1,4 do rem[j]=dist(rows[base+j-1],waypoint) end
 for j=1,3 do local a,b=rows[base+j-1],rows[base+j];local span=b.ms-a.ms;if span<=0 then r.reason="MODEL_TIME_NOT_STRICT";return r end;dt[j]=span/1000;ground[j]=dist(a,b)/dt[j];approach[j]=(rem[j]-rem[j+1])/dt[j] end
 r.ready=true;r.sample_count=4;r.remaining=rem[4];r.ground_speed=ground[3];r.approach_speed=approach[3];r.previous_ground_speed=ground[2];r.previous_approach_speed=approach[2];r.poll_ms=dt[3]*1000;r.sync_margin=math.max(0,approach[3])*dt[3];r.waypoint_tolerance=tol
 if not (approach[1]>0 and approach[2]>0 and approach[3]>0) then r.reason="NOT_APPROACHING";return r end
 if not (ground[1]>ground[2] and ground[2]>ground[3] and approach[1]>approach[2] and approach[2]>approach[3]) then r.reason="NO_SUSTAINED_DECELERATION";return r end
 local mid1=(rows[base].ms+rows[base+1].ms)*0.5;local mid3=(rows[base+2].ms+rows[base+3].ms)*0.5;local span=(mid3-mid1)/1000;if span<=0 then r.reason="DECELERATION_WINDOW_INVALID";return r end
 local gd=(ground[1]-ground[3])/span;local ad=(approach[1]-approach[3])/span;if gd<=0 or ad<=0 then r.reason="NO_SUSTAINED_DECELERATION";return r end
 r.deceleration_observed=true;r.ground_deceleration=gd;r.approach_deceleration=ad
 local stop=(approach[3]*approach[3])/(2*ad);local err=math.abs(r.remaining-stop);r.stopping_distance=stop;r.stopping_point_error=err
 r.issue_coherence_limit=tol;r.adopt_coherence_limit=tol+r.sync_margin;r.issue_coherent=err<=r.issue_coherence_limit;r.adopt_coherent=err<=r.adopt_coherence_limit
 if r.issue_coherent then r.reason="ARRIVAL_BRAKE_ISSUE_COHERENT" elseif r.adopt_coherent then r.reason="ARRIVAL_BRAKE_ADOPT_COHERENT" else r.reason="DECELERATION_OBSERVED_STOP_INCOHERENT" end
 return r
end
return A
