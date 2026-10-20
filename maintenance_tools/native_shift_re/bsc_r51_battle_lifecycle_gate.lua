-- BSC R51 RESEARCH-ONLY. DO NOT AUTOLOAD, PACKAGE AS GAMEPLAY MOD OR CALL IN AN ACTIVE GAME.
-- Script phase/model-time checks are NOT a worker-thread synchronization barrier.
-- The only battle callbacks installed here change Lua-local flags. They never read memory.
-- An explicitly opted-in direct capture is still UNSAFE for real WH3 use pending native lifetime proof.
local M = {}
local session_registered = false
local MAX_ATTEMPTS = 3
local function finite_nonnegative(v)
  return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge and v>=0
end
local function call_method(obj,name)
  if type(obj[name])~='function' then return nil,'battle_method_unavailable' end
  local ok,value=pcall(obj[name],obj)
  if not ok then return nil,'battle_method_error' end
  return value
end
local function phase(bm)
  local p,why=call_method(bm,'get_current_phase_name')
  if type(p)~='string' then return nil,why or 'battle_phase_unknown' end
  return p
end
local function restrictions(bm)
  local multiplayer,e1=call_method(bm,'is_multiplayer')
  if type(multiplayer)~='boolean' then return nil,e1 or 'multiplayer_status_unknown' end
  local replay,e2=call_method(bm,'is_replay')
  if type(replay)~='boolean' then return nil,e2 or 'replay_status_unknown' end
  if multiplayer or replay then return nil,'multiplayer_or_replay_unsupported' end
  return true
end
local function model_time(bm)
  local time,why=call_method(bm,'time_elapsed_ms')
  if not finite_nonnegative(time) then return nil,why or 'model_clock_unreliable' end
  return time
end
local function validates_snapshot(result)
  return type(result)=='table' and result.sample_type=='sequential-not-atomic' and
    result.native_patch_authorized==false and result.capture_clock_source==
      'memreader_plus_elapsed_us_since_session_start' and
    result.intra_sample_full_roster_stable==true and result.inventory_stable==true and
    result.cross_snapshot_lifetime_proven==false and
    type(result.rows)=='table' and finite_nonnegative(result.read_duration_us) and
    result.read_duration_us<=5000 and result.roster_epoch~=nil
end
function M.new(bm, clock_adapter, canonical_sampler)
  if session_registered then return nil,'one_lifecycle_session_per_lua_runtime' end
  if type(bm)~='table' then return nil,'battle_manager_required' end
  if type(bm.register_phase_change_callback)~='function' then
    return nil,'phase_change_callback_unavailable'
  end
  if type(clock_adapter)~='table' or type(clock_adapter.capture)~='function' then
    return nil,'monotonic_clock_adapter_required'
  end
  if type(canonical_sampler)~='table' or type(canonical_sampler.sample)~='function' then
    return nil,'canonical_r49_sampler_required'
  end
  local allowed,reason=restrictions(bm)
  if not allowed then return nil,reason end
  local current,why=phase(bm)
  if not current then return nil,why end
  if current=='Complete' or current=='VictoryCountdown' then
    return nil,'battle_already_finishing'
  end
  local controller={bm=bm,clock=clock_adapter,sampler=canonical_sampler,
                    attempts=0,successful=0,dead=false,last_known_phase=current}
  local function change(p)
    if controller.dead then return end
    controller.last_known_phase=p
    if p=='VictoryCountdown' or p=='Complete' then controller.dead=true end
  end
  -- Registration is control-plane only. NO memory sampling in any callback.
  for _,target in ipairs({'Deployed','VictoryCountdown','Complete'}) do
    local p=target
    local ok=pcall(bm.register_phase_change_callback,bm,p,function() change(p) end)
    if not ok then
      controller.dead=true
      return nil,'phase_callback_registration_failed'
    end
  end
  session_registered=true
  function controller:preflight()
    if self.dead then return nil,'battle_closed_or_disabled' end
    local legal,e=restrictions(self.bm)
    if not legal then return nil,e end
    local now,x=phase(self.bm)
    if not now then return nil,x end
    if now=='VictoryCountdown' or now=='Complete' then
      self.dead=true; return nil,'battle_closed_or_disabled'
    end
    if now~='Deployed' then return nil,'active_combat_phase_required' end
    local tick,t=model_time(self.bm)
    if tick==nil then return nil,t end
    return {phase=now,model_time_ms=tick,worker_threads_quiescent_proven=false,
            capture_permitted_by_phase=true, safe_for_live_game=false,
            purpose='research_only_unsynchronized_script_thread'}
  end
  function controller:capture_once(unit,opts)
    if type(opts)~='table' then return nil,'options_table_required' end
    -- Research opt-in is NOT permission to deploy the code in a game: work-thread
    -- pointer lifetime still needs a native proof. It exists for mock testing.
    if opts.experimental_unsynchronized_capture~=true then
      return nil,'explicit_experimental_opt_in_required'
    end
    if opts.sample_id~=nil or opts.time_ms~=nil then
      return nil,'caller_supplied_sample_clock_forbidden'
    end
    local before,err=self:preflight()
    if not before then return nil,err end
    if self.attempts>=MAX_ATTEMPTS then return nil,'session_capture_budget_exceeded' end
    self.attempts=self.attempts+1 -- count even failures; no continuous polling
    local request={unit_token=opts.unit_token,max_rows=opts.max_rows,
                   mode=opts.mode,start_index=opts.start_index}
    local ok,result,problem=pcall(self.clock.capture,self.sampler,unit,request)
    if not ok then return nil,'monotonic_capture_callback_error' end
    local after,finisherr=self:preflight()
    if not after then return nil,'post_capture_'..finisherr end
    if before.phase~=after.phase or before.model_time_ms~=after.model_time_ms then
      return nil,'capture_crossed_model_time_or_phase'
    end
    if not result then
      -- Never forward unknown nested exceptions: they may contain native pointers.
      return nil,'lower_sampler_rejected'
    end
    if not validates_snapshot(result) then return nil,'lower_sampler_contract_drift' end
    self.successful=self.successful+1
    result.battle_phase=before.phase
    result.model_time_ms=before.model_time_ms
    result.capture_window_grade='SCRIPT_UI_CALLBACK_OR_MANUAL_SEQUENTIAL_ONLY'
    result.model_clock_unchanged_during_capture=true
    result.engine_atomic_snapshot_proven=false
    result.worker_thread_quiescence_proven=false
    result.cannot_prove_no_memory_lifetime_race=true
    result.gameplay_patch_authorized=false
    return result
  end
  function controller:disable()
    self.dead=true
    return true
  end
  return controller
end
return M