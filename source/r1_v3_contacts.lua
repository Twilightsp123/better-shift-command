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
local function finite(n) return type(n)=='number' and n==n and n~=math.huge and n~=-math.huge end
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
