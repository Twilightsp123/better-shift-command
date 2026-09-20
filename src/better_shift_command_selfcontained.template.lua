-- Better Shift Command v1.2.2 production controller. SC1-SC6 movement/exit/execution-identity fixes retained.
-- Command identity/ACK remains native-authoritative. V3 EntitySnapshot/ContactPair evidence
-- supports bounded exit recovery while route semantics remain controller-authoritative.
-- Post-exit A2 uses route semantic completion + post-ACK fresh-mode FEG.
local RUN_ID = "V1_2_2"
local TEST_PROFILE = "ROUTE_ONLY" -- Compatibility label only; never changes motion.
local CONTROLLER_PHASE = "P2B" -- Installer can select P1E for terminal-only regression.
local CONTROLLER_VERSION = "1.2.2"
local TAG = "[BETTER_SHIFT_COMMAND] "
-- Production default: high-frequency diagnostics are disabled. Tests may explicitly re-enable them.
local DEBUG_TELEMETRY = false
local CENTER_A2_MODE = true
out(TAG .. "ENTER version=" .. CONTROLLER_VERSION .. " run=" .. RUN_ID .. " phase=" .. CONTROLLER_PHASE .. " build=BETTER_SHIFT_COMMAND_V1.2.2 debug_telemetry=" .. tostring(DEBUG_TELEMETRY))

-- out is callable; it need not have Lua type "function".
local function log(s) out(TAG .. tostring(s)) end
local telemetry_last={}
local function dlog(s)
    if not DEBUG_TELEMETRY then return end
    local event=s:match("^(%S+)")
    if event=="SCHEDULER_HEAD" or event=="ATTACK_TARGET_OBSERVED" then
        local now=tonumber(s:match("model_ms=(%d+)"))
        local key=event=="SCHEDULER_HEAD" and event or (event..":"..(s:match("uid=(%d+)") or "?"))
        if now and telemetry_last[key] and now-telemetry_last[key]<1000 then return end
        telemetry_last[key]=now
    end
    out(TAG .. tostring(s))
end
local function clean(s) return (tostring(s):gsub("[%c%s]", "_")) end
local BSC_HUGE = (type(math.huge)=="number" and math.huge) or 1e300
-- Self-contained native materializer.
-- Keep every bootstrap helper inside one closure so the controller main chunk
-- pays for exactly one local slot: ensure_embedded_native.
local ensure_embedded_native=(function()
    local EMBEDDED_NATIVE = {
        {
            disk_path = ".\\minhook.x64.dll",
            virtual_path = "/script/better_shift_command/bin/minhook_Windows_NT-x64.lua",
            size = 115712,
            sha256 = "df452eacdb076c35a80c795df920fd3c6f128faa3e0bccb0b7490e95f8659d54"
        },
        {
            disk_path = ".\\wh3_native_bridge.dll",
            virtual_path = "/script/better_shift_command/bin/bridge_Windows_NT-x64.lua",
            size = @@BRIDGE_SIZE@@,
            sha256 = "@@BRIDGE_SHA256@@"
        }
    }
    local function native_read_all(path)
        local f=io.open(path,"rb")
        if not f then return nil end
        local d=f:read("*a")
        f:close()
        return d
    end
    local function native_write_all(path,data)
        local f,err=io.open(path,"wb")
        if not f then return nil,err end
        local ok,werr=pcall(function() f:write(data) end)
        f:close()
        if not ok then return nil,werr end
        return true
    end
    local function native_payload(spec)
        if type(loadfile)~="function" then error("EMBED_LOADFILE_UNAVAILABLE") end
        local chunk,err=loadfile(spec.virtual_path)
        if type(chunk)~="function" then error("EMBED_PAYLOAD_OPEN "..clean(err or spec.virtual_path)) end
        local ok,data=pcall(chunk)
        if not ok or type(data)~="string" then error("EMBED_PAYLOAD_DECODE "..clean(data)) end
        if #data~=spec.size then error("EMBED_PAYLOAD_SIZE "..spec.disk_path.." got="..tostring(#data).." expected="..tostring(spec.size)) end
        return data
    end
    local function native_ensure_one(spec)
        local payload=native_payload(spec)
        local existing=native_read_all(spec.disk_path)
        if existing==payload then
            dlog("NATIVE_EMBED_KEEP file="..spec.disk_path.." size="..tostring(#payload).." sha256="..spec.sha256)
            return true
        end
        log("NATIVE_EMBED_WRITE file="..spec.disk_path.." size="..tostring(#payload).." sha256="..spec.sha256)
        local ok,err=native_write_all(spec.disk_path,payload)
        if not ok then error("EMBED_WRITE "..spec.disk_path.." "..clean(err)) end
        local verify=native_read_all(spec.disk_path)
        if verify~=payload then error("EMBED_VERIFY_EXACT_BYTES "..spec.disk_path) end
        log("NATIVE_EMBED_OK file="..spec.disk_path.." exact_bytes=true sha256="..spec.sha256)
        return true
    end
    return function()
        if type(io)~="table" or type(io.open)~="function" then error("EMBED_IO_UNAVAILABLE") end
        -- MinHook must be materialized before Bridge because Bridge resolves it dynamically.
        for i=1,#EMBEDDED_NATIVE do native_ensure_one(EMBEDDED_NATIVE[i]) end
    end
end)()
local function finite(n) return type(n)=="number" and n==n and n<BSC_HUGE and n>-BSC_HUGE end
local function id(s)
    return type(s)=="string" and #s>0 and #s<=10 and not s:find("[^0-9]")
        and (#s==1 or s:sub(1,1)~="0") and (#s<10 or s<="4294967295")
end
local function cmp(a,b)
    if #a~=#b then return #a<#b and -1 or 1 end
    if a==b then return 0 end
    return a<b and -1 or 1
end
local function inc(s)
    if not id(s) or s=="4294967295" then return nil end
    local t,carry={},1
    for i=#s,1,-1 do
        local n=s:byte(i)-48+carry; carry=n>=10 and 1 or 0
        t[i]=string.char(48+n%10)
    end
    return (carry==1 and "1" or "")..table.concat(t)
end
local function uid(unit)
    local ok,u=pcall(function() return unit:unique_ui_id() end)
    if not ok then return nil end
    if type(u)=="string" then return id(u) and u or nil end
    if finite(u) and u>=0 and u<=16777215 and u==math.floor(u) then return string.format("%.0f",u) end
    return nil
end
local function point(unit)
    local ok,p=pcall(function()
        local v=unit:position()
        return {x=v:get_x(),y=v:get_y(),z=v:get_z()}
    end)
    if ok and finite(p.x) and finite(p.y) and finite(p.z) then return p end
end
local function copy(p) return p and {x=p.x,y=p.y,z=p.z} or nil end
local function dist(a,b) local x,z=a.x-b.x,a.z-b.z; return math.sqrt(x*x+z*z) end
local function clamp(x,a,b) return math.max(a,math.min(b,x)) end
local function median(t)
    if #t==0 then return nil end
    local v={}; for i=1,#t do v[i]=t[i] end; table.sort(v)
    local n=#v; return n%2==1 and v[(n+1)/2] or (v[n/2]+v[n/2+1])/2
end
local function accepted(r) return r.status=="ACCEPTED" or r.status=="ACCEPTED_NO_SLOT" end
local function trace(e)
    local s=tostring(e)
    if debug and type(debug.traceback)=="function" then s=debug.traceback(s,2) end
    return s
end
-- R1_V3_HANDOFF_MODULE_BEGIN
local R1V3Handoff=(function()
-- R1 Evidence V3 handoff primitives.
-- Pure Lua 5.1 data/lifecycle logic: no game API, no orders, no timing heuristics.
local H={VERSION="R1_V3_HANDOFF_1"}
local function id(s)
    return type(s)=="string" and #s>0 and #s<=10 and not s:find("[^0-9]")
        and (#s==1 or s:sub(1,1)~="0") and (#s<10 or s<="4294967295")
end
local BSC_HUGE = (type(math.huge)=="number" and math.huge) or 1e300
local function finite(n) return type(n)=="number" and n==n and n<BSC_HUGE and n>-BSC_HUGE end
local function copy_set(src)
    local out={};for k,v in pairs(src or {}) do if v==true then out[k]=true end end;return out
end
function H.new_cohort(generation,block_id,exit_action_id)
    assert(finite(generation) and generation>=1 and generation%1==0,"invalid generation")
    assert(type(block_id)=="string" and block_id~="","invalid block id")
    assert(finite(exit_action_id) and exit_action_id>=1 and exit_action_id%1==0,"invalid exit action")
    return {generation=generation,block_id=block_id,exit_action_id=exit_action_id,members={},first_ms=nil,last_ms=nil}
end
function H.cohort_mark(c,entity,sample_ms)
    assert(type(c)=="table" and type(c.members)=="table","invalid cohort")
    assert(type(entity)=="string" and entity~="","invalid entity id")
    assert(finite(sample_ms) and sample_ms>=0,"invalid sample time")
    c.members[entity]=true;c.first_ms=c.first_ms and math.min(c.first_ms,sample_ms) or sample_ms;c.last_ms=c.last_ms and math.max(c.last_ms,sample_ms) or sample_ms
end
function H.cohort_has(c,entity) return type(c)=="table" and type(c.members)=="table" and c.members[entity]==true end
function H.cohort_update_motion(c,snapshot,dest,sample_ms)
    assert(type(c)=="table" and type(c.members)=="table","invalid cohort")
    if type(snapshot)~="table" or snapshot.schema~=3 or snapshot.complete~=true or type(snapshot.entities)~="table" then return 0,"SNAPSHOT_INVALID" end
    if type(dest)~="table" or not finite(dest.x) or not finite(dest.z) then return 0,"DESTINATION_INVALID" end
    if not finite(sample_ms) or sample_ms<0 then return 0,"TIME_INVALID" end
    local marked=0
    for i=1,#snapshot.entities do
        local e=snapshot.entities[i]
        if type(e)=="table" and type(e.entity)=="string" and e.entity~="" and e.movement_state==1 and e.motion_complete==true
            and finite(e.x) and finite(e.z) and finite(e.vx) and finite(e.vz) then
            local dx,dz=dest.x-e.x,dest.z-e.z
            if dx*e.vx+dz*e.vz>0 then
                if not c.members[e.entity] then marked=marked+1 end
                H.cohort_mark(c,e.entity,sample_ms)
            end
        end
    end
    return marked,"OK"
end
function H.freeze(existing,args)
    assert(type(args)=="table","missing handoff args")
    if existing and existing.frozen==true then return existing,false,"ALREADY_FROZEN" end
    assert(finite(args.generation) and args.generation>=1 and args.generation%1==0,"invalid generation")
    assert(type(args.block_id)=="string" and args.block_id~="","invalid block id")
    assert(finite(args.exit_action_id) and args.exit_action_id>=1 and args.exit_action_id%1==0,"invalid exit action")
    assert(id(args.exit_order_seq),"invalid exit order id")
    assert(finite(args.next_action_id) and args.next_action_id>=1 and args.next_action_id%1==0,"invalid next action")
    assert(id(args.next_target_uid),"invalid next target")
    assert(finite(args.frozen_ms) and args.frozen_ms>=0,"invalid freeze time")
    assert(type(args.cohort)=="table" and type(args.cohort.members)=="table","missing cohort")
    assert(args.cohort.generation==args.generation and args.cohort.block_id==args.block_id and args.cohort.exit_action_id==args.exit_action_id,"cohort scope mismatch")
    return {frozen=true,generation=args.generation,block_id=args.block_id,exit_action_id=args.exit_action_id,
        exit_order_seq=args.exit_order_seq,next_action_id=args.next_action_id,next_target_uid=args.next_target_uid,
        frozen_ms=args.frozen_ms,body_entities=copy_set(args.cohort.members),cohort_first_ms=args.cohort.first_ms,cohort_last_ms=args.cohort.last_ms},true,"FROZEN"
end
function H.valid(r,args)
    if type(r)~="table" or r.frozen~=true or type(args)~="table" then return false,"MISSING" end
    if r.generation~=args.generation or r.block_id~=args.block_id or r.exit_action_id~=args.exit_action_id then return false,"SCOPE_MISMATCH" end
    if r.next_action_id~=args.next_action_id or r.next_target_uid~=args.next_target_uid then return false,"SUCCESSOR_MISMATCH" end
    if args.exit_order_seq and r.exit_order_seq~=args.exit_order_seq then return false,"ORDER_MISMATCH" end
    if not finite(args.now) or args.now<r.frozen_ms then return false,"TIME_INVALID" end
    if finite(args.max_age_ms) and args.max_age_ms>=0 and args.now-r.frozen_ms>args.max_age_ms then return false,"STALE" end
    return true,"OK"
end
function H.contains(r,entity) return type(r)=="table" and type(r.body_entities)=="table" and r.body_entities[entity]==true end
return H
end)()
-- R1_V3_HANDOFF_MODULE_END
-- R1_V3_RECOVERY_MODULE_BEGIN
local R1V3Recovery=(function()
-- R1 V3 unified bounded recovery budget.
-- One budget is shared by every recovery command path for a single Exit action.
local R={VERSION="R1_V3_RECOVERY_1"}
local BSC_HUGE = (type(math.huge)=="number" and math.huge) or 1e300
local function finite(n) return type(n)=="number" and n==n and n<BSC_HUGE and n>-BSC_HUGE end
function R.new(generation,block_id,exit_action_id,max_attempts)
    assert(finite(generation) and generation>=1 and generation%1==0,"invalid generation")
    assert(type(block_id)=="string" and block_id~="","invalid block id")
    assert(finite(exit_action_id) and exit_action_id>=1 and exit_action_id%1==0,"invalid exit action")
    assert(finite(max_attempts) and max_attempts>=0 and max_attempts%1==0,"invalid recovery limit")
    return {generation=generation,block_id=block_id,exit_action_id=exit_action_id,max_attempts=max_attempts,
        used=0,closed=false,exhausted=max_attempts==0,last_ms=nil,by_reason={}}
end
function R.matches(b,generation,block_id,exit_action_id)
    return type(b)=="table" and b.generation==generation and b.block_id==block_id and b.exit_action_id==exit_action_id
end
function R.remaining(b) return math.max(0,(b.max_attempts or 0)-(b.used or 0)) end
function R.consume(b,reason,now)
    assert(type(b)=="table" and type(b.by_reason)=="table","invalid recovery budget")
    assert(type(reason)=="string" and reason~="","invalid recovery reason")
    assert(finite(now) and now>=0,"invalid recovery time")
    if b.closed then return false,"CLOSED",R.remaining(b) end
    if b.last_ms and now<b.last_ms then return false,"TIME_REVERSAL",R.remaining(b) end
    if b.used>=b.max_attempts then b.exhausted=true;return false,"EXHAUSTED",0 end
    b.used=b.used+1;b.last_ms=now;b.by_reason[reason]=(b.by_reason[reason] or 0)+1
    b.exhausted=b.used>=b.max_attempts
    return true,b.exhausted and "CONSUMED_LAST" or "CONSUMED",R.remaining(b)
end
function R.close(b,now,reason)
    assert(type(b)=="table","invalid recovery budget");assert(finite(now) and now>=0,"invalid close time")
    if b.last_ms and now<b.last_ms then return false,"TIME_REVERSAL" end
    b.closed=true;b.closed_ms=now;b.close_reason=reason or "COMPLETE";return true,"CLOSED"
end
return R
end)()
-- R1_V3_RECOVERY_MODULE_END
-- R1_V3_CONTACTS_MODULE_BEGIN
local R1V3Contacts=(function()
-- Evidence V3 contact journal cursor/validation.
-- Pure Lua 5.1: no game API, no orders.
local C={VERSION='R1_V3_CONTACT_CURSOR_1'}
local U64_MAX='18446744073709551615'
local function u64(s)
    return type(s)=='string' and #s>0 and #s<=20 and not s:find('[^0-9]')
        and (#s==1 or s:sub(1,1)~='0') and (#s<20 or s<=U64_MAX)
end
local function cmp(a,b)
    if #a~=#b then return #a<#b and -1 or 1 end
    if a==b then return 0 end
    return a<b and -1 or 1
end
local function uid(s)
    return type(s)=='string' and #s>0 and #s<=10 and not s:find('[^0-9]')
        and (#s==1 or s:sub(1,1)~='0') and (#s<10 or s<='4294967295')
end
local function entity(s) return u64(s) end
local BSC_HUGE = (type(math.huge)=="number" and math.huge) or 1e300
local function finite(n) return type(n)=='number' and n==n and n<BSC_HUGE and n>-BSC_HUGE end
function C.new() return {after='0',last_tick=nil,total=0,gaps=0} end
local function valid_event(e)
    if type(e)~='table' or not u64(e.serial) or not u64(e.tick_ms) or not uid(e.uid_a) or not uid(e.uid_b)
        or not entity(e.entity_a) or not entity(e.entity_b) or e.uid_a==e.uid_b or e.entity_a==e.entity_b then return false end
    if type(e.active_a)~='boolean' or type(e.active_b)~='boolean' then return false end
    if e.active_a and not u64(e.active_engine_seq_a) then return false end
    if e.active_b and not u64(e.active_engine_seq_b) then return false end
    return true
end
function C.consume(c,events,meta)
    assert(type(c)=='table' and u64(c.after),'invalid cursor')
    if type(events)~='table' or type(meta)~='table' then return nil,'PAGE_INVALID' end
    if meta.gap==true or meta.complete~=true then c.gaps=(c.gaps or 0)+1;return nil,'JOURNAL_GAP' end
    if not u64(meta.next_after) then return nil,'NEXT_AFTER_INVALID' end
    local out,prev={},c.after
    for i=1,#events do
        local e=events[i]
        if not valid_event(e) then return nil,'EVENT_INVALID' end
        if cmp(e.serial,prev)<=0 then return nil,'SERIAL_NOT_STRICT' end
        if c.last_tick and cmp(e.tick_ms,c.last_tick)<0 then return nil,'TICK_REVERSED' end
        out[#out+1]=e;prev=e.serial;c.last_tick=e.tick_ms
    end
    if #out>0 and cmp(meta.next_after,out[#out].serial)<0 then return nil,'CURSOR_BEHIND_EVENTS' end
    if cmp(meta.next_after,c.after)<0 then return nil,'CURSOR_REVERSED' end
    c.after=meta.next_after;c.total=(c.total or 0)+#out
    return out,'OK'
end
function C.match_for_attack(e,own_uid,target_uid,attack_seq,cohort)
    if not valid_event(e) or not uid(own_uid) or not uid(target_uid) or not u64(attack_seq) then return false end
    local own_entity,other_uid,active,seq
    if e.uid_a==own_uid then own_entity=e.entity_a;other_uid=e.uid_b;active=e.active_a;seq=e.active_engine_seq_a
    elseif e.uid_b==own_uid then own_entity=e.entity_b;other_uid=e.uid_a;active=e.active_b;seq=e.active_engine_seq_b
    else return false end
    return other_uid==target_uid and active==true and seq==attack_seq and type(cohort)=='table' and cohort[own_entity]==true
end
return C
end)()
-- R1_V3_CONTACTS_MODULE_END
-- FEG1_MODULE_BEGIN
local FEG = (function()
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
local BSC_HUGE = (type(math.huge)=="number" and math.huge) or 1e300
local function finite(n) return type(n)=="number" and n==n and n<BSC_HUGE and n>-BSC_HUGE end
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
end)()
-- FEG1_MODULE_END
local CFG={evidence_max_age_ms=500,evidence_wait_ms=5000,route_resolution_ms=2000,
    route_debt_stall_ms=8000,route_debt_progress_epsilon_m=0.05,route_debt_trend_window_ms=3000,
    route_debt_trend_required_m=0.50,route_debt_close_grace_m=3.0,route_debt_path_grace_m=1.5,
    route_debt_soft_handoff_grace_m=1.5,
    execution_stall_notice_ms=10000,attack_reassert_stall_ms=3000,attack_reassert_interval_ms=5000,attack_reassert_max=2,
    poll_ms=100,page_size=64,max_pages=16,ack_timeout_ms=5000,
    progress_gate=0.20,angle_straight=30,angle_uturn=45,speed_cap=10,speed_seconds=0.50,
    formation_straight=0.60,formation_uturn=1.00,lead_floor=12,lead_cap=50,
    execution_straight=0.70,execution_uturn=1.00,proximity=6,stall_distance=12,
    stall_speed=1.50,brake_extra=4,attack_distance=8,attack_stall_distance=12,
    cancel_observe_ms=5000,max_actions=256,max_inflight=32,
    -- Completion and handoff are separate. Completion records that a Move's route
    -- obligation has actually been satisfied; handoff asks whether changing orders
    -- now would preserve that obligation. No global 6m/10m protect-leg gate remains.
    move_reach_floor_m=1.5,move_reach_cap_m=12,move_reach_width_factor=0.25,move_reach_short_fraction=0.20,
    move_idle_finish_progress=0.50,move_idle_finish_leg_fraction=0.40,move_idle_finish_base_m=14,move_idle_finish_width_factor=0.15,
    move_idle_finish_cap_m=20,move_idle_finish_confirm_ms=700,move_idle_finish_drift_m=1.5,
    route_cut_floor_m=3,route_cut_cap_m=12,route_cut_width_factor=0.25,route_short_fraction=0.12,route_cut_safety_ratio=0.75,
    -- SC1: Move->Move waypoints are navigation guidance, not mandatory stop points.
    -- The legacy chord test remains the first/strict path. If it vetoes a genuine corner,
    -- a bounded speed/formation/turn lookahead may enter a steering corridor.
    route_corner_min_lookahead_m=8,route_corner_max_lookahead_m=45,
    route_corner_speed_seconds=2.0,route_corner_width_factor=0.35,
    route_corner_turn_base=0.70,route_corner_turn_extra=0.60,
    route_corner_current_leg_fraction=0.45,route_corner_next_leg_fraction=0.45,
    -- SC2 EARLY A/B: keep SC1's bounded lookahead, but also allow Move->Move handoff
    -- as soon as the existing predictive threshold is reached on normal-length legs.
    -- The 0.75 adjacent-leg cap preserves short-zig-zag safety while deliberately
    -- moving the handoff much earlier than SC1 for long/medium routes.
    route_corner_early_leg_fraction=0.75,
    -- SC4 STALL ESCAPE: if CA has already stopped making meaningful progress just
    -- outside the bounded turn corridor, allow a pure Move->Move steering handoff
    -- within a small adjacent-leg-capped margin. This does not widen normal cruising
    -- handoff geometry and never applies to Move->Attack.
    route_corner_stall_escape_ms=300,route_corner_stall_escape_extra_m=6.0,
    route_corner_stall_escape_current_leg_fraction=0.10,route_corner_stall_escape_next_leg_fraction=0.25,
    route_move_min_progress=0.25,route_attack_min_progress=0.60,route_attack_turn_progress=0.25,
    exit_min_displacement_m=8,exit_clear_confirm_ms=700,exit_global_contact_m=2,exit_contact_scan_ms=300,
    exit_sticky_clear_confirm_ms=1500,exit_reassert_stall_ms=1200,exit_contact_fallback_stall_ms=900,exit_reengage_stall_ms=2000,
    exit_contact_stall_ms=1800,exit_contact_progress_m=1.0,exit_reassert_interval_ms=1500,exit_reassert_max=4,target_end_confirm_ms=700,
    -- Legacy Attack geometry parameters retained for telemetry. R1 route evidence controls permission.
    attack_lead_straight=20,attack_lead_uturn=28,attack_speed_seconds=0.50,
    attack_speed_cap=5,attack_width_factor=0.10,attack_width_cap=4,
    attack_lead_cap=35,attack_execution_cap=0.45,attack_min_samples=2,
    -- Brake estimates are telemetry only in this R1 candidate. No claim of
    -- unverified braking preemption; a satisfied Move may hand off while moving.
    attack_brake_preempt_ratio=0.72,attack_brake_preempt_drop=1.50,attack_brake_preempt_min_speed=3.0,
    attack_brake_preempt_min_samples=3,attack_brake_preempt_extra=12,attack_brake_preempt_cap=45,
    attack_brake_preempt_execution_cap=0.65,
    -- Narrow U-turn cap relaxation, not an increase of the normal 35m cap.
    attack_uturn_start=135,attack_uturn_execution_cap=0.70,
    attack_poll_lead_cap=6,attack_poll_horizon_ms=750,
    attack_hold_ms=3000,attack_observation_gap_ms=1000,v3_contact_fresh_ms=300,v3_contact_mapping_radius_m=4,
    -- Diagnostics only: long approach never authorizes/cancels behaviour.
    attack_long_wait_notice_ms=30000,attack_long_wait_repeat_ms=30000,
    cold_idle_max_age_ms=1000,restart_idle_confirm_ms=700,restart_idle_max_age_ms=1500,restart_idle_drift_m=1.5,
    collection_scan_ms=1000,unknown_refresh_ms=10000,exit_trace_ms=60000,exit_trace_interval_ms=1000}
local bmgr,bridge
local S={prepared=false,started=false,failed=false,closed=false,epoch=nil,cursor="0",pending_by_uid={},pending_by_issue={},pending_count=0,last_capture_errors="0",
    states={},targets={},cancel_checks={},timer="TH_P1E_P2B_"..RUN_ID,last_model=nil,last_collection_scan=-1000000,
    unknown_retry={},collection_scans=0,dynamic_units=0,last_heartbeat=-1000000,order_count=0,dispatch_count=0,route_passes=0,cancel_passes=0,
    evidence_v3_caps={},v3_contact_cursor=R1V3Contacts.new(),v3_contact_log={},evidence_bind_retry={}}

-- Telemetry is strictly read-only. There is no behavioural test window.
local ATTACK_TRACE={}
local EXIT_TRACE={}

local Core={}
function Core.observe_attack(st,now)
    if not DEBUG_TELEMETRY then ATTACK_TRACE[st.uid]=nil; return end
    local t=ATTACK_TRACE[st.uid]
    if not t then return end
    if t.gen~=st.gen or now-t.started>2500 then ATTACK_TRACE[st.uid]=nil; return end
    if t.last and now-t.last<250 then return end
    t.last=now
    if not st.pos then return end
    if DEBUG_TELEMETRY then dlog("ATTACK_POST_SAMPLE uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
        " model_ms="..string.format("%.0f",now).." elapsed_ms="..string.format("%.0f",now-t.started)..
        " accepted_terminal="..tostring(st.terminal).." speed="..string.format("%.6f",median(st.speeds) or 0)..
        " instant_speed="..string.format("%.6f",st.speeds[#st.speeds] or 0)..
        " x="..string.format("%.6f",st.pos.x).." z="..string.format("%.6f",st.pos.z)) end
end

local function fail(reason)
    if S.failed or S.closed then return end
    S.failed=true
    log("CONTROLLER_FAIL reason="..clean(reason).." cursor="..S.cursor)
    if bridge then pcall(bridge.arm_verified_issue,false) end
    for _,st in pairs(S.states) do st.plan=nil; st.actions={}; st.owned=false end
end
local function checked(fn)
    return function()
        if S.failed or S.closed then return end
        local ok,e=xpcall(fn,trace); if not ok then fail(e) end
    end
end
local cancel,release -- forward declarations for recoverable Bridge soft-yield
local function clock()
    local t=bmgr:time_elapsed_ms()
    if not finite(t) or t<0 then error("MODEL_TIME_UNAVAILABLE") end
    return t
end
local function resync_after_recoverable(st,now,reason)
    cancel(st,"BRIDGE_RECOVERABLE_CAPTURE_"..clean(reason),now,false)
    release(st)
    st.blocked=false
    st.require_replace=true -- queued APPEND alone cannot safely recreate a lost predecessor
    local ok,rev,err=pcall(bridge.get_unit_revision,st.uid)
    if ok and id(rev) then
        st.revision=rev; st.recover_revision=rev
        if DEBUG_TELEMETRY then dlog("BRIDGE_RECOVERABLE_RESYNC uid="..st.uid.." revision="..rev.." policy=WAIT_FOR_FRESH_REPLACE") end
        return true
    end
    if ok and rev==nil and err=="MISSING" then
        st.revision=nil; st.recover_revision=nil
        if DEBUG_TELEMETRY then dlog("BRIDGE_RECOVERABLE_RESYNC uid="..st.uid.." revision=MISSING policy=WAIT_FOR_FRESH_REPLACE") end
        return true
    end
    fail("RECOVERABLE_RESYNC_uid="..st.uid.."_"..clean(err or rev)); return false
end
local function status()
    local ok,s,e=pcall(bridge.get_status)
    if not ok or type(s)~="table" then fail("STATUS_"..clean(e or s)); return nil end
    if not s.recording or s.epoch~=S.epoch or s.fatal_errors~="0" or s.gate_fault~="OK" then
        fail("BRIDGE_FATAL_STATE epoch="..clean(s.epoch).." fatal="..clean(s.fatal_errors).." capture="..clean(s.capture_errors)..
            " gate="..clean(s.gate_fault).." last="..clean(s.last_fatal_error).." path="..clean(s.last_path_stage)); return nil
    end
    if s.capture_errors~=S.last_capture_errors then
        local old=tonumber(S.last_capture_errors) or 0
        local cur=tonumber(s.capture_errors) or old
        local delta=cur-old
        local ru=id(s.last_recoverable_uid) and s.last_recoverable_uid or nil
        log("BRIDGE_RECOVERABLE_CAPTURE count="..clean(s.capture_errors).." delta="..tostring(delta)..
            " reason="..clean(s.last_recoverable_error).." uid="..clean(ru or "0").." action="..((delta==1 and ru and S.states[ru]) and "YIELD_UNIT" or "YIELD_ALL"))
        if S.pending_count>0 then fail("RECOVERABLE_CAPTURE_DURING_OWNED_PENDING"); return nil end
        local now=clock()
        if delta==1 and ru and S.states[ru] then
            if not resync_after_recoverable(S.states[ru],now,s.last_recoverable_error) then return nil end
        else
            for _,st in pairs(S.states) do
                if st.plan or st.owned or #st.actions>0 or st.revision then
                    if not resync_after_recoverable(st,now,"GLOBAL_YIELD_"..clean(s.last_recoverable_error)) then return nil end
                end
            end
        end
        S.last_capture_errors=s.capture_errors
    end
    return s
end
function Core.arm(kind)
    local s=status(); if not s then return false end
    local kind_ready=(kind=="MOVE" and s.accepted_move_seen==true) or (kind=="ATTACK" and s.accepted_attack_seen==true)
    if not kind_ready then return false end
    if s.native_issue_authorized~=true then fail("NATIVE_ISSUE_NOT_AUTHORIZED"); return false end
    if s.v3_issue_armed==true then return true end
    if s.v3_issue_calibration_ready~=true then return false end
    local ok,r,e=pcall(bridge.arm_verified_issue,true)
    if not ok or r~=true then fail("ARM_"..clean(e or r)); return false end
    s=status()
    if not s or s.v3_issue_armed~=true then fail("ARM_NOT_CONFIRMED"); return false end
    if DEBUG_TELEMETRY then dlog("BRIDGE_ARMED kind="..kind.." v3_runtime_verified=true production_exact_source=false accepted_move="..tostring(s.accepted_move_seen==true).." accepted_attack="..tostring(s.accepted_attack_seen==true)) end
    return true
end
release=function(st) pcall(function() st.uc:release_control() end) end
local function api_bool(unit,name)
    local ok,v=pcall(function() return unit[name](unit) end)
    if ok and type(v)=="boolean" then return v end
    return nil
end
local function unit_distance_to(unit,target)
    local ok,d=pcall(function() return unit:unit_distance(target) end)
    if ok and finite(d) and d>=0 then return d end
    return nil
end
local function num_or_nil(n)
    return finite(n) and string.format("%.6f",n) or "nil"
end
-- This is a BEFORE-input observation, not a post-command "not moving" guess.
-- Only a clean, pre-Deployed load, unseen/zero native revision and no prior local
-- Journal record can establish it. Any first record consumes this privilege.
-- No certificate is ever created for an unknown running or cancelled queue.
local function cold_native_state(st)
    local ok,rev,err=pcall(bridge.get_unit_revision,st.uid)
    -- BridgeHost::unit_snapshot returns Error::Missing before track(uid,root).
    -- This exact contract is NOT an arbitrary nil/error-to-zero conversion.
    if ok and rev==nil and err=="MISSING" then return "UNSEEN","MISSING" end
    if ok and rev=="0" then return "REVISION_ZERO","0" end
    return nil,nil
end
local function observe_cold_idle(st,now)
    if S.late_start or st.cold_seen or st.blocked or st.owned or st.plan or #st.actions>0 then
        st.cold_idle=nil; return
    end
    local native_state,rev=cold_native_state(st)
    local idle=api_bool(st.unit,"is_idle")
    local moving=api_bool(st.unit,"is_moving")
    local melee=api_bool(st.unit,"is_in_melee")
    local tok,target=pcall(function() return st.unit:current_target() end)
    local p=point(st.unit)
    local after,after_rev=cold_native_state(st)
    local good=native_state~=nil and after==native_state and after_rev==rev and idle==true and moving==false
        and melee==false and tok and target==nil and p~=nil
    if good then
        st.cold_note=nil
        if not st.cold_idle or st.cold_idle.native_state~=native_state then
            if DEBUG_TELEMETRY then dlog("COLD_IDLE_READY uid="..st.uid.." rev="..rev.." native_state="..native_state.." model_ms="..string.format("%.0f",now)..
                " idle=true moving=false melee=false target=nil scope=FIRST_LOCAL_ORDER_ONLY") end
        end
        st.cold_idle={revision=rev,native_state=native_state,ms=now,pos=copy(p)}
    else
        if st.cold_idle then if DEBUG_TELEMETRY then dlog("COLD_IDLE_REVOKED uid="..st.uid.." model_ms="..string.format("%.0f",now)) end end
        st.cold_idle=nil
        local note=clean(native_state)..":"..clean(idle)..":"..clean(moving)..":"..clean(melee)..":"..tostring(tok)..":"..clean(target and uid(target))
        if st.cold_note~=note then
            st.cold_note=note
            if DEBUG_TELEMETRY then dlog("COLD_IDLE_UNAVAILABLE uid="..st.uid.." native_state="..clean(native_state)..
                " idle="..clean(idle).." moving="..clean(moving).." melee="..clean(melee)..
                " target_api_ok="..tostring(tok).." target="..clean(target and uid(target))..
                " model_ms="..string.format("%.0f",now).." policy=NO_GUESSED_QUEUE_SEED") end
        end
    end
end
-- After the one-time startup certificate is consumed, a unit may still need a
-- safe queued-only restart after an explicit queue reset. A sustained clean idle
-- state can also refresh that restart evidence, but only when BSC has no plan and
-- the Bridge revision remains stable across the observation. This never repairs a
-- capture gap (require_replace stays fail-closed).
function Core.observe_restart_idle(st,now)
    if not st.cold_seen or st.plan or #st.actions>0 or st.owned or st.blocked or st.require_replace or S.pending_by_uid[st.uid] then
        st.restart_idle_candidate=nil;st.restart_idle_cert=nil;return
    end
    local ok1,rev1,err1=pcall(bridge.get_unit_revision,st.uid)
    if not ok1 or not id(rev1) then st.restart_idle_candidate=nil;st.restart_idle_cert=nil;return end
    local idle=api_bool(st.unit,"is_idle")
    local moving=api_bool(st.unit,"is_moving")
    local melee=api_bool(st.unit,"is_in_melee")
    local tok,target=pcall(function() return st.unit:current_target() end)
    local pos=point(st.unit)
    local ok2,rev2=pcall(bridge.get_unit_revision,st.uid)
    local clean_idle=idle==true and moving==false and melee==false and tok and target==nil and pos~=nil and ok2 and rev2==rev1
    if not clean_idle then st.restart_idle_candidate=nil;st.restart_idle_cert=nil;return end
    local c=st.restart_idle_candidate
    if not c or c.revision~=rev1 or now-c.last_ms>CFG.attack_observation_gap_ms or dist(c.pos,pos)>CFG.restart_idle_drift_m then
        st.restart_idle_candidate={revision=rev1,since=now,last_ms=now,pos=copy(pos)};st.restart_idle_cert=nil;return
    end
    c.last_ms=now;c.pos=copy(pos)
    if now-c.since>=CFG.restart_idle_confirm_ms then
        local fresh=not st.restart_idle_cert or st.restart_idle_cert.revision~=rev1
        st.restart_idle_cert={revision=rev1,ms=now,pos=copy(pos),reason="STABLE_CLEAN_IDLE"}
        if fresh then
            if DEBUG_TELEMETRY then dlog("QUEUE_IDLE_CERT_READY uid="..st.uid.." rev="..rev1.." model_ms="..now..
                " confirm_ms="..string.format("%.0f",now-c.since).." policy=QUEUED_RESTART_ONLY") end
        end
    end
end

function Core.observe_exit(st,now)
    if not DEBUG_TELEMETRY then EXIT_TRACE[st.uid]=nil; return end
    local t=EXIT_TRACE[st.uid]
    if not t then return end
    if t.gen~=st.gen or not st.plan or st.blocked or not st.plan[st.idx]
        or st.plan[st.idx].type~="MOVE" or st.plan[st.idx].block_kind~="EXIT_ROUTE"
        or now-t.started>CFG.exit_trace_ms then
        EXIT_TRACE[st.uid]=nil; return
    end
    if t.last and now-t.last<CFG.exit_trace_interval_ms then return end
    t.last=now
    local melee=api_bool(st.unit,"is_in_melee")
    local ok,target=pcall(function() return st.unit:current_target() end)
    local observed=(ok and target) and uid(target) or nil
    local pos=point(st.unit)
    local visible=t.target and api_bool(t.target,"is_valid_target")==true
    local target_pos=visible and point(t.target)
    local remaining=pos and dist(pos,t.dest) or nil
    local separation=(pos and target_pos) and dist(pos,target_pos) or nil
    local bbox=visible and unit_distance_to(st.unit,t.target) or nil
    if DEBUG_TELEMETRY then dlog("P2_EXIT_OBSERVED uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
        " attack_issue="..t.attack_issue.." model_ms="..string.format("%.0f",now)..
        " elapsed_ms="..string.format("%.0f",now-t.started).." melee="..clean(melee)..
        " observed="..clean(observed).." target_api_ok="..tostring(ok)..
        " remaining_C="..num_or_nil(remaining).." dist="..num_or_nil(separation)..
        " bbox_distance="..num_or_nil(bbox).." speed="..num_or_nil(median(st.speeds))..
        " instant_speed="..num_or_nil(st.speeds[#st.speeds])..
        " unit_x="..num_or_nil(pos and pos.x).." unit_z="..num_or_nil(pos and pos.z)..
        " policy=READ_ONLY_NO_REISSUE") end
    if remaining and remaining<=6 then
        if DEBUG_TELEMETRY then dlog("P2_EXIT_REACHED_PN uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
            " attack_issue="..t.attack_issue.." model_ms="..string.format("%.0f",now)..
            " elapsed_ms="..string.format("%.0f",now-t.started).." remaining_C="..num_or_nil(remaining)..
            " dist="..num_or_nil(separation).." bbox_distance="..num_or_nil(bbox)..
            " melee="..clean(melee).." observed="..clean(observed)..
            " speed="..num_or_nil(median(st.speeds)).." policy=READ_ONLY_COMPLETION_OBSERVATION") end
        EXIT_TRACE[st.uid]=nil
    end
end
-- Only Attack history queries these hints. Missing widths use the fixed default.
local function feg_width(unit)
    local ok,w=pcall(function() return unit:ordered_width() end)
    return ok and finite(w) and w>=0 and w<=500 and w or nil
end
function Core.feg_log(st,t,r,now,credited,legacy)
    if not DEBUG_TELEMETRY then return end
    if not r.just_opened and not r.reset_hold and now-(t.feg_log_ms or -1000000)<1000 then return end
    t.feg_log_ms=now;t.feg_log_phase=r.phase;t.feg_log_reason=r.reason
    if DEBUG_TELEMETRY then log("FEG_SAMPLE uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." idx="..st.idx..
        " model_ms="..string.format("%.0f",now).." episode="..r.episode.." phase="..r.phase.." reason="..r.reason..
        " gate_open="..tostring(r.open).." raw_eligible="..tostring(r.raw_eligible==true).." eligible="..tostring(r.allow)..
        " melee="..tostring(r.melee).." observed="..clean(r.observed_uid).." intended="..t.target_uid..
        " fresh_seen="..tostring(r.fresh_seen).." approach_seen="..tostring(r.approach_seen).." start_near="..tostring(r.start_near)..
        " dist="..num_or_nil(r.distance).." near="..num_or_nil(r.near).." far="..num_or_nil(r.far).." strong_far="..num_or_nil(r.strong_far)..
        " closing="..num_or_nil(r.closing).." relative_speed="..num_or_nil(r.relative_speed)..
        " actor_speed="..num_or_nil(r.actor_speed).." target_speed="..num_or_nil(r.target_speed)..
        " unit_x="..num_or_nil(r.ax).." unit_z="..num_or_nil(r.az).." target_x="..num_or_nil(r.tx).." target_z="..num_or_nil(r.tz)..
        " candidate_ms="..num_or_nil(r.candidate_ms).." credited_ms="..string.format("%.0f",credited)..
        " eligible_ms="..string.format("%.0f",t.eligible_ms).." legacy_eligible_ms="..string.format("%.0f",legacy)..
        " has_tail="..tostring(st.plan[st.idx+1]~=nil).." evidence="..clean(r.evidence)..
        " bbox_distance="..num_or_nil(r.bbox_distance).." target_known="..tostring(r.target_known)..
        " target_alive="..tostring(r.target_alive).." geometry_candidate="..tostring(r.geometry_candidate)..
        " geometry_ms="..num_or_nil(r.geometry_ms).." geometry=UNIT_POSITION_PROXY_NOT_ENTITY_COUNT") end
end
function Core.timed_attack_supported(st,require_legacy_engagement_api)
    -- The P2 timer mode is deliberately ground melee only. Do not silently
    -- reinterpret primary missile fire or flight as melee engagement.
    local ok,ammo=pcall(function() return st.unit:starting_ammo() end)
    if not ok or not finite(ammo) or ammo<0 then return false,"STARTING_AMMO_API_UNAVAILABLE" end
    if ammo>0 then return false,"RANGED_TIMING_UNSUPPORTED" end
    local flying=api_bool(st.unit,"is_currently_flying")
    local artillery=api_bool(st.unit,"is_artillery")
    if flying==nil or artillery==nil then return false,"UNIT_MODE_API_UNAVAILABLE" end
    if flying or artillery then return false,"FLIGHT_ARTILLERY_TIMING_UNSUPPORTED" end
    if require_legacy_engagement_api~=false then
        local melee=api_bool(st.unit,"is_in_melee")
        local tok=pcall(function() return st.unit:current_target() end)
        if melee==nil or not tok then return false,"ENGAGEMENT_API_UNAVAILABLE" end
    end
    return true
end
local function target_viable(a)
    if not a.target then a.target=S.targets[a.target_uid] end
    a.alive_confirmed=false
    if not a.target then return false,"TARGET_UNRESOLVED" end
    if uid(a.target)~=a.target_uid then return false,"TARGET_IDENTITY_INVALID" end
    local valid=api_bool(a.target,"is_valid_target")
    if valid==nil then return false,"TARGET_API_UNAVAILABLE" end
    -- Optional documented count supplies positive death evidence, not invalid-target inference.
    local ok,men=pcall(function() return a.target:number_of_men_alive() end)
    a.alive_confirmed=ok and finite(men) and men>0
    if ok and finite(men) and men==0 then return false,"TARGET_DEAD" end
    if not valid then
        if api_bool(a.target,"is_leaving_battle")==true then return false,"TARGET_LEFT_BATTLE" end
        return false,"TARGET_TEMPORARILY_UNAVAILABLE"
    end
    return true -- routing is still an attack, not permission for a zero-hold exit
end
local function abortable_target_reason(why)
    return why=="TARGET_DEAD" or why=="TARGET_LEFT_BATTLE"
end
local function target_ready(a,now)
    local good,why=target_viable(a)
    if good then a.end_reason=nil;a.end_since=nil;a.end_last=nil;return true end
    if abortable_target_reason(why) then
        if a.end_reason~=why or not a.end_last or now-a.end_last>CFG.attack_observation_gap_ms then
            a.end_reason=why;a.end_since=now
        end
        a.end_last=now
        if now-a.end_since>=CFG.target_end_confirm_ms then return false,why end
        return false,"TARGET_END_CONFIRMING"
    end
    a.end_reason=nil;a.end_since=nil;a.end_last=nil
    return false,why
end
local function target_wait(st,why,now)
    if st.target_wait_reason~=why or now-(st.target_wait_ms or -1000000)>=2000 then
        if DEBUG_TELEMETRY then log("TARGET_WAIT uid="..st.uid.." gen="..st.gen.." reason="..why.." model_ms="..now.." preserved_tail=true") end
        st.target_wait_reason=why;st.target_wait_ms=now
    end
    st.input_gapped=true
end
-- R1: faults are per-action records, NOT st.blocked. Input draining/observations
-- remain live and suffixes are preserved. A safe failure is not semantic completion.
local R1={}
function R1.fault(st,a,code,reason,now)
    if not a then return end
    local rt=a.runtime or {};a.runtime=rt
    -- CENTER-A2 B2 invariant: physical Entity/Frozen evidence is diagnostic only.
    -- No legacy caller is allowed to turn missing body/contact evidence into a
    -- behaviour-level fault. This global guard prevents future/forgotten call sites
    -- from reintroducing the old hard dependency.
    if CENTER_A2_MODE and code=="BLOCKED_EVIDENCE" then
        local key=clean(reason or "EVIDENCE_UNRESOLVED")
        if rt.last_center_evidence_reason~=key or now-(rt.last_center_evidence_ms or -1000000)>=2000 then
            rt.last_center_evidence_reason=key;rt.last_center_evidence_ms=now
            if DEBUG_TELEMETRY then dlog("CENTER_ENTITY_EVIDENCE_TELEMETRY uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
                " reason="..key.." hard_fault=false model_ms="..now) end
        end
        if rt.fault and rt.fault.code=="BLOCKED_EVIDENCE" then rt.fault=nil end
        return
    end
    local severity={BLOCKED_ROUTE=5,BLOCKED_EXECUTION_IDENTITY=4,BLOCKED_EXECUTION=3}
    if rt.fault and (severity[rt.fault.code] or 0)>(severity[code] or 0) then st.phase=rt.fault.code;return end
    if not rt.fault or rt.fault.code~=code or rt.fault.reason~=reason then
        rt.fault={code=code,reason=reason,since=now}
        log("ACTION_FAULT uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " code="..code.." reason="..clean(reason).." model_ms="..now..
            " preserved_tail=true semantic_success=false native_tail_restored=false")
    end
    st.phase=code
end
function R1.clear_fault(st,a,now)
    local rt=a and a.runtime
    if rt and rt.fault then
        if DEBUG_TELEMETRY then log("ACTION_FAULT_CLEARED uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " previous="..rt.fault.code.." model_ms="..now) end
        rt.fault=nil
    end
end
-- Evidence V2: exact native order identity is independent from physical snapshots.
-- Native exports facts only; all R1 verdicts are derived here.
local function array_set(t)
    local out={};if type(t)~="table" then return out end
    for i=1,#t do if type(t[i])=="string" and #t[i]>0 then out[t[i]]=true end end
    return out
end
local function copy_set(t) local out={};for k,v in pairs(t or {}) do if v then out[k]=true end end;return out end
local function count_set(t) local n=0;for _ in pairs(t or {}) do n=n+1 end;return n end
-- Authoritative execution identity adapter.
-- V3 is the production source. V2 is a compatibility fallback only when V3
-- execution identity is unavailable; a live V3 provider is never mixed with V2.
local function action_execution_identity(a)
    if not a then return nil,nil,nil end
    local rt=a.runtime or {}
    local seq=rt.accepted_receipt and rt.accepted_seq or a.seq
    if rt.accepted_receipt and not rt.accepted_seq then return nil,nil,nil,"ACCEPTED_WITHOUT_NATIVE_SEQUENCE" end
    local receipt=rt.accepted_receipt or a.serial
    local lifetime=rt.accepted_lifetime or a.unit_lifetime
    if not id(seq) or not id(receipt) or not id(lifetime) then return nil,nil,nil,"ACTION_IDENTITY_INCOMPLETE" end
    return seq,receipt,lifetime,"OK"
end
local function normalize_active_execution(st,e,provider,schema)
    if type(e)~="table" or e.schema~=schema or e.epoch~=S.epoch or e.unit_uid~=st.uid or e.complete~=true then
        return nil,provider.."_ORDER_IDENTITY_INVALID"
    end
    local x={provider=provider,schema=schema,active=e.active==true,known=e.known==true,
        epoch=e.epoch,unit_uid=e.unit_uid,unit_lifetime=e.unit_lifetime,
        active_engine_seq=e.active_engine_seq,accepted_journal_serial=e.accepted_journal_serial,
        kind=e.kind,target_uid=e.target_uid,dest_x=e.dest_x,dest_z=e.dest_z,raw=e}
    if not x.active then return x,"INACTIVE" end
    if not id(x.active_engine_seq) or (x.kind~="MOVE" and x.kind~="ATTACK") then
        return nil,provider.."_ACTIVE_IDENTITY_INVALID"
    end
    if x.known and (not id(x.accepted_journal_serial) or not id(x.unit_lifetime)) then
        return nil,provider.."_KNOWN_IDENTITY_INVALID"
    end
    return x,"OK"
end
function R1.read_active_execution(st)
    local v3=S.evidence_v3_caps or {}
    if v3.execution_identity==true then
        if type(bridge.read_active_order_identity_v3)~="function" then return nil,"V3_PROVIDER_UNAVAILABLE" end
        local ok,e,reason=pcall(bridge.read_active_order_identity_v3,st.uid)
        if not ok then return nil,"V3_PROVIDER_EXCEPTION" end
        if type(e)~="table" then return nil,reason or "V3_ORDER_IDENTITY_UNAVAILABLE" end
        return normalize_active_execution(st,e,"V3",3)
    end
    local v2=S.evidence_caps or {}
    if v2.execution_identity==true then
        if type(bridge.read_active_order_identity_v2)~="function" then return nil,"V2_PROVIDER_UNAVAILABLE" end
        local ok,e,reason=pcall(bridge.read_active_order_identity_v2,st.uid)
        if not ok then return nil,"V2_PROVIDER_EXCEPTION" end
        if type(e)~="table" then return nil,reason or "V2_ORDER_IDENTITY_UNAVAILABLE" end
        return normalize_active_execution(st,e,"V2",2)
    end
    return nil,"EXECUTION_IDENTITY_PROVIDER_UNAVAILABLE"
end
function R1.execution_matches_action(e,a)
    if type(e)~="table" or e.active~=true then return false,"EXECUTION_INACTIVE" end
    if e.known~=true then return false,"EXECUTION_NOT_MAPPED" end
    if not a or (a.type~="MOVE" and a.type~="ATTACK") then return false,"ACTION_UNSUPPORTED" end
    if e.kind~=a.type then return false,"EXECUTION_KIND_MISMATCH" end
    local seq,receipt,lifetime,why=action_execution_identity(a)
    if not seq then return false,why end
    if e.accepted_journal_serial~=receipt or e.unit_lifetime~=lifetime then return false,"EXECUTION_RECEIPT_OR_LIFETIME_MISMATCH" end
    if e.active_engine_seq~=seq then return false,"EXECUTION_SEQUENCE_MISMATCH" end
    if a.type=="ATTACK" and e.target_uid~=a.target_uid then return false,"EXECUTION_TARGET_MISMATCH" end
    if a.type=="MOVE" then
        if not a.pos or not finite(e.dest_x) or not finite(e.dest_z)
            or math.abs(e.dest_x-a.pos.x)>0.05 or math.abs(e.dest_z-a.pos.z)>0.05 then
            return false,"EXECUTION_DESTINATION_MISMATCH"
        end
    end
    return true,"OK"
end
function R1.order_evidence(st,a,now)
    local e,why=R1.read_active_execution(st)
    if not e then return nil,why end
    local match,mwhy=R1.execution_matches_action(e,a)
    if not match then return nil,mwhy end
    return e,"OK"
end
-- Backward internal name retained for non-reconciliation callers/tests. It is now
-- V3-first and can only fall back to V2 when V3 execution identity is unavailable.
R1.evidence=R1.order_evidence

function Core.valid_entity_snapshot(e,now)
    if type(e)~="table" or e.schema~=2 or e.complete~=true or not finite(e.model_ms)
        or e.model_ms>now or now-e.model_ms>CFG.evidence_max_age_ms then return false end
    if not finite(e.slot_count) or not finite(e.live_count) or e.slot_count<1 or e.slot_count%1~=0
        or e.live_count<0 or e.live_count%1~=0 or e.live_count>e.slot_count then return false end
    for _,k in ipairs({"dead_count","local_state0_count","local_state1_count","local_state2_count","local_state3_count",
        "melee_locked_count","movement_idle_count","movement_pathing_count","movement_halted_count"}) do
        if not finite(e[k]) or e[k]<0 or e[k]%1~=0 then return false end
    end
    if e.live_count>0 and (not finite(e.median_x) or not finite(e.median_z)) then return false end
    if e.motion_complete==true and (not finite(e.previous_model_ms) or not finite(e.median_vx) or not finite(e.median_vz)
        or not finite(e.motion_matched_count) or e.motion_matched_count<1) then return false end
    if type(e.melee_locked_entities)~="table" or #e.melee_locked_entities~=e.melee_locked_count then return false end
    return true
end
function Core.valid_combat_snapshot(e)
    if type(e)~="table" or e.schema~=2 or e.complete~=true then return false end
    for _,k in ipairs({"coarse_contact_count","group_count","active_melee_group_count"}) do
        if not finite(e[k]) or e[k]<0 or e[k]%1~=0 then return false end
    end
    if type(e.active_target_uids)~="table" then return false end
    for i=1,#e.active_target_uids do if not id(e.active_target_uids[i]) then return false end end
    return true
end
function R1.refresh_physical(st,now)
    if not S.evidence_caps then return end
    if S.evidence_caps.entity_snapshot and type(bridge.read_entity_snapshot_v2)=="function" then
        local ok,e,reason=pcall(bridge.read_entity_snapshot_v2,st.uid,now)
        if ok and Core.valid_entity_snapshot(e,now) then
            e.locked_set=array_set(e.melee_locked_entities);st.r1_entity=e;st.r1_entity_reason="OK"
        else
            st.r1_entity=nil;st.r1_entity_reason=(ok and ((type(e)=="table" and e.probe_reason) or reason) or "PROVIDER_EXCEPTION") or "ENTITY_SNAPSHOT_INVALID"
        end
    end
    if S.evidence_caps.combat_groups and type(bridge.read_combat_groups_v2)=="function" then
        local ok,e,reason=pcall(bridge.read_combat_groups_v2,st.uid)
        if ok and Core.valid_combat_snapshot(e) then
            e.target_set=array_set(e.active_target_uids);st.r1_combat=e;st.r1_combat_reason="OK"
        else
            st.r1_combat=nil;st.r1_combat_reason=(ok and ((type(e)=="table" and e.probe_reason) or reason) or "PROVIDER_EXCEPTION") or "COMBAT_SNAPSHOT_INVALID"
        end
    end
end
function Core.valid_entity_snapshot_v3(e,now)
    if type(e)~="table" or e.schema~=3 or e.complete~=true or not finite(e.model_ms)
        or e.model_ms>now or now-e.model_ms>CFG.evidence_max_age_ms or type(e.entities)~="table" then return false end
    if not finite(e.live_count) or e.live_count<0 or e.live_count%1~=0 or #e.entities~=e.live_count then return false end
    for i=1,#e.entities do
        local v=e.entities[i]
        if type(v)~="table" or type(v.entity)~="string" or v.entity=="" or not finite(v.x) or not finite(v.z)
            or not finite(v.movement_state) or v.movement_state%1~=0 then return false end
        if v.motion_complete==true and (not finite(v.vx) or not finite(v.vz)) then return false end
    end
    return true
end
function R1.v3_refresh_physical(st,now)
    local caps=S.evidence_v3_caps or {}
    if caps.entity_snapshot~=true or type(bridge.read_entity_snapshot_v3)~="function" then st.r1_v3_entity=nil;st.r1_v3_entity_reason="CAPABILITY_UNAVAILABLE";return end
    local ok,e,provider_reason=pcall(bridge.read_entity_snapshot_v3,st.uid,now)
    if ok and Core.valid_entity_snapshot_v3(e,now) then
        st.r1_v3_entity=e;st.r1_v3_entity_reason="OK"
    else
        st.r1_v3_entity=nil
        local why=ok and ((type(e)=="table" and e.probe_reason) or provider_reason or "SNAPSHOT_INVALID") or "PROVIDER_EXCEPTION"
        st.r1_v3_entity_reason=why
        if DEBUG_TELEMETRY and (st.r1_v3_entity_log_reason~=why or now-(st.r1_v3_entity_log_ms or -1000000)>=5000) then
            st.r1_v3_entity_log_reason=why;st.r1_v3_entity_log_ms=now
            if DEBUG_TELEMETRY then dlog("V3_ENTITY_SNAPSHOT_MISS uid="..st.uid.." reason="..clean(why).." model_ms="..now.." root_source=VALIDATED_LUA_USERDATA") end
        end
    end
end
function R1.v3_order_for(st,a)
    local caps=S.evidence_v3_caps or {}
    if caps.execution_identity~=true then return nil,"CAPABILITY_UNAVAILABLE" end
    local e,why=R1.read_active_execution(st)
    if not e or e.provider~="V3" then return nil,why or "ORDER_UNAVAILABLE" end
    local match,mwhy=R1.execution_matches_action(e,a)
    if not match then return nil,mwhy end
    return e,"OK"
end
function R1.v3_handoff_scope(st,a,b,now)
    local nexta=st.plan and st.plan[st.idx+1]
    local h=b and b.v3_pre_handoff_candidate
    if not h or not nexta or nexta.type~="ATTACK" then return nil,"PRE_HANDOFF_MISSING" end
    -- The frozen cohort is a generation/block identity, not a short-lived sensor sample.
    -- It remains valid for this Exit -> Attack handoff until the generation is replaced.
    local ok,why=R1V3Handoff.valid(h,{generation=st.gen,block_id=a.block_id,exit_action_id=a.action_id,
        next_action_id=nexta.action_id,next_target_uid=nexta.target_uid,now=now})
    if not ok then return nil,"PRE_HANDOFF_"..clean(why) end
    return h,"OK"
end
function R1.v3_update_exit_candidate(st,now)
    if not st.plan then return end
    local a=st.plan[st.idx];if not a or a.block_kind~="EXIT_ROUTE" or a.type~="MOVE" then return end
    local b=st.block_state and st.block_state[a.block_id];if not b then return end
    local e=st.r1_v3_entity
    local order=R1.v3_order_for(st,a)
    -- Never create or enlarge the body cohort without exact proof that this Exit MOVE
    -- is the currently executing engine order. After that proof disappears, only the
    -- already-frozen record may be reused.
    if e and order and not b.v3_pre_handoff_candidate then
        local c=b.v3_body_cohort
        if not c or c.generation~=st.gen or c.block_id~=a.block_id or c.exit_action_id~=a.action_id then
            c=R1V3Handoff.new_cohort(st.gen,a.block_id,a.action_id);b.v3_body_cohort=c
        end
        R1V3Handoff.cohort_update_motion(c,e,a.pos,e.model_ms)
    end
    local nexta=st.plan[st.idx+1]
    if not e or not order or not nexta or nexta.type~="ATTACK" or not b.v3_body_cohort or b.v3_pre_handoff_candidate then return end
    local present=0
    for i=1,#e.entities do if b.v3_body_cohort.members[e.entities[i].entity] then present=present+1 end end
    if e.live_count<=0 or present*2<=e.live_count then return end
    local rec,created=R1V3Handoff.freeze(b.v3_pre_handoff_candidate,{generation=st.gen,block_id=a.block_id,exit_action_id=a.action_id,
        exit_order_seq=order.active_engine_seq,next_action_id=nexta.action_id,next_target_uid=nexta.target_uid,
        frozen_ms=e.model_ms,cohort=b.v3_body_cohort})
    if created then
        b.v3_pre_handoff_candidate=rec;b.v3_pre_handoff_sample_ms=e.model_ms
        if DEBUG_TELEMETRY then dlog("R1_V3_PRE_HANDOFF_FROZEN uid="..st.uid.." gen="..st.gen.." block="..clean(a.block_id)..
            " exit_action="..a.action_id.." exit_order="..clean(rec.exit_order_seq)..
            " next_attack="..nexta.action_id.." target="..clean(nexta.target_uid)..
            " body_count="..tostring(count_set(rec.body_entities)).." live="..tostring(e.live_count).." model_ms="..now) end
    end
end
function R1.v3_drain_contacts(now)
    local caps=S.evidence_v3_caps or {}
    if caps.contact_pairs~=true or type(bridge.read_contact_events_v3)~="function" then S.v3_contact_healthy=false;return true,"CONTACT_CAPABILITY_UNAVAILABLE" end
    local ok,events,meta=pcall(bridge.read_contact_events_v3,S.v3_contact_cursor.after,128)
    if not ok then S.v3_contact_healthy=false;return false,"CONTACT_PROVIDER_EXCEPTION" end
    local accepted,why=R1V3Contacts.consume(S.v3_contact_cursor,events,meta)
    if not accepted then S.v3_contact_healthy=false;return false,why end
    S.v3_contact_healthy=true
    for i=1,#accepted do
        local e=accepted[i];e.model_seen_ms=now
        S.v3_contact_log[#S.v3_contact_log+1]=e
    end
    while #S.v3_contact_log>2048 do table.remove(S.v3_contact_log,1) end
    return true,"OK"
end

function R1.v3_exit_body_status(st,a,now)
    local e=st and st.r1_v3_entity
    if not e or not finite(e.model_ms) or now-e.model_ms>CFG.evidence_max_age_ms then return nil,"ENTITY_STALE" end
    local b=st.block_state and st.block_state[a.block_id]
    if not b then return nil,"BLOCK_STATE_MISSING" end
    local order,order_reason=R1.v3_order_for(st,a)
    local h,hreason=R1.v3_handoff_scope(st,a,b,now)
    local own_owner_ready=false;local nearby_unmapped=0
    if type(bridge.contact_owner_ready_v3)=="function" then
        local ook,ov=pcall(bridge.contact_owner_ready_v3,st.uid);own_owner_ready=ook and ov==true
        if own_owner_ready then
            for tu,target in pairs(S.targets) do
                local valid=api_bool(target,"is_valid_target")
                if valid==true then
                    local d=unit_distance_to(st.unit,target)
                    if d and d<=CFG.v3_contact_mapping_radius_m then
                        local tok,tv=pcall(bridge.contact_owner_ready_v3,tu)
                        if not tok or tv~=true then nearby_unmapped=nearby_unmapped+1 end
                    end
                end
            end
        end
    end
    local contact_mapping_ready=own_owner_ready and nearby_unmapped==0
    local member_set=nil
    -- While the exact Exit order is live, the growing cohort is valid evidence.
    -- Once CA naturally retires that order at P1 completion, only the cohort frozen
    -- under the proven Exit order may carry identity across the boundary.
    if h and type(h.body_entities)=="table" then member_set=h.body_entities
    elseif order and b.v3_body_cohort and type(b.v3_body_cohort.members)=="table" then member_set=b.v3_body_cohort.members
    else return nil,order and (hreason or "COHORT_MISSING") or (hreason or order_reason or "EXIT_ORDER_UNPROVEN") end
    local live,present,progressing=0,0,0
    local present_set={}
    for i=1,#e.entities do
        local v=e.entities[i];live=live+1
        if member_set[v.entity] then
            present=present+1;present_set[v.entity]=true
            -- Progressing-majority permission is only legal while the exact Exit MOVE
            -- is still active. Frozen evidence is used only for route-complete body-clear.
            if order and v.movement_state==1 and v.motion_complete==true and finite(v.vx) and finite(v.vz) and a.pos then
                local dx,dz=a.pos.x-v.x,a.pos.z-v.z
                if dx*v.vx+dz*v.vz>0 then progressing=progressing+1 end
            end
        end
    end
    local contacted={}
    if S.v3_contact_healthy~=false then
        for i=#S.v3_contact_log,1,-1 do
            local ce=S.v3_contact_log[i]
            if not ce.model_seen_ms or now-ce.model_seen_ms>CFG.v3_contact_fresh_ms then break end
            local own_entity,other_uid
            if ce.uid_a==st.uid then own_entity=ce.entity_a;other_uid=ce.uid_b
            elseif ce.uid_b==st.uid then own_entity=ce.entity_b;other_uid=ce.uid_a end
            if own_entity and present_set[own_entity] and S.targets[other_uid] then contacted[own_entity]=true end
        end
    end
    local contact_count=count_set(contacted)
    return {order=order,order_reason=order_reason,handoff=h,live=live,body=present,progressing=progressing,contacted=contact_count,
        sample_ms=e.model_ms,body_established=live>0 and present*2>live,
        progressing_majority=order~=nil and live>0 and progressing*2>live,
        contact_mapping_ready=contact_mapping_ready,nearby_unmapped=nearby_unmapped,own_owner_ready=own_owner_ready,
        body_contact_majority=contact_mapping_ready and present>0 and contact_count*2>=present},"OK"
end

function R1.entity(st,now)
    local e=st.r1_entity
    if not e or not finite(e.model_ms) or now-e.model_ms>CFG.evidence_max_age_ms then return nil end
    return e
end
function R1.combat(st,now) return st.r1_combat end
function R1.combat_has_target(c,target_uid) return c and c.target_set and c.target_set[target_uid]==true end
function R1.majority_locked(e)
    return e and e.live_count>0 and ((e.melee_locked_count*2)>=e.live_count or (e.local_state3_count*2)>=e.live_count)
end
function R1.body_operable(e,route_done)
    if not e or e.live_count<=0 or (e.melee_locked_count*2)>=e.live_count or (e.local_state3_count*2)>=e.live_count then return false end
    -- While the Exit route is still owed, "operable" means the robust body core is
    -- still under CA path-following, not merely "not in melee". Once the route is
    -- independently complete, a halted/free majority is allowed to hand off.
    if route_done then return true end
    return (e.movement_pathing_count*2)>e.live_count
end
function R1.combat_clear(c)
    return c and c.active_melee_group_count==0 and c.coarse_contact_count==0
end
function R1.projected_motion_to(e,pos)
    if not e or e.motion_complete~=true or not pos then return nil end
    local dx,dz=pos.x-e.median_x,pos.z-e.median_z;local l=math.sqrt(dx*dx+dz*dz)
    if l<0.001 then return 0 end
    return e.median_vx*(dx/l)+e.median_vz*(dz/l)
end
function R1.trace_physical(st,a,now)
    if not S.evidence_caps or (S.evidence_caps.entity_snapshot~=true and S.evidence_caps.combat_groups~=true) then return end
    local e,c=R1.entity(st,now),R1.combat(st,now)
    local sig=(e and ("E:"..e.melee_locked_count..":"..e.movement_pathing_count..":"..e.local_state3_count) or ("E!"..clean(st.r1_entity_reason)))..
        ":"..(c and ("C:"..c.active_melee_group_count..":"..#c.active_target_uids) or ("C!"..clean(st.r1_combat_reason)))
    if a.r1_evidence_trace_signature==sig and now-(a.r1_evidence_trace_ms or -1000000)<1000 then return end
    a.r1_evidence_trace_signature=sig;a.r1_evidence_trace_ms=now
    if e then
        if DEBUG_TELEMETRY then log("R1_ENTITY_SNAPSHOT uid="..st.uid.." gen="..st.gen.." action="..a.action_id.." type="..a.type..
            " live="..e.live_count.." slots="..e.slot_count.." melee_locked="..e.melee_locked_count..
            " state3="..e.local_state3_count.." pathing="..e.movement_pathing_count.." halted="..e.movement_halted_count..
            " motion="..tostring(e.motion_complete==true).." vx="..num_or_nil(e.median_vx).." vz="..num_or_nil(e.median_vz).." model_ms="..now) end
    else
        if DEBUG_TELEMETRY then log("R1_ENTITY_SNAPSHOT_MISS uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " reason="..clean(st.r1_entity_reason).." model_ms="..now) end
    end
    if c then
        if DEBUG_TELEMETRY then log("R1_COMBAT_GROUPS uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " groups="..c.group_count.." active="..c.active_melee_group_count.." coarse="..c.coarse_contact_count..
            " targets="..table.concat(c.active_target_uids,",").." model_ms="..now) end
    else
        if DEBUG_TELEMETRY then log("R1_COMBAT_GROUPS_MISS uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " reason="..clean(st.r1_combat_reason).." model_ms="..now) end
    end
end

function R1.begin_fresh_episode(st,a,now)
    if not a.requires_fresh_engagement or not st.attack then return end
    st.attack.fresh={required=true,started_ms=now,handoff=a.v3_handoff_record,
        contact_seen=false,last_match_serial=nil,last_match_ms=nil,last_reason="WAIT_CONTACT_PAIR"}
    local h=a.v3_handoff_record
    if DEBUG_TELEMETRY then log("R1_V3_CONTACT_EPISODE_BEGIN uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
        " target="..a.target_uid.." handoff="..tostring(h~=nil)..
        " body_count="..tostring(h and count_set(h.body_entities) or 0).." model_ms="..now) end
end
function R1.fresh_engagement(st,a,now)
    local t=st.attack;local f=t and t.fresh
    if not f or not f.required then return nil,"NOT_REQUIRED",0 end
    local caps=S.evidence_v3_caps or {}
    if caps.contact_pairs~=true or caps.target_specific_physical_contact~=true then return false,"CONTACT_PAIR_CAPABILITY_UNAVAILABLE",0 end
    if S.v3_contact_healthy==false then return false,"CONTACT_JOURNAL_GAP",0 end
    local order,order_reason=R1.v3_order_for(st,a)
    if not order then return false,order_reason or "ORDER_IDENTITY_UNAVAILABLE",0 end
    local h=f.handoff or a.v3_handoff_record
    local prev=st.plan and st.plan[st.idx-1]
    if not h or not prev or prev.block_kind~="EXIT_ROUTE" then return false,"FROZEN_HANDOFF_MISSING",0 end
    local valid,why=R1V3Handoff.valid(h,{generation=st.gen,block_id=prev.block_id,exit_action_id=prev.action_id,
        next_action_id=a.action_id,next_target_uid=a.target_uid,now=now})
    if not valid then return false,"HANDOFF_"..clean(why),0 end
    local newest=nil
    for i=#S.v3_contact_log,1,-1 do
        local e=S.v3_contact_log[i]
        if e.model_seen_ms and now-e.model_seen_ms<=CFG.v3_contact_fresh_ms
            and R1V3Contacts.match_for_attack(e,st.uid,a.target_uid,order.active_engine_seq,h.body_entities) then newest=e;break end
    end
    if not newest then f.last_reason="NO_CURRENT_BODY_CONTACT_EVENT";return false,f.last_reason,0 end
    f.contact_seen=true;f.last_match_serial=newest.serial;f.last_match_ms=now;f.last_reason="BODY_CONTACT_INTENDED_EXACT_ORDER"
    return true,f.last_reason,1
end

local function action_runtime(a)
    if not a.runtime then
        a.runtime={semantic_done=false,done_ms=nil,done_reason=nil,entered_ms=nil,entry_pos=nil,
            best_remaining=nil,last_remaining=nil,last_progress_ms=nil,movement_seen=false,idle_candidate=nil,
            handoff_committed=false,handoff_ms=nil,handoff_reason=nil,successor_action_id=nil}
    end
    return a.runtime
end
local function enter_action(st,a,now,reason)
    local rt=action_runtime(a)
    if rt.entered_ms then return rt end
    local p=st.pos or point(st.unit) or a.origin
    rt.entered_ms=now;rt.entry_pos=copy(p);rt.last_progress_ms=now;rt.entry_reason=reason
    if a.type=="MOVE" and p and a.pos then
        rt.best_remaining=dist(p,a.pos);rt.last_remaining=rt.best_remaining
    elseif a.type=="ATTACK" and a.requires_fresh_engagement and st.plan and st.idx>1 then
        local prev=st.plan[st.idx-1];local b=prev and st.block_state and st.block_state[prev.block_id] or nil
        if b and b.v3_pre_handoff_candidate then
            a.v3_handoff_record=b.v3_pre_handoff_candidate;b.v3_handoff_record=a.v3_handoff_record
            if DEBUG_TELEMETRY then dlog("R1_V3_HANDOFF_FROZEN uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
                " exit_action="..prev.action_id.." exit_order="..clean(a.v3_handoff_record.exit_order_seq)..
                " body_count="..tostring(count_set(a.v3_handoff_record.body_entities)).." frozen_ms="..clean(a.v3_handoff_record.frozen_ms).." model_ms="..now) end
        end
    end
    if DEBUG_TELEMETRY then dlog("ACTION_ENTER uid="..st.uid.." gen="..st.gen.." action="..a.action_id.." type="..a.type..
        " block="..clean(a.block_id).." block_kind="..clean(a.block_kind).." reason="..clean(reason).." model_ms="..now) end
    return rt
end
local function mark_action_complete(st,a,reason,now,remaining)
    local rt=action_runtime(a)
    if rt.semantic_done then return false end
    rt.semantic_done=true;rt.done_ms=now;rt.done_reason=reason;rt.done_remaining=remaining
    R1.clear_fault(st,a,now)
    if DEBUG_TELEMETRY then dlog("ACTION_COMPLETE uid="..st.uid.." gen="..st.gen.." action="..a.action_id.." cursor="..st.idx..
        " type="..a.type.." block="..clean(a.block_id).." block_kind="..clean(a.block_kind)..
        " reason="..reason.." remaining="..num_or_nil(remaining).." model_ms="..now) end
    return true
end
function Core.mark_handoff_committed(st,a,nexta,reason,now,g)
    local rt=action_runtime(a)
    if rt.handoff_committed then return end
    rt.handoff_committed=true;rt.handoff_ms=now;rt.handoff_reason=reason;rt.successor_action_id=nexta and nexta.action_id or nil
    local b=st.block_state and st.block_state[a.block_id]
    if b and R1V3Recovery.matches(b.v3_recovery_budget,st.gen,a.block_id,a.action_id) then
        R1V3Recovery.close(b.v3_recovery_budget,now,"HANDOFF_COMMITTED")
    end
    if DEBUG_TELEMETRY then dlog("ACTION_HANDOFF_COMMITTED uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
        " successor="..clean(nexta and nexta.action_id).." reason="..clean(reason)..
        " semantic_done="..tostring(rt.semantic_done).." remaining="..num_or_nil(g and g.remaining)..
        " cut_error="..num_or_nil(g and g.cut_error).." cut_tolerance="..num_or_nil(g and g.cut_tolerance)..
        " route_mode="..clean(g and g.route_mode).." debt_mode="..clean(g and g.route_debt_mode)..
        " debt_count="..clean(g and g.route_debt_count).." debt_error="..num_or_nil(g and g.route_debt_error).." debt_limit="..num_or_nil(g and g.route_debt_limit)..
        " corner_window="..num_or_nil(g and g.corner_window).." corner_base="..num_or_nil(g and g.corner_window_base).." corner_early="..num_or_nil(g and g.corner_window_early)..
        " stall_escape="..tostring(g and g.corner_stall_escape==true).." stall_no_progress_ms="..num_or_nil(g and g.corner_stall_no_progress_ms)..
        " stall_escape_limit="..num_or_nil(g and g.corner_stall_escape_limit).." model_ms="..now) end
    if g and g.route_debt_mode=="SOFT_PRESERVED" then
        if DEBUG_TELEMETRY then dlog("ROUTE_DEBT_SOFT_CONTINUE uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " successor="..clean(nexta and nexta.action_id).." debt_count="..clean(g.route_debt_count)..
            " debt_error="..num_or_nil(g.route_debt_error).." debt_limit="..num_or_nil(g.route_debt_limit)..
            " model_ms="..now.." policy=KEEP_DEBT_BACKGROUND_MOVE_TO_MOVE_ONLY") end
    end
end
local function ensure_block_state(st,id,kind)
    st.block_state=st.block_state or {}
    local b=st.block_state[id]
    if not b then
        b={id=id,kind=kind,exit_committed=false,exit_started_ms=nil,exit_start_pos=nil,
            exit_source_target_uid=nil,exit_source_target=nil,last_reassert_ms=-1000000,reasserts=0,
            clear_candidate=nil,contact_scan=nil,blocked_logged=false,route_debts={},
            fresh_baseline_locked=nil,fresh_baseline_ms=nil,
            v3_body_cohort=nil,v3_handoff_record=nil,v3_recovery_budget=nil}
        st.block_state[id]=b
    end
    return b
end
local function v3_recovery_budget(st,a)
    if not st or not a then return nil end
    local b=ensure_block_state(st,a.block_id or ("M"..a.action_id),a.block_kind or "MOVE_ROUTE")
    local r=b.v3_recovery_budget
    if not R1V3Recovery.matches(r,st.gen,a.block_id,a.action_id) then
        r=R1V3Recovery.new(st.gen,a.block_id,a.action_id,CFG.exit_reassert_max);b.v3_recovery_budget=r
    end
    return r
end
local function v3_recovery_available(st,a,now,reason)
    local r=v3_recovery_budget(st,a);if not r then return false,nil,"MISSING" end
    if r.closed then return false,r,"CLOSED" end
    if R1V3Recovery.remaining(r)<=0 then
        local code=reason=="EXIT_REASSERT" and "EXIT_RECOVERY_BUDGET_EXHAUSTED" or "RECOVERY_BUDGET_EXHAUSTED_"..clean(reason)
        R1.fault(st,a,"BLOCKED_EXECUTION",code,now)
        return false,r,"EXHAUSTED"
    end
    return true,r,"OK"
end
local function v3_recovery_commit(r,reason,now)
    if not r then return false,"MISSING" end
    local ok,why,left=R1V3Recovery.consume(r,reason,now)
    return ok,why,left
end
-- Blocks are assigned from the original Shift chain, not guessed from timing.
-- Consecutive Move actions share one route block. A Move immediately after an
-- Attack starts an EXIT_ROUTE block whose disengagement obligation follows every
-- Move in that block until the next Attack.
function Core.assign_block(st,a)
    local prev=st.actions[#st.actions]
    if a.type=="ATTACK" then
        if prev and prev.type=="MOVE" and prev.block_kind=="EXIT_ROUTE" then
            a.requires_fresh_engagement=true
        end
        a.block_kind="ATTACK";a.block_id="A"..a.action_id
        ensure_block_state(st,a.block_id,a.block_kind)
        return
    end
    if prev and prev.type=="MOVE" and not (st.block_state[prev.block_id] and st.block_state[prev.block_id].closed) then
        a.block_kind=prev.block_kind or "MOVE_ROUTE";a.block_id=prev.block_id or ("M"..prev.action_id)
        a.source_attack_id=prev.source_attack_id;a.source_target_uid=prev.source_target_uid
        ensure_block_state(st,a.block_id,a.block_kind)
        return
    end
    if prev and prev.type=="ATTACK" then
        a.block_kind="EXIT_ROUTE";a.block_id="E"..a.action_id
        a.source_attack_id=prev.action_id;a.source_target_uid=prev.target_uid
        local b=ensure_block_state(st,a.block_id,a.block_kind)
        b.exit_source_target_uid=prev.target_uid;b.exit_source_target=prev.target
        return
    end
    a.block_kind="MOVE_ROUTE";a.block_id="M"..a.action_id
    ensure_block_state(st,a.block_id,a.block_kind)
end
local function current_block(st)
    local a=st.plan and st.plan[st.idx]
    return a and a.block_id and st.block_state and st.block_state[a.block_id] or nil
end
-- If a future Attack is removed because its target is confirmed dead/left before
-- execution, the following Move block is no longer an exit from that Attack.
function Core.detach_skipped_attack_block(st,index,attack_id)
    local first=st.plan and st.plan[index]
    if not first or first.type~="MOVE" or first.source_attack_id~=attack_id then return end
    local old_id=first.block_id
    local prev=st.plan[index-1]
    local new_kind,new_id,source_id,source_uid
    if prev and prev.type=="MOVE" then
        new_kind=prev.block_kind or "MOVE_ROUTE";new_id=prev.block_id or ("M"..prev.action_id)
        source_id=prev.source_attack_id;source_uid=prev.source_target_uid
    else
        new_kind="MOVE_ROUTE";new_id="M"..first.action_id
    end
    local i=index
    while st.plan[i] and st.plan[i].type=="MOVE" and st.plan[i].block_id==old_id do
        local a=st.plan[i];a.block_kind=new_kind;a.block_id=new_id;a.source_attack_id=source_id;a.source_target_uid=source_uid;i=i+1
    end
    ensure_block_state(st,new_id,new_kind)
    if old_id~=new_id and st.block_state then st.block_state[old_id]=nil end
end
local function bind_evidence_unit(u,unit,label)
    if not u or not unit or not bridge or type(bridge.bind_evidence_unit_v3)~="function" then return false end
    local now=clock();local retry=S.evidence_bind_retry and S.evidence_bind_retry[u]
    if retry and now<(retry.next_ms or 0) then return false end
    local ok,bound,root=pcall(bridge.bind_evidence_unit_v3,u,unit)
    if ok and bound==true and type(root)=="string" then
        S.evidence_bound=S.evidence_bound or {};S.evidence_bind_retry[u]=nil
        if S.evidence_bound[u]~=root then
            S.evidence_bound[u]=root
            if DEBUG_TELEMETRY then dlog("R1_V3_EVIDENCE_ROOT_BOUND uid="..u.." root="..root.." source="..clean(label)) end
        end
        return true
    end
    local reason=clean(root or bound or (ok and "BIND_REJECTED" or "PROVIDER_EXCEPTION"))
    local r=retry or {};local changed=r.reason~=reason
    if changed or not r.last_log_ms or now-r.last_log_ms>=10000 then
        if DEBUG_TELEMETRY then dlog("R1_V3_EVIDENCE_ROOT_BIND_MISS uid="..tostring(u).." source="..clean(label).." reason="..reason.." retry_ms=5000") end
        r.last_log_ms=now
    end
    r.reason=reason;r.next_ms=now+5000;S.evidence_bind_retry[u]=r
    return false
end
function Core.new_state(su,dynamic)
    dynamic=dynamic==true
    return {uid=uid(su.unit),unit=su.unit,uc=su.uc,gen=0,revision=nil,actions={},plan=nil,
        idx=1,owned=false,terminal=false,blocked=false,require_replace=dynamic,recover_revision=nil,speeds={},pos=nil,prev_pos=nil,last_pos=nil,
        last_sample=nil,origin=nil,moves=0,last_wait=-1000000,refused=nil,phase=dynamic and "WAIT_FOR_REPLACE" or "NATIVE_TRACKING",
        attack=nil,model_step_ms=0,cold_seen=dynamic,cold_idle=nil,queue_reset_cert=nil,restart_idle_candidate=nil,restart_idle_cert=nil,
        dynamic=dynamic,last_seen_scan=nil,block_state={},action_serial=0,action_base=0}
end
local function collection_count(c)
    if not c then return nil end
    local ok,n=pcall(function() return c:count() end)
    if ok and finite(n) and n>=0 and n==math.floor(n) then return n end
    return nil
end
local function register_local_sunit(su,dynamic,label,now,strict)
    local u=su and su.unit and uid(su.unit)
    if not u or not su or not su.uc then
        if strict then error("BAD_LOCAL_SCRIPTUNIT") end
        if DEBUG_TELEMETRY then dlog("DYNAMIC_LOCAL_SKIPPED label="..clean(label).." reason=BAD_SCRIPTUNIT") end
        return nil,false
    end
    bind_evidence_unit(u,su.unit,label)
    local st=S.states[u]
    if not st then
        st=Core.new_state(su,dynamic);S.states[u]=st
        if dynamic then S.dynamic_units=S.dynamic_units+1 end
        if DEBUG_TELEMETRY then log((dynamic and "REGISTER_LOCAL_DYNAMIC" or "REGISTER_LOCAL").." uid="..u.." source="..clean(label)..
            " policy="..(dynamic and "WAIT_FOR_FRESH_REPLACE" or "INITIAL")) end
    end
    st.last_seen_scan=now
    return st,true
end
local function register_local_collection(c,dynamic,label,now,strict)
    local n=collection_count(c)
    if n==nil then
        if strict then error("NO_LOCAL_SCRIPTUNITS") end
        return 0
    end
    if strict and n<1 then error("NO_LOCAL_SCRIPTUNITS") end
    local added=0
    for i=1,n do
        local ok,su=pcall(function() return c:item(i) end)
        if ok and su then
            local before=su.unit and uid(su.unit)
            local existed=before and S.states[before]~=nil
            local _,good=register_local_sunit(su,dynamic,label,now,strict)
            if good and not existed then added=added+1 end
        elseif strict then error("BAD_LOCAL_SCRIPTUNIT") end
    end
    return added
end
function Core.register_target_unit(unit,label)
    local u=unit and uid(unit)
    if not u then return false end
    bind_evidence_unit(u,unit,label)
    if not S.targets[u] then
        S.targets[u]=unit;if DEBUG_TELEMETRY then dlog("REGISTER_TARGET_DYNAMIC uid="..u.." source="..clean(label)) end
        return true
    end
    return false
end
local function register_target_collection(c,label)
    local n=collection_count(c);if not n then return 0 end
    local added=0
    for i=1,n do
        local ok,su=pcall(function() return c:item(i) end)
        if ok and su and su.unit and Core.register_target_unit(su.unit,label) then added=added+1 end
    end
    return added
end
local function reinforcement_count(alliance,army)
    local ok,n=pcall(function() return bmgr:num_reinforcing_armies_for_army_in_alliance(alliance,army) end)
    if ok and finite(n) and n>=0 and n==math.floor(n) then return n end
    return 0
end
local function refresh_collections(now,force,initial)
    if not force and now-S.last_collection_scan<CFG.collection_scan_ms then return true end
    S.last_collection_scan=now;S.collection_scans=S.collection_scans+1
    local local_added,target_added=0,0
    local ook,own=pcall(function() return bmgr:get_scriptunits_for_local_players_army() end)
    if not ook then if initial then error("NO_LOCAL_SCRIPTUNITS") else if DEBUG_TELEMETRY then dlog("DYNAMIC_SCAN_LOCAL_ERROR") end end
    elseif own then local_added=local_added+register_local_collection(own,not initial,"local_main",now,initial)
    elseif initial then error("NO_LOCAL_SCRIPTUNITS") end

    -- CA exposes reinforcing scriptunit groups separately. Register them before they
    -- enter the field so their first real player command cannot race discovery.
    local pa_ok,pa=pcall(function() return bmgr:get_player_alliance_num() end)
    local la_ok,la=pcall(function() return bmgr:local_army() end)
    if pa_ok and la_ok and finite(pa) and finite(la) then
        for ri=1,reinforcement_count(pa,la) do
            local rok,rc=pcall(function() return bmgr:get_scriptunits_for_army(pa,la,ri) end)
            if rok and rc then local_added=local_added+register_local_collection(rc,true,"local_reinforcement_"..ri,now,false) end
        end
    end

    -- Late-spawned units can appear directly in the live player army. Reuse CA's
    -- already-created script_unit so we never fabricate a unitcontroller ourselves.
    local aok,army=pcall(function() return bmgr:get_player_army() end)
    if aok and army then
        local uok,units=pcall(function() return army:units() end)
        local n=uok and collection_count(units) or nil
        if n then
            for i=1,n do
                local bok,bu=pcall(function() return units:item(i) end)
                if bok and bu then
                    local sok,su=pcall(function() return bmgr:get_scriptunit_for_unit(bu) end)
                    if sok and su then
                        local u=uid(bu);local existed=u and S.states[u]~=nil
                        local _,good=register_local_sunit(su,true,"local_live_army",now,false)
                        if good and not existed then local_added=local_added+1 end
                    end
                end
            end
        end
    end

    local eok,enemy=pcall(function() return bmgr:get_scriptunits_for_main_enemy_army_to_local_player() end)
    if eok and enemy then target_added=target_added+register_target_collection(enemy,"enemy_main") end
    local ea_ok,ea=pcall(function() return bmgr:get_non_player_alliance_num() end)
    local na_ok,na=false,nil
    if ea_ok then na_ok,na=pcall(function() return bmgr:num_armies_in_alliance(ea) end) end
    if ea_ok and na_ok and finite(na) and na>=0 then
        for ai=1,na do
            local mok,mc=pcall(function() return bmgr:get_scriptunits_for_army(ea,ai) end)
            if mok and mc then target_added=target_added+register_target_collection(mc,"enemy_army_"..ai) end
            for ri=1,reinforcement_count(ea,ai) do
                local rok,rc=pcall(function() return bmgr:get_scriptunits_for_army(ea,ai,ri) end)
                if rok and rc then target_added=target_added+register_target_collection(rc,"enemy_reinforcement_"..ai.."_"..ri) end
            end
        end
    end
    if local_added>0 or target_added>0 then
        if DEBUG_TELEMETRY then log("DYNAMIC_COLLECTION_REFRESH local_added="..local_added.." target_added="..target_added..
            " states="..tostring((function() local n=0;for _ in pairs(S.states) do n=n+1 end;return n end)())..
            " model_ms="..string.format("%.0f",now)) end
    end
    return true
end
local function collections() return refresh_collections(clock(),true,true) end
local begin_attack_history
local register_route_obligation
local function sample(st,now)
    local p=point(st.unit)
    if not p then
        if st.plan then log("UNIT_UNAVAILABLE uid="..st.uid); cancel(st,"UNIT_UNAVAILABLE",now,false); st.blocked=true; st.phase="UNIT_UNAVAILABLE" end
        return
    end
    local previous=st.last_pos and copy(st.last_pos) or nil
    if st.last_sample and now>st.last_sample and previous then
        st.model_step_ms=now-st.last_sample
        local speed=dist(p,previous)*1000/(now-st.last_sample)
        if finite(speed) then st.speeds[#st.speeds+1]=speed; if #st.speeds>5 then table.remove(st.speeds,1) end end
    end
    st.prev_pos=previous;st.pos=p; st.last_pos=copy(p); st.last_sample=now
end
cancel=function(st,reason,now,observe)
    local old=st.gen
    if st.attack then
        if DEBUG_TELEMETRY then log("FEG_CANCEL uid="..st.uid.." gen="..old.." issue="..st.attack.issue.." reason="..reason..
            " model_ms="..string.format("%.0f",now).." eligible_ms="..string.format("%.0f",st.attack.eligible_ms)) end
    end
    st.cold_idle=nil;st.queue_reset_cert=nil;st.restart_idle_candidate=nil;st.restart_idle_cert=nil; EXIT_TRACE[st.uid]=nil
    if st.plan or st.owned then
        local tracked=st.plan~=nil
        if DEBUG_TELEMETRY then dlog("GEN_CANCEL uid="..st.uid.." gen="..old.." reason="..reason.." owned="..tostring(st.owned).." tracked="..tostring(tracked).." terminal="..tostring(st.terminal).." phase="..clean(st.phase).." model_ms="..string.format("%.0f",now)) end
        -- A player-native Attack-first plan is actively tracked even before Lua has
        -- issued any command. REPLACE must still prove that the old generation stays dead.
        if DEBUG_TELEMETRY and observe and tracked and not st.terminal then
            S.cancel_checks[#S.cancel_checks+1]={uid=st.uid,gen=old,start=now,logged=false}
        end
    end
    st.gen=st.gen+1; st.actions={}; st.plan=nil; st.idx=1; st.origin=nil
    st.owned=false; st.terminal=false; st.moves=0; st.refused=nil; st.attack=nil; st.phase="CANCELLED"; st.input_gapped=false; st.tail_reached=false; st.recover_revision=nil
    st.block_state={};st.action_serial=0;st.action_base=0;st.native_arrival=nil;st.unverified_native_successor=nil
    -- A pending native order is NOT relabelled to the new generation.
end
local function action(st,r,now)
    if type(r.is_queued)~="boolean" then return nil,"QUEUED_MISSING" end
    local a={type=r.order_type,serial=r.serial,seq=r.engine_seq_valid and r.engine_seq or nil,
        revision=r.unit_revision,unit_lifetime=r.unit_lifetime,queued=r.is_queued,origin=point(st.unit),captured_ms=now}
    if a.type=="MOVE" then
        if not finite(r.dest_x) or not finite(r.dest_y) or not finite(r.dest_z) then return nil,"MOVE_PAYLOAD" end
        a.pos={x=r.dest_x,y=r.dest_y,z=r.dest_z}
    elseif a.type=="ATTACK" then
        if not id(r.target_uid) then return nil,"ATTACK_UID" end
        if not S.targets[r.target_uid] then refresh_collections(now,true,false) end
        a.target_uid=r.target_uid; a.target=S.targets[r.target_uid]
    else return nil,"UNSUPPORTED_KIND" end
    return a
end
local function plan_supported(st,actions,suffix_only)
    if #actions==0 then return false,"EMPTY_PLAN" end
    local first=actions[1]
    if not suffix_only then
        local attack_first=CONTROLLER_PHASE=="P2B" and first.type=="ATTACK" and first.queued==false
        if first.type~="MOVE" and not attack_first then
            return false,first.type=="ATTACK" and "ATTACK_FIRST_PHASE2_REQUIRED" or "MOVE_OR_ATTACK_FIRST_REQUIRED"
        end
    end
    local attacks=0
    for i,a in ipairs(actions) do
        if a.type=="ATTACK" then
            attacks=attacks+1
            if not id(a.target_uid) then return false,"TARGET_UID_INVALID" end
            if CONTROLLER_PHASE=="P1E" and i<#actions then return false,"TAIL_AFTER_ATTACK_PHASE2_REQUIRED" end
        end
    end
    if CONTROLLER_PHASE=="P1E" and attacks>1 then return false,"MULTIPLE_ATTACKS_PHASE2_REQUIRED" end
    return true
end
function Core.ingest(r,now)
    local st=S.states[r.unit_uid]
    if not st then
        if not S.targets[r.unit_uid] and (not S.unknown_retry[r.unit_uid] or now>=S.unknown_retry[r.unit_uid]) then
            refresh_collections(now,true,false)
            st=S.states[r.unit_uid]
            if not st then S.unknown_retry[r.unit_uid]=now+CFG.unknown_refresh_ms end
        end
        if not st then
            if DEBUG_TELEMETRY then dlog("ORDER_IGNORED_UNREGISTERED uid="..clean(r.unit_uid).." serial="..clean(r.serial).." type="..clean(r.order_type)..
                " queued="..clean(r.is_queued).." rev="..clean(r.unit_revision).." model_ms="..string.format("%.0f",now)) end
            return
        end
    end
    -- A recoverable Bridge capture is processed before Journal ingestion and
    -- snapshots the authoritative native revision. Records already represented by
    -- that snapshot are historical/lossy input and must not be re-admitted.
    if st.recover_revision then
        local c=cmp(r.unit_revision,st.recover_revision)
        if c<=0 then
            if DEBUG_TELEMETRY then dlog("RECOVERY_RECORD_SKIPPED uid="..st.uid.." rev="..r.unit_revision.." through="..st.recover_revision.." serial="..r.serial) end
            return
        end
        st.recover_revision=nil
    end
    local cold=not st.cold_seen and st.cold_idle or nil
    st.cold_seen=true; st.cold_idle=nil -- including failed/unsupported first orders
    if DEBUG_TELEMETRY then S.order_count=S.order_count+1 end
    if DEBUG_TELEMETRY then dlog("ORDER uid="..st.uid.." serial="..r.serial.." type="..clean(r.order_type).." status="..clean(r.status)..
        " source="..clean(r.source).." issue="..clean(r.script_issue_id).." rev="..r.unit_revision.." queued="..clean(r.is_queued).." target="..clean(r.target_uid)..(r.order_type=="MOVE" and (" x="..clean(r.dest_x).." z="..clean(r.dest_z)) or "")) end
    if r.input_sampled~=nil then
        if DEBUG_TELEMETRY then dlog("ORDER_INPUT uid="..st.uid.." serial="..r.serial.." type="..clean(r.order_type)..
            " source="..clean(r.source).." queued="..clean(r.is_queued)..
            " stage="..clean(r.input_stage).." sampled="..tostring(r.input_sampled)..
            " foreground="..clean(r.input_foreground).." shift="..clean(r.input_shift)..
            " left_shift="..clean(r.input_left_shift).." right_shift="..clean(r.input_right_shift)..
            " ctrl="..clean(r.input_ctrl).." alt="..clean(r.input_alt)..
            " sample_tick_ms="..clean(r.input_tick_ms).." model_ms="..now..
            " policy=OBSERVATION_ONLY_NOT_CLICK_TIME_PROOF") end
    end
    local p=S.pending_by_uid[st.uid]
    if r.source=="OUR_CONTROLLER" then
        if not p or r.script_issue_id~=p.issue or r.unit_uid~=p.uid then
            fail("UNEXPECTED_OWN_ACK uid="..st.uid.." issue="..clean(r.script_issue_id)); return
        end
        if S.pending_by_issue[r.script_issue_id]~=p then fail("OWN_ISSUE_INDEX_MISMATCH");return end
        S.pending_by_uid[st.uid]=nil;S.pending_by_issue[p.issue]=nil;S.pending_count=S.pending_count-1
        if st.gen~=p.gen then
            -- Native ledger advancement is independent of old-generation plan ownership.
            -- A late ACK may update revision, but cannot revive actions or cursor.
            if accepted(r) then
                if r.order_type~=p.kind or r.is_queued~=false or r.unit_revision~=inc(p.revision)
                    or (p.kind=="ATTACK" and r.target_uid~=p.target_uid)
                    or (p.kind=="MOVE" and (not finite(r.dest_x) or not finite(r.dest_y) or not finite(r.dest_z))) then fail("LATE_OWN_ACK_CONTRACT");return end
                if not st.revision or r.unit_revision==inc(st.revision) then st.revision=r.unit_revision
                elseif cmp(r.unit_revision,st.revision)>0 then fail("LATE_OWN_ACK_REVISION_GAP");return end
            end
            if DEBUG_TELEMETRY then dlog("LATE_OWN_ACK_IGNORED uid="..st.uid.." gen="..p.gen.." issue="..p.issue.." status="..r.status.." ledger_revision="..clean(st.revision)) end
            return
        end
        if not accepted(r) then
            if r.status=="REJECTED_STALE" and p.saw_append and st.plan and not st.blocked
                and st.idx==p.previous_idx and st.plan[p.idx]==p.action
                and r.unit_revision==st.revision and cmp(st.revision,p.revision)>0
                and r.order_type==p.kind and r.is_queued==false
                and (p.kind~="ATTACK" or r.target_uid==p.target_uid) then
                st.owned=p.previous_owned
                st.phase=st.attack and (st.attack.previous_eligible and "ATTACK_HOLD" or "ATTACK_APPROACH") or "MOVE_TRACKING"
                st.input_gapped=true
                if DEBUG_TELEMETRY then dlog("OWN_STALE_AFTER_APPEND uid="..st.uid.." gen="..st.gen.." issue="..p.issue..
                    " idx="..p.idx.." expected_revision="..p.revision.." rev="..st.revision..
                    " model_ms="..string.format("%.0f",now).." policy=REDECIDE_NEW_ISSUE_NO_STALE_REPLAY") end
                return
            end
            cancel(st,"OWN_"..clean(r.status),now,false); st.blocked=true
            log("ISSUE_REJECTED uid="..st.uid.." status="..clean(r.status)); return
        end
        if r.order_type~=p.kind or r.is_queued~=false or r.unit_revision~=inc(p.revision) then
            fail("OWN_ACK_CONTRACT"); return
        end
        if p.kind=="ATTACK" and r.target_uid~=p.target_uid then fail("OWN_TARGET_MISMATCH"); return end
        if p.kind=="MOVE" then
            local q=p.action.pos
            if not finite(r.dest_x) or not finite(r.dest_y) or not finite(r.dest_z) then
                fail("OWN_MOVE_PAYLOAD_INVALID"); return
            end
            local dx,dy,dz=r.dest_x-q.x,r.dest_y-q.y,r.dest_z-q.z
            local delta=math.sqrt(dx*dx+dy*dy+dz*dz)
            if delta>0.05 then
                if DEBUG_TELEMETRY then dlog("OWN_MOVE_CANONICALIZED uid="..st.uid.." gen="..p.gen.." issue="..p.issue.." idx="..p.idx..
                    " expected_x="..string.format("%.6f",q.x).." expected_y="..string.format("%.6f",q.y).." expected_z="..string.format("%.6f",q.z)..
                    " actual_x="..string.format("%.6f",r.dest_x).." actual_y="..string.format("%.6f",r.dest_y).." actual_z="..string.format("%.6f",r.dest_z)..
                    " dx="..string.format("%.6f",dx).." dy="..string.format("%.6f",dy).." dz="..string.format("%.6f",dz).." distance="..string.format("%.6f",delta)) end
            end
            -- The native accepted command is authoritative after strong issue/source/revision identity closes.
            -- CA may canonicalize the destination when rebuilding a nonqueued Move from a queued waypoint.
            q.x,q.y,q.z=r.dest_x,r.dest_y,r.dest_z
        end
        st.revision=r.unit_revision
        action_runtime(p.action).accepted_seq=r.engine_seq_valid and r.engine_seq or nil
        action_runtime(p.action).accepted_receipt=r.serial
        action_runtime(p.action).accepted_lifetime=r.unit_lifetime
        if not p.reassert_current then
            local previous=st.plan[p.previous_idx]
            if previous and previous.type=="MOVE" and action_runtime(previous).handoff_committed and not action_runtime(previous).semantic_done then
                local hg=p.handoff_geometry or {}
                if hg.route_mode=="STEERING_CORNER" then
                    -- The successor was accepted while the unit was inside the bounded turn corridor.
                    -- That is the completion proof for an intermediate navigation waypoint: do not
                    -- create a debt that would force the formation to return and physically stamp Pn.
                    mark_action_complete(st,previous,"STEERING_CORNER_HANDOFF",now,hg.remaining)
                    if DEBUG_TELEMETRY then dlog("STEERING_CORNER_COMMITTED uid="..st.uid.." gen="..st.gen.." action="..previous.action_id..
                        " successor="..clean(p.action and p.action.action_id).." remaining="..num_or_nil(hg.remaining)..
                        " corner_window="..num_or_nil(hg.corner_window).." lookahead="..num_or_nil(hg.corner_lookahead)..
                        " turn_factor="..num_or_nil(hg.corner_turn_factor).." model_ms="..now) end
                else
                    register_route_obligation(st,previous,hg,now)
                end
            end
        end
        st.idx=p.idx; st.owned=true
        if not p.reassert_current then st.origin=p.origin end
        local enter_reason=p.reassert_attack and "CURRENT_ATTACK_REASSERT_ACK" or (p.reassert_current and "CURRENT_MOVE_REASSERT_ACK" or "OWN_ACK")
        enter_action(st,st.plan[p.idx],now,enter_reason)
        if p.kind=="MOVE" then
            if not p.reassert_current then st.moves=st.moves+1 end
            st.phase="MOVE_TRACKING"
            if DEBUG_TELEMETRY then dlog((p.reassert_current and "CURRENT_MOVE_REASSERT_ACK" or "OWN_MOVE_ACK").." uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." idx="..p.idx.." rev="..st.revision.." model_ms="..string.format("%.0f",now)) end
            if p.after_attack then
                st.plan[p.idx].role="POST_ATTACK_EXIT"
                local b=st.plan[p.idx].block_id and ensure_block_state(st,st.plan[p.idx].block_id,st.plan[p.idx].block_kind) or nil
                if b then
                    b.exit_started_ms=b.exit_started_ms or now
                    b.exit_start_pos=b.exit_start_pos or copy(p.origin)
                    b.exit_source_target_uid=b.exit_source_target_uid or p.source_attack_target_uid
                    b.exit_source_target=b.exit_source_target or (b.exit_source_target_uid and S.targets[b.exit_source_target_uid])
                end
                if p.attack_abort then
                    if DEBUG_TELEMETRY then log("ATTACK_ABORT_EXIT_ACK uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." idx="..p.idx..
                        " attack_issue="..clean(p.attack_issue).." reason="..p.attack_abort.." model_ms="..string.format("%.0f",now)..
                        " hold_ms="..string.format("%.0f",p.hold_ms or 0).." preserved_tail=true claim=COMMAND_ACCEPTED") end
                else
                    if DEBUG_TELEMETRY then log("FEG_EXIT_ACK uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." idx="..p.idx..
                        " attack_issue="..p.attack_issue.." model_ms="..string.format("%.0f",now)..
                        " hold_ms="..string.format("%.0f",p.hold_ms).." claim=COMMAND_ACCEPTED_NOT_PHYSICAL_DISENGAGEMENT") end
                    if DEBUG_TELEMETRY then dlog("P2_MOVE_AFTER_ATTACK_ACK uid="..st.uid.." gen="..st.gen.." issue="..p.issue..
                        " idx="..p.idx.." attack_issue="..p.attack_issue.." hold_ms="..string.format("%.0f",p.hold_ms)..
                        " model_ms="..string.format("%.0f",now).." expected_revision="..p.revision.." rev="..st.revision..
                        " claim=COMMAND_ACCEPTED_NOT_PHYSICAL_DISENGAGEMENT") end
                    if DEBUG_TELEMETRY then
                        EXIT_TRACE[st.uid]={gen=st.gen,issue=p.issue,attack_issue=p.attack_issue,started=now,
                            dest=copy(st.plan[p.idx].pos),target=st.plan[p.idx-1].target}
                    end
                end
                st.attack=nil
            end
        else
            if DEBUG_TELEMETRY then dlog("OWN_ATTACK_ACK uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." idx="..p.idx.." target="..p.target_uid.." rev="..st.revision.." model_ms="..string.format("%.0f",now)) end
            if p.attack_abort then
                if DEBUG_TELEMETRY then log("ATTACK_ABORT_SUCCESSOR_ACK uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." idx="..p.idx..
                    " kind=ATTACK reason="..p.attack_abort.." model_ms="..string.format("%.0f",now).." preserved_tail=true") end
            end
            if CONTROLLER_PHASE=="P2B" then
                if p.reassert_attack then
                    local t=st.attack
                    local a=st.plan[p.idx]
                    if not t or t.done or not a or a.type~="ATTACK" then fail("ATTACK_REASSERT_ACK_STATE");return end
                    local preserved=t.eligible_ms or 0
                    t.issue=p.issue;t.accepted_ms=now;t.last_ms=now;t.previous_eligible=false
                    t.feg=FEG.new(now,feg_width(st.unit),feg_width(a.target),nil,{require_fresh_reentry=a.requires_fresh_engagement==true})
                    t.feg_result=nil;t.feg_sample_ms=nil;t.center_a2=nil;t.abort_reason=nil
                    t.execution_reasserts=(t.execution_reasserts or 0)+1
                    local art=action_runtime(a);art.no_execution_since=nil;art.last_attack_reassert_ack_ms=now
                    if art.fault and art.fault.reason=="ATTACK_ACCEPTED_BUT_NO_EXECUTION_EVIDENCE" then R1.clear_fault(st,a,now) end
                    R1.begin_fresh_episode(st,a,now)
                    st.phase="ATTACK_APPROACH"
                    if DEBUG_TELEMETRY then log("ATTACK_REASSERT_ACK uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
                        " issue="..p.issue.." target="..a.target_uid.." preserved_eligible_ms="..string.format("%.0f",preserved)..
                        " accepted_seq="..clean(art.accepted_seq).." count="..tostring(t.execution_reasserts)..
                        " model_ms="..string.format("%.0f",now).." policy=SAME_ACTION_SAME_TARGET_FRESH_GATE_RESET") end
                else
                    begin_attack_history(st,st.plan[p.idx],now,"OUR_CONTROLLER",p.issue)
                end
            end
            if not st.plan[p.idx+1] then
                if CONTROLLER_PHASE=="P1E" then st.terminal=true; st.phase="TERMINAL_ATTACK" end
                if st.moves>0 then
                    if DEBUG_TELEMETRY then S.route_passes=S.route_passes+1 end
                    if DEBUG_TELEMETRY then dlog("CASE_ROUTE_PASS uid="..st.uid.." gen="..st.gen.." own_moves="..st.moves.." attack_target="..p.target_uid.." visual_smoothness=UNASSESSED") end
                end
                if DEBUG_TELEMETRY then dlog("PHASE1_ATTACK_TERMINAL uid="..st.uid.." gen="..st.gen.." model_ms="..string.format("%.0f",now)) end
                if DEBUG_TELEMETRY then dlog("ATTACK_CURRENT_TAIL uid="..st.uid.." gen="..st.gen.." issue="..p.issue..
                    " model_ms="..string.format("%.0f",now).." automatic_exit=false appendable=true history="..
                    tostring(st.attack~=nil).." reason=NO_KNOWN_SUCCESSOR_YET") end
            end
        end
        return
    end
    if not accepted(r) then
        if DEBUG_TELEMETRY then dlog("EXTERNAL_RECORD_NOT_ACCEPTED uid="..st.uid.." serial="..r.serial.." type="..clean(r.order_type)..
            " status="..clean(r.status).." queued="..clean(r.is_queued).." rev="..r.unit_revision.." model_ms="..string.format("%.0f",now)) end
        if r.status=="INDETERMINATE" then fail("EXTERNAL_INDETERMINATE") end
        return
    end
    if st.revision and r.unit_revision~=inc(st.revision) then
        -- A capture anomaly can be raised after the poll preflight but before this
        -- page is ingested. Re-check status once so recoverable loss gets a chance
        -- to resync instead of being misclassified as a fatal revision gap.
        local before=S.last_capture_errors
        if not status() then return end
        if S.last_capture_errors~=before and st.recover_revision and cmp(r.unit_revision,st.recover_revision)<=0 then return end
        if st.revision and r.unit_revision~=inc(st.revision) then
            fail("EXTERNAL_REVISION_DISCONTINUITY uid="..st.uid); return
        end
    end
    st.revision=r.unit_revision
    if r.order_type~="MOVE" and r.order_type~="ATTACK" then
        local kind=r.order_type
        local reset_pos=point(st.unit)
        cancel(st,"EXTERNAL_"..clean(kind),now,true); st.blocked=false
        if kind=="HALT" then
            st.require_replace=false
            st.queue_reset_cert={revision=r.unit_revision,ms=now,pos=copy(reset_pos),reason="HALT_ACCEPTED"}
            if DEBUG_TELEMETRY then dlog("QUEUE_RESET_CERT_READY uid="..st.uid.." rev="..r.unit_revision.." reason=HALT_ACCEPTED model_ms="..now..
                " policy=NEXT_QUEUED_ORDER_MAY_SEED") end
        end
        return
    end
    local a,err=action(st,r,now)
    if not a then cancel(st,err,now,false); st.blocked=true; log("INPUT_REFUSED uid="..st.uid.." reason="..err); return end
    if not a.queued then
        cancel(st,"EXTERNAL_REPLACE",now,true); st.blocked=false; st.require_replace=false
    elseif (st.owned or (p and p.uid==st.uid)) and CONTROLLER_PHASE=="P1E" then
        cancel(st,"P1E_COMPAT_LIVE_APPEND_UNSUPPORTED",now,false); st.blocked=true
        if DEBUG_TELEMETRY then log("LIVE_APPEND_YIELD uid="..st.uid.." remaining_lua_plan_discarded=true") end; return
    elseif st.require_replace then
        if DEBUG_TELEMETRY then dlog("QUEUED_IGNORED_WAITING_FOR_REPLACE uid="..st.uid.." serial="..r.serial.." rev="..r.unit_revision) end
        return
    elseif st.blocked then
        if DEBUG_TELEMETRY then dlog("QUEUED_IGNORED_BLOCKED uid="..st.uid.." serial="..r.serial.." type="..a.type..
            " rev="..r.unit_revision.." phase="..clean(st.phase).." model_ms="..string.format("%.0f",now)) end
        return
    elseif #st.actions==0 then
        local age=cold and now-cold.ms or BSC_HUGE
        local cold_good=a.type=="MOVE" and cold and
            ((cold.native_state=="UNSEEN" and cold.revision=="MISSING") or
             (cold.native_state=="REVISION_ZERO" and cold.revision=="0")) and r.unit_revision=="1"
            and age>=0 and age<=CFG.cold_idle_max_age_ms and not S.late_start
        local reset=st.queue_reset_cert
        local reset_good=reset and id(reset.revision) and r.unit_revision==inc(reset.revision)
        local idle_cert=st.restart_idle_cert
        local idle_age=idle_cert and now-idle_cert.ms or BSC_HUGE
        local idle_good=idle_cert and id(idle_cert.revision) and r.unit_revision==inc(idle_cert.revision)
            and idle_age>=0 and idle_age<=CFG.restart_idle_max_age_ms
        if not cold_good and not reset_good and not idle_good then
            st.blocked=true
            if DEBUG_TELEMETRY then dlog("QUEUED_WITHOUT_REPLACE_IGNORED uid="..st.uid.." serial="..r.serial..
                " reason=NO_TRUSTED_QUEUE_EMPTY_PREDECESSOR native_plan_preserved=true") end
            return
        end
        st.gen=st.gen+1
        if cold_good then
            a.origin=copy(cold.pos); a.seed_mode="COLD_IDLE_QUEUED"
            if DEBUG_TELEMETRY then dlog("COLD_IDLE_SEED uid="..st.uid.." gen="..st.gen.." serial="..a.serial..
                " native_queued=true snapshot_revision="..cold.revision.." native_state="..cold.native_state.." rev="..r.unit_revision..
                " snapshot_ms="..string.format("%.0f",cold.ms).." age_ms="..string.format("%.0f",age)..
                " model_ms="..string.format("%.0f",now).." origin=OBSERVED_IDLE_BEFORE_FIRST_ORDER") end
        elseif reset_good then
            a.origin=copy(reset.pos or a.origin);a.seed_mode="QUEUE_RESET_QUEUED"
            if DEBUG_TELEMETRY then dlog("QUEUE_RESET_SEED uid="..st.uid.." gen="..st.gen.." serial="..a.serial..
                " reset_revision="..reset.revision.." rev="..r.unit_revision.." reset_reason="..clean(reset.reason)..
                " model_ms="..now.." origin=TRUSTED_QUEUE_RESET") end
        else
            a.origin=copy(idle_cert.pos or a.origin);a.seed_mode="STABLE_IDLE_QUEUED"
            if DEBUG_TELEMETRY then dlog("QUEUE_IDLE_SEED uid="..st.uid.." gen="..st.gen.." serial="..a.serial..
                " snapshot_revision="..idle_cert.revision.." rev="..r.unit_revision.." age_ms="..string.format("%.0f",idle_age)..
                " model_ms="..now.." origin=STABLE_CLEAN_IDLE") end
        end
        st.queue_reset_cert=nil;st.restart_idle_cert=nil;st.restart_idle_candidate=nil
        -- Preserve native queued=true. Do not forge a REPLACE or send a priming order.
    end
    if #st.actions>=CFG.max_actions and st.plan and st.idx>1 and not S.pending_by_uid[st.uid] then
        local n=st.idx-1
        for i=1,#st.actions-n do st.actions[i]=st.actions[i+n] end
        for i=#st.actions,#st.actions-n+1,-1 do st.actions[i]=nil end
        st.idx=1;st.action_base=(st.action_base or 0)+n
        if DEBUG_TELEMETRY then dlog("ACTION_HISTORY_COMPACTED uid="..st.uid.." removed="..n.." retained="..#st.actions) end
    end
    if #st.actions>=CFG.max_actions then
        log("ACTION_ADMISSION_REFUSED uid="..st.uid.." serial="..a.serial.." reason=ACTION_CAP existing_plan_preserved=true")
        return
    end
    st.action_serial=(st.action_serial or 0)+1;a.action_id=st.action_serial
    Core.assign_block(st,a)
    action_runtime(a)
    -- The action log is canonical: published indices and execution origin never reset on APPEND.
    local active=st.plan~=nil
    if active and st.plan~=st.actions then fail("CANONICAL_PLAN_IDENTITY"); return end
    st.actions[#st.actions+1]=a
    -- Validate only the active/future suffix. Historical completed actions (most
    -- importantly an Attack-first action whose target later dies/routes) must not
    -- veto a new Shift APPEND after execution has already advanced past them.
    local candidate={}
    local from=active and math.max(1,st.idx) or 1
    for i=from,#st.actions do candidate[#candidate+1]=st.actions[i] end
    local supported,why=plan_supported(st,candidate,active)
    if active and not supported then
        table.remove(st.actions,#st.actions)
        if a.block_id and (a.type=="ATTACK" or not st.actions[#st.actions] or st.actions[#st.actions].block_id~=a.block_id) then
            st.block_state[a.block_id]=nil
        end
        log("APPEND_REFUSED uid="..st.uid.." reason="..why.." policy=PRESERVE_EXISTING_ACTIONS");return
    end
    if not active then st.phase="NATIVE_TRACKING" end
    st.tail_reached=false
    if a.queued and p and p.uid==st.uid and p.gen==st.gen then p.saw_append=true end
    if DEBUG_TELEMETRY then dlog("ACTION_CAPTURE uid="..st.uid.." gen="..st.gen.." idx="..#st.actions.." type="..a.type.." serial="..a.serial.." queued="..tostring(a.queued).." seed_mode="..(a.seed_mode or "REPLACE_OR_APPEND").." model_ms="..string.format("%.0f",now)..
        " block="..clean(a.block_id).." block_kind="..clean(a.block_kind)..
        (a.pos and (" x="..string.format("%.6f",a.pos.x).." z="..string.format("%.6f",a.pos.z)) or (" target="..clean(a.target_uid)))) end
    if active then
        if DEBUG_TELEMETRY then dlog("PLAN_APPENDED uid="..st.uid.." gen="..st.gen.." serial="..a.serial..
            " idx="..#st.actions.." cursor="..st.idx.." actions="..#st.actions..
            " owned="..tostring(st.owned).." phase="..st.phase..
            " eligible_ms="..string.format("%.0f",st.attack and st.attack.eligible_ms or 0)..
            " model_ms="..string.format("%.0f",now).." timer_reset=false origin_reset=false") end
    end
end
function Core.valid_record(r,previous)
    return type(r)=="table" and r.epoch==S.epoch and id(r.serial) and cmp(r.serial,previous)>0
        and id(r.command_id) and id(r.unit_uid) and id(r.unit_revision) and id(r.script_issue_id)
        and type(r.order_type)=="string" and type(r.status)=="string" and type(r.source)=="string"
        and type(r.engine_seq_valid)=="boolean" and (not r.engine_seq_valid or id(r.engine_seq))
end
local function drain(now)
    for page=1,CFG.max_pages do
        local ok,rows,m=pcall(bridge.read_journal,S.epoch,S.cursor,CFG.page_size)
        if not ok or type(rows)~="table" or type(m)~="table" then fail("JOURNAL_"..clean(m or rows)); return false end
        if m.epoch~=S.epoch or m.gap~=false or m.overrun~=false or m.complete~=true or m.error~="Ok" or m.journal_fault~="Ok" then
            fail("JOURNAL_METADATA gap="..clean(m.gap).." overrun="..clean(m.overrun).." fault="..clean(m.journal_fault)); return false
        end
        if not id(m.next_after) or not id(m.newest_serial) or #rows>64 or m.count~=#rows then fail("JOURNAL_PAGE_CONTRACT"); return false end
        local previous=S.cursor
        for i=1,#rows do
            if not Core.valid_record(rows[i],previous) then fail("JOURNAL_RECORD_CONTRACT"); return false end
            previous=rows[i].serial
        end
        if m.next_after~=previous or cmp(m.newest_serial,previous)<0 then fail("JOURNAL_CURSOR_CONTRACT"); return false end
        -- Validate the entire page BEFORE ingesting any part of it.
        for i=1,#rows do Core.ingest(rows[i],now); if S.failed then return false end end
        if #rows>0 then
            local aok,a,ae=pcall(bridge.acknowledge,S.epoch,m.next_after)
            if not aok or a~=true then fail("ACK_"..clean(ae or a)); return false end
            S.cursor=m.next_after
        end
        if S.cursor==m.newest_serial then return true end
        if #rows==0 then fail("EMPTY_PAGE_WITH_BACKLOG"); return false end
    end
    -- Bounded work; no dispatch until every known earlier record is consumed.
    if DEBUG_TELEMETRY then log("JOURNAL_BACKLOG_DEFER cursor="..S.cursor) end
    return false
end
begin_attack_history=function(st,a,now,source,issue)
    st.phase="ATTACK_APPROACH"
    st.attack={issue=issue,idx=st.idx,accepted_ms=now,last_ms=now,eligible_ms=0,noneligible_ms=0,
        previous_eligible=false,observed_once=false,last_log=-1000000,done=false,
        target_uid=a.target_uid,long_wait_next_ms=CFG.attack_long_wait_notice_ms,
        target_last_pos=nil,target_last_ms=nil,target_speed=nil,native_player=(source=="PLAYER_NATIVE")}
    st.attack.feg=FEG.new(now,feg_width(st.unit),feg_width(a.target),nil,{require_fresh_reentry=a.requires_fresh_engagement==true})
    st.attack.legacy_eligible_ms=0;st.attack.legacy_previous=false
    R1.begin_fresh_episode(st,a,now)
    if DEBUG_TELEMETRY then log("FEG_ATTACK_BEGIN uid="..st.uid.." gen="..st.gen.." issue="..issue.." idx="..st.idx..
        " intended="..a.target_uid.." model_ms="..string.format("%.0f",now)..
        " source="..source.." has_tail="..tostring(st.plan[st.idx+1]~=nil)..
        " near="..num_or_nil(st.attack.feg.near).." hold_ms="..CFG.attack_hold_ms.." timer_reset=NEW_ATTACK_ONLY") end
    if a.requires_fresh_engagement then
        local art=action_runtime(a)
        if DEBUG_TELEMETRY then log("CENTER_A2_ACK uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " issue="..issue.." target="..a.target_uid.." accepted_seq="..clean(art.accepted_seq)..
            " accepted_receipt="..clean(art.accepted_receipt).." accepted_lifetime="..clean(art.accepted_lifetime)..
            " model_ms="..string.format("%.0f",now).." policy=POST_ACK_FRESH_EVIDENCE_ONLY") end
    end
    if DEBUG_TELEMETRY then dlog("ATTACK_ACCEPTED uid="..st.uid.." gen="..st.gen.." issue="..issue.." idx="..st.idx..
        " expected_revision="..st.revision.." rev="..st.revision.." intended="..a.target_uid..
        " model_ms="..string.format("%.0f",now).." hold_required_ms="..CFG.attack_hold_ms..
        " approach_timeout=DISABLED long_wait_notice_ms="..CFG.attack_long_wait_notice_ms..
        " hold_mode=MELEE_CURRENT_TARGET_OBSERVATION has_tail="..tostring(st.plan[st.idx+1]~=nil)..
        " appendable=true source="..source.." native_serial="..clean(a.serial)) end
end
function Core.activate(st)
    if st.plan or st.blocked or #st.actions==0 then return end
    local first=st.actions[1]
    local attack_first=CONTROLLER_PHASE=="P2B" and first.type=="ATTACK" and first.queued==false
    -- v1.0.7 observes a single current Move immediately. A successor is not
    -- required to record completion; takeover/dispatch still waits for a real tail.
    if #st.actions<1 then return end
    local good,why=plan_supported(st,st.actions)
    if not good then
        if st.refused~=why then
            log("TAKEOVER_REFUSED uid="..st.uid.." gen="..st.gen.." reason="..why.." native_plan_preserved=true")
            st.refused=why
        end
        return
    end
    if not first.origin then return end
    -- Each input payload was already copied at admission. The live native queue is NOT consulted.
    st.plan=st.actions; st.idx=1; st.origin=copy(first.origin)
    enter_action(st,first,clock(),attack_first and "PLAYER_ATTACK_ADOPTED" or "PLAYER_MOVE_ADOPTED")
    if attack_first then first.seed_mode="PLAYER_ATTACK_REPLACE" end
    st.phase=attack_first and "ATTACK_APPROACH" or "MOVE_TRACKING"
    if DEBUG_TELEMETRY then dlog("PLAN_ACTIVATED uid="..st.uid.." gen="..st.gen.." actions="..#st.plan..
        " cursor=1 phase="..CONTROLLER_PHASE.." appendable=true seed_mode="..(first.seed_mode or "REPLACE")..
        " first_type="..first.type.." model_ms="..string.format("%.0f",clock())) end
    if attack_first then
        -- The player's ordinary RMB Attack is already native-accepted. Never re-issue it.
        -- Start engagement history immediately so a later Shift pN does not reset the timer.
        st.owned=false
        if DEBUG_TELEMETRY then dlog("PLAYER_ATTACK_ADOPTED uid="..st.uid.." gen="..st.gen.." serial="..first.serial..
            " target="..first.target_uid.." rev="..st.revision.." appendable=true reissued=false") end
        begin_attack_history(st,first,clock(),"PLAYER_NATIVE","0")
    end
end
local function geometry(st,nexta)
    local a=st.plan[st.idx]; local p=st.pos
    if not p or a.type~="MOVE" then return nil end
    local origin=st.origin; local remain=dist(p,a.pos); local leg=dist(origin,a.pos)
    local progress=leg>0.001 and clamp((leg-remain)/leg,0,1) or 1
    local speed=median(st.speeds); local stall=#st.speeds>=2 and speed<=CFG.stall_speed
    local ratio=0
    if nexta.type=="MOVE" then
        local x,z=a.pos.x-origin.x,a.pos.z-origin.z
        local nx,nz=nexta.pos.x-a.pos.x,nexta.pos.z-a.pos.z
        local l=math.sqrt(x*x+z*z)*math.sqrt(nx*nx+nz*nz)
        if l>0.001 then ratio=math.acos(clamp((x*nx+z*nz)/l,-1,1))/math.pi end
    end
    local width=0; local ok,w=pcall(function() return st.unit:ordered_width() end)
    if ok and finite(w) and w>0 and w<=500 then width=w end
    local angle=CFG.angle_straight+(CFG.angle_uturn-CFG.angle_straight)*ratio
    local lead=math.min(CFG.lead_cap,math.max(CFG.lead_floor,
        angle+math.min(CFG.speed_cap,(speed or 0)*CFG.speed_seconds),
        width*(CFG.formation_straight+(CFG.formation_uturn-CFG.formation_straight)*ratio)))
    lead=math.min(lead,leg*(CFG.execution_straight+(CFG.execution_uturn-CFG.execution_straight)*ratio))
    return {remaining=remain,leg=leg,progress=progress,speed=speed or 0,stall=stall,threshold=lead,ratio=ratio}
end
local function attack_geometry(st,nexta,g)
    -- Only the immediate ATTACK is inspected; never inspect a post-ATTACK MOVE.
    local target=nexta.target and point(nexta.target)
    if not target then return nil end
    local a=st.plan[st.idx]
    local x,z=a.pos.x-st.origin.x,a.pos.z-st.origin.z
    local nx,nz=target.x-a.pos.x,target.z-a.pos.z
    local l=math.sqrt(x*x+z*z)*math.sqrt(nx*nx+nz*nz)
    local ratio=l>0.001 and math.acos(clamp((x*nx+z*nz)/l,-1,1))/math.pi or 0
    local angle=ratio*180
    local width=0; local ok,w=pcall(function() return st.unit:ordered_width() end)
    if ok and finite(w) and w>0 and w<=500 then width=w end
    local raw=math.min(CFG.attack_lead_cap,CFG.attack_lead_straight+
        (CFG.attack_lead_uturn-CFG.attack_lead_straight)*ratio+
        math.min(CFG.attack_speed_cap,g.speed*CFG.attack_speed_seconds)+
        math.min(CFG.attack_width_cap,width*CFG.attack_width_factor))
    local severity=clamp((angle-CFG.attack_uturn_start)/(180-CFG.attack_uturn_start),0,1)
    local cap=CFG.attack_execution_cap+(CFG.attack_uturn_execution_cap-CFG.attack_execution_cap)*severity
    local base=math.min(raw,g.leg*cap)
    -- Only a short, cap-limited high-angle leg gets a bounded one-poll margin.
    -- The margin cannot bypass the execution cap, 20% progress or 35m global cap.
    local dt=math.min(st.model_step_ms or 0,CFG.attack_poll_horizon_ms)/1000
    local instant=st.speeds[#st.speeds] or 0
    local margin=0
    if severity>0 and g.leg*CFG.attack_execution_cap<raw then
        margin=math.min(CFG.attack_poll_lead_cap,math.min(g.speed,instant)*dt)*severity
    end
    g.threshold=math.min(CFG.attack_lead_cap,g.leg*cap,raw+margin)
    g.raw_threshold=raw; g.base_threshold=base; g.poll_margin=margin; g.execution_cap=cap
    g.ratio=ratio; g.angle_deg=angle; g.width=width; g.target_pos=target
    g.instant_speed=instant; g.samples=#st.speeds; g.model_step_ms=st.model_step_ms or 0
    g.input_age_ms=math.max(0,clock()-nexta.captured_ms)
    g.late_input=g.input_age_ms<=g.model_step_ms and g.remaining<=g.threshold
    return g
end
local function attack_brake_state(g)
    local instant=g.instant_speed or 0
    local drop=(g.speed or 0)-instant
    local signal=g.samples>=CFG.attack_brake_preempt_min_samples
        and g.speed>=CFG.attack_brake_preempt_min_speed
        and instant<math.max(CFG.stall_speed,g.speed*CFG.attack_brake_preempt_ratio)
        and drop>=CFG.attack_brake_preempt_drop
    local threshold=math.min(CFG.attack_brake_preempt_cap,g.threshold+CFG.attack_brake_preempt_extra,
        g.leg*CFG.attack_brake_preempt_execution_cap)
    g.brake_signal=signal;g.brake_drop=drop;g.brake_threshold=threshold
    return signal,threshold,drop
end
local function ordered_width_hint(st)
    local ok,w=pcall(function() return st.unit:ordered_width() end)
    return ok and finite(w) and w>=0 and w<=500 and w or 0
end
local function move_reach_tolerance(st,leg)
    local tol=clamp(ordered_width_hint(st)*CFG.move_reach_width_factor,CFG.move_reach_floor_m,CFG.move_reach_cap_m)
    if finite(leg) and leg>0 then
        tol=math.min(tol,math.max(CFG.move_reach_floor_m,leg*CFG.move_reach_short_fraction))
    end
    return tol
end
function Core.move_idle_finish_envelope(st)
    return math.min(CFG.move_idle_finish_cap_m,CFG.move_idle_finish_base_m+ordered_width_hint(st)*CFG.move_idle_finish_width_factor)
end
local function point_segment_error(p,a,b)
    local vx,vz=b.x-a.x,b.z-a.z
    local wx,wz=p.x-a.x,p.z-a.z
    local ll=vx*vx+vz*vz
    if ll<=0.000001 then return dist(p,a) end
    local t=clamp((wx*vx+wz*vz)/ll,0,1)
    local q={x=a.x+t*vx,y=0,z=a.z+t*vz}
    return dist(p,q)
end
register_route_obligation=function(st,a,g,now)
    if not a or a.type~="MOVE" then return end
    local rt=action_runtime(a)
    if rt.semantic_done then return end
    local b=a.block_id and ensure_block_state(st,a.block_id,a.block_kind) or nil
    if not b then return end
    b.route_debts=b.route_debts or {}
    if b.route_debts[a.action_id] then return end
    local initial_remaining=st.pos and dist(st.pos,a.pos) or nil
    b.route_debts[a.action_id]={action=a,
        tolerance=math.max(CFG.move_reach_floor_m,g and g.cut_tolerance or move_reach_tolerance(st)),
        since=now,best_remaining=initial_remaining,last_remaining=initial_remaining,last_progress_ms=now,
        trend_start_ms=now,trend_start_remaining=initial_remaining,trend_gain_m=0,trend_window_ms=0}
    if DEBUG_TELEMETRY then dlog("ROUTE_OBLIGATION_TRANSFERRED uid="..st.uid.." gen="..st.gen.." block="..b.id.." action="..a.action_id..
        " tolerance="..num_or_nil(b.route_debts[a.action_id].tolerance).." model_ms="..now) end
end
function Core.observe_route_obligations(st,now)
    if not st.pos or not st.block_state then return end
    for _,b in pairs(st.block_state) do
        if b.route_debts then
            for aid,debt in pairs(b.route_debts) do
                local a=debt.action
                if not a or action_runtime(a).semantic_done then
                    b.route_debts[aid]=nil
                else
                    local tolerance=debt.tolerance or move_reach_tolerance(st)
                    local remaining=dist(st.pos,a.pos)
                    if debt.best_remaining==nil or remaining<debt.best_remaining-CFG.route_debt_progress_epsilon_m then
                        debt.best_remaining=remaining;debt.last_progress_ms=now
                    end
                    if debt.trend_start_remaining==nil then
                        debt.trend_start_ms=now;debt.trend_start_remaining=remaining
                    elseif now-(debt.trend_start_ms or now)>=CFG.route_debt_trend_window_ms then
                        debt.trend_gain_m=(debt.trend_start_remaining or remaining)-remaining
                        debt.trend_window_ms=now-(debt.trend_start_ms or now)
                        debt.trend_start_ms=now;debt.trend_start_remaining=remaining
                    end
                    debt.last_remaining=remaining;debt.last_sample_ms=now
                    local passed=st.prev_pos and point_segment_error(a.pos,st.prev_pos,st.pos)<=tolerance
                    if remaining<=tolerance or passed then
                        mark_action_complete(st,a,"HANDOFF_ROUTE_OBLIGATION_SATISFIED",now,remaining)
                        b.route_debts[aid]=nil
                        if DEBUG_TELEMETRY then dlog("ROUTE_OBLIGATION_SATISFIED uid="..st.uid.." gen="..st.gen.." block="..b.id.." action="..a.action_id..
                            " remaining="..num_or_nil(remaining).." tolerance="..num_or_nil(tolerance).." model_ms="..now) end
                    end
                end
            end
        end
    end
end
local function block_route_clear(st,a)
    if not a or not a.block_id or not st.block_state then return true end
    local b=st.block_state[a.block_id]
    if not b or not b.route_debts then return true end
    for _,debt in pairs(b.route_debts) do
        if debt and debt.action and not action_runtime(debt.action).semantic_done then return false,b end
    end
    return true,b
end
local function stalled_route_debt(st,b,now)
    if not st or not b or not b.route_debts or not st.pos then return nil end
    local current_action=st.plan and st.plan[st.idx] or nil
    for _,debt in pairs(b.route_debts) do
        if debt and debt.action and not action_runtime(debt.action).semantic_done then
            local tolerance=debt.tolerance or move_reach_tolerance(st)
            local remaining=dist(st.pos,debt.action.pos)
            local no_progress=now-(debt.last_progress_ms or debt.since or now)
            -- Near the owed waypoint, do not declare the route dead. CA formations can
            -- oscillate by several metres while turning/reforming before crossing it.
            if remaining>tolerance+CFG.route_debt_close_grace_m and no_progress>=CFG.route_debt_stall_ms then
                local live_gain=(debt.trend_start_remaining or remaining)-remaining
                local trend_gain=math.max(debt.trend_gain_m or 0,live_gain)
                local path_error=nil
                if current_action and current_action.type=="MOVE" and current_action.pos then
                    path_error=point_segment_error(debt.action.pos,st.pos,current_action.pos)
                end
                local current_path_can_pay=path_error~=nil and path_error<=tolerance+CFG.route_debt_path_grace_m
                if trend_gain<CFG.route_debt_trend_required_m and not current_path_can_pay then
                    debt.stall_remaining=remaining;debt.stall_no_progress_ms=no_progress
                    debt.stall_trend_gain_m=trend_gain;debt.stall_path_error=path_error
                    return debt
                end
            end
        end
    end
    return nil
end
local function move_route_debt_soft_continue(st,cur,nexta,g)
    local clear,b=block_route_clear(st,cur)
    if clear then
        g.route_debt_mode="CLEAR";g.route_debt_count=0
        return true,"PRIOR_ROUTE_CLEAR"
    end
    -- SC3: route debt remains authoritative evidence, but a pure Move->Move handoff
    -- no longer hard-blocks solely because an earlier waypoint has not yet been
    -- physically stamped. The PROPOSED replacement chord must still preserve every
    -- unresolved debt inside its tolerance corridor. If it would cut away from any
    -- owed waypoint, keep the old hard block. Attack/final-route checks still use
    -- block_route_clear() directly and therefore remain strict.
    if not nexta or nexta.type~="MOVE" or not st.pos or not nexta.pos or not b or not b.route_debts then
        g.route_debt_mode="HARD";g.route_debt_reason="PRIOR_ROUTE_OBLIGATION_PENDING"
        return false,g.route_debt_reason
    end
    local count,max_error,max_limit=0,0,0
    for _,debt in pairs(b.route_debts) do
        if debt and debt.action and not action_runtime(debt.action).semantic_done then
            count=count+1
            local tolerance=debt.tolerance or move_reach_tolerance(st)
            local limit=tolerance+CFG.route_debt_soft_handoff_grace_m
            local path_error=point_segment_error(debt.action.pos,st.pos,nexta.pos)
            if path_error>max_error then max_error=path_error end
            if limit>max_limit then max_limit=limit end
            if path_error>limit then
                g.route_debt_mode="HARD";g.route_debt_count=count;g.route_debt_error=path_error;g.route_debt_limit=limit
                g.route_debt_reason="PRIOR_ROUTE_OBLIGATION_DEVIATION"
                return false,g.route_debt_reason
            end
        end
    end
    g.route_debt_mode="SOFT_PRESERVED";g.route_debt_count=count;g.route_debt_error=max_error;g.route_debt_limit=max_limit
    g.route_debt_reason="PRIOR_ROUTE_OBLIGATION_SOFT_CONTINUE"
    return true,g.route_debt_reason
end
local function route_handoff_ready(st,g,nexta)
    local cur=st.plan[st.idx]
    local rt=action_runtime(cur)
    local prior_clear=block_route_clear(st,cur)
    if not prior_clear then
        -- Move->Attack remains hard: no unresolved earlier waypoint may leak across
        -- the semantic boundary. Only pure Move->Move can use SC3 soft continuation.
        if nexta.type=="ATTACK" then
            g.route_safe=false;g.route_mode="BLOCKED";g.route_reason="PRIOR_ROUTE_OBLIGATION_PENDING"
            g.route_debt_mode="HARD";g.route_debt_reason=g.route_reason
            return false,g.route_reason
        end
        local soft_ok,soft_reason=move_route_debt_soft_continue(st,cur,nexta,g)
        if not soft_ok then
            g.route_safe=false;g.route_mode="BLOCKED";g.route_reason=soft_reason
            return false,g.route_reason
        end
    else
        g.route_debt_mode="CLEAR";g.route_debt_count=0
    end
    if rt.semantic_done then
        g.route_safe=true;g.route_mode="COMPLETE";g.route_reason="ACTION_COMPLETE";g.cut_error=0;g.cut_tolerance=BSC_HUGE
        return true,g.route_reason
    end
    -- Move -> Attack remains intentionally strict and is outside SC1.
    -- Only Move -> Move may interpret an intermediate waypoint as steering guidance.
    if nexta.type=="ATTACK" then
        g.route_safe=false;g.route_mode="BLOCKED";g.route_reason="ATTACK_REQUIRES_ROUTE_COMPLETE"
        return false,g.route_reason
    end
    local q=nexta.pos
    if not st.pos or not q then
        g.route_safe=false;g.route_mode="BLOCKED";g.route_reason="NEXT_ENDPOINT_UNAVAILABLE"
        return false,g.route_reason
    end

    -- A. Preserve the old strict path first. If the direct successor chord still
    -- passes close enough to the current waypoint, nothing about B2 changes.
    local next_leg=dist(cur.pos,q)
    local tol=clamp(ordered_width_hint(st)*CFG.route_cut_width_factor,CFG.route_cut_floor_m,CFG.route_cut_cap_m)
    if g.leg<60 then tol=math.min(tol,math.max(1,g.leg*CFG.route_short_fraction)) end
    local min_progress=CFG.route_move_min_progress
    local err=point_segment_error(cur.pos,st.pos,q)
    -- A very short successor leg must not be swallowed merely because formation-width
    -- tolerance is large. Cap strict chord slack by the adjacent-leg scale as well.
    local next_leg_limit=math.max(1,next_leg*CFG.route_corner_next_leg_fraction)
    local safe_limit=math.min(tol*CFG.route_cut_safety_ratio,next_leg_limit)
    g.cut_error=err;g.cut_tolerance=tol;g.cut_safe_limit=safe_limit;g.route_min_progress=min_progress;g.next_leg=next_leg
    if g.progress>=min_progress and err<=safe_limit then
        g.route_safe=true;g.route_mode="PATH_SAFE";g.route_reason="PATH_DEVIATION_SAFE_WITH_MARGIN"
        return true,g.route_reason
    end

    -- B. SC1 steering corridor. A waypoint is an intermediate navigation guide,
    -- not an arrival target. Predict a bounded turn-start distance from live speed,
    -- formation width and turn severity, then cap it by BOTH adjacent legs so short
    -- zig-zags cannot be swallowed wholesale. This gate does not itself dispatch:
    -- advance() still requires the original proximity/predictive/brake thresholds.
    local width=ordered_width_hint(st)
    local lookahead=clamp((g.speed or 0)*CFG.route_corner_speed_seconds+width*CFG.route_corner_width_factor,
        CFG.route_corner_min_lookahead_m,CFG.route_corner_max_lookahead_m)
    local turn_factor=CFG.route_corner_turn_base+CFG.route_corner_turn_extra*(g.ratio or 0)
    local base_corner_window=math.min(lookahead*turn_factor,
        g.leg*CFG.route_corner_current_leg_fraction,
        next_leg*CFG.route_corner_next_leg_fraction)
    -- SC2 EARLY A/B: if CA has already started braking before SC1's dynamic corridor,
    -- entering the controller's existing predictive threshold should pre-empt that
    -- arrival profile. Keep a 75% cap on BOTH adjacent legs so tiny nodes are not
    -- swallowed. No debt/ACK/Attack/Native semantics are changed by this experiment.
    local early_corner_window=math.min(g.threshold or 0,
        g.leg*CFG.route_corner_early_leg_fraction,
        next_leg*CFG.route_corner_early_leg_fraction)
    local corner_window=math.max(base_corner_window,early_corner_window)
    g.corner_lookahead=lookahead;g.corner_turn_factor=turn_factor;g.corner_window_base=base_corner_window
    g.corner_window_early=early_corner_window;g.corner_window=corner_window;g.next_leg=next_leg

    if g.progress>=min_progress and g.remaining<=corner_window then
        g.route_safe=true;g.route_mode="STEERING_CORNER";g.route_reason="TURN_CORRIDOR_ENTERED"
        return true,g.route_reason
    end

    -- SC4: the 1020 live log showed pure Move->Move units parked just outside the
    -- corridor (e.g. remaining 17.23m vs corner 16.36m) for several model seconds.
    -- Once this action has already moved, a sustained lack of waypoint progress or
    -- the existing low-speed stall signal is evidence that CA's arrival behaviour is
    -- winning the race. Escape only inside a small margin capped by BOTH adjacent
    -- legs and the already-computed predictive threshold; short zig-zags therefore
    -- retain their protection. ACK semantics stay STEERING_CORNER, so the rounded
    -- waypoint completes without creating return debt exactly like SC1/SC2.
    local stall_now=clock()
    local no_progress_ms=rt.last_progress_ms and math.max(0,stall_now-rt.last_progress_ms) or 0
    local stall_escape_margin=math.min(CFG.route_corner_stall_escape_extra_m,
        g.leg*CFG.route_corner_stall_escape_current_leg_fraction,
        next_leg*CFG.route_corner_stall_escape_next_leg_fraction)
    local stall_escape_limit=math.min(g.threshold or 0,corner_window+stall_escape_margin)
    local stall_escape_signal=g.stall or (rt.movement_seen and no_progress_ms>=CFG.route_corner_stall_escape_ms)
    g.corner_stall_no_progress_ms=no_progress_ms;g.corner_stall_escape_margin=stall_escape_margin
    g.corner_stall_escape_limit=stall_escape_limit;g.corner_stall_escape_signal=stall_escape_signal
    if g.progress>=min_progress and stall_escape_signal and g.remaining<=stall_escape_limit then
        g.route_safe=true;g.route_mode="STEERING_CORNER";g.route_reason="TURN_CORRIDOR_STALL_ESCAPE";g.corner_stall_escape=true
        if DEBUG_TELEMETRY then dlog("TURN_CORRIDOR_STALL_ESCAPE uid="..st.uid.." gen="..st.gen.." action="..cur.action_id..
            " successor="..clean(nexta.action_id).." remaining="..num_or_nil(g.remaining).." speed="..num_or_nil(g.speed)..
            " no_progress_ms="..num_or_nil(no_progress_ms).." corner_window="..num_or_nil(corner_window)..
            " escape_limit="..num_or_nil(stall_escape_limit).." next_leg="..num_or_nil(next_leg).." model_ms="..stall_now) end
        return true,g.route_reason
    end

    g.route_safe=false;g.route_mode="BLOCKED"
    g.route_reason=g.progress<min_progress and "ROUTE_PROGRESS_REQUIRED" or "TURN_CORRIDOR_REQUIRED"
    return false,g.route_reason
end
function Core.observe_move_completion(st,now)
    if not st.plan then return end
    local a=st.plan[st.idx]
    if not a or a.type~="MOVE" or not st.pos then return end
    local rt=enter_action(st,a,now,"CURRENT_MOVE_OBSERVED")
    local origin=st.origin or a.origin or rt.entry_pos
    if not origin then return end
    local remaining=dist(st.pos,a.pos)
    local leg=math.max(0.000001,dist(origin,a.pos))
    local progress=clamp((leg-remaining)/leg,0,1)
    local speed=median(st.speeds) or 0
    if not rt.best_remaining or remaining<rt.best_remaining-0.25 then
        rt.best_remaining=remaining;rt.last_progress_ms=now
    end
    rt.last_remaining=remaining;rt.progress=progress
    if speed>CFG.stall_speed or (rt.entry_pos and dist(rt.entry_pos,st.pos)>1) then rt.movement_seen=true end
    if rt.semantic_done then return end
    local reach=move_reach_tolerance(st,leg)
    local passed=st.prev_pos and point_segment_error(a.pos,st.prev_pos,st.pos)<=reach
    if remaining<=reach or passed then
        mark_action_complete(st,a,passed and "ROUTE_NODE_PASSED" or "ROUTE_NODE_REACHED",now,remaining)
        rt.idle_candidate=nil
        return
    end
    local idle=api_bool(st.unit,"is_idle")==true and api_bool(st.unit,"is_moving")==false
        and api_bool(st.unit,"is_in_melee")==false
    local ok,target=pcall(function() return st.unit:current_target() end)
    local idle_limit=math.min(Core.move_idle_finish_envelope(st),math.max(CFG.move_reach_floor_m,leg*CFG.move_idle_finish_leg_fraction))
    local natural=idle and ok and target==nil and rt.movement_seen and progress>=CFG.move_idle_finish_progress
        and remaining<=idle_limit
    if not natural then rt.idle_candidate=nil;return end
    local c=rt.idle_candidate
    if not c or now-c.last_ms>CFG.attack_observation_gap_ms or dist(c.pos,st.pos)>CFG.move_idle_finish_drift_m then
        rt.idle_candidate={since=now,last_ms=now,pos=copy(st.pos)};return
    end
    c.last_ms=now
    if now-c.since>=CFG.move_idle_finish_confirm_ms then
        mark_action_complete(st,a,"NATIVE_IDLE_ROUTE_FINISH",now,remaining)
    end
end
function Core.mark_exit_committed(st,b,reason,now,displacement,nearest,contacts)
    if b.exit_committed then return end
    b.exit_committed=true;b.exit_commit_ms=now;b.exit_commit_reason=reason
    if DEBUG_TELEMETRY then log("EXIT_BLOCK_COMMITTED uid="..st.uid.." gen="..st.gen.." block="..b.id..
        " reason="..reason.." displacement="..num_or_nil(displacement).." nearest_enemy_bbox="..num_or_nil(nearest)..
        " contact_count="..clean(contacts).." model_ms="..now.." claim=HISTORICAL_EVIDENCE_NOT_PERMANENT_PERMISSION") end
end
function Core.scan_exit_enemy_contacts(st,b,now,observed)
    local cached=b.contact_scan
    if cached and now-cached.ms<CFG.exit_contact_scan_ms then return cached end
    local count,nearest,unknown=0,nil,next(S.targets)==nil
    local contact_uids={}
    for tu,target in pairs(S.targets) do
        local skip=false
        local okmen,men=pcall(function() return target:number_of_men_alive() end)
        if okmen and finite(men) and men==0 then skip=true end
        if not skip then
            local valid=api_bool(target,"is_valid_target")
            if valid==true then
                local d=unit_distance_to(st.unit,target)
                if d==nil then unknown=true
                else
                    nearest=not nearest and d or math.min(nearest,d)
                    if d<=CFG.exit_global_contact_m then count=count+1;contact_uids[#contact_uids+1]=tu end
                end
            else
                -- Hidden/entering/leaving/unmeasurable is not proof of absence.
                unknown=true
            end
        end
    end
    table.sort(contact_uids)
    cached={ms=now,count=count,nearest=nearest,unknown=unknown,uids=table.concat(contact_uids,",")}
    b.contact_scan=cached
    if DEBUG_TELEMETRY and (not b.last_contact_log_ms or now-b.last_contact_log_ms>=1000 or b.logged_uids~=cached.uids or b.logged_unknown~=unknown) then
        b.last_contact_log_ms=now;b.logged_uids=cached.uids;b.logged_unknown=unknown
        if DEBUG_TELEMETRY then dlog("EXIT_GLOBAL_CONTACTS uid="..st.uid.." gen="..st.gen.." block="..b.id..
            " melee="..clean(api_bool(st.unit,"is_in_melee")).." observed="..clean(observed)..
            " contacts="..count.." contact_uids="..clean(cached.uids).." nearest_enemy_bbox="..num_or_nil(nearest)..
            " unknown="..tostring(unknown).." model_ms="..now) end
    end
    return cached
end
function Core.observe_exit_block(st,now)
    local a=st.plan and st.plan[st.idx]
    if not a or a.type~="MOVE" or a.block_kind~="EXIT_ROUTE" then return end
    local b=current_block(st);if not b or b.closed or not b.exit_started_ms or not st.pos then return end
    local rt=action_runtime(a)
    local src=b.exit_source_target
    if src and not b.source_ended_logged then
        local ok,men=pcall(function() return src:number_of_men_alive() end)
        if ok and men==0 then b.source_ended_logged=true;if DEBUG_TELEMETRY then dlog("EXIT_SOURCE_TARGET_ENDED_WAIT_GLOBAL_CLEAR uid="..st.uid.." gen="..st.gen.." block="..b.id.." model_ms="..now) end end
    end
    local displacement=b.exit_start_pos and dist(b.exit_start_pos,st.pos) or 0
    local melee=api_bool(st.unit,"is_in_melee")
    local ok,current=pcall(function() return st.unit:current_target() end)
    local observed=(ok and current) and uid(current) or nil
    local contacts=Core.scan_exit_enemy_contacts(st,b,now,observed)
    R1.trace_physical(st,a,now)
    local reason;local v3status,v3why=R1.v3_exit_body_status(st,a,now)
    if DEBUG_TELEMETRY then
        local sig=v3status and table.concat({tostring(v3status.live),tostring(v3status.body),tostring(v3status.progressing),
            tostring(v3status.contacted),tostring(v3status.body_established),tostring(v3status.progressing_majority),
            tostring(v3status.body_contact_majority),tostring(v3status.contact_mapping_ready),tostring(v3status.nearby_unmapped),tostring(v3status.order~=nil),tostring(v3status.handoff~=nil)},":") or ("MISS:"..clean(v3why))
        if b.v3_exit_status_sig~=sig or now-(b.v3_exit_status_log_ms or -1000000)>=1500 then
            b.v3_exit_status_sig=sig;b.v3_exit_status_log_ms=now
            if DEBUG_TELEMETRY then dlog("V3_EXIT_BODY_STATUS uid="..st.uid.." gen="..st.gen.." block="..clean(b.id)..
                " action="..a.action_id.." route_done="..tostring(rt.semantic_done)..
                " live="..tostring(v3status and v3status.live or 0).." body="..tostring(v3status and v3status.body or 0)..
                " progressing="..tostring(v3status and v3status.progressing or 0).." contacted="..tostring(v3status and v3status.contacted or 0)..
                " body_established="..tostring(v3status and v3status.body_established or false)..
                " progressing_majority="..tostring(v3status and v3status.progressing_majority or false)..
                " body_contact_majority="..tostring(v3status and v3status.body_contact_majority or false)..
                " contact_mapping_ready="..tostring(v3status and v3status.contact_mapping_ready or false)..
                " nearby_unmapped="..tostring(v3status and v3status.nearby_unmapped or 0)..
                " live_order="..tostring(v3status and v3status.order~=nil or false)..
                " pre_frozen="..tostring(v3status and v3status.handoff~=nil or false)..
                " reason="..clean(v3why).." model_ms="..now) end
        end
    end
    if displacement>=CFG.exit_min_displacement_m and v3status then
        if not rt.semantic_done and v3status.progressing_majority then
            reason="V3_BODY_MAJORITY_PROGRESSING_EXACT_EXIT_ORDER"
        elseif rt.semantic_done and v3status.body_established and v3status.contact_mapping_ready and not v3status.body_contact_majority and S.v3_contact_healthy~=false then
            reason="V3_ROUTE_DONE_BODY_MAJORITY_OPERABLE"
        end
    elseif ((S.evidence_v3_caps or {}).entity_snapshot~=true or (S.evidence_v3_caps or {}).execution_identity~=true)
        and displacement>=CFG.exit_min_displacement_m and ok and contacts and contacts.count==0 and not contacts.unknown then
        -- Compatibility only when V3 evidence is unavailable. This path never uses
        -- the retracted +0x74 collision-profile field as a melee state.
        if melee==false then reason="LEGACY_GLOBAL_MELEE_CLEARED_AFTER_EXIT_MOTION"
        elseif melee==true then reason="LEGACY_GLOBAL_CONTACT_CLEAR_STICKY_MELEE" end
    end
    b.last_observed_uid=observed;b.last_melee=melee;b.last_displacement=displacement
    b.last_global_contacts=contacts and contacts.count
    b.last_global_contact_unknown=not contacts or contacts.unknown
    b.evidence_ms=now;b.entity_operable=v3status and (v3status.progressing_majority or (rt.semantic_done and v3status.body_established and v3status.contact_mapping_ready and not v3status.body_contact_majority)) or false
    b.combat_clear=false;b.evidence_reason=reason or (v3why or "CONTACT_OR_EVIDENCE_UNRESOLVED")
    if not reason then
        b.clear_candidate=nil
        if b.exit_permission then
            if DEBUG_TELEMETRY then log("EXIT_PERMISSION_REVOKED uid="..st.uid.." gen="..st.gen.." block="..b.id..
                " action="..a.action_id.." model_ms="..now.." history_preserved=true reason="..b.evidence_reason) end
        end
        b.exit_permission=false
        return
    end
    -- Fresh observations renew a CURRENT permit, not the historical completion bit.
    local sample_ms=v3status and v3status.sample_ms or now
    local required=(reason=="LEGACY_GLOBAL_CONTACT_CLEAR_STICKY_MELEE") and CFG.exit_sticky_clear_confirm_ms or CFG.exit_clear_confirm_ms
    local c=b.clear_candidate
    if not c or c.reason~=reason or sample_ms<c.last_ms or sample_ms-c.last_ms>CFG.attack_observation_gap_ms then
        if b.exit_permission then
            if DEBUG_TELEMETRY then log("EXIT_PERMISSION_REVOKED uid="..st.uid.." gen="..st.gen.." block="..b.id..
                " action="..a.action_id.." model_ms="..now.." history_preserved=true reason=CLEAR_EVIDENCE_CHANGED_OR_GAPPED") end
        end
        b.clear_candidate={reason=reason,since=sample_ms,last_ms=sample_ms};b.exit_permission=false;return
    end
    c.last_ms=sample_ms
    if sample_ms-c.since>=required then
        if not b.exit_permission then
            if DEBUG_TELEMETRY then log("EXIT_PERMISSION_READY uid="..st.uid.." gen="..st.gen.." block="..b.id.." reason="..reason.." model_ms="..now) end
        end
        b.exit_permission=true;b.permission_ms=sample_ms
        Core.mark_exit_committed(st,b,reason,now,displacement,contacts and contacts.nearest,contacts and contacts.count)
        if rt.fault and rt.fault.code=="BLOCKED_EVIDENCE" then R1.clear_fault(st,a,now) end
    end
end

local function exit_gate_ready(st,nexta)
    local a=st.plan[st.idx]
    if not a or a.block_kind~="EXIT_ROUTE" or nexta.type~="ATTACK" then return true end
    -- CENTER-A2 RESEARCH: the player's Exit waypoint is an intent/route obligation.
    -- Physical disengagement is NOT a precondition for issuing the next Attack;
    -- fresh engagement is proven after A2 ACK by a fresh-mode FEG episode.
    local rt=action_runtime(a)
    local clear=block_route_clear(st,a)
    return rt.semantic_done==true and clear==true
end

local function transition_handoff_ready(st,g,nexta)
    -- R04/R07: exit evidence never erases ANY Move, including the final one.
    local route_ok,why=route_handoff_ready(st,g,nexta)
    if not route_ok then return false,why end
    return true,why
end

local function attack_metrics(g,now)
    return " execution_cap="..string.format("%.6f",g.execution_cap)..
        " poll_margin="..string.format("%.6f",g.poll_margin)..
        " model_step_ms="..string.format("%.0f",g.model_step_ms)..
        " input_age_ms="..string.format("%.0f",g.input_age_ms).." late_input="..tostring(g.late_input)..
        " leg="..string.format("%.6f",g.leg)..
        " progress="..string.format("%.6f",g.progress).." instant_speed="..string.format("%.6f",g.instant_speed)..
        " speed_samples="..g.samples.." angle_deg="..string.format("%.6f",g.ratio*180)..
        " width="..string.format("%.6f",g.width).." raw_threshold="..string.format("%.6f",g.raw_threshold)..
        " target_x="..string.format("%.6f",g.target_pos.x).." target_z="..string.format("%.6f",g.target_pos.z)
end
local function skip_future_attack_keep_tail(st,index,why,now)
    local a=st.plan and st.plan[index]
    local tail=st.plan and st.plan[index+1]
    if not a or a.type~="ATTACK" or not abortable_target_reason(why) then return false end
    local skipped_action_id=a.action_id
    table.remove(st.plan,index) -- st.plan and st.actions are the canonical same table while active.
    Core.detach_skipped_attack_block(st,index,skipped_action_id)
    st.refused=nil;st.blocked=false;st.phase="MOVE_TRACKING";st.tail_reached=false
    if DEBUG_TELEMETRY then log("ATTACK_SKIPPED_CONTINUE_TAIL uid="..st.uid.." gen="..st.gen.." skipped_idx="..index..
        " reason="..why.." successor_type="..(tail and tail.type or "NONE").." model_ms="..string.format("%.0f",now)..
        " policy=PRESERVE_P1_AND_REEVALUATE_SUCCESSOR") end
    return true
end

function Core.vector_at(st,p)
    -- The v0.5.0 runtime-tested constructor is v_offset, not a guessed v() ABI.
    local base=st.unit:position()
    return v_offset(base,p.x-base:get_x(),p.y-base:get_y(),p.z-base:get_z())
end
local function dispatch(st,index,reason,g,now,opts)
    opts=opts or {}
    if S.pending_by_uid[st.uid] or S.pending_count>=CFG.max_inflight or S.failed then return end
    local generation=st.gen
    local selected_base=st.action_base or 0
    local selected=st.plan and st.plan[index]
    if not status() then return end
    if not drain(now) or S.pending_by_uid[st.uid] or S.pending_count>=CFG.max_inflight or S.failed or st.gen~=generation or not st.plan then return end
    if not status() or S.pending_by_uid[st.uid] or S.pending_count>=CFG.max_inflight or S.failed or st.gen~=generation or not st.plan then return end
    if (st.action_base or 0)~=selected_base then
        if DEBUG_TELEMETRY then dlog("DISPATCH_REDECIDE_COMPACTED uid="..st.uid.." gen="..st.gen) end;return
    end
    local expected_index=opts.reassert_current and st.idx or (st.idx+1)
    if st.plan[index]~=selected or index~=expected_index then fail("DISPATCH_CURSOR_IDENTITY"); return end
    local a=st.plan[index]
    if not a then fail("DISPATCH_ACTION_MISSING"); return end
    if not Core.arm(a.type) then
        if now-st.last_wait>=1000 then
            st.last_wait=now; if DEBUG_TELEMETRY then dlog("WAIT_CALIBRATION uid="..st.uid.." kind="..a.type.." note=natural_player_"..string.lower(a.type).."_required") end
        end
        return
    end
    local rev=st.revision
    if not id(rev) then fail("PLAN_REVISION_MISSING"); return end
    local ok,current,err=pcall(bridge.get_unit_revision,st.uid)
    if not ok or not id(current) then fail("REVISION_"..clean(err or current)); return end
    -- Do NOT replace rev with current. That would reauthorize a stale plan.
    if current~=rev then
        cancel(st,"REVISION_CHANGED_BEFORE_DISPATCH",now,true); st.blocked=true; return
    end
    if a.type=="ATTACK" then
        local cur=st.plan[st.idx]
        if cur and cur.type=="MOVE" then
            if not action_runtime(cur).semantic_done or not block_route_clear(st,cur) then
                if DEBUG_TELEMETRY then log("HANDOFF_POST_DRAIN_DEFER uid="..st.uid.." gen="..st.gen.." reason=R1_GUARD_RECHECK model_ms="..now) end
                return
            end
        end
        local good,why=target_ready(a,now)
        if not good then
            if skip_future_attack_keep_tail(st,index,why,now) then return end
            target_wait(st,why,now);return
        end
    end
    if st.attack and not st.attack.done then
        local good,why=target_ready(st.plan[st.idx],now)
        if not good then
            if abortable_target_reason(why) then opts.attack_abort=why
            else target_wait(st,why,now);return end
        end
    end
    local from_attack=st.attack~=nil and not opts.reassert_current
    local after_attack=a.type=="MOVE" and from_attack
    local attack_issue=from_attack and st.attack.issue or nil
    local attack_target_uid=from_attack and st.plan[st.idx].target_uid or nil
    local hold_ms=from_attack and st.attack.eligible_ms or nil
    if from_attack and not opts.attack_abort and (not st.attack.done or hold_ms<CFG.attack_hold_ms) then fail("ATTACK_HOLD_NOT_DONE"); return end
    if from_attack and not opts.attack_abort and not st.attack.done and (not st.attack.feg_result or not st.attack.feg_result.allow or st.attack.feg_sample_ms~=now) then
        if DEBUG_TELEMETRY then log("FEG_DISPATCH_DEFER uid="..st.uid.." gen="..st.gen.." reason=NO_CURRENT_QUALIFIED_CONTACT") end
        return
    end
    local origin=point(st.unit); if not origin then cancel(st,"UNIT_POSITION",now,false); return end
    local called=false
    local issue_args={a.type,false,st.uid,rev,function()
        called=true
        if S.failed or S.closed or st.gen~=generation or not st.plan then error("CALLBACK_GENERATION_INVALID") end
        local cok,ce=pcall(function()
            if a.type=="MOVE" then st.uc:goto_location(Core.vector_at(st,a.pos),true)
            else st.uc:attack_unit(a.target,true,true) end
        end)
        release(st)
        if not cok then error(ce) end
    end}
    if a.type=="MOVE" then issue_args[6]=a.pos.x;issue_args[7]=a.pos.y;issue_args[8]=a.pos.z end
    local sent,issue,result=pcall(bridge.issue_verified_command,unpack(issue_args))
    if not sent or not id(issue) or result~="PENDING_NATIVE_ACCEPTANCE" or not called then
        if sent and issue==nil and (result=="ISSUE_CAPACITY" or result=="ISSUE_ALREADY_PENDING") and not called then
            if DEBUG_TELEMETRY then dlog("NATIVE_BACKPRESSURE uid="..st.uid.." reason="..result) end;return
        end
        if sent and issue==nil and result=="REJECTED_STALE" and not called then
            cancel(st,"REJECTED_STALE",now,true); st.blocked=true; return
        end
        fail("ISSUE_"..clean(a.type).."_"..clean(result or issue)); return
    end
    local pending={uid=st.uid,gen=generation,issue=issue,kind=a.type,idx=index,origin=origin,
        revision=rev,target_uid=a.target_uid,started=now,after_attack=after_attack,attack_issue=attack_issue,hold_ms=hold_ms,
        source_attack_target_uid=attack_target_uid,reassert_current=opts.reassert_current==true,
        reassert_attack=opts.reassert_attack==true,previous_origin=copy(st.origin),
        attack_abort=opts.attack_abort,previous_idx=st.idx,previous_owned=st.owned,action=a,saw_append=false,
        handoff_geometry={cut_tolerance=g.cut_tolerance,cut_error=g.cut_error,remaining=g.remaining,route_reason=g.route_reason,
            route_mode=g.route_mode,corner_window=g.corner_window,corner_window_base=g.corner_window_base,
            corner_window_early=g.corner_window_early,corner_lookahead=g.corner_lookahead,
            corner_turn_factor=g.corner_turn_factor,corner_stall_escape=g.corner_stall_escape,
            corner_stall_no_progress_ms=g.corner_stall_no_progress_ms,corner_stall_escape_margin=g.corner_stall_escape_margin,
            corner_stall_escape_limit=g.corner_stall_escape_limit,next_leg=g.next_leg,ratio=g.ratio,
            route_debt_mode=g.route_debt_mode,route_debt_count=g.route_debt_count,
            route_debt_error=g.route_debt_error,route_debt_limit=g.route_debt_limit}}
    S.pending_by_uid[st.uid]=pending;S.pending_by_issue[issue]=pending;S.pending_count=S.pending_count+1
    if not opts.reassert_current then
        local previous=st.plan[pending.previous_idx]
        if previous and previous.type=="MOVE" then Core.mark_handoff_committed(st,previous,a,reason,now,g) end
    end
    st.last_dispatch_ms=now
    if DEBUG_TELEMETRY then S.dispatch_count=S.dispatch_count+1 end; st.owned=true
    if opts.reassert_attack then st.phase="REASSERT_ATTACK_PENDING"
    elseif opts.reassert_current then st.phase="REASSERT_MOVE_PENDING"
    else st.phase=(a.type=="MOVE" and "ISSUE_MOVE_PENDING" or "ISSUE_ATTACK_PENDING") end
    if DEBUG_TELEMETRY and a.type=="ATTACK" then ATTACK_TRACE[st.uid]={gen=generation,issue=issue,started=now} end
    local dispatch_tag=opts.reassert_attack and "REASSERT_ATTACK" or (opts.reassert_current and "REASSERT_MOVE" or ("DISPATCH_"..a.type))
    if DEBUG_TELEMETRY then dlog(dispatch_tag.." uid="..st.uid.." gen="..generation.." issue="..issue.." idx="..index..
        " expected_revision="..rev.." target="..clean(a.target_uid).." reason="..reason.." remaining="..string.format("%.3f",g.remaining)..
        " threshold="..string.format("%.6f",g.threshold).." speed="..string.format("%.6f",g.speed)..
        " route_mode="..clean(g.route_mode).." debt_mode="..clean(g.route_debt_mode).." debt_count="..clean(g.route_debt_count)..
        " debt_error="..num_or_nil(g.route_debt_error).." debt_limit="..num_or_nil(g.route_debt_limit)..
        " corner_window="..num_or_nil(g.corner_window).." corner_base="..num_or_nil(g.corner_window_base).." corner_early="..num_or_nil(g.corner_window_early)..
        " stall_escape="..tostring(g.corner_stall_escape==true).." stall_no_progress_ms="..num_or_nil(g.corner_stall_no_progress_ms)..
        " stall_escape_limit="..num_or_nil(g.corner_stall_escape_limit)..
        (a.pos and (" dest_x="..string.format("%.6f",a.pos.x).." dest_z="..string.format("%.6f",a.pos.z)) or "")..
        " model_ms="..string.format("%.0f",now).." attack_abort="..clean(opts.attack_abort or "NONE")..
        (a.type=="ATTACK" and ((opts.reassert_attack and " recovery=same_action_same_target"
            or (from_attack and (" previous_attack_issue="..attack_issue.." hold_ms="..string.format("%.0f",hold_ms or 0))
            or (attack_metrics(g,now).." brake_signal="..tostring(g.brake_signal)..
                " brake_drop="..string.format("%.6f",g.brake_drop or 0)..
                " brake_threshold="..string.format("%.6f",g.brake_threshold or g.threshold)))).." test_delayed=false") or "")) end
    if from_attack and opts.attack_abort then
        if DEBUG_TELEMETRY then log("ATTACK_ABORT_SUCCESSOR_ISSUED uid="..st.uid.." gen="..generation.." issue="..issue.." idx="..index..
            " kind="..a.type.." attack_issue="..clean(attack_issue).." reason="..opts.attack_abort..
            " model_ms="..string.format("%.0f",now).." preserved_tail=true") end
    elseif after_attack then
        if DEBUG_TELEMETRY then log("FEG_EXIT_ISSUED uid="..st.uid.." gen="..generation.." issue="..issue.." idx="..index..
            " attack_issue="..attack_issue.." model_ms="..string.format("%.0f",now)..
            " hold_ms="..string.format("%.0f",hold_ms).." gate_open_ms="..string.format("%.0f",st.attack.feg.open_ms)..
            " dest_x="..num_or_nil(a.pos.x).." dest_z="..num_or_nil(a.pos.z).." claim=COMMAND_SUBMITTED") end
        if DEBUG_TELEMETRY then dlog("DISPATCH_MOVE_AFTER_ATTACK uid="..st.uid.." gen="..generation.." issue="..issue.." idx="..index..
            " attack_issue="..attack_issue.." expected_revision="..rev.." hold_ms="..string.format("%.0f",hold_ms)..
            " model_ms="..string.format("%.0f",now).." target_x="..string.format("%.6f",a.pos.x).." target_z="..string.format("%.6f",a.pos.z)) end
    end
end
function Core.advance_attack(st,now,observe_only)
    local t=st.attack
    if not t then fail("ATTACK_STATE_MISSING"); return end
    local a=st.plan[st.idx]
    enter_action(st,a,now,"ATTACK_TRACKING")
    -- Attack completion is a latched historical fact. A later Shift append must not
    -- require the target still to be in the same contact state at append time.
    if t.done then
        st.phase="ATTACK_COMPLETE_APPENDABLE"
        local tail=st.plan[st.idx+1]
        if not observe_only and tail and not S.pending_by_uid[st.uid] and S.pending_count<CFG.max_inflight then
            dispatch(st,st.idx+1,"ATTACK_COMPLETE_LATCHED",{remaining=0,threshold=0,speed=median(st.speeds) or 0},now)
        end
        return
    end
    local good,why=target_ready(a,now)
    if not good then
        local tail=st.plan[st.idx+1]
        if tail and abortable_target_reason(why) then
            if t.abort_reason~=why then
                if DEBUG_TELEMETRY then log("ATTACK_TARGET_ABORT_CONTINUE uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." idx="..st.idx..
                    " reason="..why.." successor_type="..(tail and tail.type or "NONE").." model_ms="..string.format("%.0f",now)..
                    " eligible_ms="..string.format("%.0f",t.eligible_ms).." preserved_tail=true") end
            end
            t.abort_reason=why;st.phase="ATTACK_ABORT_WAIT_TAIL"
            if not observe_only and not S.pending_by_uid[st.uid] and S.pending_count<CFG.max_inflight then
                dispatch(st,st.idx+1,"ATTACK_TARGET_ABORT_CONTINUE",
                    {remaining=0,threshold=0,speed=median(st.speeds) or 0},now,{attack_abort=why})
            end
            return
        end
        if abortable_target_reason(why) then
            t.abort_reason=why;st.phase="ATTACK_ENDED_APPENDABLE"
        else target_wait(st,why,now) end
        -- Do not erase the root: an append arriving next poll still belongs here.
        return
    end
    local supported,unsupported=Core.timed_attack_supported(st,true)
    if not supported then
        st.phase="NATIVE_ATTACK_UNTIMED"
        if st.plan[st.idx+1] then target_wait(st,unsupported,now) end
        return -- keep native terminal Attack and the known suffix, never fake timed missile/flight melee
    end
    if false and a.requires_fresh_engagement then
        local delta=math.max(0,now-t.last_ms)
        local fresh,fresh_reason,fresh_count=R1.fresh_engagement(st,a,now)
        local interval=fresh==true and t.previous_eligible and delta<=CFG.attack_observation_gap_ms and not st.input_gapped
        local credited=interval and delta or 0
        if delta>CFG.attack_observation_gap_ms or st.input_gapped then
            if DEBUG_TELEMETRY then log("ATTACK_OBSERVATION_GAP uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                " delta_ms="..string.format("%.0f",delta).." model_ms="..string.format("%.0f",now).." credited_ms=0") end
        end
        st.input_gapped=false;t.previous_eligible=(fresh==true);t.last_ms=now
        t.eligible_ms=t.eligible_ms+credited;t.noneligible_ms=t.noneligible_ms+(delta-credited)
        t.fresh_result={eligible=fresh==true,reason=fresh_reason,count=fresh_count};t.feg_result={allow=fresh==true,evidence="V3_CONTACT_"..clean(fresh_reason)};t.feg_sample_ms=now
        if fresh then
            if action_runtime(a).fault and action_runtime(a).fault.code=="BLOCKED_EVIDENCE" then R1.clear_fault(st,a,now) end
            t.feg.open_ms=t.feg.open_ms or now
        else R1.fault(st,a,"BLOCKED_EVIDENCE",fresh_reason or "V3_CONTACT_UNPROVEN",now) end
        if DEBUG_TELEMETRY then dlog("R1_V3_ATTACK_CONTACT uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " target="..a.target_uid.." eligible="..tostring(fresh==true).." reason="..clean(fresh_reason)..
            " credited_ms="..credited.." eligible_ms="..t.eligible_ms.." model_ms="..now) end
        if t.eligible_ms>=CFG.attack_hold_ms then
            t.done=true;mark_action_complete(st,a,"ATTACK_HOLD_COMPLETE",now,0)
            if DEBUG_TELEMETRY then dlog("ATTACK_HOLD_DONE uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." idx="..st.idx..
                " intended="..a.target_uid.." eligible_ms="..string.format("%.0f",t.eligible_ms)..
                " model_ms="..string.format("%.0f",now).." claim=V3_TARGET_SPECIFIC_BODY_CONTACT_TIME") end
        end
        if t.done and not st.plan[st.idx+1] then st.phase="ATTACK_COMPLETE_APPENDABLE" end
        return
    end
    local melee=api_bool(st.unit,"is_in_melee")
    local ok,target=pcall(function() return st.unit:current_target() end)
    if melee==nil or not ok then cancel(st,"ENGAGEMENT_API_UNAVAILABLE",now,false); st.blocked=true; if st.owned then release(st) end; return end
    local observed=target and uid(target) or nil
    local raw_eligible=melee==true and observed==a.target_uid
    local delta=math.max(0,now-t.last_ms)
    -- Diagnostic counter for what v1.0.1 would have credited; NEVER drives orders.
    if raw_eligible and t.legacy_previous and delta<=CFG.attack_observation_gap_ms and not st.input_gapped then
        t.legacy_eligible_ms=t.legacy_eligible_ms+delta
    end
    t.legacy_previous=raw_eligible
    local target_pos=point(a.target)
    local contact_distance=unit_distance_to(st.unit,a.target)
    local r=FEG.update(t.feg,{now=now,ax=st.pos and st.pos.x,az=st.pos and st.pos.z,
        tx=target_pos and target_pos.x,tz=target_pos and target_pos.z,
        melee=melee,target_match=observed==a.target_uid,target_known=target~=nil,
        target_alive=a.alive_confirmed==true,bbox_distance=contact_distance,input_gap=st.input_gapped})
    r.melee=melee;r.observed_uid=observed
    r.ax=st.pos and st.pos.x;r.az=st.pos and st.pos.z
    r.tx=target_pos and target_pos.x;r.tz=target_pos and target_pos.z
    t.feg_result=r;t.feg_sample_ms=now
    if a.requires_fresh_engagement then
        t.center_a2=t.center_a2 or {fresh=false,approach=false,open=false,credited=false}
        local ca=t.center_a2
        if r.fresh_seen and not ca.fresh then
            ca.fresh=true
            if DEBUG_TELEMETRY then log("CENTER_A2_FRESH_SEEN uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
                " issue="..t.issue.." dist="..num_or_nil(r.distance).." bbox_distance="..num_or_nil(contact_distance)..
                " melee="..tostring(melee).." observed="..clean(observed).." model_ms="..now) end
        end
        if r.approach_seen and not ca.approach then
            ca.approach=true
            if DEBUG_TELEMETRY then log("CENTER_A2_APPROACH_SEEN uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
                " issue="..t.issue.." dist="..num_or_nil(r.distance).." bbox_distance="..num_or_nil(contact_distance)..
                " closing="..num_or_nil(r.closing).." actor_speed="..num_or_nil(r.actor_speed)..
                " observed="..clean(observed).." model_ms="..now) end
        end
    end
    if DEBUG_TELEMETRY and r.distance and r.distance<=(r.strong_far or r.far) and now-(t.contact_trace_ms or -1000000)>=200 then
        t.contact_trace_ms=now
        if DEBUG_TELEMETRY then log("ATTACK_CONTACT_SAMPLE uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." model_ms="..now..
            " ax="..num_or_nil(r.ax).." az="..num_or_nil(r.az).." tx="..num_or_nil(r.tx).." tz="..num_or_nil(r.tz)..
            " melee="..tostring(melee).." observed="..clean(observed).." intended="..a.target_uid..
            " bbox_distance="..num_or_nil(contact_distance).." evidence="..clean(r.evidence)..
            " eligible="..tostring(r.allow).." geometry_ms="..num_or_nil(r.geometry_ms)) end
    end
    if r.reset_hold then
        if DEBUG_TELEMETRY then log("FEG_RELOCK uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." episode="..r.episode..
            " model_ms="..string.format("%.0f",now).." previous_credit_ms="..string.format("%.0f",t.eligible_ms)..
            " reason="..r.reason) end
        t.previous_eligible=false;t.ready_logged=false -- R06: preserve already qualified credit on relock
    end
    if r.just_opened then
        if DEBUG_TELEMETRY then log("FEG_OPEN uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." episode="..r.episode..
            " model_ms="..string.format("%.0f",now).." reason="..r.reason..
            " dist="..num_or_nil(r.distance).." near="..num_or_nil(r.near).." strong_far="..num_or_nil(r.strong_far)..
            " confirmation_ms="..num_or_nil(r.candidate_ms).." credited_ms=0 claim=HEURISTIC_NOT_MAJORITY_PROOF") end
        if a.requires_fresh_engagement then
            if DEBUG_TELEMETRY then log("CENTER_A2_GATE_OPEN uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
                " issue="..t.issue.." reason="..clean(r.reason).." dist="..num_or_nil(r.distance)..
                " bbox_distance="..num_or_nil(contact_distance).." closing="..num_or_nil(r.closing)..
                " fresh_seen="..tostring(r.fresh_seen).." approach_seen="..tostring(r.approach_seen)..
                " model_ms="..now) end
        end
    end
    local eligible=r.allow -- ordinary Attack keeps mature FEG behavior.
    R1.trace_physical(st,a,now)
    local interval=eligible and t.previous_eligible and not r.just_opened and not r.reset_hold
        and delta<=CFG.attack_observation_gap_ms and not st.input_gapped
    local credited=interval and delta or 0
    if a.requires_fresh_engagement and credited>0 and t.center_a2 and not t.center_a2.credited then
        t.center_a2.credited=true
        if DEBUG_TELEMETRY then log("CENTER_A2_FIRST_CREDIT uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " issue="..t.issue.." credited_ms="..credited.." dist="..num_or_nil(r.distance)..
            " bbox_distance="..num_or_nil(contact_distance).." reason="..clean(r.reason)..
            " model_ms="..now) end
    end
    if delta>CFG.attack_observation_gap_ms or st.input_gapped then
        if DEBUG_TELEMETRY then log("ATTACK_OBSERVATION_GAP uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
            " delta_ms="..string.format("%.0f",delta).." model_ms="..string.format("%.0f",now).." credited_ms=0") end
    end
    st.input_gapped=false
    t.eligible_ms=t.eligible_ms+credited
    t.noneligible_ms=t.noneligible_ms+(delta-credited)
    Core.feg_log(st,t,r,now,credited,t.legacy_eligible_ms)

    local elapsed=math.max(0,now-t.accepted_ms)
    local bbox_distance,center_distance,target_speed,actor_speed,instant_speed
    if DEBUG_TELEMETRY then
        -- Read-only engagement telemetry. unit_distance() is CA's public shortest
        -- unit-to-unit distance (bounding boxes), while center_distance is diagnostic only.
        local target_pos=point(a.target)
        bbox_distance=contact_distance
        center_distance=(st.pos and target_pos) and dist(st.pos,target_pos) or nil
        if target_pos and t.target_last_pos and t.target_last_ms and now>t.target_last_ms then
            target_speed=dist(target_pos,t.target_last_pos)*1000/(now-t.target_last_ms)
            if not finite(target_speed) then target_speed=nil end
        end
        if target_pos then t.target_last_pos=copy(target_pos);t.target_last_ms=now end
        if target_speed then t.target_speed=target_speed end
        actor_speed=median(st.speeds) or 0
        instant_speed=st.speeds[#st.speeds] or 0

        -- Debug build logs each interval so the collector can reconstruct eligibility.
        if DEBUG_TELEMETRY then dlog("ATTACK_TARGET_OBSERVED uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." idx="..st.idx..
            " rev="..st.revision.." intended="..a.target_uid.." observed="..clean(observed)..
            " melee="..tostring(melee).." eligible="..tostring(eligible).." previous_eligible="..tostring(t.previous_eligible)..
            " delta_ms="..string.format("%.0f",delta).." credited_ms="..string.format("%.0f",credited)..
            " eligible_ms="..string.format("%.0f",t.eligible_ms).." noneligible_ms="..string.format("%.0f",t.noneligible_ms)..
            " elapsed_ms="..string.format("%.0f",elapsed).." dist="..num_or_nil(center_distance)..
            " speed="..string.format("%.6f",actor_speed).." bbox_distance="..num_or_nil(bbox_distance)..
            " center_distance="..num_or_nil(center_distance).." actor_speed="..string.format("%.6f",actor_speed)..
            " instant_speed="..string.format("%.6f",instant_speed).." target_speed="..num_or_nil(target_speed or t.target_speed)..
            " unit_x="..num_or_nil(st.pos and st.pos.x).." unit_z="..num_or_nil(st.pos and st.pos.z)..
            " target_x="..num_or_nil(target_pos and target_pos.x).." target_z="..num_or_nil(target_pos and target_pos.z)..
            " model_ms="..string.format("%.0f",now)) end
    end
    if eligible and not t.previous_eligible then
        if DEBUG_TELEMETRY then dlog("ATTACK_HOLD_BEGIN uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." model_ms="..string.format("%.0f",now)..
            " resumed="..tostring(t.observed_once).." eligible_ms="..string.format("%.0f",t.eligible_ms).." test_delay=false") end
        if not t.cancel_test_announced then
            if DEBUG_TELEMETRY then dlog("ATTACK_RMB_CANCEL_TEST_READY uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                " model_ms="..string.format("%.0f",now).." phase=ATTACK_HOLD action=PLAIN_RMB_D behaviour_change=false") end
            t.cancel_test_announced=true
        end
        t.observed_once=true
    elseif not eligible and t.previous_eligible then
        if DEBUG_TELEMETRY then dlog("ATTACK_HOLD_SUSPEND uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." model_ms="..string.format("%.0f",now)..
            " eligible_ms="..string.format("%.0f",t.eligible_ms).." reason=OBSERVATION_NOT_ELIGIBLE") end
    end
    if elapsed>=t.long_wait_next_ms and t.eligible_ms<CFG.attack_hold_ms then
        if DEBUG_TELEMETRY then
            if DEBUG_TELEMETRY then log("ATTACK_APPROACH_LONG_WAIT uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                " elapsed_ms="..string.format("%.0f",elapsed).." eligible_ms="..string.format("%.0f",t.eligible_ms)..
                " noneligible_ms="..string.format("%.0f",t.noneligible_ms).." observed="..clean(observed)..
                " melee="..tostring(melee).." bbox_distance="..num_or_nil(bbox_distance)..
                " center_distance="..num_or_nil(center_distance).." actor_speed="..string.format("%.6f",actor_speed or 0)..
                " target_speed="..num_or_nil(target_speed or t.target_speed).." model_ms="..string.format("%.0f",now)..
                " policy=DIAGNOSTIC_ONLY_NO_BEHAVIOUR_CHANGE") end
        else
            if DEBUG_TELEMETRY then log("ATTACK_APPROACH_LONG_WAIT uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                " elapsed_ms="..string.format("%.0f",elapsed).." eligible_ms="..string.format("%.0f",t.eligible_ms)..
                " policy=DIAGNOSTIC_ONLY_NO_BEHAVIOUR_CHANGE") end
        end
        repeat t.long_wait_next_ms=t.long_wait_next_ms+CFG.attack_long_wait_repeat_ms
        until t.long_wait_next_ms>elapsed
    end
    t.last_ms=now; t.previous_eligible=eligible; st.phase=eligible and "ATTACK_HOLD" or "ATTACK_APPROACH"
    if t.eligible_ms>=CFG.attack_hold_ms and eligible then
        if not t.done then
            t.done=true
            mark_action_complete(st,a,"ATTACK_HOLD_COMPLETE",now,0)
            if DEBUG_TELEMETRY then dlog("ATTACK_HOLD_DONE uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." idx="..st.idx..
                " intended="..a.target_uid.." eligible_ms="..string.format("%.0f",t.eligible_ms)..
                " model_ms="..string.format("%.0f",now).." claim=OBSERVED_ELIGIBLE_MODEL_TIME_LATCHED") end
        end
        if not st.plan[st.idx+1] then
            if not t.ready_logged then
                t.ready_logged=true
                if DEBUG_TELEMETRY then dlog("ATTACK_HOLD_READY_NO_TAIL uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                    " eligible_ms="..string.format("%.0f",t.eligible_ms).." model_ms="..string.format("%.0f",now)..
                    " policy=CONTINUE_NATIVE_ATTACK_NO_INVENTED_MOVE completion_latched=true") end
            end
            st.phase="ATTACK_COMPLETE_APPENDABLE"
            return
        end
        if not observe_only then dispatch(st,st.idx+1,"ATTACK_HOLD_DONE",{remaining=0,threshold=0,speed=median(st.speeds) or 0},now) end
    end
end

function Core.current_move_geometry(st)
    local a=st.plan and st.plan[st.idx]
    if not a or a.type~="MOVE" or not st.pos then return nil end
    local origin=st.origin or a.origin or st.pos
    local remain=dist(st.pos,a.pos);local leg=math.max(0.000001,dist(origin,a.pos))
    return {remaining=remain,leg=leg,progress=clamp((leg-remain)/leg,0,1),speed=median(st.speeds) or 0,
        instant_speed=st.speeds[#st.speeds] or 0,stall=(median(st.speeds) or 0)<=CFG.stall_speed,
        threshold=0,ratio=0,samples=#st.speeds}
end
local function reassert_current_move(st,reason,now)
    if S.pending_by_uid[st.uid] or S.pending_count>=CFG.max_inflight then return false end
    local a=st.plan and st.plan[st.idx]
    if not a or a.type~="MOVE" then return false end
    local g=Core.current_move_geometry(st);if not g then return false end
    dispatch(st,st.idx,reason,g,now,{reassert_current=true})
    return S.pending_by_uid[st.uid]~=nil
end
function Core.reassert_current_attack(st,reason,now)
    local a=st.plan and st.plan[st.idx]
    local t=st.attack
    if not a or a.type~="ATTACK" or not t or t.done or t.native_player then return false end
    if S.pending_by_uid[st.uid] or S.pending_count>=CFG.max_inflight then return false end
    local rt=action_runtime(a)
    local submitted=rt.attack_reassert_submitted or 0
    if submitted>=CFG.attack_reassert_max then return false end
    if now-(rt.last_attack_reassert_ms or -1000000)<CFG.attack_reassert_interval_ms then return false end
    local g={remaining=0,threshold=0,speed=median(st.speeds) or 0,cut_tolerance=0,cut_error=0,route_reason="CURRENT_ATTACK_RECOVERY"}
    dispatch(st,st.idx,reason,g,now,{reassert_current=true,reassert_attack=true})
    local pending=S.pending_by_uid[st.uid]
    if pending and pending.reassert_attack and pending.action==a then
        rt.attack_reassert_submitted=submitted+1;rt.last_attack_reassert_ms=now
        if DEBUG_TELEMETRY then log("ATTACK_REASSERT_ISSUED uid="..st.uid.." gen="..st.gen.." action="..a.action_id..
            " issue="..pending.issue.." target="..a.target_uid.." count="..rt.attack_reassert_submitted..
            " preserved_eligible_ms="..string.format("%.0f",t.eligible_ms or 0).." model_ms="..now..
            " policy=BOUNDED_SAME_ACTION_SAME_TARGET") end
        return true
    end
    return false
end
function Core.maybe_reassert_exit(st,now)
    local unresolved=st.unverified_native_successor
    if unresolved and unresolved.gen==st.gen and unresolved.ms==now then return false end
    local a=st.plan and st.plan[st.idx]
    if not a or a.type~="MOVE" or a.block_kind~="EXIT_ROUTE" then return false end
    local b=current_block(st);local rt=action_runtime(a)
    if not b or b.closed or not b.exit_started_ms or rt.semantic_done then return false end
    if S.pending_by_uid[st.uid] or S.pending_count>=CFG.max_inflight then return false end
    -- Layer 1: execution identity. SC5 is only a physical-disengagement recovery
    -- after exact proof that this same Exit MOVE is still the native active order.
    -- If Native has promoted a future Attack, reconciliation owns the recovery.
    if (S.evidence_v3_caps or {}).execution_identity==true then
        local active,identity_reason=R1.read_active_execution(st)
        local matches=active and R1.execution_matches_action(active,a) or false
        if not matches then
            if DEBUG_TELEMETRY and (b.last_identity_defer_reason~=clean(identity_reason) or now-(b.last_identity_defer_ms or -1000000)>=1500) then
                b.last_identity_defer_reason=clean(identity_reason);b.last_identity_defer_ms=now
                if DEBUG_TELEMETRY then dlog("EXIT_REASSERT_DEFER_IDENTITY uid="..st.uid.." gen="..st.gen.." block="..clean(b.id)..
                    " action="..a.action_id.." active_kind="..clean(active and active.kind)..
                    " active_engine_seq="..clean(active and active.active_engine_seq).." provider="..clean(active and active.provider)..
                    " reason="..clean(identity_reason or "ACTIVE_NOT_CURRENT_ACTION").." model_ms="..now) end
            end
            return false
        end
    end
    local speed=median(st.speeds) or 0
    local no_progress=now-(rt.last_progress_ms or now)
    local contacts=b.contact_scan
    local contact_fresh=contacts and now-contacts.ms<=CFG.evidence_max_age_ms and contacts.count>0
    if not contact_fresh or speed>CFG.stall_speed then return false end

    local confirmed_candidate=false
    local evidence_mode="NONE"
    local required_stall=CFG.exit_reassert_stall_ms
    local v3why="UNUSED"
    if (S.evidence_v3_caps or {}).execution_identity==true then
        -- Prefer exact V3 body/order evidence whenever it is live. SC5 adds one
        -- narrow fallback for the live failure seen at 10:44: the exact Exit MOVE
        -- ACK was known, but the EntitySnapshot aged out (ENTITY_STALE) while a
        -- positive global enemy contact and near-zero locomotion were still visible.
        -- Positive contact is used only as evidence that the body is still physically
        -- pinned; sticky melee=true or contact absence can never trigger this path.
        local status,why=R1.v3_exit_body_status(st,a,now);v3why=why or "OK"
        if status then
            confirmed_candidate=status.progressing_majority~=true
            evidence_mode="V3_BODY_NOT_PROGRESSING"
        elseif why=="ENTITY_STALE" then
            required_stall=CFG.exit_contact_fallback_stall_ms
            confirmed_candidate=contact_fresh
            evidence_mode="V3_ENTITY_STALE_CONTACT_FALLBACK"
        end
    else
        confirmed_candidate=contact_fresh
        evidence_mode="LEGACY_POSITIVE_CONTACT"
    end
    if not confirmed_candidate or no_progress<required_stall then return false end
    local budget_ok,budget=v3_recovery_available(st,a,now,"EXIT_REASSERT")
    if not budget_ok then return false end
    if now-(b.last_reassert_ms or -1000000)<CFG.exit_reassert_interval_ms then return false end
    if reassert_current_move(st,"EXIT_REASSERT_STALLED",now) then
        local consumed,why,left=v3_recovery_commit(budget,"EXIT_REASSERT",now)
        if not consumed then R1.fault(st,a,"BLOCKED_EXECUTION","RECOVERY_ACCOUNTING_"..clean(why),now);return false end
        b.reasserts=budget.used;b.last_reassert_ms=now
        log("EXIT_BLOCK_REASSERT uid="..st.uid.." gen="..st.gen.." block="..b.id.." action="..a.action_id..
            " count="..b.reasserts.." remaining_budget="..left.." no_progress_ms="..no_progress.." required_stall_ms="..required_stall..
            " contacts="..contacts.count.." speed="..num_or_nil(speed).." evidence="..evidence_mode.." v3_reason="..clean(v3why)..
            " model_ms="..now.." shared_budget=true")
        return true
    end
    return false
end

local function rollback_native_future_to_current(st,cur,future,future_index,e,now,fault_reason,route_reason,recovery_reason)
    st.unverified_native_successor={gen=st.gen,action=cur.action_id,next_action=future and future.action_id or nil,
        future_index=future_index,ms=now,exact=true,provider=e and e.provider or nil}
    R1.fault(st,cur,"BLOCKED_EXECUTION_IDENTITY",fault_reason,now)
    local budget_ok,budget=v3_recovery_available(st,cur,now,"NATIVE_ROLLBACK")
    if budget_ok and S.pending_count<CFG.max_inflight and reassert_current_move(st,recovery_reason,now) then
        local consumed,rwhy,left=v3_recovery_commit(budget,"NATIVE_ROLLBACK",now)
        if not consumed then R1.fault(st,cur,"BLOCKED_EXECUTION","RECOVERY_ACCOUNTING_"..clean(rwhy),now);return false end
        log("NATIVE_SUCCESSOR_ROLLBACK uid="..st.uid.." gen="..st.gen.." action="..cur.action_id..
            " blocked_successor="..clean(future and future.action_id).." future_index="..clean(future_index)..
            " active_kind="..clean(e and e.kind).." active_engine_seq="..clean(e and e.active_engine_seq)..
            " provider="..clean(e and e.provider).." route_reason="..clean(route_reason)..
            " remaining_budget="..left.." model_ms="..now.." preserved_tail=true shared_budget=true")
        return true
    end
    return false
end
function Core.reconcile_native_successor(st,now)
    if not st.plan or st.blocked or S.pending_by_uid[st.uid] then return false end
    local cur=st.plan[st.idx]
    if not cur or cur.type~="MOVE" then return false end

    -- Read the native active execution exactly once. V3 is authoritative in the
    -- production build; V2 is used only on a genuinely V3-unavailable compatibility
    -- host. current_target() never authorizes a transition or rollback.
    local e,ewhy=R1.read_active_execution(st)
    if not e or e.active~=true or e.known~=true then
        local nexta=st.plan[st.idx+1]
        local ok,target=pcall(function() return st.unit:current_target() end)
        local observed=(ok and target) and uid(target) or nil
        if nexta and nexta.type=="ATTACK" and observed==nexta.target_uid then
            st.unverified_native_successor={gen=st.gen,action=cur.action_id,next_action=nexta.action_id,ms=now,exact=false,reason=ewhy}
            R1.fault(st,cur,"BLOCKED_EXECUTION_IDENTITY","CURRENT_TARGET_IS_NOT_ACTION_ID",now)
        else
            st.unverified_native_successor=nil
            if cur.runtime and cur.runtime.fault and cur.runtime.fault.code=="BLOCKED_EXECUTION_IDENTITY" then R1.clear_fault(st,cur,now) end
        end
        return false
    end

    local current_match=R1.execution_matches_action(e,cur)
    if current_match then
        st.unverified_native_successor=nil
        if cur.runtime and cur.runtime.fault and cur.runtime.fault.code=="BLOCKED_EXECUTION_IDENTITY" then R1.clear_fault(st,cur,now) end
        return false
    end

    -- The engine may have promoted any captured future queue item before Lua's
    -- canonical cursor advanced. Identify the exact future action, but never skip
    -- intermediate canonical actions just because Native overran them.
    local future_index=nil;local future=nil
    for i=st.idx+1,#st.plan do
        local match=R1.execution_matches_action(e,st.plan[i])
        if match then future_index=i;future=st.plan[i];break end
    end
    if not future then
        st.unverified_native_successor={gen=st.gen,action=cur.action_id,ms=now,exact=true,provider=e.provider,noncanonical=true}
        R1.fault(st,cur,"BLOCKED_EXECUTION_IDENTITY","ACTIVE_EXECUTION_NOT_CANONICAL",now)
        if DEBUG_TELEMETRY then dlog("NATIVE_EXECUTION_NOT_CANONICAL uid="..st.uid.." gen="..st.gen.." action="..cur.action_id..
            " active_kind="..clean(e.kind).." active_engine_seq="..clean(e.active_engine_seq).." provider="..clean(e.provider).." model_ms="..now) end
        return false
    end

    if future_index~=st.idx+1 or future.type~="ATTACK" then
        return rollback_native_future_to_current(st,cur,future,future_index,e,now,
            "NATIVE_FUTURE_OVERRUN","CANONICAL_INTERMEDIATE_ACTIONS_OWED","NATIVE_FUTURE_OVERRUN_ROLLBACK_TO_CURRENT_MOVE")
    end

    local g=geometry(st,future)
    if g then g=attack_geometry(st,future,g) end
    local route_ok,why=false,"SUCCESSOR_GEOMETRY_UNAVAILABLE"
    if g then route_ok,why=transition_handoff_ready(st,g,future) end
    if not route_ok then
        return rollback_native_future_to_current(st,cur,future,future_index,e,now,
            "NATIVE_ADVANCED_BEFORE_PERMISSION",why,"NATIVE_SUCCESSOR_ROLLBACK_TO_CURRENT_MOVE")
    end

    R1.clear_fault(st,cur,now)
    st.unverified_native_successor=nil
    st.idx=st.idx+1;st.origin=copy(st.pos);st.owned=false;st.tail_reached=false
    enter_action(st,future,now,"NATIVE_SUCCESSOR_ADOPTED")
    begin_attack_history(st,future,now,"NATIVE_CHAIN","0")
    if DEBUG_TELEMETRY then log("NATIVE_SUCCESSOR_ADOPTED uid="..st.uid.." gen="..st.gen.." action="..future.action_id..
        " target="..future.target_uid.." previous_action="..cur.action_id.." active_engine_seq="..e.active_engine_seq..
        " provider="..clean(e.provider).." route_reason="..clean(why).." model_ms="..now) end
    return true
end
local function advance(st,now)
    if not st.plan or st.terminal or st.blocked then return end
    if S.pending_by_uid[st.uid] then return end
    local cur=st.plan[st.idx]
    if not cur then return end
    if cur.type=="ATTACK" then
        local t=st.attack
        if t and st.plan[st.idx+1] then
            if t.done then dispatch(st,st.idx+1,"ATTACK_COMPLETE_LATCHED",{remaining=0,threshold=0,speed=median(st.speeds) or 0},now)
            elseif t.abort_reason then dispatch(st,st.idx+1,"ATTACK_TARGET_ABORT_CONTINUE",{remaining=0,threshold=0,speed=median(st.speeds) or 0},now,{attack_abort=t.abort_reason}) end
        end
        return
    end
    if st.unverified_native_successor and st.unverified_native_successor.gen==st.gen
        and st.unverified_native_successor.action==cur.action_id and st.unverified_native_successor.ms==now then return end
    local rt=action_runtime(cur)
    local nexta=st.plan[st.idx+1]
    if not nexta then
        if rt.semantic_done then
            local route_clear,b=block_route_clear(st,cur)
            if not route_clear then
                st.phase="ROUTE_OBLIGATION_UNVERIFIED_APPENDABLE"
                if b and not b.route_blocked_logged then
                    b.route_blocked_logged=true
                    if DEBUG_TELEMETRY then log("ROUTE_BLOCK_WAITING_FOR_OBLIGATION uid="..st.uid.." gen="..st.gen.." block="..b.id..
                        " current_action="..cur.action_id.." policy=NO_SILENT_WAYPOINT_DROP model_ms="..now) end
                end
                return
            end
            if cur.block_kind=="EXIT_ROUTE" then
                local b=current_block(st)
                if b and not b.closed and not b.exit_permission and DEBUG_TELEMETRY then
                    if DEBUG_TELEMETRY then dlog("CENTER_EXIT_ROUTE_COMPLETE_WITHOUT_ENTITY_PERMISSION uid="..st.uid.." gen="..st.gen.." block="..b.id..
                        " action="..cur.action_id.." model_ms="..now.." policy=ROUTE_SEMANTICS_AUTHORITATIVE") end
                end
            end
            local closed_block=current_block(st)
            if closed_block and cur.block_kind=="EXIT_ROUTE" and not closed_block.closed then
                closed_block.closed=true;closed_block.closed_ms=now
                if DEBUG_TELEMETRY then log("EXIT_BLOCK_CLOSED uid="..st.uid.." gen="..st.gen.." block="..closed_block.id.." model_ms="..now.." route_and_exit_satisfied=true") end
            end
            if not st.tail_reached then
                st.tail_reached=true;st.phase="MOVE_COMPLETE_APPENDABLE";release(st)
                if DEBUG_TELEMETRY then dlog("FINAL_MOVE_SEMANTIC_COMPLETE uid="..st.uid.." gen="..st.gen.." idx="..st.idx..
                    " action="..cur.action_id.." reason="..clean(rt.done_reason).." model_ms="..now.." appendable=true") end
            end
        else
        end
        return
    end
    if S.pending_count>=CFG.max_inflight then return end
    local g=geometry(st,nexta); if not g then return end
    local reason
    if nexta.type=="ATTACK" then
        local viable,invalid_reason=target_ready(nexta,now)
        if not viable then
            if skip_future_attack_keep_tail(st,st.idx+1,invalid_reason,now) then return end
            target_wait(st,invalid_reason,now);return
        end
        g=attack_geometry(st,nexta,g)
        if not g then target_wait(st,"ATTACK_TARGET_POSITION_UNAVAILABLE",now);return end
        attack_brake_state(g)
        local route_ok,route_reason=transition_handoff_ready(st,g,nexta)
        local exit_ok=exit_gate_ready(st,nexta)
        if not exit_ok then
            st.phase="EXIT_ROUTE_PROTECT"
            if now-(st.last_wait or -1000000)>=1000 then
                st.last_wait=now
                if DEBUG_TELEMETRY then dlog("EXIT_BLOCK_PROTECT uid="..st.uid.." gen="..st.gen.." block="..clean(cur.block_id)..
                    " current_action="..cur.action_id.." next_attack="..nexta.action_id.." route_complete="..tostring(rt.semantic_done)..
                    " route_safe="..tostring(route_ok).." model_ms="..now) end
            end
            return
        end
        if not route_ok then
            if DEBUG_TELEMETRY and now-st.last_wait>=1000 then
                st.last_wait=now
                if DEBUG_TELEMETRY then dlog("ATTACK_ROUTE_PROTECT uid="..st.uid.." gen="..st.gen.." remaining="..num_or_nil(g.remaining)..
                    " progress="..num_or_nil(g.progress).." cut_error="..num_or_nil(g.cut_error).." cut_tolerance="..num_or_nil(g.cut_tolerance)..
                    " route_reason="..clean(route_reason).." model_ms="..now) end
            end
            return
        elseif rt.semantic_done and not reason then
            reason="ATTACK_AFTER_ROUTE_COMPLETE"
        end
        if DEBUG_TELEMETRY and not reason and now-st.last_wait>=1000 then
            st.last_wait=now
            if DEBUG_TELEMETRY then dlog("ATTACK_TRANSITION_WAIT uid="..st.uid.." gen="..st.gen.." remaining="..string.format("%.6f",g.remaining)..
                " threshold="..string.format("%.6f",g.threshold).." speed="..string.format("%.6f",g.speed)..
                " route_safe="..tostring(g.route_safe).." cut_error="..num_or_nil(g.cut_error).." cut_tolerance="..num_or_nil(g.cut_tolerance)..attack_metrics(g,now)) end
        end
    else
        local route_ok,route_reason=route_handoff_ready(st,g,nexta)
        if not route_ok then
            if DEBUG_TELEMETRY and now-st.last_wait>=1000 then
                st.last_wait=now
                if DEBUG_TELEMETRY then dlog("MOVE_ROUTE_PROTECT uid="..st.uid.." gen="..st.gen.." remaining="..num_or_nil(g.remaining)..
                    " progress="..num_or_nil(g.progress).." cut_error="..num_or_nil(g.cut_error).." cut_tolerance="..num_or_nil(g.cut_tolerance)..
                    " route_mode="..clean(g.route_mode).." debt_mode="..clean(g.route_debt_mode).." debt_count="..clean(g.route_debt_count)..
                    " debt_error="..num_or_nil(g.route_debt_error).." debt_limit="..num_or_nil(g.route_debt_limit)..
                    " speed="..num_or_nil(g.speed).." stall="..tostring(g.stall==true)..
                    " corner_window="..num_or_nil(g.corner_window).." stall_no_progress_ms="..num_or_nil(g.corner_stall_no_progress_ms)..
                    " stall_escape_limit="..num_or_nil(g.corner_stall_escape_limit).." route_reason="..clean(route_reason).." model_ms="..now) end
            end
            return
        elseif rt.semantic_done then reason="MOVE_AFTER_NODE_COMPLETE"
        elseif g.remaining<=CFG.proximity then reason="PROXIMITY_A"
        elseif g.remaining<=CFG.stall_distance and g.stall then reason="PROXIMITY_B_STALL"
        elseif g.remaining<=g.threshold then reason="PREDICTIVE"
        elseif g.stall and g.remaining<=math.min(CFG.lead_cap,g.threshold+CFG.brake_extra) then reason="BRAKE_FALLBACK" end
    end
    if reason then dispatch(st,st.idx+1,reason,g,now) end
end
function Core.maintain_current_action(st,now)
    if not st.plan or st.blocked or st.terminal then return end
    local a=st.plan[st.idx];if not a then return end
    local rt=action_runtime(a)
    if a.type=="MOVE" then
        local clear,b=block_route_clear(st,a)
        if rt.semantic_done and not clear then
            local stalled=stalled_route_debt(st,b,now)
            if stalled then
                R1.fault(st,a,"BLOCKED_ROUTE","PREDICTION_DEBT_UNREACHABLE_BY_CURRENT_MOVE",now)
                if not b.route_failure_logged then
                    b.route_failure_logged=true
                    log("ROUTE_UNRECOVERABLE uid="..st.uid.." gen="..st.gen.." block="..b.id..
                        " action="..a.action_id.." debt_action="..clean(stalled.action and stalled.action.action_id)..
                        " best_remaining="..num_or_nil(stalled.best_remaining).." current_remaining="..num_or_nil(stalled.stall_remaining)..
                        " no_progress_ms="..tostring(stalled.stall_no_progress_ms or (now-(stalled.last_progress_ms or stalled.since or now)))..
                        " trend_gain_m="..num_or_nil(stalled.stall_trend_gain_m).." path_error="..num_or_nil(stalled.stall_path_error)..
                        " preserved_tail=true automatic_backtrack=false model_ms="..now)
                end
            end
            return
        elseif b then b.unresolved_since=nil end
        if not S.pending_by_uid[st.uid] and st.last_dispatch_ms~=now then Core.maybe_reassert_exit(st,now) end
        if a.block_kind=="EXIT_ROUTE" and b and not b.closed and not b.exit_permission and not S.pending_by_uid[st.uid] and (rt.semantic_done or now-(rt.last_progress_ms or now)>=CFG.evidence_wait_ms) then
            if CENTER_A2_MODE and st.plan[st.idx+1] and st.plan[st.idx+1].type=="ATTACK" then
                if now-(b.center_evidence_log_ms or -1000000)>=1500 then
                    b.center_evidence_log_ms=now
                    if DEBUG_TELEMETRY then dlog("CENTER_EXIT_ENTITY_TELEMETRY_UNRESOLVED uid="..st.uid.." gen="..st.gen..
                        " block="..clean(b.id).." action="..a.action_id.." route_done="..tostring(rt.semantic_done)..
                        " evidence_reason="..clean(b.evidence_reason).." hard_gate=false model_ms="..now) end
                end
                if rt.fault and rt.fault.code=="BLOCKED_EVIDENCE" then R1.clear_fault(st,a,now) end
            elseif not rt.fault or rt.fault.code~="BLOCKED_EXECUTION" then
                R1.fault(st,a,"BLOCKED_EVIDENCE",rt.semantic_done and "ROUTE_DONE_BODY_CLEAR_UNPROVEN" or "BODY_VS_RESIDUAL_CONTACT_UNRESOLVED",now)
            end
        elseif not rt.semantic_done and now-(rt.last_progress_ms or now)<CFG.exit_reassert_stall_ms then
            if rt.fault and (rt.fault.code=="BLOCKED_EVIDENCE" or rt.fault.code=="BLOCKED_EXECUTION") then R1.clear_fault(st,a,now) end
        end
    elseif a.type=="ATTACK" and st.attack and not st.attack.done then
        local ok,cur=pcall(function() return st.unit:current_target() end)
        local stable=ok and cur==nil and api_bool(st.unit,"is_moving")==false and api_bool(st.unit,"is_in_melee")==false
        if stable then
            rt.no_execution_since=rt.no_execution_since or now
            local stalled_ms=now-rt.no_execution_since
            local submitted=rt.attack_reassert_submitted or 0
            if not st.attack.native_player and st.owned and stalled_ms>=CFG.attack_reassert_stall_ms
                and submitted<CFG.attack_reassert_max and not S.pending_by_uid[st.uid] then
                if Core.reassert_current_attack(st,"ATTACK_REASSERT_NO_EXECUTION",now) then return end
            end
            if stalled_ms>=CFG.execution_stall_notice_ms and (st.attack.native_player or submitted>=CFG.attack_reassert_max) then
                R1.fault(st,a,"BLOCKED_EXECUTION","ATTACK_ACCEPTED_BUT_NO_EXECUTION_EVIDENCE",now)
            end
        else
            rt.no_execution_since=nil
            if rt.fault and rt.fault.reason=="ATTACK_ACCEPTED_BUT_NO_EXECUTION_EVIDENCE" then R1.clear_fault(st,a,now) end
        end
    end
end

function Core.handoff_urgency(st,now)
    if not st.plan or st.terminal or st.blocked then return BSC_HUGE,"INACTIVE" end
    if S.pending_by_uid[st.uid] then return BSC_HUGE,"OWN_PENDING" end
    local cur=st.plan[st.idx]
    if not cur then return BSC_HUGE,"NO_CURSOR" end
    if cur.type=="ATTACK" then
        local t=st.attack;local tail=st.plan[st.idx+1]
        if not t then return BSC_HUGE,"ATTACK_STATE_MISSING" end
        if t.done and tail then return -1000000,"ATTACK_COMPLETE_LATCHED" end
        if not tail then return BSC_HUGE,"ATTACK_NO_EXIT_READY" end
        if t.abort_reason then return -900000,"ATTACK_ABORT_TAIL_READY" end
        local left=math.max(0,CFG.attack_hold_ms-(t.eligible_ms or 0))
        local qualified=t.feg_result and t.feg_result.allow
        local horizon=math.max(CFG.poll_ms,st.model_step_ms or 0)
        if qualified and left<=horizon then return -500000+left,"ATTACK_EXIT_IMMINENT" end
        return 100000+left,"ATTACK_HOLD"
    end
    local rt=action_runtime(cur)
    local nexta=st.plan[st.idx+1]
    if not nexta then
        if rt.semantic_done then return -100,"MOVE_COMPLETE_NO_SUCCESSOR" end
        return BSC_HUGE,"NO_SUCCESSOR"
    end
    local g=geometry(st,nexta);if not g then return BSC_HUGE,"NO_GEOMETRY" end
    if nexta.type=="ATTACK" then
        if not target_viable(nexta) then return BSC_HUGE,"TARGET_NOT_READY" end
        g=attack_geometry(st,nexta,g);if not g then return BSC_HUGE,"ATTACK_TARGET_POSITION_UNAVAILABLE" end
        attack_brake_state(g)
        local route_ok=transition_handoff_ready(st,g,nexta)
        if not exit_gate_ready(st,nexta) then return 50000,"EXIT_BLOCK_PROTECT" end
        if not route_ok then return 50000+(g.cut_error or 0),"ATTACK_ROUTE_PROTECT" end
        if rt.semantic_done then return -800000,"MOVE_COMPLETE_ATTACK_READY" end
    else
        local route_ok=route_handoff_ready(st,g,nexta)
        if not route_ok then return 50000+(g.cut_error or 0),"MOVE_ROUTE_PROTECT" end
        if rt.semantic_done then return -700000,"MOVE_NODE_COMPLETE" end
    end
    local speed=math.max(g.instant_speed or g.speed or 0,0.25)
    local slack=g.remaining-(g.threshold or 0)
    local score=slack<=0 and (-10000+slack) or (slack/speed)
    if nexta.type=="MOVE" then
        if g.remaining<=CFG.proximity then score=-20000+g.remaining
        elseif g.remaining<=CFG.stall_distance and g.stall then score=-15000+g.remaining end
    else
        if g.remaining<=CFG.attack_distance then score=-20000+g.remaining
        elseif g.remaining<=CFG.attack_stall_distance and g.stall then score=-15000+g.remaining end
    end
    return score,nexta.type.."_HANDOFF"
end
function Core.scheduled_states(now)
    local q={}
    for _,st in pairs(S.states) do
        local score,why=Core.handoff_urgency(st,now)
        q[#q+1]={st=st,score=score,why=why}
    end
    table.sort(q,function(a,b)
        if a.score~=b.score then return a.score<b.score end
        local at,bt=a.st.last_dispatch_ms or -1,b.st.last_dispatch_ms or -1
        if at~=bt then return at<bt end
        return cmp(a.st.uid,b.st.uid)<0
    end)
    if DEBUG_TELEMETRY and q[1] and finite(q[1].score) then
        if DEBUG_TELEMETRY then dlog("SCHEDULER_HEAD uid="..q[1].st.uid.." urgency="..string.format("%.6f",q[1].score).." reason="..q[1].why..
            " pending="..tostring(S.pending_count>0).." pending_count="..S.pending_count.." model_ms="..string.format("%.0f",now)) end
    end
    return q
end
function Core.recover_ack_timeout(p,now)
    if not p or not p.reassert_current then return false end
    local st=S.states[p.uid]
    if not st or st.gen~=p.gen or not st.plan or st.plan[p.idx]~=p.action then return false end
    local a=p.action
    if not a then return false end
    if type(bridge.cancel_pending_issue)~="function" then return false end
    local ok,res=pcall(bridge.cancel_pending_issue,p.issue)
    if not ok or res~=true then return false end
    S.pending_by_uid[st.uid]=nil;S.pending_by_issue[p.issue]=nil;S.pending_count=math.max(0,S.pending_count-1)
    st.owned=p.previous_owned
    st.phase=st.attack and (st.attack.previous_eligible and "ATTACK_HOLD" or "ATTACK_APPROACH") or "MOVE_TRACKING"
    st.input_gapped=true
    if p.reassert_attack then
        local rt=action_runtime(a)
        rt.attack_reassert_submitted=math.max(0,(rt.attack_reassert_submitted or 1)-1)
        rt.last_attack_reassert_ms=now
        log("ATTACK_REASSERT_ACK_TIMEOUT uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." action="..a.action_id..
            " target="..clean(a.target_uid).." model_ms="..now.." policy=CANCEL_PENDING_AND_REDECIDE")
        return true
    end
    if a.type~="MOVE" or a.block_kind~="EXIT_ROUTE" then return false end
    local b=ensure_block_state(st,a.block_id,a.block_kind)
    local r=v3_recovery_budget(st,a)
    log("ACK_RECOVERY_CANCELLED uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." action="..a.action_id..
        " remaining_budget="..clean(r and R1V3Recovery.remaining(r) or nil).." model_ms="..now.." policy=REDECIDE_NO_BLIND_REISSUE")
    return true
end
function Core.poll_core()
    if not S.started then return end
    local now=clock()
    if S.last_model and now<S.last_model then fail("MODEL_TIME_REVERSED"); return end
    -- Recoverable capture state must be consumed before Journal rows. Otherwise a
    -- deliberately skipped/lossy external record can surface first as a fatal
    -- revision discontinuity. Postflight closes the race with native activity that
    -- occurs while the Journal page is being drained.
    if not status() then return end
    refresh_collections(now,false,false)
    if not drain(now) or S.failed then
        for _,st in pairs(S.states) do st.input_gapped=true end
        return
    end
    if not status() then return end
    local cok,cwhy=R1.v3_drain_contacts(now);if not cok then
        for _,st in pairs(S.states) do st.input_gapped=true end
        log("R1_V3_CONTACT_GAP reason="..clean(cwhy).." model_ms="..now)
    end
    for _,pending in pairs(S.pending_by_issue) do
        if now-pending.started>=CFG.ack_timeout_ms then
            if Core.recover_ack_timeout(pending,now) then return end
            fail("OWN_ACK_TIMEOUT issue="..pending.issue);return
        end
    end
    if DEBUG_TELEMETRY and now-S.last_heartbeat>=2000 then
        S.last_heartbeat=now
        local hs=status()
        if not hs then return end
        if DEBUG_TELEMETRY then dlog("HEARTBEAT run="..RUN_ID.." model_ms="..string.format("%.0f",now).." cursor="..S.cursor..
            " orders="..S.order_count.." dispatches="..S.dispatch_count.." route_passes="..S.route_passes.." cancel_passes="..S.cancel_passes..
            " pending="..tostring(S.pending_count>0).." pending_count="..S.pending_count.." states="..tostring((function() local n=0;for _ in pairs(S.states) do n=n+1 end;return n end)())) end
        if DEBUG_TELEMETRY then dlog("BRIDGE_STATUS epoch="..clean(hs.epoch).." recording="..tostring(hs.recording)..
            " capture="..clean(hs.capture_errors).." fatal="..clean(hs.fatal_errors).." gate="..clean(hs.gate_fault)..
            " authorized="..tostring(hs.native_issue_authorized).." armed="..tostring(hs.v3_issue_armed).." calibration="..tostring(hs.v3_issue_calibration_ready)..
            " accepted_move="..tostring(hs.accepted_move_seen).." accepted_attack="..tostring(hs.accepted_attack_seen)..
            " mapped="..clean(hs.mapped_orders).." unmapped="..clean(hs.unmapped_orders)..
            " handler_seen="..clean(hs.handler_seen).." handler_resolved="..clean(hs.handler_resolved).." handler_missed="..clean(hs.handler_missed)..
            " packet_seen="..clean(hs.native_packet_seen).." packet_mapped="..clean(hs.native_packet_mapped)..
            " path="..clean(hs.last_path_stage).." last_recoverable="..clean(hs.last_recoverable_error)..
            " last_fatal="..clean(hs.last_fatal_error)) end
    end
    -- Real callback still drains input when paused; model-time motion does not advance.
    if S.last_model==now then return end
    S.last_model=now
    for _,st in pairs(S.states) do
        sample(st,now);R1.refresh_physical(st,now);R1.v3_refresh_physical(st,now);observe_cold_idle(st,now); Core.observe_restart_idle(st,now); Core.activate(st);R1.v3_update_exit_candidate(st,now); Core.observe_attack(st,now); Core.observe_exit(st,now)
        Core.observe_move_completion(st,now); Core.observe_route_obligations(st,now); Core.observe_exit_block(st,now)
        if st.plan and st.plan[st.idx] and st.plan[st.idx].type=="ATTACK" and not st.blocked then Core.advance_attack(st,now,true) end
    end
    -- Reconciliation is observation, not a dispatch. It runs before scheduler capacity
    -- decisions so a native queue advance cannot leave Lua stuck on the previous Move.
    for _,st in pairs(S.states) do Core.reconcile_native_successor(st,now); if S.failed then return end end
    local schedule=Core.scheduled_states(now)
    for _,entry in ipairs(schedule) do advance(entry.st,now); if S.failed then return end end
    for _,entry in ipairs(schedule) do Core.maintain_current_action(entry.st,now); if S.failed then return end end
    if DEBUG_TELEMETRY then
        for _,c in ipairs(S.cancel_checks) do
            if not c.logged and now-c.start>=CFG.cancel_observe_ms then
                c.logged=true; S.cancel_passes=S.cancel_passes+1
                if DEBUG_TELEMETRY then dlog("CASE_CANCEL_PASS uid="..c.uid.." gen="..c.gen.." observation_ms="..string.format("%.0f",now-c.start).." claim=NO_NEW_LUA_DISPATCH_FOR_CANCELLED_GENERATION") end
            end
        end
    end
end
local function poll()
    if S.polling then fail("POLL_REENTRY"); return end
    S.polling=true
    local ok,e=xpcall(Core.poll_core,trace)
    S.polling=false
    if not ok then fail(e) end
end
local function stop(reason)
    if S.closed then return end
    log("SESSION_END run="..RUN_ID.." reason="..reason.." route_passes="..S.route_passes.." cancel_passes="..S.cancel_passes)
    if bmgr then pcall(function() bmgr:remove_real_callback(S.timer) end) end
    if bridge then
        pcall(bridge.arm_verified_issue,false)
        if S.epoch then pcall(bridge.end_battle,S.epoch) end
    end
    S.started=false; S.closed=true; S.pending_by_uid={}; S.pending_by_issue={}; S.pending_count=0
end
local function prepare()
    if S.prepared or S.started then return end
    if DEBUG_TELEMETRY then dlog("OBSERVER_PREPARE run="..RUN_ID) end
    local ok,r,e=pcall(bridge.start_observer,true)
    if not ok or r~=true then fail("OBSERVER_"..clean(e or r)); return end
    local sok,ss,se=pcall(bridge.get_status)
    if not sok or type(ss)~="table" then fail("STATUS_AFTER_OBSERVER_"..clean(se or ss)); return end
    if ss.native_issue_authorized~=true then fail("NATIVE_ISSUE_NOT_AUTHORIZED_AFTER_OBSERVER"); return end
    if DEBUG_TELEMETRY then dlog("V3_NATIVE_ISSUE_AUTHORIZED native_error="..clean(ss.native_error).." adapter_error="..clean(ss.adapter_error)) end
    local eok,epoch,ee=pcall(bridge.begin_battle,"th_p1e_p2b_"..RUN_ID)
    if not eok or not id(epoch) or epoch=="0" then fail("BEGIN_"..clean(ee or epoch)); return end
    S.epoch=epoch; S.cursor="0"; S.prepared=true;S.v3_contact_cursor=R1V3Contacts.new();S.v3_contact_log={};S.v3_contact_healthy=true
    S.evidence_v3_caps={game_build_verified=false,execution_identity=false,entity_snapshot=false,combat_groups=false,contact_pairs=false,target_specific_physical_contact=false}
    if type(bridge.r1_evidence_capabilities_v3)=="function" then
        local v3ok,v3=pcall(bridge.r1_evidence_capabilities_v3)
        if v3ok and type(v3)=="table" and v3.schema==3 and v3.game_build_verified==true then S.evidence_v3_caps=v3 end
    end
    S.evidence_caps={game_build_verified=false,execution_identity=false,entity_snapshot=false,combat_groups=false,fresh_engagement=false}
    if type(bridge.r1_evidence_capabilities_v2)=="function" then
        local cok,caps=pcall(bridge.r1_evidence_capabilities_v2)
        if cok and type(caps)=="table" and caps.schema==2 and caps.game_build_verified==true
            and caps.execution_identity==true and type(caps.build_id)=="string" and #caps.build_id>0 then
            S.evidence_caps=caps
        end
    end
    if DEBUG_TELEMETRY then log("R1_V3_CAPABILITIES schema=3 execution_identity="..tostring(S.evidence_v3_caps.execution_identity==true)..
        " entity_snapshot="..tostring(S.evidence_v3_caps.entity_snapshot==true)..
        " combat_groups="..tostring(S.evidence_v3_caps.combat_groups==true)..
        " contact_pairs="..tostring(S.evidence_v3_caps.contact_pairs==true)..
        " target_specific="..tostring(S.evidence_v3_caps.target_specific_physical_contact==true)..
        " build_id="..clean(S.evidence_v3_caps.build_id or "NONE")) end
    if DEBUG_TELEMETRY then log("R1_CAPABILITIES schema=2 execution_identity="..tostring(S.evidence_caps.execution_identity==true)..
        " entity_snapshot="..tostring(S.evidence_caps.entity_snapshot==true)..
        " combat_groups="..tostring(S.evidence_caps.combat_groups==true)..
        " fresh_engagement="..tostring(S.evidence_caps.fresh_engagement==true)..
        " build_id="..clean(S.evidence_caps.build_id or "NONE")..
        " native_verdicts=false requirement=R1") end
    -- Read only. No unitcontroller calls until the existing 500ms takeover delay.
    -- Missing early collections never justify a fabricated predecessor.
    if not S.late_start then
        local early_ok,early_err=pcall(function()
            collections()
            local now=clock()
            for _,st in pairs(S.states) do sample(st,now);observe_cold_idle(st,now) end
        end)
        if not early_ok then log("EARLY_BASELINE_UNAVAILABLE reason="..clean(early_err)) end
    end
    if DEBUG_TELEMETRY then dlog("OBSERVER_READY run="..RUN_ID.." epoch="..epoch.." takeover_delay_ms=500") end
end
local function start()
    if S.started then return end
    if not S.prepared then prepare(); if not S.prepared then return end end
    if DEBUG_TELEMETRY then dlog("START run="..RUN_ID) end
    collections()
    local now=clock()
    -- Preserve a PRE-input certificate until the first journal drain. Re-reading
    -- native revision here would revoke it after commands during the 500ms delay.
    for _,st in pairs(S.states) do sample(st,now) end
    S.last_model=now
    local tok,te=pcall(function() bmgr:repeat_real_callback(checked(poll),CFG.poll_ms,S.timer) end)
    if not tok then fail("TIMER_"..clean(te)); return end
    S.started=true
    if DEBUG_TELEMETRY then dlog("READY run="..RUN_ID.." epoch="..S.epoch.." page_size=64 uid_argument=decimal_string") end
    -- Consume recoverable status before the first Journal page, then re-check it
    -- after draining. Observer was already active during the 500 ms takeover delay.
    if not status() then return end
    if not drain(now) then return end
    if not status() then return end
    for _,st in pairs(S.states) do observe_cold_idle(st,now) end
    if DEBUG_TELEMETRY then dlog("INPUT_READY run="..RUN_ID.." route=SHIFT_MOVE_CHAIN_ATTACK_SHIFT_MOVE_CONTINUOUS_APPEND") end
end
function Core.boot()
    if TEST_PROFILE~="JOINT" and TEST_PROFILE~="ROUTE_ONLY" then error("INVALID_TEST_PROFILE") end
    if CONTROLLER_PHASE~="P1E" and CONTROLLER_PHASE~="P2B" then error("INVALID_CONTROLLER_PHASE") end
    if DEBUG_TELEMETRY then dlog("TEST_BEHAVIOUR_DISABLED profile="..TEST_PROFILE.." artificial_attack_delay_ms=0") end
    if _VERSION~="Lua 5.1" then error("WRONG_LUA_VERSION "..tostring(_VERSION)) end
    local ok,b=pcall(function() return bm end)
    if not ok or not b then error("BATTLE_MANAGER_UNAVAILABLE") end
    bmgr=b; if DEBUG_TELEMETRY then dlog("BATTLE_MANAGER_OK") end
    if type(package)~="table" or type(package.loadlib)~="function" then error("LOADLIB_UNAVAILABLE") end
    ensure_embedded_native()
    local lok,loader,le=pcall(package.loadlib,".\\wh3_native_bridge.dll","luaopen_wh3_native_bridge")
    if not lok or type(loader)~="function" then error("DLL_LOAD "..clean(le or loader)) end
    local bok,module,be=pcall(loader)
    if not bok or type(module)~="table" then error("DLL_INIT "..clean(be or module)) end
    bridge=module
    for _,k in ipairs({"version","number_abi_probe","exact_id_probe","get_status","start_observer","begin_battle","end_battle",
        "get_unit_revision","arm_verified_issue","issue_verified_command","cancel_pending_issue","read_journal","acknowledge",
        "r1_evidence_capabilities_v3","bind_evidence_unit_v3","read_active_order_identity_v3","read_entity_snapshot_v3","read_combat_groups_v3","read_contact_events_v3","contact_owner_ready_v3"}) do
        if type(bridge[k])~="function" then error("MISSING_BRIDGE_API "..k) end
    end
    if bridge.version()~="1.0.15-r4-evidence-v3-validated-userdata-root" then error("WRONG_BRIDGE_VERSION") end
    local n,f=bridge.number_abi_probe(); local a,c=bridge.exact_id_probe()
    if n~=16777215 or f~=1.5 or a~="4294967295" or c~="16777217" then error("BRIDGE_ABI_SELFTEST") end
    log("BRIDGE_OK version=1.0.15-r4-evidence-v3-validated-userdata-root")
    if DEBUG_TELEMETRY then log("FEG_CONFIG version="..FEG.VERSION.." enabled=true confirmation_ms="..FEG.DEFAULTS.confirm_ms..
        " close_confirmation_ms="..FEG.DEFAULTS.close_confirm_ms.." sample_window_ms="..FEG.DEFAULTS.window_ms..
        " sustained_contact_ms="..FEG.DEFAULTS.contact_confirm_ms.." geometry_confirm_ms="..FEG.DEFAULTS.geometry_confirm_ms.." hold_ms="..CFG.attack_hold_ms.." charging_required=false native_changed=true max_inflight="..CFG.max_inflight) end
    local scheduled=false
    local function schedule()
        if scheduled or S.started or S.failed or S.closed then return end
        scheduled=true; if DEBUG_TELEMETRY then dlog("PHASE_CALLBACK Deployed") end
        -- Start observing immediately so input during the validated 500 ms safety
        -- delay is not lost. Only scripted takeover/dispatch remains delayed.
        prepare()
        if S.failed or not S.prepared then return end
        bmgr:callback(checked(start),500)
    end
    bmgr:register_phase_change_callback("Deployed",checked(schedule))
    bmgr:register_phase_change_callback("VictoryCountdown",function() stop("VictoryCountdown") end)
    bmgr:register_phase_change_callback("Complete",function() stop("Complete") end)
    local phase=bmgr:get_current_phase_name()
    S.late_start=(phase=="Deployed")
    if DEBUG_TELEMETRY then dlog("LOADED phase="..clean(phase).." run="..RUN_ID) end
    if phase=="Deployed" then schedule() else if DEBUG_TELEMETRY then dlog("WAITING_FOR_DEPLOYED") end end
end
local ok,err=xpcall(Core.boot,trace)
if not ok then fail(err) end
