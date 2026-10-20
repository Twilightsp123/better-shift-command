-- BSC R50 research-only: a monotonic clock adapter for the *canonical* R49 sampler.
-- This DOES NOT load a MOD, call native functions, write memory or register callbacks.
-- Import explicitly and invoke once only when permitted/safe. NOT game tested.
local M = {}
local epoch=nil
local last_ms=nil
local sequence=0
local MAX_CLOCK_MS=16777215 -- CA Lua 24-bit integer precision safety bound
local function valid_number(v)
  return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge and v>=0
end
function M.capture(sampler,unit,opts)
  if type(sampler)~='table' or type(sampler.sample)~='function' then
    return nil,'canonical_sampler_module_required'
  end
  if type(opts)~='table' then return nil,'options_table_required' end
  if opts.sample_id~=nil or opts.time_ms~=nil then
    return nil,'caller_supplied_sample_clock_forbidden'
  end
  local mr=rawget(_G,'memreader_plus')
  if not mr or _G.memreader_plus_release~='0_13_0' or
     type(mr.ticks)~='function' or type(mr.elapsed_us)~='function' then
    return nil,'memreader_plus_monotonic_api_unavailable'
  end
  if sequence>=16777215 then return nil,'sample_sequence_overflow' end
  -- Epoch is a typed tick object; do not subtract or convert it in plain Lua.
  local start=epoch or mr.ticks()
  local ok,elapsed=pcall(mr.elapsed_us,start)
  if not ok or not valid_number(elapsed) then return nil,'invalid_monotonic_tick' end
  local ms=math.floor(elapsed/1000)
  if ms>MAX_CLOCK_MS then return nil,'sampler_clock_budget_exceeded' end
  if last_ms and ms<=last_ms then return nil,'sample_less_than_one_millisecond_since_previous' end
  local request={
    unit_token=opts.unit_token,
    sample_id=sequence+1,
    time_ms=ms,
    max_rows=opts.max_rows,
    start_index=opts.start_index,
    mode=opts.mode,
  }
  local success,result,problem=pcall(sampler.sample,unit,request)
  if not success then return nil,'guarded_sampler_exception' end
  if not result then return nil,problem or 'sampler_failed' end
  -- Fail closed on a fake/corrupted sampler. Canonical R49 must return the
  -- requested sample ID and timestamp and keep its non-atomic caveat.
  if result.sample_id~=request.sample_id or result.time_ms~=ms or
     result.sample_type~='sequential-not-atomic' or
     result.native_patch_authorized~=false then
    return nil,'sampler_timestamp_contract_drift'
  end
  if not epoch then epoch=start end
  sequence=sequence+1
  last_ms=ms
  result.capture_clock_source='memreader_plus_elapsed_us_since_session_start'
  return result
end
function M.reset(sampler)
  if type(sampler)~='table' or type(sampler.reset)~='function' then
    return nil,'canonical_sampler_reset_required'
  end
  local ok,result=pcall(sampler.reset)
  if not ok or result~=true then return nil,'canonical_sampler_reset_failed' end
  epoch=nil;last_ms=nil;sequence=0
  return true
end
return M
