-- R1 Evidence V3 handoff primitives.
-- Pure Lua 5.1 data/lifecycle logic: no game API, no orders, no timing heuristics.
local H={VERSION="R1_V3_HANDOFF_1"}
local function id(s)
    return type(s)=="string" and #s>0 and #s<=10 and not s:find("[^0-9]")
        and (#s==1 or s:sub(1,1)~="0") and (#s<10 or s<="4294967295")
end
local function finite(n) return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge end
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
