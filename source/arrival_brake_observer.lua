local A=(function()
    local A={VERSION="ARRIVAL_BRAKE_G1"}
    local HUGE=(type(math.huge)=="number" and math.huge) or 1e300
    local function finite(n) return type(n)=="number" and n==n and n<HUGE and n>-HUGE end
    local function valid_point(p) return type(p)=="table" and finite(p.x) and finite(p.z) end
    local function valid_sample(s) return type(s)=="table" and finite(s.ms) and valid_point(s) end
    local function distance(a,b) local dx,dz=a.x-b.x,a.z-b.z;return math.sqrt(dx*dx+dz*dz) end
    function A.observe(samples,waypoint,entered_ms)
        local r={ready=false,braking=false,boundary_crossed=false,reason="WARMUP",sample_count=0}
        if type(samples)~="table" or not valid_point(waypoint) then r.reason="INPUT_INVALID";return r end
        if not finite(entered_ms) then r.reason="ENTRY_NOT_ESTABLISHED";return r end
        local rows={}
        for i=1,#samples do local s=samples[i];if valid_sample(s) and s.ms>=entered_ms then rows[#rows+1]=s end end
        r.sample_count=#rows;if #rows<4 then return r end
        local base=#rows-3;local rem,ground,approach,dt={},{},{},{}
        for j=1,4 do rem[j]=distance(rows[base+j-1],waypoint) end
        for j=1,3 do
            local a,b=rows[base+j-1],rows[base+j];local span=b.ms-a.ms
            if span<=0 then r.reason="MODEL_TIME_NOT_STRICT";return r end
            dt[j]=span/1000;ground[j]=distance(a,b)/dt[j];approach[j]=(rem[j]-rem[j+1])/dt[j]
        end
        r.ready=true;r.sample_count=4;r.remaining=rem[4];r.ground_speed=ground[3];r.approach_speed=approach[3]
        r.previous_ground_speed=ground[2];r.previous_approach_speed=approach[2];r.poll_ms=dt[3]*1000
        r.sync_margin=math.max(0,approach[3])*dt[3]
        if not (approach[1]>0 and approach[2]>0 and approach[3]>0) then r.reason="NOT_APPROACHING";return r end
        if not (ground[1]>ground[2] and ground[2]>ground[3] and approach[1]>approach[2] and approach[2]>approach[3]) then r.reason="NO_SUSTAINED_DECELERATION";return r end
        local mid1=(rows[base].ms+rows[base+1].ms)*0.5;local mid3=(rows[base+2].ms+rows[base+3].ms)*0.5;local span=(mid3-mid1)/1000
        if span<=0 then r.reason="DECELERATION_WINDOW_INVALID";return r end
        local ground_decel=(ground[1]-ground[3])/span;local approach_decel=(approach[1]-approach[3])/span
        if ground_decel<=0 or approach_decel<=0 then r.reason="NO_SUSTAINED_DECELERATION";return r end
        r.ground_deceleration=ground_decel;r.approach_deceleration=approach_decel
        r.stopping_distance=(approach[3]*approach[3])/(2*approach_decel);r.preempt_distance=r.stopping_distance+r.sync_margin
        r.braking=true;r.boundary_crossed=r.remaining<=r.preempt_distance
        r.reason=r.boundary_crossed and "ARRIVAL_BRAKE_BOUNDARY_REACHED" or "ARRIVAL_BRAKE_OBSERVED";return r
    end
    return A
end)()
return A
