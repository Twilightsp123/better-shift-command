-- Turn Handoff P2B-HF5 / 0.2.5 production-logging derivative.
-- Core control behavior is intended to remain identical to runtime-validated HF5.
-- High-frequency diagnostic telemetry is disabled by default for release use.
-- One persistent action log, stable execution cursor, accepted queued APPEND at any stage.
-- No synthetic destination, no timer reset on APPEND, no repeated escape orders.
-- Frozen dependency: v0.5.0 Experimental Bridge. No native code is changed.
-- P2B supports MOVE* -> ATTACK -> observed melee hold -> MOVE* and direct ATTACK -> Shift MOVE*.
-- A player-native non-queued ATTACK is adopted, never re-issued; its engagement history remains appendable.
local RUN_ID = "P1E_P2B_DIRECT" -- Installer substitutes a unique receipt-bound ID.
local TEST_PROFILE = "ROUTE_ONLY" -- Compatibility label only; never changes motion.
local CONTROLLER_PHASE = "P2B" -- Installer can select P1E for terminal-only regression.
local CONTROLLER_VERSION = "0.2.5" -- Phase/installer protocol stays P2B; no file-tree rename.
local TAG = "[BETTER_SHIFT_COMMAND] "
-- Production release default. Set true only in the dedicated debug build.
local DEBUG_TELEMETRY = false
out(TAG .. "ENTER version=" .. CONTROLLER_VERSION .. " run=" .. RUN_ID .. " test_profile=" .. TEST_PROFILE .. " phase=" .. CONTROLLER_PHASE .. " build=BETTER_SHIFT_COMMAND_V1.0 debug_telemetry=" .. tostring(DEBUG_TELEMETRY))

-- out is callable; it need not have Lua type "function".
local function log(s) out(TAG .. tostring(s)) end
local function dlog(s) if DEBUG_TELEMETRY then out(TAG .. tostring(s)) end end
local function clean(s) return (tostring(s):gsub("[%c%s]", "_")) end
local function finite(n) return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge end
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
local CFG={poll_ms=100,page_size=64,max_pages=16,ack_timeout_ms=5000,
    progress_gate=0.20,angle_straight=30,angle_uturn=45,speed_cap=10,speed_seconds=0.50,
    formation_straight=0.60,formation_uturn=1.00,lead_floor=12,lead_cap=50,
    execution_straight=0.70,execution_uturn=1.00,proximity=6,stall_distance=12,
    stall_speed=1.50,brake_extra=4,attack_distance=8,attack_stall_distance=12,
    cancel_observe_ms=5000,max_actions=256,
    -- ATTACK-specific policy; MOVE geometry/decisions below remain byte-identical.
    attack_lead_straight=20,attack_lead_uturn=28,attack_speed_seconds=0.50,
    attack_speed_cap=5,attack_width_factor=0.10,attack_width_cap=4,
    attack_lead_cap=35,attack_execution_cap=0.45,attack_min_samples=2,
    -- Narrow U-turn cap relaxation, not an increase of the global 35m cap.
    attack_uturn_start=135,attack_uturn_execution_cap=0.70,
    attack_poll_lead_cap=6,attack_poll_horizon_ms=750,
    attack_hold_ms=3000,attack_observation_gap_ms=1000,
    -- Diagnostics only: long approach never authorizes/cancels behaviour.
    attack_long_wait_notice_ms=30000,attack_long_wait_repeat_ms=30000,
    cold_idle_max_age_ms=1000,exit_trace_ms=60000,exit_trace_interval_ms=1000}
local bmgr,bridge
local S={started=false,failed=false,closed=false,epoch=nil,cursor="0",pending=nil,
    states={},targets={},cancel_checks={},timer="TH_P1E_P2B_"..RUN_ID,last_model=nil,
    last_heartbeat=-1000000,order_count=0,dispatch_count=0,route_passes=0,cancel_passes=0}

-- Telemetry is strictly read-only. There is no behavioural test window.
local ATTACK_TRACE={}
local EXIT_TRACE={}

local function observe_attack(st,now)
    if not DEBUG_TELEMETRY then ATTACK_TRACE[st.uid]=nil; return end
    local t=ATTACK_TRACE[st.uid]
    if not t then return end
    if t.gen~=st.gen or now-t.started>2500 then ATTACK_TRACE[st.uid]=nil; return end
    if t.last and now-t.last<250 then return end
    t.last=now
    if not st.pos then return end
    dlog("ATTACK_POST_SAMPLE uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
        " model_ms="..string.format("%.0f",now).." elapsed_ms="..string.format("%.0f",now-t.started)..
        " accepted_terminal="..tostring(st.terminal).." speed="..string.format("%.6f",median(st.speeds) or 0)..
        " instant_speed="..string.format("%.6f",st.speeds[#st.speeds] or 0)..
        " x="..string.format("%.6f",st.pos.x).." z="..string.format("%.6f",st.pos.z))
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
local function clock()
    local t=bmgr:time_elapsed_ms()
    if not finite(t) or t<0 then error("MODEL_TIME_UNAVAILABLE") end
    return t
end
local function status()
    local ok,s,e=pcall(bridge.get_status)
    if not ok or type(s)~="table" then fail("STATUS_"..clean(e or s)); return nil end
    if not s.recording or s.epoch~=S.epoch or s.capture_errors~="0" or s.gate_fault~="OK" then
        fail("BRIDGE_STATE epoch="..clean(s.epoch).." capture="..clean(s.capture_errors).." gate="..clean(s.gate_fault)); return nil
    end
    return s
end
local function arm()
    local s=status(); if not s then return false end
    if s.experimental_issue_armed==true then return true end
    if s.experimental_calibration_ready~=true then return false end
    local ok,r,e=pcall(bridge.arm_verified_issue,true)
    if not ok or r~=true then fail("ARM_"..clean(e or r)); return false end
    s=status()
    if not s or s.experimental_issue_armed~=true then fail("ARM_NOT_CONFIRMED"); return false end
    log("BRIDGE_ARMED production_exact_source=false")
    return true
end
local function release(st) pcall(function() st.uc:release_control() end) end
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
            dlog("COLD_IDLE_READY uid="..st.uid.." rev="..rev.." native_state="..native_state.." model_ms="..string.format("%.0f",now)..
                " idle=true moving=false melee=false target=nil scope=FIRST_LOCAL_ORDER_ONLY")
        end
        st.cold_idle={revision=rev,native_state=native_state,ms=now,pos=copy(p)}
    else
        if st.cold_idle then dlog("COLD_IDLE_REVOKED uid="..st.uid.." model_ms="..string.format("%.0f",now)) end
        st.cold_idle=nil
        local note=clean(native_state)..":"..clean(idle)..":"..clean(moving)..":"..clean(melee)..":"..tostring(tok)..":"..clean(target and uid(target))
        if st.cold_note~=note then
            st.cold_note=note
            dlog("COLD_IDLE_UNAVAILABLE uid="..st.uid.." native_state="..clean(native_state)..
                " idle="..clean(idle).." moving="..clean(moving).." melee="..clean(melee)..
                " target_api_ok="..tostring(tok).." target="..clean(target and uid(target))..
                " model_ms="..string.format("%.0f",now).." policy=NO_GUESSED_QUEUE_SEED")
        end
    end
end
local function observe_exit(st,now)
    if not DEBUG_TELEMETRY then EXIT_TRACE[st.uid]=nil; return end
    local t=EXIT_TRACE[st.uid]
    if not t then return end
    if t.gen~=st.gen or not st.plan or st.blocked or now-t.started>CFG.exit_trace_ms then
        EXIT_TRACE[st.uid]=nil; return
    end
    if t.last and now-t.last<CFG.exit_trace_interval_ms then return end
    t.last=now
    local melee=api_bool(st.unit,"is_in_melee")
    local ok,target=pcall(function() return st.unit:current_target() end)
    local observed=(ok and target) and uid(target) or nil
    local pos=point(st.unit)
    local target_pos=t.target and point(t.target)
    local remaining=pos and dist(pos,t.dest) or nil
    local separation=(pos and target_pos) and dist(pos,target_pos) or nil
    local bbox=t.target and unit_distance_to(st.unit,t.target) or nil
    dlog("P2_EXIT_OBSERVED uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
        " attack_issue="..t.attack_issue.." model_ms="..string.format("%.0f",now)..
        " elapsed_ms="..string.format("%.0f",now-t.started).." melee="..clean(melee)..
        " observed="..clean(observed).." target_api_ok="..tostring(ok)..
        " remaining_C="..num_or_nil(remaining).." dist="..num_or_nil(separation)..
        " bbox_distance="..num_or_nil(bbox).." speed="..num_or_nil(median(st.speeds))..
        " instant_speed="..num_or_nil(st.speeds[#st.speeds])..
        " unit_x="..num_or_nil(pos and pos.x).." unit_z="..num_or_nil(pos and pos.z)..
        " policy=READ_ONLY_NO_REISSUE")
    if remaining and remaining<=6 then
        dlog("P2_EXIT_REACHED_PN uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
            " attack_issue="..t.attack_issue.." model_ms="..string.format("%.0f",now)..
            " elapsed_ms="..string.format("%.0f",now-t.started).." remaining_C="..num_or_nil(remaining)..
            " dist="..num_or_nil(separation).." bbox_distance="..num_or_nil(bbox)..
            " melee="..clean(melee).." observed="..clean(observed)..
            " speed="..num_or_nil(median(st.speeds)).." policy=READ_ONLY_COMPLETION_OBSERVATION")
        EXIT_TRACE[st.uid]=nil
    end
end
local function timed_attack_supported(st)
    -- The P2 timer mode is deliberately ground melee only. Do not silently
    -- reinterpret primary missile fire or flight as melee engagement.
    local ok,ammo=pcall(function() return st.unit:starting_ammo() end)
    if not ok or not finite(ammo) or ammo<0 then return false,"STARTING_AMMO_API_UNAVAILABLE" end
    if ammo>0 then return false,"RANGED_TIMING_UNSUPPORTED" end
    local flying=api_bool(st.unit,"is_currently_flying")
    local artillery=api_bool(st.unit,"is_artillery")
    if flying==nil or artillery==nil then return false,"UNIT_MODE_API_UNAVAILABLE" end
    if flying or artillery then return false,"FLIGHT_ARTILLERY_TIMING_UNSUPPORTED" end
    local melee=api_bool(st.unit,"is_in_melee")
    local tok=pcall(function() return st.unit:current_target() end)
    if melee==nil or not tok then return false,"ENGAGEMENT_API_UNAVAILABLE" end
    return true
end
local function target_viable(a)
    if not a.target or uid(a.target)~=a.target_uid then return false,"TARGET_IDENTITY_INVALID" end
    local alive=api_bool(a.target,"is_valid_target")
    local routing=api_bool(a.target,"is_routing")
    if alive==nil or routing==nil then return false,"TARGET_API_UNAVAILABLE" end
    if not alive then return false,"TARGET_INVALID" end
    if routing then return false,"TARGET_ROUTING" end
    return true
end
local function new_state(su)
    return {uid=uid(su.unit),unit=su.unit,uc=su.uc,gen=0,revision=nil,actions={},plan=nil,
        idx=1,owned=false,terminal=false,blocked=false,speeds={},pos=nil,last_pos=nil,
        last_sample=nil,origin=nil,moves=0,last_wait=-1000000,refused=nil,phase="NATIVE_TRACKING",attack=nil,model_step_ms=0,cold_seen=false,cold_idle=nil}
end
local function collections()
    -- Same two collection methods used by the runtime-validated v0.5.0 client.
    local own=bmgr:get_scriptunits_for_local_players_army()
    local enemy=bmgr:get_scriptunits_for_main_enemy_army_to_local_player()
    if not own or own:count()<1 then error("NO_LOCAL_SCRIPTUNITS") end
    for i=1,own:count() do
        local su=own:item(i); local u=su and su.unit and uid(su.unit)
        if not u or not su.uc then error("BAD_LOCAL_SCRIPTUNIT") end
        if not S.states[u] then
            S.states[u]=new_state(su); log("REGISTER_LOCAL uid="..u)
        end
    end
    if enemy then
        for i=1,enemy:count() do
            local su=enemy:item(i); local u=su and su.unit and uid(su.unit)
            if u then S.targets[u]=su.unit end
        end
    end
end
local cancel
local begin_attack_history
local function sample(st,now)
    local p=point(st.unit)
    if not p then
        if st.plan then log("UNIT_UNAVAILABLE uid="..st.uid); cancel(st,"UNIT_UNAVAILABLE",now,false); st.blocked=true; st.phase="UNIT_UNAVAILABLE" end
        return
    end
    if st.last_sample and now>st.last_sample then
        st.model_step_ms=now-st.last_sample
        local speed=dist(p,st.last_pos)*1000/(now-st.last_sample)
        if finite(speed) then st.speeds[#st.speeds+1]=speed; if #st.speeds>5 then table.remove(st.speeds,1) end end
    end
    st.pos=p; st.last_pos=copy(p); st.last_sample=now
end
cancel=function(st,reason,now,observe)
    local old=st.gen
    st.cold_idle=nil; EXIT_TRACE[st.uid]=nil
    if st.plan or st.owned then
        local tracked=st.plan~=nil
        log("GEN_CANCEL uid="..st.uid.." gen="..old.." reason="..reason.." owned="..tostring(st.owned).." tracked="..tostring(tracked).." terminal="..tostring(st.terminal).." phase="..clean(st.phase).." model_ms="..string.format("%.0f",now))
        -- A player-native Attack-first plan is actively tracked even before Lua has
        -- issued any command. REPLACE must still prove that the old generation stays dead.
        if observe and tracked and not st.terminal then
            S.cancel_checks[#S.cancel_checks+1]={uid=st.uid,gen=old,start=now,logged=false}
        end
    end
    st.gen=st.gen+1; st.actions={}; st.plan=nil; st.idx=1; st.origin=nil
    st.owned=false; st.terminal=false; st.moves=0; st.refused=nil; st.attack=nil; st.phase="CANCELLED"; st.input_gapped=false; st.tail_reached=false
    -- A pending native order is NOT relabelled to the new generation.
end
local function action(st,r,now)
    if type(r.is_queued)~="boolean" then return nil,"QUEUED_MISSING" end
    local a={type=r.order_type,serial=r.serial,seq=r.engine_seq_valid and r.engine_seq or nil,
        revision=r.unit_revision,queued=r.is_queued,origin=point(st.unit),captured_ms=now}
    if a.type=="MOVE" then
        if not finite(r.dest_x) or not finite(r.dest_y) or not finite(r.dest_z) then return nil,"MOVE_PAYLOAD" end
        a.pos={x=r.dest_x,y=r.dest_y,z=r.dest_z}
    elseif a.type=="ATTACK" then
        if not id(r.target_uid) then return nil,"ATTACK_UID" end
        a.target_uid=r.target_uid; a.target=S.targets[r.target_uid]
    else return nil,"UNSUPPORTED_KIND" end
    return a
end
local function plan_supported(st,actions)
    if #actions==0 then return false,"EMPTY_PLAN" end
    local first=actions[1]
    local attack_first=CONTROLLER_PHASE=="P2B" and first.type=="ATTACK" and first.queued==false
    if first.type~="MOVE" and not attack_first then
        return false,first.type=="ATTACK" and "ATTACK_FIRST_PHASE2_REQUIRED" or "MOVE_OR_ATTACK_FIRST_REQUIRED"
    end
    local attacks=0
    for i,a in ipairs(actions) do
        if a.type=="ATTACK" then
            attacks=attacks+1
            if not a.target or uid(a.target)~=a.target_uid then return false,"TARGET_UNRESOLVED" end
            if CONTROLLER_PHASE=="P2B" then
                local ok,why=timed_attack_supported(st); if not ok then return false,why end
                local good,reason=target_viable(a); if not good then return false,reason end
            elseif i<#actions then return false,"TAIL_AFTER_ATTACK_PHASE2_REQUIRED" end
        end
    end
    if CONTROLLER_PHASE=="P1E" and attacks>1 then return false,"MULTIPLE_ATTACKS_PHASE2_REQUIRED" end
    return true
end
local function ingest(r,now)
    local st=S.states[r.unit_uid]
    if not st then return end
    local cold=not st.cold_seen and st.cold_idle or nil
    st.cold_seen=true; st.cold_idle=nil -- including failed/unsupported first orders
    S.order_count=S.order_count+1
    dlog("ORDER uid="..st.uid.." serial="..r.serial.." type="..clean(r.order_type).." status="..clean(r.status)..
        " source="..clean(r.source).." issue="..clean(r.script_issue_id).." rev="..r.unit_revision.." queued="..clean(r.is_queued).." target="..clean(r.target_uid)..(r.order_type=="MOVE" and (" x="..clean(r.dest_x).." z="..clean(r.dest_z)) or ""))
    local p=S.pending
    if r.source=="OUR_CONTROLLER" then
        if not p or r.script_issue_id~=p.issue or r.unit_uid~=p.uid then
            fail("UNEXPECTED_OWN_ACK uid="..st.uid.." issue="..clean(r.script_issue_id)); return
        end
        S.pending=nil
        if st.gen~=p.gen then
            log("LATE_OWN_ACK_IGNORED uid="..st.uid.." gen="..p.gen.." issue="..p.issue.." status="..r.status)
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
                log("OWN_STALE_AFTER_APPEND uid="..st.uid.." gen="..st.gen.." issue="..p.issue..
                    " idx="..p.idx.." expected_revision="..p.revision.." rev="..st.revision..
                    " model_ms="..string.format("%.0f",now).." policy=REDECIDE_NEW_ISSUE_NO_STALE_REPLAY")
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
            if not finite(r.dest_x) or not finite(r.dest_y) or not finite(r.dest_z)
                or math.abs(r.dest_x-q.x)>0.05 or math.abs(r.dest_y-q.y)>0.05 or math.abs(r.dest_z-q.z)>0.05 then
                fail("OWN_MOVE_PAYLOAD_MISMATCH"); return
            end
        end
        st.revision=r.unit_revision; st.idx=p.idx; st.origin=p.origin; st.owned=true
        if p.kind=="MOVE" then
            st.moves=st.moves+1; st.phase="MOVE_TRACKING"
            log("OWN_MOVE_ACK uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." idx="..p.idx.." rev="..st.revision.." model_ms="..string.format("%.0f",now))
            if p.after_attack then
                log("P2_MOVE_AFTER_ATTACK_ACK uid="..st.uid.." gen="..st.gen.." issue="..p.issue..
                    " idx="..p.idx.." attack_issue="..p.attack_issue.." hold_ms="..string.format("%.0f",p.hold_ms)..
                    " model_ms="..string.format("%.0f",now).." expected_revision="..p.revision.." rev="..st.revision..
                    " claim=COMMAND_ACCEPTED_NOT_PHYSICAL_DISENGAGEMENT")
                if DEBUG_TELEMETRY then
                    EXIT_TRACE[st.uid]={gen=st.gen,issue=p.issue,attack_issue=p.attack_issue,started=now,
                        dest=copy(st.plan[p.idx].pos),target=st.plan[p.idx-1].target}
                end
                st.attack=nil
            end
        else
            log("OWN_ATTACK_ACK uid="..st.uid.." gen="..st.gen.." issue="..p.issue.." idx="..p.idx.." target="..p.target_uid.." rev="..st.revision.." model_ms="..string.format("%.0f",now))
            if CONTROLLER_PHASE=="P2B" then
                begin_attack_history(st,st.plan[p.idx],now,"OUR_CONTROLLER",p.issue)
            end
            if not st.plan[p.idx+1] then
                if CONTROLLER_PHASE=="P1E" then st.terminal=true; st.phase="TERMINAL_ATTACK" end
                if st.moves>0 then
                    S.route_passes=S.route_passes+1
                    dlog("CASE_ROUTE_PASS uid="..st.uid.." gen="..st.gen.." own_moves="..st.moves.." attack_target="..p.target_uid.." visual_smoothness=UNASSESSED")
                end
                log("PHASE1_ATTACK_TERMINAL uid="..st.uid.." gen="..st.gen.." model_ms="..string.format("%.0f",now))
                log("ATTACK_CURRENT_TAIL uid="..st.uid.." gen="..st.gen.." issue="..p.issue..
                    " model_ms="..string.format("%.0f",now).." automatic_exit=false appendable=true history="..
                    tostring(st.attack~=nil).." reason=NO_KNOWN_SUCCESSOR_YET")
            end
        end
        return
    end
    if not accepted(r) then
        if r.status=="INDETERMINATE" then fail("EXTERNAL_INDETERMINATE") end
        return
    end
    if st.revision and r.unit_revision~=inc(st.revision) then
        fail("EXTERNAL_REVISION_DISCONTINUITY uid="..st.uid); return
    end
    st.revision=r.unit_revision
    if r.order_type~="MOVE" and r.order_type~="ATTACK" then
        cancel(st,"EXTERNAL_"..clean(r.order_type),now,true); st.blocked=false; return
    end
    local a,err=action(st,r,now)
    if not a then cancel(st,err,now,false); st.blocked=true; log("INPUT_REFUSED uid="..st.uid.." reason="..err); return end
    if not a.queued then
        cancel(st,"EXTERNAL_REPLACE",now,true); st.blocked=false
    elseif (st.owned or (p and p.uid==st.uid)) and CONTROLLER_PHASE=="P1E" then
        cancel(st,"P1E_COMPAT_LIVE_APPEND_UNSUPPORTED",now,false); st.blocked=true
        log("LIVE_APPEND_YIELD uid="..st.uid.." remaining_lua_plan_discarded=true"); return
    elseif st.blocked then return
    elseif #st.actions==0 then
        local age=cold and now-cold.ms or math.huge
        local good=a.type=="MOVE" and cold and
            ((cold.native_state=="UNSEEN" and cold.revision=="MISSING") or
             (cold.native_state=="REVISION_ZERO" and cold.revision=="0")) and r.unit_revision=="1"
            and age>=0 and age<=CFG.cold_idle_max_age_ms and not S.late_start
        if not good then
            st.blocked=true
            dlog("QUEUED_WITHOUT_REPLACE_IGNORED uid="..st.uid.." serial="..r.serial..
                " reason=NO_FRESH_COLD_IDLE_PREDECESSOR native_plan_preserved=true")
            return
        end
        st.gen=st.gen+1
        a.origin=copy(cold.pos); a.seed_mode="COLD_IDLE_QUEUED"
        -- Preserve native queued=true. Do not forge a REPLACE or send a priming order.
        dlog("COLD_IDLE_SEED uid="..st.uid.." gen="..st.gen.." serial="..a.serial..
            " native_queued=true snapshot_revision="..cold.revision.." native_state="..cold.native_state.." rev="..r.unit_revision..
            " snapshot_ms="..string.format("%.0f",cold.ms).." age_ms="..string.format("%.0f",age)..
            " model_ms="..string.format("%.0f",now).." origin=OBSERVED_IDLE_BEFORE_FIRST_ORDER")
    end
    if #st.actions>=CFG.max_actions then cancel(st,"ACTION_CAP",now,false); st.blocked=true; return end
    -- The action log is canonical: published indices and execution origin never reset on APPEND.
    local active=st.plan~=nil
    if active and st.plan~=st.actions then fail("CANONICAL_PLAN_IDENTITY"); return end
    st.actions[#st.actions+1]=a
    -- Validate the not-yet-executed suffix. Completed attacks need not remain valid forever.
    local candidate={st.actions[1]}
    for i=math.max(2,st.idx),#st.actions do candidate[#candidate+1]=st.actions[i] end
    local supported,why=plan_supported(st,candidate)
    if active and not supported then
        cancel(st,"APPEND_"..why,now,false); st.blocked=true
        log("APPEND_REFUSED uid="..st.uid.." reason="..why.." policy=YIELD_NO_GUESSED_ACTION"); return
    end
    if not active then st.phase="NATIVE_TRACKING" end
    st.tail_reached=false
    if a.queued and p and p.uid==st.uid and p.gen==st.gen then p.saw_append=true end
    dlog("ACTION_CAPTURE uid="..st.uid.." gen="..st.gen.." idx="..#st.actions.." type="..a.type.." serial="..a.serial.." queued="..tostring(a.queued).." seed_mode="..(a.seed_mode or "REPLACE_OR_APPEND").." model_ms="..string.format("%.0f",now)..
        (a.pos and (" x="..string.format("%.6f",a.pos.x).." z="..string.format("%.6f",a.pos.z)) or (" target="..clean(a.target_uid))))
    if active then
        dlog("PLAN_APPENDED uid="..st.uid.." gen="..st.gen.." serial="..a.serial..
            " idx="..#st.actions.." cursor="..st.idx.." actions="..#st.actions..
            " owned="..tostring(st.owned).." phase="..st.phase..
            " eligible_ms="..string.format("%.0f",st.attack and st.attack.eligible_ms or 0)..
            " model_ms="..string.format("%.0f",now).." timer_reset=false origin_reset=false")
    end
end
local function valid_record(r,previous)
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
            if not valid_record(rows[i],previous) then fail("JOURNAL_RECORD_CONTRACT"); return false end
            previous=rows[i].serial
        end
        if m.next_after~=previous or cmp(m.newest_serial,previous)<0 then fail("JOURNAL_CURSOR_CONTRACT"); return false end
        -- Validate the entire page BEFORE ingesting any part of it.
        for i=1,#rows do ingest(rows[i],now); if S.failed then return false end end
        if #rows>0 then
            local aok,a,ae=pcall(bridge.acknowledge,S.epoch,m.next_after)
            if not aok or a~=true then fail("ACK_"..clean(ae or a)); return false end
            S.cursor=m.next_after
        end
        if S.cursor==m.newest_serial then return true end
        if #rows==0 then fail("EMPTY_PAGE_WITH_BACKLOG"); return false end
    end
    -- Bounded work; no dispatch until every known earlier record is consumed.
    log("JOURNAL_BACKLOG_DEFER cursor="..S.cursor)
    return false
end
begin_attack_history=function(st,a,now,source,issue)
    st.phase="ATTACK_APPROACH"
    st.attack={issue=issue,idx=st.idx,accepted_ms=now,last_ms=now,eligible_ms=0,noneligible_ms=0,
        previous_eligible=false,observed_once=false,last_log=-1000000,done=false,
        target_uid=a.target_uid,long_wait_next_ms=CFG.attack_long_wait_notice_ms,
        target_last_pos=nil,target_last_ms=nil,target_speed=nil,native_player=(source=="PLAYER_NATIVE")}
    log("ATTACK_ACCEPTED uid="..st.uid.." gen="..st.gen.." issue="..issue.." idx="..st.idx..
        " expected_revision="..st.revision.." rev="..st.revision.." intended="..a.target_uid..
        " model_ms="..string.format("%.0f",now).." hold_required_ms="..CFG.attack_hold_ms..
        " approach_timeout=DISABLED long_wait_notice_ms="..CFG.attack_long_wait_notice_ms..
        " hold_mode=MELEE_CURRENT_TARGET_OBSERVATION has_tail="..tostring(st.plan[st.idx+1]~=nil)..
        " appendable=true source="..source.." native_serial="..clean(a.serial))
end
local function activate(st)
    if st.plan or st.blocked or #st.actions==0 then return end
    local first=st.actions[1]
    local attack_first=CONTROLLER_PHASE=="P2B" and first.type=="ATTACK" and first.queued==false
    if #st.actions<2 and not attack_first then return end
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
    if attack_first then first.seed_mode="PLAYER_ATTACK_REPLACE" end
    st.phase=attack_first and "ATTACK_APPROACH" or "MOVE_TRACKING"
    log("PLAN_ACTIVATED uid="..st.uid.." gen="..st.gen.." actions="..#st.plan..
        " cursor=1 phase="..CONTROLLER_PHASE.." appendable=true seed_mode="..(first.seed_mode or "REPLACE")..
        " first_type="..first.type.." model_ms="..string.format("%.0f",clock()))
    if attack_first then
        -- The player's ordinary RMB Attack is already native-accepted. Never re-issue it.
        -- Start engagement history immediately so a later Shift pN does not reset the timer.
        st.owned=false
        log("PLAYER_ATTACK_ADOPTED uid="..st.uid.." gen="..st.gen.." serial="..first.serial..
            " target="..first.target_uid.." rev="..st.revision.." appendable=true reissued=false")
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

local function vector_at(st,p)
    -- The v0.5.0 runtime-tested constructor is v_offset, not a guessed v() ABI.
    local base=st.unit:position()
    return v_offset(base,p.x-base:get_x(),p.y-base:get_y(),p.z-base:get_z())
end
local function dispatch(st,index,reason,g,now)
    if S.pending or S.failed then return end
    local generation=st.gen
    local selected=st.plan and st.plan[index]
    if not drain(now) or S.pending or S.failed or st.gen~=generation or not st.plan then return end
    if st.plan[index]~=selected or index~=st.idx+1 then fail("DISPATCH_CURSOR_IDENTITY"); return end
    if not arm() then
        if now-st.last_wait>=1000 then
            st.last_wait=now; log("WAIT_CALIBRATION uid="..st.uid.." note=natural_player_move_and_attack_required")
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
    local a=st.plan[index]
    if not a then fail("DISPATCH_ACTION_MISSING"); return end
    if a.type=="ATTACK" and (not a.target or uid(a.target)~=a.target_uid) then
        cancel(st,"TARGET_INVALIDATED",now,false); st.blocked=true; return
    end
    if st.attack or (a.type=="ATTACK" and st.plan[index+1]) then
        local current_attack=st.attack and st.plan[st.idx] or a
        local good,why=target_viable(current_attack)
        if not good then cancel(st,why,now,false); st.blocked=true; release(st); return end
    end
    local from_attack=st.attack~=nil
    local after_attack=a.type=="MOVE" and from_attack
    local attack_issue=from_attack and st.attack.issue or nil
    local hold_ms=from_attack and st.attack.eligible_ms or nil
    if from_attack and (not st.attack.done or hold_ms<CFG.attack_hold_ms) then fail("ATTACK_HOLD_NOT_DONE"); return end
    local origin=point(st.unit); if not origin then cancel(st,"UNIT_POSITION",now,false); return end
    local called=false
    local sent,issue,result=pcall(bridge.issue_verified_command,a.type,false,st.uid,rev,function()
        called=true
        if S.failed or S.closed or st.gen~=generation or not st.plan then error("CALLBACK_GENERATION_INVALID") end
        local cok,ce=pcall(function()
            if a.type=="MOVE" then st.uc:goto_location(vector_at(st,a.pos),true)
            else st.uc:attack_unit(a.target,true,true) end
        end)
        release(st)
        if not cok then error(ce) end
    end)
    if not sent or not id(issue) or result~="PENDING_NATIVE_ACCEPTANCE" or not called then
        if sent and issue==nil and result=="REJECTED_STALE" and not called then
            cancel(st,"REJECTED_STALE",now,true); st.blocked=true; return
        end
        fail("ISSUE_"..clean(a.type).."_"..clean(result or issue)); return
    end
    S.pending={uid=st.uid,gen=generation,issue=issue,kind=a.type,idx=index,origin=origin,
        revision=rev,target_uid=a.target_uid,started=now,after_attack=after_attack,attack_issue=attack_issue,hold_ms=hold_ms,
        previous_idx=st.idx,previous_owned=st.owned,action=a,saw_append=false}
    S.dispatch_count=S.dispatch_count+1; st.owned=true; st.phase=a.type=="MOVE" and "ISSUE_MOVE_PENDING" or "ISSUE_ATTACK_PENDING"
    if DEBUG_TELEMETRY and a.type=="ATTACK" then ATTACK_TRACE[st.uid]={gen=generation,issue=issue,started=now} end
    log("DISPATCH_"..a.type.." uid="..st.uid.." gen="..generation.." issue="..issue.." idx="..index..
        " expected_revision="..rev.." target="..clean(a.target_uid).." reason="..reason.." remaining="..string.format("%.3f",g.remaining)..
        " threshold="..string.format("%.6f",g.threshold).." speed="..string.format("%.6f",g.speed)..
        (a.pos and (" dest_x="..string.format("%.6f",a.pos.x).." dest_z="..string.format("%.6f",a.pos.z)) or "")..
        " model_ms="..string.format("%.0f",now)..
        (a.type=="ATTACK" and ((from_attack and (" previous_attack_issue="..attack_issue.." hold_ms="..string.format("%.0f",hold_ms))
            or attack_metrics(g,now)).." test_delayed=false") or ""))
    if after_attack then
        log("DISPATCH_MOVE_AFTER_ATTACK uid="..st.uid.." gen="..generation.." issue="..issue.." idx="..index..
            " attack_issue="..attack_issue.." expected_revision="..rev.." hold_ms="..string.format("%.0f",hold_ms)..
            " model_ms="..string.format("%.0f",now).." target_x="..string.format("%.6f",a.pos.x).." target_z="..string.format("%.6f",a.pos.z))
    end
end
local function advance_attack(st,now)
    local t=st.attack
    if not t then fail("ATTACK_STATE_MISSING"); return end
    local a=st.plan[st.idx]
    local good,why=target_viable(a)
    if not good then
        log("ATTACK_TARGET_INVALID uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." reason="..why.." model_ms="..string.format("%.0f",now))
        cancel(st,why,now,false); st.blocked=true; release(st); return
    end
    local supported,unsupported=timed_attack_supported(st)
    if not supported then cancel(st,unsupported,now,false); st.blocked=true; release(st); return end
    local melee=api_bool(st.unit,"is_in_melee")
    local ok,target=pcall(function() return st.unit:current_target() end)
    if melee==nil or not ok then cancel(st,"ENGAGEMENT_API_UNAVAILABLE",now,false); st.blocked=true; if st.owned then release(st) end; return end
    local observed=target and uid(target) or nil
    local eligible=melee==true and observed==a.target_uid
    local delta=math.max(0,now-t.last_ms)
    local interval=eligible and t.previous_eligible and delta<=CFG.attack_observation_gap_ms and not st.input_gapped
    local credited=interval and delta or 0
    if delta>CFG.attack_observation_gap_ms or st.input_gapped then
        log("ATTACK_OBSERVATION_GAP uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
            " delta_ms="..string.format("%.0f",delta).." model_ms="..string.format("%.0f",now).." credited_ms=0")
    end
    st.input_gapped=false
    t.eligible_ms=t.eligible_ms+credited
    t.noneligible_ms=t.noneligible_ms+(delta-credited)

    local elapsed=math.max(0,now-t.accepted_ms)
    local bbox_distance,center_distance,target_speed,actor_speed,instant_speed
    if DEBUG_TELEMETRY then
        -- Read-only engagement telemetry. unit_distance() is CA's public shortest
        -- unit-to-unit distance (bounding boxes), while center_distance is diagnostic only.
        local target_pos=point(a.target)
        bbox_distance=unit_distance_to(st.unit,a.target)
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
        dlog("ATTACK_TARGET_OBSERVED uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." idx="..st.idx..
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
            " model_ms="..string.format("%.0f",now))
    end
    if eligible and not t.previous_eligible then
        log("ATTACK_HOLD_BEGIN uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." model_ms="..string.format("%.0f",now)..
            " resumed="..tostring(t.observed_once).." eligible_ms="..string.format("%.0f",t.eligible_ms).." test_delay=false")
        if not t.cancel_test_announced then
            dlog("ATTACK_RMB_CANCEL_TEST_READY uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                " model_ms="..string.format("%.0f",now).." phase=ATTACK_HOLD action=PLAIN_RMB_D behaviour_change=false")
            t.cancel_test_announced=true
        end
        t.observed_once=true
    elseif not eligible and t.previous_eligible then
        log("ATTACK_HOLD_SUSPEND uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." model_ms="..string.format("%.0f",now)..
            " eligible_ms="..string.format("%.0f",t.eligible_ms).." reason=OBSERVATION_NOT_ELIGIBLE")
    end
    if elapsed>=t.long_wait_next_ms and t.eligible_ms<CFG.attack_hold_ms then
        if DEBUG_TELEMETRY then
            log("ATTACK_APPROACH_LONG_WAIT uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                " elapsed_ms="..string.format("%.0f",elapsed).." eligible_ms="..string.format("%.0f",t.eligible_ms)..
                " noneligible_ms="..string.format("%.0f",t.noneligible_ms).." observed="..clean(observed)..
                " melee="..tostring(melee).." bbox_distance="..num_or_nil(bbox_distance)..
                " center_distance="..num_or_nil(center_distance).." actor_speed="..string.format("%.6f",actor_speed or 0)..
                " target_speed="..num_or_nil(target_speed or t.target_speed).." model_ms="..string.format("%.0f",now)..
                " policy=DIAGNOSTIC_ONLY_NO_BEHAVIOUR_CHANGE")
        else
            log("ATTACK_APPROACH_LONG_WAIT uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                " elapsed_ms="..string.format("%.0f",elapsed).." eligible_ms="..string.format("%.0f",t.eligible_ms)..
                " policy=DIAGNOSTIC_ONLY_NO_BEHAVIOUR_CHANGE")
        end
        repeat t.long_wait_next_ms=t.long_wait_next_ms+CFG.attack_long_wait_repeat_ms
        until t.long_wait_next_ms>elapsed
    end
    t.last_ms=now; t.previous_eligible=eligible; st.phase=eligible and "ATTACK_HOLD" or "ATTACK_APPROACH"
    if t.eligible_ms>=CFG.attack_hold_ms then
        if not st.plan[st.idx+1] then
            if not t.ready_logged then
                t.ready_logged=true
                log("ATTACK_HOLD_READY_NO_TAIL uid="..st.uid.." gen="..st.gen.." issue="..t.issue..
                    " eligible_ms="..string.format("%.0f",t.eligible_ms).." model_ms="..string.format("%.0f",now)..
                    " policy=CONTINUE_NATIVE_ATTACK_NO_INVENTED_MOVE")
            end
            return
        end
        if not t.done then
            t.done=true
            log("ATTACK_HOLD_DONE uid="..st.uid.." gen="..st.gen.." issue="..t.issue.." idx="..st.idx..
                " intended="..a.target_uid.." eligible_ms="..string.format("%.0f",t.eligible_ms)..
                " model_ms="..string.format("%.0f",now).." claim=OBSERVED_ELIGIBLE_MODEL_TIME")
        end
        dispatch(st,st.idx+1,"ATTACK_HOLD_DONE",{remaining=0,threshold=0,speed=median(st.speeds) or 0},now)
    end
end

local function advance(st,now)
    if not st.plan or st.terminal or st.blocked then return end
    if S.pending and S.pending.uid==st.uid then return end
    if st.plan[st.idx].type=="ATTACK" then advance_attack(st,now); return end
    if S.pending then return end
    local nexta=st.plan[st.idx+1]
    if not nexta then
        local remaining=st.pos and dist(st.pos,st.plan[st.idx].pos) or math.huge
        if remaining<=CFG.proximity and not st.tail_reached then
            st.tail_reached=true; st.phase="MOVE_CURRENT_TAIL_REACHED"; release(st)
            dlog("FINAL_MOVE_POSITION_REACHED uid="..st.uid.." gen="..st.gen.." idx="..st.idx..
                " remaining="..string.format("%.6f",remaining).." model_ms="..string.format("%.0f",now).." appendable=true visual_disengagement=UNASSESSED")
        end
        return
    end
    local g=geometry(st,nexta); if not g then return end
    local reason
    if nexta.type=="ATTACK" then
        g=attack_geometry(st,nexta,g)
        if not g then
            cancel(st,"ATTACK_TARGET_POSITION_UNAVAILABLE",now,false); st.blocked=true; return
        end
        local progress_ok=g.progress>=CFG.progress_gate
        -- Two motion estimates must agree that we are still moving; a stale median
        -- alone must not certify a moving handoff after the latest sample stopped.
        local moving=g.samples>=CFG.attack_min_samples and g.speed>CFG.stall_speed and g.instant_speed>CFG.stall_speed
        local sharp_braking=g.instant_speed<math.max(CFG.stall_speed,g.speed*0.55)
        if progress_ok and g.late_input and sharp_braking and g.samples>=CFG.attack_min_samples and g.remaining<=g.threshold then
            -- Cannot issue an ATTACK before it exists in the input stream.
            reason="ATTACK_LATE_INPUT_RECOVERY"
        elseif progress_ok and moving and g.remaining>CFG.attack_distance and g.remaining<=g.threshold then
            reason="ATTACK_PREDICTIVE"
        elseif progress_ok and g.samples>=CFG.attack_min_samples and g.remaining<=g.threshold and g.remaining>CFG.attack_stall_distance and not moving then
            reason="ATTACK_BRAKING_RECOVERY"
        elseif progress_ok and g.remaining<=CFG.attack_distance then
            reason="ATTACK_ENDPOINT_FALLBACK"
        elseif progress_ok and g.remaining<=CFG.attack_stall_distance and g.stall then
            reason="ATTACK_STALL_FALLBACK"
        end
        if DEBUG_TELEMETRY and not reason and now-st.last_wait>=1000 then
            st.last_wait=now
            dlog("ATTACK_TRANSITION_WAIT uid="..st.uid.." gen="..st.gen.." remaining="..string.format("%.6f",g.remaining)..
                " threshold="..string.format("%.6f",g.threshold).." speed="..string.format("%.6f",g.speed)..attack_metrics(g,now))
        end
    else
        -- Geometry remains the P1B parameterized v6.5-style kernel. It is not
        -- claimed to be an identical copy of the unavailable original v6.5 Lua.
        local progress_ok=g.progress>=CFG.progress_gate
        if g.remaining<=CFG.proximity and (not st.owned or progress_ok) then reason="PROXIMITY_A"
        elseif g.remaining<=CFG.stall_distance and g.stall and (not st.owned or progress_ok) then reason="PROXIMITY_B_STALL"
        elseif progress_ok and g.remaining<=g.threshold then reason="PREDICTIVE"
        elseif progress_ok and g.stall and g.remaining<=math.min(CFG.lead_cap,g.threshold+CFG.brake_extra) then reason="BRAKE_FALLBACK" end
    end
    if reason then dispatch(st,st.idx+1,reason,g,now) end
end
local function poll_core()
    if not S.started then return end
    local now=clock()
    if S.last_model and now<S.last_model then fail("MODEL_TIME_REVERSED"); return end
    if not drain(now) or S.failed then
        for _,st in pairs(S.states) do st.input_gapped=true end
        return
    end
    if not status() then return end
    if S.pending and now-S.pending.started>=CFG.ack_timeout_ms then fail("OWN_ACK_TIMEOUT issue="..S.pending.issue); return end
    if DEBUG_TELEMETRY and now-S.last_heartbeat>=2000 then
        S.last_heartbeat=now
        dlog("HEARTBEAT run="..RUN_ID.." model_ms="..string.format("%.0f",now).." cursor="..S.cursor..
            " orders="..S.order_count.." dispatches="..S.dispatch_count.." route_passes="..S.route_passes.." cancel_passes="..S.cancel_passes)
    end
    -- Real callback still drains input when paused; model-time motion does not advance.
    if S.last_model==now then return end
    S.last_model=now
    for _,st in pairs(S.states) do sample(st,now); observe_cold_idle(st,now); activate(st); observe_attack(st,now); observe_exit(st,now) end
    for _,st in pairs(S.states) do advance(st,now); if S.failed then return end end
    for _,c in ipairs(S.cancel_checks) do
        if not c.logged and now-c.start>=CFG.cancel_observe_ms then
            c.logged=true; S.cancel_passes=S.cancel_passes+1
            dlog("CASE_CANCEL_PASS uid="..c.uid.." gen="..c.gen.." observation_ms="..string.format("%.0f",now-c.start).." claim=NO_NEW_LUA_DISPATCH_FOR_CANCELLED_GENERATION")
        end
    end
end
local function poll()
    if S.polling then fail("POLL_REENTRY"); return end
    S.polling=true
    local ok,e=xpcall(poll_core,trace)
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
    S.started=false; S.closed=true; S.pending=nil
end
local function start()
    if S.started then return end
    log("START run="..RUN_ID)
    local ok,r,e=pcall(bridge.start_observer,true)
    if not ok or r~=true then fail("OBSERVER_"..clean(e or r)); return end
    local eok,epoch,ee=pcall(bridge.begin_battle,"th_p1e_p2b_"..RUN_ID)
    if not eok or not id(epoch) or epoch=="0" then fail("BEGIN_"..clean(ee or epoch)); return end
    S.epoch=epoch; S.cursor="0"
    collections()
    local now=clock(); for _,st in pairs(S.states) do sample(st,now) end
    S.last_model=now
    local tok,te=pcall(function() bmgr:repeat_real_callback(checked(poll),CFG.poll_ms,S.timer) end)
    if not tok then fail("TIMER_"..clean(te)); return end
    S.started=true
    log("READY run="..RUN_ID.." epoch="..epoch.." page_size=64 uid_argument=decimal_string")
    -- Validate the actual first Journal call before declaring the phase usable.
    if not drain(now) or not status() then return end
    for _,st in pairs(S.states) do observe_cold_idle(st,now) end
    log("INPUT_READY run="..RUN_ID.." route=SHIFT_MOVE_CHAIN_ATTACK_SHIFT_MOVE_CONTINUOUS_APPEND")
end
local function boot()
    if TEST_PROFILE~="JOINT" and TEST_PROFILE~="ROUTE_ONLY" then error("INVALID_TEST_PROFILE") end
    if CONTROLLER_PHASE~="P1E" and CONTROLLER_PHASE~="P2B" then error("INVALID_CONTROLLER_PHASE") end
    log("TEST_BEHAVIOUR_DISABLED profile="..TEST_PROFILE.." artificial_attack_delay_ms=0")
    if _VERSION~="Lua 5.1" then error("WRONG_LUA_VERSION "..tostring(_VERSION)) end
    local ok,b=pcall(function() return bm end)
    if not ok or not b then error("BATTLE_MANAGER_UNAVAILABLE") end
    bmgr=b; log("BATTLE_MANAGER_OK")
    if type(package)~="table" or type(package.loadlib)~="function" then error("LOADLIB_UNAVAILABLE") end
    local lok,loader,le=pcall(package.loadlib,".\\wh3_native_bridge.dll","luaopen_wh3_native_bridge")
    if not lok or type(loader)~="function" then error("DLL_LOAD "..clean(le or loader)) end
    local bok,module,be=pcall(loader)
    if not bok or type(module)~="table" then error("DLL_INIT "..clean(be or module)) end
    bridge=module
    for _,k in ipairs({"version","number_abi_probe","exact_id_probe","get_status","start_observer","begin_battle","end_battle",
        "get_unit_revision","arm_verified_issue","issue_verified_command","read_journal","acknowledge"}) do
        if type(bridge[k])~="function" then error("MISSING_BRIDGE_API "..k) end
    end
    if bridge.version()~="0.5.0-attack-native-token" then error("WRONG_BRIDGE_VERSION") end
    local n,f=bridge.number_abi_probe(); local a,c=bridge.exact_id_probe()
    if n~=16777215 or f~=1.5 or a~="4294967295" or c~="16777217" then error("BRIDGE_ABI_SELFTEST") end
    log("BRIDGE_OK version=0.5.0-attack-native-token")
    local scheduled=false
    local function schedule()
        if scheduled or S.started or S.failed or S.closed then return end
        scheduled=true; log("PHASE_CALLBACK Deployed")
        -- Reuse the runtime-validated start delay, not a UI-click bootstrap.
        bmgr:callback(checked(start),500)
    end
    bmgr:register_phase_change_callback("Deployed",checked(schedule))
    bmgr:register_phase_change_callback("VictoryCountdown",function() stop("VictoryCountdown") end)
    bmgr:register_phase_change_callback("Complete",function() stop("Complete") end)
    local phase=bmgr:get_current_phase_name()
    S.late_start=(phase=="Deployed")
    log("LOADED phase="..clean(phase).." run="..RUN_ID)
    if phase=="Deployed" then schedule() else log("WAITING_FOR_DEPLOYED") end
end
local ok,err=xpcall(boot,trace)
if not ok then fail(err) end
