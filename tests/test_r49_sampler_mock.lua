-- Lua 5.3 mock of the memreader Plus 0.13.0 API contract. Does NOT load a DLL/game.
local SRC=arg[1]
assert(SRC, 'pass Lua research sampler path as first arg')
local original_type=type
local BASE=0x140000000
local TICK=BASE+0x03086f04
local GATE=BASE+0x03087378
local MEMBER_VT=BASE+0x03912950
local UNKNOWN_VT=BASE+0x03ac5c40
local ACTION=BASE+0x03919b28
local TICK_BYTES=string.char(0x48,0x8b,0xc4,0x48,0x89,0x58,0x10)
local GATE_BYTES=string.char(0x44,0x38,0xbf,0xf8,0x06,0,0,0x75,0x09,
                             0x44,0x38,0xbf,0,0x06,0,0,0x75,0x5c)
local function ptr(x)
 return setmetatable({address=x},{__add=function() error('typed pointer arithmetic forbidden') end,
                                __sub=function() error('typed pointer arithmetic forbidden') end})
end
local function address(x)
 if x==nil or x==false then return 0 end
 assert(original_type(x)=='table' and x.address,'expected typed pointer')
 return x.address
end
local function hex(p) return string.format('%016X',address(p)) end
local function fresh()
 local x={stamp='6acec6f4',hook=nil,live_bad=false,restore_bad=false,roster={0xB100,0xB200},
          elapsed=0,cost=4,roster_change_during=false,positions_bad=false,
          count_bad=false,member_action_flip=false,actor_class=MEMBER_VT,
          invalid_vt=false,missing_api=nil}
 local u={__battle_unit_userdata=true, number_of_men_alive=function() return x.count_bad and 1 or #x.roster end}
 local mem={base=ptr(BASE),plus_version='0.13.0'}
 local function tickcost() x.elapsed=x.elapsed+x.cost end
 function mem.tostring(p) return hex(p) end
 function mem.is_null(p) return not p or p==false or address(p)==0 end
 function mem.eq(a,b) return address(a)==address(b) end
 function mem.add(p,n)
  assert(original_type(n)=='number' and n==math.floor(n))
  return ptr(address(p)+n)
 end
 function mem.ud_topointer(v) assert(v==u); tickcost(); return ptr(0xAAA0) end
 function mem.read_uint16(p,off)
  tickcost()
  if address(p)==BASE then
   if off==0x3c then return 0x80 end
   if off==0x3e then return 0 end
   if off==0x80+0x18 then return 0x20B end
   if off==0x80+8 then return x.stamp=='6acec6f4' and 0xc6f4 or 0xbad0 end
   if off==0x80+10 then return x.stamp=='6acec6f4' and 0x6ace or 0x8888 end
   if off==0x80+0x50 then return 0x9000 end
   if off==0x80+0x52 then return 0xe02 end
  end
  error('unexpected uint16 '..hex(p)..'+'..off)
 end
 function mem.read(p,off,n)
  tickcost()
  if address(p)==BASE and off==0x80 and n==4 then return 'PE\0\0' end
  if address(p)==TICK and off==0 and n==#TICK_BYTES then
   return x.live_bad and ('\x90'..TICK_BYTES:sub(2)) or TICK_BYTES
  end
  if address(p)==GATE and off==0 and n==#GATE_BYTES then return GATE_BYTES end
  if address(p)==0xAAB0 and off==0 and n==#x.roster*8 then
   local r={}
   for _,a in ipairs(x.roster) do r[#r+1]=string.pack('<I8',a) end
   if x.roster_change_during then
    x.read_roster=(x.read_roster or 0)+1
    if x.read_roster==2 then r[2]=string.pack('<I8',0xB300) end
   end
   return table.concat(r)
  end
  error('unexpected read '..hex(p)..' '..off..' '..n)
 end
 function mem.read_original(p,off,n)
  tickcost()
  if address(p)==TICK then return x.restore_bad and ('\x90'..TICK_BYTES:sub(2)) or TICK_BYTES end
  if address(p)==GATE then return GATE_BYTES end
  error('unexpected read_original')
 end
 function mem.hook_info(p)
  tickcost()
  if address(p)==TICK then return x.hook and {kind=x.hook} or nil end
  return nil
 end
 function mem.read_pointer(p,off)
  tickcost()
  local a=address(p)
  if a==MEMBER_VT then
   if off==0x18 then return ptr(TICK) end
   if off==0x20 then return ptr(BASE+0x030592bc) end
  elseif a==0xAAA0 and off==8 then return ptr(0xAA10)
  elseif a==0xAA10 and off==0xa8 then return ptr(0xAAB0)
  elseif a==0xAAB0 and off%8==0 then return ptr(x.roster[1+off/8] or 0)
  elseif a==0xB100 or a==0xB200 or a==0xB300 then
   if off==0 then return ptr(x.invalid_vt and 0x5555 or (a==0xB200 and x.actor_class or MEMBER_VT)) end
   if off==0x330 then
    x.action_reads=(x.action_reads or 0)+1
    if x.member_action_flip and x.action_reads==2 then return ptr(0x15001230) end
    return ptr(ACTION)
   end
   if off==0x1f0 then return ptr(0) end
  end
  error('unexpected pointer read '..hex(p)..'+'..off)
 end
 function mem.read_int32(p,off)
  tickcost();local a=address(p)
  if a==0xAA10 and off==0xa4 then return #x.roster end
  if a==0xB100 or a==0xB200 or a==0xB300 then
   if off==0x324 then return 4 end
  end
  error('unexpected int32')
 end
 function mem.read_uint8(p,off)
  tickcost();local a=address(p)
  if a==0xB100 or a==0xB200 or a==0xB300 then
   if off==0x108 then return 2 end
   if off==0x155 then return 4 end
   if off==0x340 then return 1 end
  end
  error('unexpected uint8')
 end
 function mem.read_float(p,off)
  tickcost();local a=address(p)
  if a==0xB100 or a==0xB200 or a==0xB300 then
   if off==0x88 then return a==0xB100 and 0 or 1.2 end
   if off==0x8c then return 0 end
   if off==0x90 then return x.positions_bad and 0/0 or 3.0 end
   if off==0x1e0 then return 2 end
   if off==0x1e4 or off==0x1e8 then return 4 end
   if off==0x13c or off==0x140 or off==0x144 then return 0.2 end
   if off==0xe0 or off==0xe8 then return 0.5 end
  end
  error('unexpected float')
 end
 function mem.ticks() return {t0=x.elapsed} end
 function mem.elapsed_us(t) return x.elapsed-t.t0 end
 if x.missing_api then mem[x.missing_api]=nil end
 return x,u,mem
end
local env={}
setmetatable(env,{__index=_G})
env._G=env
env.memreader_plus_release='0_13_0'
env.type=function(v)
 if original_type(v)=='table' and v.__battle_unit_userdata then return 'userdata' end
 return original_type(v)
end
local chunk=assert(loadfile(SRC,'t',env))
local M=assert(chunk())
local PASS=0
local function run(name,fn)
 local ok,why=pcall(fn)
 if not ok then error('FAIL '..name..': '..tostring(why)) end
 print('PASS '..name)
 PASS=PASS+1
end
local function one(x,u,m,token,seq,t)
 env.memreader_plus=m
 return M.sample(u,{unit_token=token or 'one_unit',sample_id=seq or 0,time_ms=t or 0,max_rows=2})
end
run('genuine_mock_baseline_and_typed_pointer_math',function()
 M.reset();local x,u,m=fresh()
 local r,why=one(x,u,m)
 assert(r and not why,why);assert(r.sampled_count==2)
 assert(r.roster_bytes_checked==16 and r.intra_sample_full_roster_stable)
 assert(r.rows[1].action=='b2_general_action_vtable')
 assert(r.rows[1].member_type=='ordinary_exact_vtable')
 assert(r.rows[1].read_offset_us>0 and r.read_duration_us>0)
 assert(r.cross_snapshot_lifetime_proven==false and r.sample_type=='sequential-not-atomic')
end)
run('same_roster_retains_anonymized_id',function()
 M.reset();local x,u,m=fresh()
 local a=assert(one(x,u,m,'one',1,100))
 local b=assert(one(x,u,m,'one',2,130))
 assert(a.rows[1].member_id==b.rows[1].member_id and a.roster_epoch==b.roster_epoch)
end)
run('roster_change_resets_epoch_even_for_unsampled_member',function()
 M.reset();local x,u,m=fresh();x.roster={0xB100,0xB200,0xB300}
 local a=assert(one(x,u,m,'one',1,100))
 x.roster[2]=0xB400
 local b=assert(one(x,u,m,'one',2,130))
 assert(b.roster_epoch>a.roster_epoch)
 assert(b.rows[1].member_id~=a.rows[1].member_id)
end)
run('duplicate_roster_pointer_rejected_even_if_unsampled',function()
 M.reset();local x,u,m=fresh();x.roster={0xB100,0xB200,0xB200}
 local r,why=one(x,u,m)
 assert(not r and why=='duplicate_roster_pointer',why)
end)
run('inter_sample_gap_resets_epoch',function()
 M.reset();local x,u,m=fresh()
 local a=assert(one(x,u,m,'one',1,100))
 local b=assert(one(x,u,m,'one',2,500))
 assert(b.roster_epoch>a.roster_epoch)
end)
run('unknown_member_class_kept_as_position_only',function()
 M.reset();local x,u,m=fresh();x.actor_class=UNKNOWN_VT
 local r=assert(one(x,u,m))
 assert(r.sampled_count==2 and r.all_member_types_typed==false)
 assert(r.rows[2].member_type=='unknown_position_only')
 assert(r.rows[2].stored_goal_xz==nil)
end)
run('reject_unknown_member_class_outside_game_image',function()
 M.reset();local x,u,m=fresh();x.invalid_vt=true
 local r,why=one(x,u,m)
 assert(not r and why=='member_vtable_outside_exe',why)
end)
run('guard_detects_existing_derpy_cave',function()
 M.reset();local x,u,m=fresh();x.hook='cave'
 local r,why=one(x,u,m)
 assert(not r and why=='member_tick_hook_or_cave_present',why)
end)
run('guard_detects_live_only_code_change',function()
 M.reset();local x,u,m=fresh();x.live_bad=true
 local r,why=one(x,u,m)
 assert(not r and why=='member_tick_original_or_live_bytes_drift',why)
end)
run('guard_detects_wrong_pe_timestamp',function()
 M.reset();local x,u,m=fresh();x.stamp='00000000'
 local r,why=one(x,u,m)
 assert(not r and why=='game_build_mismatch',why)
end)
run('rejects_mid_sample_complete_roster_mutation',function()
 M.reset();local x,u,m=fresh();x.roster_change_during=true
 local r,why=one(x,u,m)
 assert(not r and why=='full_member_roster_changed_during_read',why)
end)
run('rejects_latency_overrun',function()
 M.reset();local x,u,m=fresh();x.cost=150
 local r,why=one(x,u,m)
 assert(not r and why=='sample_read_budget_exceeded',why)
end)
run('rejects_NaN_position',function()
 M.reset();local x,u,m=fresh();x.positions_bad=true
 local r,why=one(x,u,m)
 assert(not r and why=='invalid_member_position',why)
end)
run('rejects_action_flip_during_read',function()
 M.reset();local x,u,m=fresh();x.member_action_flip=true
 local r,why=one(x,u,m)
 assert(not r and why=='member_action_changed_mid_sample',why)
end)
run('rejects_monotonicity_violation',function()
 M.reset();local x,u,m=fresh();assert(one(x,u,m,'one',1,100))
 local r,why=one(x,u,m,'one',2,100)
 assert(not r and why=='non_monotonic_sample_clock',why)
end)
run('rejects_multiple_unit_tokens',function()
 M.reset();local x,u,m=fresh();assert(one(x,u,m,'one',1,100))
 local r,why=one(x,u,m,'two',2,120)
 assert(not r and why=='one_unit_per_session_call_reset_before_new_unit',why)
end)
run('read_error_fail_closed',function()
 M.reset();local x,u,m=fresh();m.read_float=function() error('inaccessible') end
 local r,why=one(x,u,m)
 assert(not r and why=='guarded_read_error',why)
end)
run('rejects_unavailable_DLL',function()
 M.reset();local x,u,m=fresh();env.memreader_plus=nil
 local r,why=M.sample(u,{unit_token='one',sample_id=0,time_ms=0})
 assert(not r and why=='memreader_plus_not_loaded',why)
end)
run('rejects_missing_native_timing_API',function()
 M.reset();local x,u,m=fresh();m.elapsed_us=nil
 local r,why=one(x,u,m)
 assert(not r and why=='missing_memreader_api_elapsed_us',why)
end)
run('rejects_no_manual_identity',function()
 M.reset();local x,u,m=fresh();env.memreader_plus=m
 local r,why=M.sample(u,{sample_id=0,time_ms=0})
 assert(not r and why=='invalid_anonymous_unit_token',why)
end)
print(string.format('R49_LUA_MOCK_ALL_PASS=%d',PASS))
