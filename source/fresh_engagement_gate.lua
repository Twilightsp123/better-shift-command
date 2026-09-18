-- FEG4: block-aware attack evidence. Matched-melee may use a wider formation-aware
-- contact envelope; geometry-only fallback remains deliberately strict. Neither path
-- proves entity-majority contact.
-- Lua 5.1-compatible. Pure calculations; no game API calls, no orders, no I/O.
-- position() calculation is undocumented; no claim this proves majority contact.
local G={VERSION="FEG4"}
G.DEFAULTS={window_ms=600,max_gap_ms=1000,confirm_ms=700,close_confirm_ms=1000,
    clear_melee_ms=300,relock_ms=600,near_default_m=28,near_min_m=16,near_max_m=34,
    hold_margin_m=6,far_margin_m=12,settle_relative_mps=2.5,settle_closing_mps=1.25,
    hold_relative_mps=4,hold_closing_mps=2,settle_actor_mps=3.5,hold_actor_mps=4.5,approach_drop_m=4,approach_mps=0.5,
    contact_confirm_ms=1200,max_observed_speed_mps=80,
    geometry_confirm_ms=1500,geometry_bbox_m=1,
    strong_width_factor=0.25,strong_extra_cap_m=40}
local function finite(n) return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge end
local function len(x,z) return math.sqrt(x*x+z*z) end
local function width(w) return finite(w) and w>=0 and w<=500 end
local function conf(custom)
    local c={};for k,v in pairs(G.DEFAULTS) do c[k]=v end
    for k,v in pairs(custom or {}) do assert(c[k]~=nil and finite(v) and v>0,"invalid FEG parameter "..tostring(k));c[k]=v end
    return c
end
function G.new(now,own_width,target_width,custom,opts)
    assert(finite(now) and now>=0,"invalid gate time")
    local c=conf(custom);local radius=c.near_default_m
    -- Ordered widths are a bounded size HINT, not an actual footprint/depth.
    -- Freeze once per Attack; later Shift appends must not change this estimate.
    if width(own_width) and width(target_width) then
        radius=math.max(c.near_min_m,math.min(c.near_max_m,
            12+0.2*(math.min(own_width,80)+math.min(target_width,80))))
    end
    local width_sum=(width(own_width) and math.min(own_width,80) or 0)+(width(target_width) and math.min(target_width,80) or 0)
    local strong_far=radius+c.far_margin_m+math.min(c.strong_extra_cap_m,width_sum*c.strong_width_factor)
    opts=opts or {}
    return {cfg=c,created=now,near=radius,hold_near=radius+c.hold_margin_m,
        far=radius+c.far_margin_m,strong_far=strong_far,phase="WAIT",samples={},opened=false,
        geometry_ms=0,geometry_last=false,intended_seen=false,
        contact_ms=0,contact_last=false,candidate_ms=0,candidate_last=false,clear_ms=0,previous_nonmelee=false,
        fresh_seen=false,approach_seen=false,peak_closing=0,far_ms=0,previous_far=false,
        last_ms=nil,last_valid=false,episode=1,start_near=nil,max_distance=nil,
        require_fresh_reentry=opts.require_fresh_reentry==true}
end
local function reset_sampling(g)
    g.samples={};g.geometry_ms=0;g.geometry_last=false;g.contact_ms=0;g.contact_last=false;g.candidate_ms=0;g.candidate_last=false;g.clear_ms=0
    g.previous_nonmelee=false;g.far_ms=0;g.previous_far=false;g.last_valid=false
end
function G.update(g,s)
    local c=g.cfg;local now=s.now
    assert(finite(now) and now>=g.created,"invalid gate clock")
    local r={allow=false,open=g.opened,phase=g.phase,reason="WAIT",near=g.near,
        hold_near=g.hold_near,far=g.far,episode=g.episode,reset_hold=false,
        just_opened=false,candidate_ms=g.candidate_ms,window_ready=false}
    local dt=g.last_ms and now-g.last_ms or 0
    if dt<0 then error("FEG_MODEL_TIME_REVERSED") end
    if g.last_ms==now then r.reason="DUPLICATE_MODEL_TIME"; return r end
    g.last_ms=now
    local valid=finite(s.ax) and finite(s.az) and finite(s.tx) and finite(s.tz)
        and type(s.melee)=="boolean" and type(s.target_match)=="boolean"
    if not valid then
        reset_sampling(g);g.phase="WAIT_DATA";r.phase=g.phase;r.reason="POSITION_OR_STATE_UNAVAILABLE";return r
    end
    local rx,rz=s.tx-s.ax,s.tz-s.az;local distance=len(rx,rz)
    if not finite(distance) then reset_sampling(g);r.reason="INVALID_DISTANCE";return r end
    r.distance=distance
    local gap=s.input_gap==true or dt>c.max_gap_ms
    if gap then reset_sampling(g) end
    local prev=g.samples[#g.samples]
    if prev and dt>0 then
        local aspeed=len(s.ax-prev.ax,s.az-prev.az)*1000/dt
        local tspeed=len(s.tx-prev.tx,s.tz-prev.tz)*1000/dt
        if aspeed>c.max_observed_speed_mps or tspeed>c.max_observed_speed_mps then
            reset_sampling(g);gap=true;r.discontinuity=true
        end
    end
    local contiguous=g.last_valid and not gap and dt>0 and dt<=c.max_gap_ms
    g.last_valid=true
    if g.start_near==nil then g.start_near=distance<=g.hold_near end
    g.max_distance=math.max(g.max_distance or distance,distance)
    local nonmelee=s.melee==false
    if nonmelee then
        g.clear_ms=(contiguous and g.previous_nonmelee) and (g.clear_ms+dt) or 0
        if g.clear_ms>=c.clear_melee_ms then g.fresh_seen=true end
    else g.clear_ms=0 end
    g.previous_nonmelee=nonmelee
    local rows=g.samples
    rows[#rows+1]={ms=now,ax=s.ax,az=s.az,tx=s.tx,tz=s.tz,rx=rx,rz=rz,d=distance}
    -- Keep the nearest sample at/before the time-window boundary and all after it.
    -- Poll is 100 model-ms at 1x, faster playback changes spacing, not time units.
    while #rows>2 and rows[2].ms<=now-c.window_ms do table.remove(rows,1) end
    local base=rows[1];local span=now-base.ms
    if span>=c.window_ms then
        r.window_ready=true
        r.closing=(base.d-distance)*1000/span
        r.relative_speed=len(rx-base.rx,rz-base.rz)*1000/span
        r.actor_speed=len(s.ax-base.ax,s.az-base.az)*1000/span
        r.target_speed=len(s.tx-base.tx,s.tz-base.tz)*1000/span
        g.peak_closing=math.max(g.peak_closing,r.closing)
        if g.max_distance-distance>=c.approach_drop_m and g.peak_closing>=c.approach_mps then g.approach_seen=true end
    end
    r.fresh_seen=g.fresh_seen;r.approach_seen=g.approach_seen;r.start_near=g.start_near
    local raw=s.melee==true and s.target_match==true
    r.raw_eligible=raw
    -- nil target is NOT a different target and NOT an API failure. The caller
    -- supplies target_known explicitly; old callers lacking metadata cannot use
    -- this fallback. A different positive target revokes previous matching evidence.
    if s.target_known==true and not s.target_match then g.intended_seen=false
    elseif s.target_match then g.intended_seen=true end
    local target_consistent=s.target_match or (s.target_known==false and g.intended_seen)
    local bbox_ok=finite(s.bbox_distance) and s.bbox_distance>=0 and s.bbox_distance<=c.geometry_bbox_m
    -- Matched-melee is stronger than geometry-only contact, but a unit-level melee
    -- flag can still describe only part of a formation. Near matched melee therefore
    -- remains valid without bbox data; extended formation contact requires bbox overlap
    -- and a bounded width-derived center envelope.
    local raw_near=raw and distance<=g.hold_near
    local raw_extended=raw and bbox_ok and distance<=g.strong_far
    local raw_contact=raw_near or raw_extended
    -- Do not reintroduce the old "body must settle" veto under another name:
    -- formation representative positions may shift while boxes stay in contact.
    -- Use continuous near + bbox contact, then a separate full hold; a brief
    -- fly-by cannot finish that dwell plus hold. Slow overlap is still a heuristic,
    -- not proof of entity contact. Large discontinuities above are rejected.
    local geometry_candidate=s.target_alive==true and target_consistent and bbox_ok
        and distance<=(g.opened and g.hold_near or g.near) and r.window_ready
        and (g.approach_seen or g.fresh_seen or (not g.require_fresh_reentry and g.start_near)) and not gap
    g.geometry_ms=(geometry_candidate and contiguous and g.geometry_last) and (g.geometry_ms+dt) or 0
    g.geometry_last=geometry_candidate
    local geometry_qualified=geometry_candidate and g.geometry_ms>=c.geometry_confirm_ms
    r.bbox_distance=s.bbox_distance;r.target_known=s.target_known;r.target_alive=s.target_alive
    r.geometry_candidate=geometry_candidate;r.geometry_ms=g.geometry_ms;r.geometry_qualified=geometry_qualified
    r.strong_far=g.strong_far;r.raw_contact=raw_contact
    r.evidence=raw_contact and "MATCHED_MELEE" or (geometry_qualified and "GEOMETRY_PROXY" or "NONE")
    -- A matched-melee formation can legitimately have distant representative
    -- centers while the bounding boxes still overlap. Do not relock that stronger
    -- contact path merely because it exceeds the geometry-only far radius.
    local far=distance>(raw_contact and g.strong_far or g.far)
    if far then g.far_ms=(contiguous and g.previous_far) and (g.far_ms+dt) or 0 else g.far_ms=0 end
    g.previous_far=far
    -- Real geometric separation sustained across samples starts a NEW local episode.
    -- Unlike transient melee false, this explicitly invalidates old engagement credit.
    if g.opened and g.far_ms>=c.relock_ms then
        g.opened=false;g.episode=g.episode+1;g.open_ms=nil
        g.geometry_ms=0;g.geometry_last=false;g.contact_ms=0;g.contact_last=false;g.candidate_ms=0;g.candidate_last=false;g.approach_seen=false;g.fresh_seen=false
        g.max_distance=distance;g.peak_closing=0;g.start_near=false
        r.reset_hold=true;r.open=false;r.episode=g.episode;g.phase="WAIT"
        r.reason="SEPARATION_RELOCK";r.phase=g.phase;r.candidate_ms=0
        return r
    end
    if g.opened then
        -- Confirmation is latched for this episode. Ordinary formation/target
        -- motion no longer suspends credit. Each sample still requires either
        -- matched melee or independently confirmed bounding-box contact, plus
        -- valid observation, near geometry and gap rules.
        local strong_allow=raw_contact and r.window_ready and not gap
        local geometry_allow=geometry_qualified and distance<=g.hold_near and r.window_ready and not gap
        r.allow=strong_allow or geometry_allow
        g.phase=r.allow and "HOLD" or "SUSPENDED"
        r.reason=r.allow and (strong_allow and "QUALIFIED_CONTACT" or "QUALIFIED_GEOMETRY_CONTACT") or (not raw_contact and "MELEE_OR_TARGET_MISMATCH" or
            (distance>g.strong_far and "BODY_SEPARATED" or (gap and "OBSERVATION_GAP" or "RATE_WARMUP")))
        r.open=true;r.phase=g.phase;return r
    end
    if geometry_qualified and not raw then
        g.opened=true;g.open_ms=now;g.phase="HOLD";g.open_mode="GEOMETRY_CONTACT_CONFIRMED"
        r.allow=true;r.just_opened=true;r.open=true;r.reason=g.open_mode
        r.candidate_ms=g.geometry_ms;r.phase=g.phase;return r
    end
    -- No path admits a bare melee false->true edge. ALL entry paths require geometry.
    local evidence=g.fresh_seen or g.approach_seen or (not g.require_fresh_reentry and g.start_near)
    local settled=r.window_ready and r.relative_speed<=c.settle_relative_mps and r.actor_speed<=c.settle_actor_mps and math.abs(r.closing)<=c.settle_closing_mps
    local contact=raw_contact and r.window_ready and evidence and not gap
    g.contact_ms=(contact and contiguous and g.contact_last) and (g.contact_ms+dt) or 0
    g.contact_last=contact
    -- Bounded fallback for a close, sustained melee with the intended target.
    -- Not a majority-of-models detector and not proof of a charge bonus.
    local sustained=contact and g.contact_ms>=c.contact_confirm_ms
    local candidate=raw_contact and distance<=g.near and settled and evidence and not gap
    if sustained and not candidate then
        g.opened=true;g.open_ms=now;g.phase="HOLD";g.open_mode="SUSTAINED_NEAR_CONTACT"
        r.allow=true;r.just_opened=true;r.open=true;r.reason=g.open_mode
        r.candidate_ms=g.contact_ms;r.phase=g.phase;return r
    end
    if candidate then
        g.candidate_ms=(contiguous and g.candidate_last) and (g.candidate_ms+dt) or 0
        local mode=g.approach_seen and "APPROACH_SETTLED" or (g.fresh_seen and "FRESH_MELEE_NEAR_SETTLED" or "CLOSE_START_SETTLED")
        local required=mode=="CLOSE_START_SETTLED" and c.close_confirm_ms or c.confirm_ms
        r.required_ms=required;r.mode=mode
        if g.candidate_ms>=required or sustained then
            g.opened=true;g.open_ms=now;g.phase="HOLD";g.open_mode=mode
            -- First open sample is eligible, but caller must credit ZERO interval on this edge.
            r.allow=true;r.just_opened=true;r.open=true;r.reason=mode
        else g.phase="CONFIRMING";r.reason=mode end
    else
        g.candidate_ms=0;g.phase="WAIT"
        r.reason=not raw_contact and "MELEE_OR_TARGET_MISMATCH" or (distance>g.strong_far and "BODY_FAR" or
            (gap and "OBSERVATION_GAP" or (not r.window_ready and "RATE_WARMUP" or
            (not settled and "BODY_STILL_APPROACHING_OR_MOVING" or "NO_FRESH_EVIDENCE"))))
    end
    if geometry_candidate and not raw then
        g.phase="CONFIRMING_GEOMETRY";r.reason="GEOMETRY_CONTACT_CONFIRMING"
    end
    g.candidate_last=candidate;r.candidate_ms=geometry_candidate and not raw and g.geometry_ms or g.candidate_ms;r.phase=g.phase
    return r
end
return G
