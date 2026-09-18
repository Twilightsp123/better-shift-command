-- Executes the EXACT shipped controller in a CA-like fixture.
-- Host interpreter version is printed truthfully. The simulated game environment
-- advertises Lua 5.1; this is not execution in the WH3 process or proof of its ABI.
local actual_version=_VERSION
local path=assert(arg[1],"pass controller Lua path")
if arg[2]=="-" then arg[2]=nil end
local PASS,FAIL=0,0
local function check(v,msg) assert(v,msg or "assertion") end
local function test(name,fn)
 local ok,e=pcall(fn)
 if ok then PASS=PASS+1; print("PASS "..name) else FAIL=FAIL+1; print("FAIL "..name.." :: "..tostring(e)) end
end
local function plus(s)
 local a,carry={},1
 for i=#s,1,-1 do local n=s:byte(i)-48+carry; carry=n>=10 and 1 or 0; a[i]=string.char(48+n%10) end
 return (carry==1 and "1" or "")..table.concat(a)
end
local function valid(s) return type(s)=="string" and #s>0 and #s<=10 and not s:find("[^0-9]") and (#s==1 or s:sub(1,1)~="0") and (#s<10 or s<="4294967295") end
local function vec(x,y,z) return {get_x=function()return x end,get_y=function()return y end,get_z=function()return z end} end
local function F(options)
 local f={cfg=options or {},logs={},phase="Deployment",now=0,callbacks={},timers={},delay={},records={},
     revision={},native_by_uid={},pending_count=0,serial="0",issued=0,reads=0,acks=0,commands={},releases=0,recording=false,armed=false,read_sizes={}}
 f.serial=f.cfg.initial_serial or "0"
 function f:has(s) for _,v in ipairs(self.logs) do if v:find(s,1,true) then return true end end return false end
 function f:count(s) local n=0;for _,v in ipairs(self.logs) do if v:find(s,1,true) then n=n+1 end end return n end
 function f:emit(kind,queued,x,z,target,who,source,issue,status)
  who=who or "1001"; source=source or "UNKNOWN"; self.serial=plus(self.serial)
  status=status or "ACCEPTED"
  if status=="ACCEPTED" or status=="ACCEPTED_NO_SLOT" then self.revision[who]=plus(self.revision[who] or "0") end
  local r={epoch="1",serial=self.serial,command_id=self.serial,engine_seq_valid=status~="ACCEPTED_NO_SLOT",
    engine_seq=self.serial,unit_uid=who,unit_lifetime="1",unit_revision=self.revision[who] or "0",order_type=kind,
    is_queued=queued,source=source,script_issue_id=issue or "0",status=status,
    dest_x=x or 0,dest_y=0,dest_z=z or 0,target_uid=target or "2001"}
  if kind=="MOVE" then self.seen_move=true end
  if kind=="ATTACK" then self.seen_attack=true end
  self.records[#self.records+1]=r; return r
 end
 local function unit(u,x,z)
  local o={u=u,x=x,z=z}
  function o:unique_ui_id() return self.u end
  function o:position() if self.dead or self.position_error then error("unit gone") end;return vec(self.x,0,self.z) end
  function o:ordered_width() return f.cfg.width or 10 end
  if f.cfg.cold_idle then
   function o:is_idle() return self.idle~=false end
   function o:is_moving() return self.moving==true end
  end
  function o:starting_ammo() if f.cfg.missing_combat_api then error("missing combat api") end;return self.ammo or 0 end
  function o:is_currently_flying() return self.flying or false end
  function o:is_artillery() return self.artillery or false end
  function o:is_in_melee() if f.cfg.missing_combat_api then error("missing melee api") end;return self.melee or false end
  function o:current_target() if f.cfg.current_target_error then error("target api failed") end;return self.target end
  function o:unit_distance(target)
   if f.cfg.unit_distance_error then error("distance api failed") end
   local dx,dz=self.x-target.x,self.z-target.z;return math.sqrt(dx*dx+dz*dz)
  end
  function o:is_valid_target() return not self.dead and not self.hidden and not self.leaving end
  function o:number_of_men_alive() return self.dead and 0 or 60 end
  function o:is_leaving_battle() return self.leaving or false end
  function o:is_routing() return self.routing or false end
  return o
 end
 f.unit=unit("1001",0,0);f.unit2=unit("1002",0,0);f.enemy=unit("2001",200,200);f.other=unit("2002",400,400)
 local function uc(u)
  local o={}
  function o:goto_location(v,fast)
   if f.cfg.command_throw then error("command_failed") end
   check(f.in_callback,"no raw calibration commands permitted")
   f.draft={kind="MOVE",x=v:get_x(),z=v:get_z(),uid=u.u,fast=fast}
  end
  function o:attack_unit(target,primary,fast)
   check(f.in_callback,"no raw attack calibration")
   if f.cfg.command_throw then error("attack_failed") end
   f.draft={kind="ATTACK",target=target.u,uid=u.u,primary=primary,fast=fast}
  end
  function o:release_control() f.releases=f.releases+1 end
  return o
 end
 local locals={{unit=f.unit,uc=uc(f.unit)}}
 if f.cfg.two_units then locals[2]={unit=f.unit2,uc=uc(f.unit2)} end
 local enemies={{unit=f.enemy}}
 local reinforcement_groups={}
 local enemy_reinforcement_groups={}
 local function collection(list)
  return {count=function()return #list end,item=function(_,i)return list[i] end}
 end
 local function all_local_sunits()
  local out={};for _,su in ipairs(locals)do out[#out+1]=su end
  for _,g in ipairs(reinforcement_groups)do for _,su in ipairs(g)do out[#out+1]=su end end
  return out
 end
 local function find_su(bu)
  for _,su in ipairs(all_local_sunits())do if su.unit==bu then return su end end
  for _,su in ipairs(enemies)do if su.unit==bu then return su end end
  for _,g in ipairs(enemy_reinforcement_groups)do for _,su in ipairs(g)do if su.unit==bu then return su end end end
 end
 function f:add_reinforcement(u,x,z)
  local bu=unit(u or tostring(1002+#reinforcement_groups),x or 0,z or 0);local su={unit=bu,uc=uc(bu)}
  reinforcement_groups[#reinforcement_groups+1]={su};return bu,su
 end
 function f:add_late_local(u,x,z)
  local bu=unit(u or tostring(1100+#locals),x or 0,z or 0);local su={unit=bu,uc=uc(bu)};locals[#locals+1]=su;return bu,su
 end
 function f:add_enemy_reinforcement(u,x,z)
  local bu=unit(u or tostring(2100+#enemy_reinforcement_groups),x or 200,z or 200);local su={unit=bu}
  enemy_reinforcement_groups[#enemy_reinforcement_groups+1]={su};return bu,su
 end
 local player_army={units=function()local a={};for _,su in ipairs(all_local_sunits())do a[#a+1]=su.unit end;return collection(a)end}
 local bm={}
 function bm:get_current_phase_name() return f.phase end
 function bm:time_elapsed_ms() return f.now end
 function bm:register_phase_change_callback(p,cb) f.callbacks[p]=cb end
 function bm:callback(cb,ms) f.delay[#f.delay+1]=cb; check(ms==500,"validated startup delay") end
 function bm:repeat_real_callback(cb,ms,name) check(ms==100);f.timers[name]=cb;f.timer=cb end
 function bm:remove_real_callback(name) f.timers[name]=nil;f.timer=nil end
 function bm:get_scriptunits_for_local_players_army() if f.cfg.collection_error then error("collection_missing") end;return collection(locals) end
 function bm:get_scriptunits_for_main_enemy_army_to_local_player() return collection(enemies) end
 function bm:get_player_alliance_num() return 1 end
 function bm:get_non_player_alliance_num() return 2 end
 function bm:local_army() return 1 end
 function bm:num_armies_in_alliance(a) return a==1 and 1 or 1 end
 function bm:num_reinforcing_armies_for_army_in_alliance(a,army)
  if army~=1 then return 0 end
  return a==1 and #reinforcement_groups or #enemy_reinforcement_groups
 end
 function bm:get_scriptunits_for_army(a,army,ri)
  if army~=1 then return false end
  if a==1 then return ri and collection(reinforcement_groups[ri] or {}) or collection(locals) end
  if a==2 then return ri and collection(enemy_reinforcement_groups[ri] or {}) or collection(enemies) end
  return false
 end
 function bm:get_player_army() return player_army end
 function bm:get_scriptunit_for_unit(bu) return find_su(bu) end
 local B={}
 function B.version()return f.cfg.wrong_version and "0.1.1" or "1.0.15-r4-evidence-v3-validated-userdata-root" end

 local function mirror_v2_order_to_v3(e)
  if type(e)~="table" then return e end
  local o={} for k,v in pairs(e) do o[k]=v end
  o.schema=3
  return o
 end
 local function mirror_v2_entity_to_v3(e,now,u,ff)
  if type(e)~="table" or e.complete~=true then
   return {schema=3,complete=false,probe_reason=type(e)=="table" and (e.probe_reason or "SYNTHETIC_ENTITY_UNAVAILABLE") or "SYNTHETIC_ENTITY_UNAVAILABLE",model_ms=now,entities={},live_count=0}
  end
  local n=math.max(0,math.floor(e.live_count or 0));local path=math.max(0,math.min(n,math.floor(e.movement_pathing_count or 0)))
  local idle=math.max(0,math.min(n-path,math.floor(e.movement_idle_count or 0)));local ents={}
  local vx,vz=e.median_vx or 0,e.median_vz or 0
  if path>0 and math.abs(vx)+math.abs(vz)<0.0001 and ff and ff.evidence_record and ff.evidence_record.order_type=='MOVE' then
   local dx=(ff.evidence_record.dest_x or 0)-(e.median_x or 0);local dz=(ff.evidence_record.dest_z or 0)-(e.median_z or 0);local l=math.sqrt(dx*dx+dz*dz)
   if l>0.001 then vx=dx/l;vz=dz/l end
  end
  for i=1,n do
   local state=(i<=path) and 1 or ((i<=path+idle) and 0 or 2)
   local ent={entity=tostring(u).."_v2_"..tostring(i),x=(e.median_x or 0)+(i-1)*0.001,z=e.median_z or 0,movement_state=state,motion_complete=e.motion_complete==true}
   if ent.motion_complete then ent.vx=(state==1) and vx or 0;ent.vz=(state==1) and vz or 0 end
   ents[#ents+1]=ent
  end
  return {schema=3,complete=true,probe_reason="MIRRORED_V2_FIXTURE",model_ms=e.model_ms or now,slot_count=e.slot_count or n,live_count=n,dead_count=e.dead_count or 0,
   movement_idle_count=e.movement_idle_count or idle,movement_pathing_count=e.movement_pathing_count or path,movement_halted_count=e.movement_halted_count or math.max(0,n-path-idle),
   median_x=e.median_x or 0,median_z=e.median_z or 0,motion_complete=e.motion_complete==true,motion_matched_count=e.motion_matched_count or (e.motion_complete and n or 0),
   previous_model_ms=e.previous_model_ms,median_vx=e.median_vx,median_vz=e.median_vz,entities=ents}
 end
 local function mirror_v2_combat_to_v3(e)
  if type(e)~="table" then return {schema=3,complete=false,probe_reason="SYNTHETIC_COMBAT_UNAVAILABLE"} end
  local o={} for k,v in pairs(e) do o[k]=v end;o.schema=3;return o
 end
 function B.r1_evidence_capabilities_v3()
  local enabled=f.cfg.native_evidence_v3==true or f.cfg.native_evidence_v2==true
   or type(f.cfg.native_order_evidence_v3)=="function" or type(f.cfg.native_entity_evidence_v3)=="function" or type(f.cfg.native_contact_events_v3)=="function"
   or type(f.cfg.native_order_evidence)=="function" or type(f.cfg.native_entity_evidence)=="function" or type(f.cfg.native_combat_evidence)=="function"
  if enabled then return {schema=3,game_build_verified=true,execution_identity=true,entity_snapshot=true,combat_groups=true,contact_pairs=type(f.cfg.native_contact_events_v3)=="function",target_specific_physical_contact=type(f.cfg.native_contact_events_v3)=="function",build_id="SYNTHETIC_V3_TEST_ONLY"} end
  return {schema=3,game_build_verified=false,execution_identity=false,entity_snapshot=false,combat_groups=false,contact_pairs=false,target_specific_physical_contact=false,build_id="TEST_UNAVAILABLE"}
 end
 function B.bind_evidence_unit_v3(u,unit) return true,"900000" end
 function B.read_active_order_identity_v3(u)
  if type(f.cfg.native_order_evidence_v3)=="function" then return f.cfg.native_order_evidence_v3(f,u) end
  if type(f.cfg.native_order_evidence)=="function" then return mirror_v2_order_to_v3(f.cfg.native_order_evidence(f,u)) end
  return nil,"ORDER_IDENTITY_UNAVAILABLE"
 end
 function B.read_entity_snapshot_v3(u,now)
  if type(f.cfg.native_entity_evidence_v3)=="function" then return f.cfg.native_entity_evidence_v3(f,u,now) end
  if type(f.cfg.native_entity_evidence)=="function" then return mirror_v2_entity_to_v3(f.cfg.native_entity_evidence(f,u,now),now,u,f) end
  return {schema=3,complete=false,probe_reason="SYNTHETIC_ENTITY_UNAVAILABLE",model_ms=now,entities={},live_count=0},nil
 end
 function B.read_combat_groups_v3(u)
  if type(f.cfg.native_combat_evidence_v3)=="function" then return f.cfg.native_combat_evidence_v3(f,u) end
  if type(f.cfg.native_combat_evidence)=="function" then return mirror_v2_combat_to_v3(f.cfg.native_combat_evidence(f,u)) end
  return {schema=3,complete=false,probe_reason="SYNTHETIC_COMBAT_UNAVAILABLE"},nil
 end
 function B.read_contact_events_v3(after,count)
  if type(f.cfg.native_contact_events_v3)=="function" then return f.cfg.native_contact_events_v3(f,after,count) end
  return {},{schema=3,next_after=after,newest=after,oldest="0",dropped="0",read_tick_ms=tostring(math.floor(f.now)),gap=false,complete=true,count=0}
 end
 function B.contact_owner_ready_v3(u)
  if type(f.cfg.contact_owner_ready_v3)=="function" then return f.cfg.contact_owner_ready_v3(f,u) end
  if type(f.cfg.contact_owner_missing)=="table" and f.cfg.contact_owner_missing[u] then return false end
  return true
 end
 function B.r1_evidence_capabilities_v2()
  local enabled=f.cfg.native_evidence_v2==true or type(f.cfg.native_order_evidence)=="function" or type(f.cfg.native_entity_evidence)=="function" or type(f.cfg.native_combat_evidence)=="function"
  if enabled then return {schema=2,game_build_verified=true,execution_identity=true,entity_snapshot=true,combat_groups=true,fresh_engagement=true,build_id="SYNTHETIC_TEST_ONLY"} end
  return {schema=2,game_build_verified=false,execution_identity=false,entity_snapshot=false,combat_groups=false,fresh_engagement=false,build_id="TEST_UNAVAILABLE"}
 end
 function B.bind_evidence_unit_v2(u,unit) return true,"900000" end
 function B.read_active_order_identity_v2(u)
  if type(f.cfg.native_order_evidence)=="function" then return f.cfg.native_order_evidence(f,u) end
  return nil,"ORDER_IDENTITY_UNAVAILABLE"
 end
 function B.read_entity_snapshot_v2(u,now)
  if type(f.cfg.native_entity_evidence)=="function" then return f.cfg.native_entity_evidence(f,u,now) end
  return {schema=2,complete=false,probe_reason="SYNTHETIC_ENTITY_UNAVAILABLE",model_ms=now},nil
 end
 function B.read_combat_groups_v2(u)
  if type(f.cfg.native_combat_evidence)=="function" then return f.cfg.native_combat_evidence(f,u) end
  return {schema=2,complete=false,probe_reason="SYNTHETIC_COMBAT_UNAVAILABLE"},nil
 end
 function B.number_abi_probe()return 16777215,1.5 end
 function B.exact_id_probe()return "4294967295","16777217" end
 function B.start_observer(ack)check(ack==true);if f.cfg.observer_fail then return false,"TEST_FAIL" end;return true end
 function B.begin_battle(s)
  check(type(s)=="string" and #s<=64)
  if f.cfg.begin_nil then return nil,"BEGIN_DENIED" end
  f.recording=true;return "1"
 end
 function B.end_battle(e)check(e=="1");f.recording=false;return true end
 function B.get_status()
  local ready=((f.seen_move or f.seen_attack) and not f.cfg.no_calibration) or false
  return {epoch="1",recording=f.recording,capture_errors=f.cfg.capture_errors or "0",fatal_errors=f.cfg.fatal_errors or "0",gate_fault=f.cfg.gate_fault or "OK",
    last_recoverable_uid=f.cfg.last_recoverable_uid or "0",last_recoverable_error=f.cfg.last_recoverable_error or "NONE",last_fatal_error=f.cfg.last_fatal_error or "NONE",
    native_issue_authorized=true,v3_issue_calibration_ready=ready,v3_issue_armed=f.armed,
    experimental_calibration_ready=ready,experimental_issue_armed=f.armed,
    accepted_move_seen=f.seen_move==true,accepted_attack_seen=f.seen_attack==true,exact_source=false,verified_issue=true}
 end
 function B.arm_verified_issue(a) f.armed=a;if a then check(f.seen_move or f.seen_attack) end;return true end
 function B.get_unit_revision(u)
  check(valid(u),"revision MUST receive uid string")
  if f.cfg.revision_race then f.revision[u]=plus(f.revision[u]);f.cfg.revision_race=false end
  if f.cfg.revision_error then return nil,"OTHER_ERROR" end
  if f.cfg.native_missing and not f.revision[u] then return nil,"MISSING" end
  return f.revision[u] or "0"
 end
 function B.read_journal(epoch,cursor,count)
  f.reads=f.reads+1;f.read_sizes[#f.read_sizes+1]=count
  if f.on_read then f.on_read(f, f.reads) end
  check(epoch=="1" and valid(cursor));check(count>=1 and count<=64 and count==math.floor(count),"COUNT_RANGE_1_TO_64")
  if f.cfg.journal_nil then return nil,"READ_DENIED" end
  local rows={};local started=cursor=="0"
  for _,r in ipairs(f.records) do
   if started and #rows<count then rows[#rows+1]=r end
   if r.serial==cursor then started=true end
  end
  local next_after=#rows>0 and rows[#rows].serial or cursor
  local m={epoch="1",next_after=next_after,newest_serial=f.serial,oldest_serial="0",dropped="0",
    gap=f.cfg.gap or false,overrun=f.cfg.overrun or false,complete=not f.cfg.gap,
    count=#rows,error=f.cfg.gap and "Overrun" or "Ok",journal_fault=f.cfg.journal_fault or "Ok"}
  if f.cfg.bad_epoch then m.epoch="2" end
  if f.cfg.bad_cursor then m.next_after="9999" end
  if f.cfg.bad_page_tail and #rows>=2 then rows[#rows].serial="bad" end
  f.delivered=next_after
  return rows,m
 end
 function B.acknowledge(e,c)
  check(e=="1" and valid(c) and c==f.delivered,"ack must equal validated page cursor")
  if f.cfg.ack_fail then return nil,"ACK_DENIED" end
  f.acks=f.acks+1;f.ack=c;return true
 end
 function B.cancel_pending_issue(issue)
  check(valid(issue),"issue id must be exact decimal string")
  local found=nil
  for uid,p in pairs(f.native_by_uid) do if p.issue==issue then found=p;f.native_by_uid[uid]=nil;break end end
  if not found then return nil,"MISSING" end
  f.pending_count=math.max(0,f.pending_count-1);found.cancelled=true
  if f.native_pending==found then
   f.native_pending=nil
   for _,cmd in ipairs(f.commands)do if not cmd.delivered and not cmd.cancelled then f.native_pending=cmd;break end end
  end
  return true
 end
 function B.issue_verified_command(kind,q,u,rev,cb,dx,dy,dz)
  check(kind=="MOVE" or kind=="ATTACK");check(q==false);check(valid(u) and valid(rev));check(type(cb)=="function")
  check(f.armed and not f.native_by_uid[u],"one pending per recipient")
  check(f.pending_count<32,"bounded thirty-two pending")
  if kind=="MOVE" then check(type(dx)=="number" and type(dy)=="number" and type(dz)=="number","Move fallback guard coordinates") end
  if f.cfg.gate_race then f.revision[u]=plus(f.revision[u]);f.cfg.gate_race=false end
  if rev~=f.revision[u] then return nil,"REJECTED_STALE" end
  f.draft=nil;f.in_callback=true
  if f.cfg.poll_reentry then f.timer() end
  local ok,e=pcall(cb);f.in_callback=false
  if not ok then return nil,"LUA_CALLBACK_FAILED" end
  check(f.draft,"one publish expected");check(f.draft.uid==u)
  f.issued=f.issued+1;local issue=tostring(f.issued)
  local p={draft=f.draft,rev=rev,issue=issue,started=f.now}
  f.native_by_uid[u]=p;f.pending_count=f.pending_count+1
  f.native_pending=f.native_pending or p;f.commands[#f.commands+1]=p
  return issue,"PENDING_NATIVE_ACCEPTANCE"
 end
 function f:deliver(who)
  local p=who and self.native_by_uid[who] or self.native_pending
  if not p then return end
  self.native_by_uid[p.draft.uid]=nil;self.pending_count=self.pending_count-1
  p.delivered=true;self.native_pending=nil
  for _,cmd in ipairs(self.commands)do if not cmd.delivered then self.native_pending=cmd;break end end
  local d=p.draft;local result=self.cfg.reject_native and "NATIVE_REJECTED" or "ACCEPTED"
  if self.revision[d.uid]~=p.rev then result="REJECTED_STALE" end
  if self.cfg.no_slot then result="ACCEPTED_NO_SLOT" end
  local r=self:emit(d.kind,false,d.x,d.z,d.target,d.uid,"OUR_CONTROLLER",p.issue,result)
  if result=="ACCEPTED" then self.evidence_record=r end
  if self.cfg.wrong_own_issue then r.script_issue_id="999" end
  if self.cfg.wrong_own_target then r.target_uid="2999" end
  if self.cfg.wrong_own_revision then r.unit_revision="999" end
  if self.cfg.wrong_move_payload then r.dest_x=r.dest_x+5 end
 end
 local env={unpack=unpack or table.unpack,_VERSION="Lua 5.1",_G={},package={loadlib=function()return function()return B end end}}
 env.out=setmetatable({}, {__call=function(_,s) f.logs[#f.logs+1]="<"..f.now.."ms> "..s end})
 env.print=function()error("stdout fallback forbidden")end
 env.v_offset=function(v,x,y,z) return vec(v:get_x()+x,v:get_y()+y,v:get_z()+z) end
 setmetatable(env,{__index=function(_,k)if k=="bm" then return f.cfg.no_bm and nil or bm end;return _G[k] end})
 if f.cfg.no_bm then setmetatable(env,{__index=function(_,k)if k=="bm" then return nil end;return _G[k] end}) end
 if f.cfg.no_vector then env.v_offset=false end
 f.phase=f.cfg.late_load and "Deployed" or f.phase
 local chunk
 local actual_path=f.cfg.controller_path or path
 if true then
  local h=assert(io.open(actual_path,"rb"));local source=h:read("*a");h:close()
  -- Production source defaults telemetry off. Synthetic tests turn it on unless a case explicitly disables it.
  if f.cfg.disable_debug then
   source=source:gsub("local DEBUG_TELEMETRY = true","local DEBUG_TELEMETRY = false",1)
  else
   source=source:gsub("local DEBUG_TELEMETRY = false","local DEBUG_TELEMETRY = true",1)
  end
  if f.cfg.profile then
   local n;source,n=source:gsub('local TEST_PROFILE = "ROUTE_ONLY"', 'local TEST_PROFILE = "'..f.cfg.profile..'"')
   check(n==1,"installer profile substitution")
  end
  if f.cfg.controller_phase then
   local n;source,n=source:gsub('local CONTROLLER_PHASE = "P2B"','local CONTROLLER_PHASE = "'..f.cfg.controller_phase..'"')
   check(n==1,"phase substitution")
  end
  if actual_version=="Lua 5.1" then chunk=assert(loadstring(source,"@"..actual_path));setfenv(chunk,env)
  else chunk=assert(load(source,"@"..actual_path,"t",env)) end
 elseif actual_version=="Lua 5.1" then chunk=assert(loadfile(actual_path));setfenv(chunk,env)
 else chunk=assert(loadfile(actual_path,"t",env)) end
 chunk()
 function f:start()
  self.phase="Deployed";if self.callbacks.Deployed then self.callbacks.Deployed() end
  local delays=self.delay;self.delay={};for _,fn in ipairs(delays)do fn()end
 end
 function f:tick(t,x,z)
  self.now=t;if x then self.unit.x=x;self.unit.z=z end
  if self.timer then self.timer() end
 end
 function f:route(who)
  self:emit("MOVE",false,100,0,nil,who)
  self:emit("MOVE",true,100,100,nil,who)
  self:emit("ATTACK",true,nil,nil,"2001",who)
 end
 return f
end

return {new=F,vec=vec,valid=valid,plus=plus}
