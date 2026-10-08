-- T2MOVE_D_EVIDENCE_OBSERVER_1
-- Pure deterministic evidence. No issue/adopt/commit/cursor authority.
local D={VERSION="T2MOVE_D_EVIDENCE_OBSERVER_1",authoritative=false}
local huge=math.huge or 1e300
local function finite(v)return type(v)=="number" and v==v and v<huge and v>-huge end
local function identity(v)return type(v)=="string" or (finite(v) and v>=0) end
local function encode(v)
 if type(v)=="string" then return "s"..#v..":"..v end
 if finite(v) then return "n"..string.format("%.17g",v) end
 if type(v)=="boolean" then return v and "b1" or "b0" end
 return nil
end
local function pack(items)
 local out={}
 for _,v in ipairs(items) do local s=encode(v);if not s then return nil end;out[#out+1]=#s..":"..s end
 return table.concat(out,"|")
end
local function copy_scalars(g)
 local out={}
 for k,v in pairs(g) do if type(k)=="string" and (type(v)=="string" or type(v)=="boolean" or finite(v)) then out[k]=v end end
 return out
end
local common={"remaining","leg","next_leg","progress","route_min_progress","threshold","stall","route_mode","route_debt_mode","arrival_brake_ready","arrival_sync_margin"}
local by_mode={PATH_SAFE={"cut_error","cut_safe_limit","cut_tolerance"},STEERING_CORNER={"corner_window","corner_window_base","corner_window_early"}}
D.REQUIRED_GEOMETRY=common;D.MODE_FIELDS=by_mode
function D.copy_move_geometry(g)
 if type(g)~="table" or not by_mode[g.route_mode] then return nil,"MOVE_ROUTE_MODE_NOT_PROVEN" end
 for _,key in ipairs(common) do if g[key]==nil then return nil,"MOVE_SNAPSHOT_MISSING_"..key end end
 for _,key in ipairs(by_mode[g.route_mode]) do if g[key]==nil then return nil,"MOVE_SNAPSHOT_MISSING_"..key end end
 for _,key in ipairs({"remaining","leg","next_leg","progress","route_min_progress","threshold","arrival_sync_margin"}) do
  if not finite(g[key]) then return nil,"MOVE_SNAPSHOT_INVALID_"..key end
 end
 for _,key in ipairs(by_mode[g.route_mode]) do if not finite(g[key]) then return nil,"MOVE_SNAPSHOT_INVALID_"..key end end
 if type(g.stall)~="boolean" or type(g.arrival_brake_ready)~="boolean" then return nil,"MOVE_SNAPSHOT_BOOLEAN_INVALID" end
 if g.route_debt_mode~="CLEAR" and g.route_debt_mode~="SOFT_PRESERVED" then return nil,"MOVE_SNAPSHOT_DEBT_NOT_PROVEN" end
 if g.route_debt_mode=="SOFT_PRESERVED" then
  for _,key in ipairs({"route_debt_count","route_debt_error","route_debt_limit"}) do
   if not finite(g[key]) then return nil,"MOVE_SNAPSHOT_MISSING_"..key end
  end
 end
 return copy_scalars(g),"OK"
end
function D.route_debt_signature(st,current)
 if type(st)~="table" or type(current)~="table" or not identity(current.action_id)
    or not identity(current.block_id) then return nil,"DEBT_OWNER_UNPROVEN" end
 local blocks=st.block_state
 if blocks~=nil and type(blocks)~="table" then return nil,"BLOCK_STATE_UNAVAILABLE" end
 local block=blocks and blocks[current.block_id] or nil
 if block~=nil and type(block)~="table" then return nil,"BLOCK_IDENTITY_INVALID" end
 if block and block.route_debts~=nil and type(block.route_debts)~="table" then return nil,"DEBT_MAP_INVALID" end
 local items={}
 local debt_map=block and block.route_debts or nil
 if debt_map then
  for key,debt in pairs(debt_map) do
   if not identity(key) or type(debt)~="table" or type(debt.action)~="table"
     or not identity(debt.action.action_id) or debt.action.action_id~=key
     or not identity(debt.action.block_id) or debt.action.block_id~=current.block_id
     or debt.action.type~="MOVE" or not finite(debt.tolerance)
     or debt.tolerance<0 or type(debt.action.pos)~="table"
     or not finite(debt.action.pos.x) or not finite(debt.action.pos.z) then
    return nil,"DEBT_RECORD_UNPROVEN"
   end
   local rt=debt.action.runtime
   local done=rt and rt.semantic_done==true or false
   local record=pack({key,debt.action.block_id,debt.action.action_id,
     debt.tolerance,debt.action.pos.x,debt.action.pos.z,done})
   if not record then return nil,"DEBT_RECORD_UNPROVEN" end
   items[#items+1]=record
  end
 end
 table.sort(items)
 local header=pack({current.block_id,current.action_id,current.block_kind or "NONE",
   block and block.id or current.block_id,block and block.kind or current.block_kind or "NONE",
   block and block.closed==true or false,#items})
 if not header then return nil,"DEBT_HEADER_UNPROVEN" end
 return header.."#"..table.concat(items,"#"),"OK"
end
function D.capture(f)
 if type(f)~="table" or f.exact_current_execution~=true or f.current_kind~="MOVE"
    or f.successor_kind~="MOVE" or f.successor_index~=f.current_index+1
    or not identity(f.gen) or not identity(f.revision) or not identity(f.unit_lifetime)
    or not identity(f.current_action_id) or not identity(f.successor_action_id)
    or not finite(f.now_ms) or not finite(f.poll_ms) or f.poll_ms<=0
    or not finite(f.current_index) or not identity(f.debt_signature) then
  return nil,"MOVE_CAPTURE_IDENTITY_INVALID"
 end
 local g,why=D.copy_move_geometry(f.geometry);if not g then return nil,why end
 local history=f.motion_samples
 if type(history)~="table" or #history<2 then return nil,"MOVE_CAPTURE_SAMPLES_MISSING" end
 local prev,cur=history[#history-1],history[#history]
 if type(prev)~="table" or type(cur)~="table" or not finite(prev.ms)
    or not finite(cur.ms) or not finite(prev.x) or not finite(prev.z)
    or not finite(cur.x) or not finite(cur.z) or cur.ms~=f.now_ms
    or cur.ms-prev.ms~=f.poll_ms then return nil,"MOVE_CAPTURE_SAMPLE_CLOCK_MISMATCH" end
 if not finite(f.waypoint_x) or not finite(f.waypoint_z) then return nil,"MOVE_CAPTURE_WAYPOINT_MISSING" end
 local function distance(x,z)local dx,dz=x-f.waypoint_x,z-f.waypoint_z;return math.sqrt(dx*dx+dz*dz) end
 local before=distance(prev.x,prev.z);local after=distance(cur.x,cur.z)
 if math.abs(after-g.remaining)>1e-7*math.max(1,after,g.remaining) then
  return nil,"MOVE_CAPTURE_GEOMETRY_NOT_CURRENT"
 end
 local dx,dz=cur.x-prev.x,cur.z-prev.z
 local evidence={previous_sample_ms=prev.ms,current_sample_ms=cur.ms,
   previous_remaining=before,current_remaining=after,ground_distance=math.sqrt(dx*dx+dz*dz)}
 return {version=D.VERSION,authoritative=false,gen=f.gen,revision=f.revision,
   current_action_id=f.current_action_id,successor_action_id=f.successor_action_id,
   current_index=f.current_index,successor_index=f.successor_index,
   unit_lifetime=f.unit_lifetime,sample_ms=f.now_ms,poll_ms=f.poll_ms,
   debt_signature=f.debt_signature,route_ok=f.route_ok==true,issue_open=f.issue_open==true,
   geometry=g,evidence=evidence},"OK"
end
function D.revalidate(c,f)
 if type(c)~="table" or type(f)~="table" then return false,"MOVE_D_EVIDENCE_MISSING" end
 for _,key in ipairs({"gen","revision","unit_lifetime","current_action_id","successor_action_id",
   "current_index","successor_index","debt_signature"}) do
  if c[key]~=f[key] then return false,"MOVE_D_REVALIDATE_"..key end
 end
 if f.exact_native_successor~=true or f.successor_index~=f.current_index+1 then
  return false,"MOVE_D_NATIVE_NOT_IMMEDIATE"
 end
 if not finite(f.now_ms) or not finite(f.observed_step_ms) or f.observed_step_ms<=0
    or f.now_ms<c.sample_ms or f.now_ms-c.sample_ms>f.observed_step_ms then
  return false,"MOVE_D_STALE_OBSERVATION"
 end
 return true,"OK"
end
return D
