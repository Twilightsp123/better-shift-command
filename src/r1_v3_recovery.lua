-- R1 V3 unified bounded recovery budget.
-- One budget is shared by every recovery command path for a single Exit action.
local R={VERSION="R1_V3_RECOVERY_1"}
local function finite(n) return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge end
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
