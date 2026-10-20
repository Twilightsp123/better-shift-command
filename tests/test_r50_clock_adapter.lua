-- Direct Lua execution with a fully synthetic memreader clock and sampler.
local src=assert(arg[1]);local M=assert(loadfile(src))()
local now=0
_G.memreader_plus_release='0_13_0'
_G.memreader_plus={ticks=function()return {initial=now} end,
   elapsed_us=function(epoch)return now-epoch.initial end}
local calls={}
local canon={}
function canon.sample(unit,opts)
  calls[#calls+1]=opts
  return {sample_id=opts.sample_id,time_ms=opts.time_ms,
          sample_type='sequential-not-atomic',native_patch_authorized=false,
          inventory_stable=true,rows={}}
end
function canon.reset() return true end
local n=0
local function t(name,fn)
  local ok,e=pcall(fn)
  if not ok then error('FAILED '..name..': '..tostring(e)) end
  n=n+1;print('PASS '..name)
end
local function capture(extra)
  local o={unit_token='test',max_rows=2};if extra then for k,v in pairs(extra) do o[k]=v end end
  return M.capture(canon,{},o)
end
t('initial time comes from memreader not caller',function()
  local r=assert(capture())
  assert(r.time_ms==0 and r.sample_id==1 and #calls==1)
  assert(r.capture_clock_source=='memreader_plus_elapsed_us_since_session_start')
end)
t('monotonic sub-ms sample is rejected',function()
  now=700;local r,e=capture()
  assert(not r and e=='sample_less_than_one_millisecond_since_previous')
end)
t('one full ms interval succeeds',function()
  now=1250;local r=assert(capture())
  assert(r.time_ms==1 and r.sample_id==2)
end)
t('long gap is not hidden by fake timestamp',function()
  now=660000;local r=assert(capture())
  assert(r.time_ms==660 and r.sample_id==3)
end)
t('caller cannot forge time',function()
  now=880000;local r,e=capture({time_ms=4})
  assert(not r and e=='caller_supplied_sample_clock_forbidden')
end)
t('caller cannot forge sample id',function()
  local r,e=capture({sample_id=300})
  assert(not r and e=='caller_supplied_sample_clock_forbidden')
end)
t('failed sampler does not advance sequence',function()
  now=900000;local save=canon.sample
  canon.sample=function()return nil,'temporary_sampling_failure' end
  local r,e=capture();assert(not r and e=='temporary_sampling_failure')
  canon.sample=save
  r=assert(capture());assert(r.sample_id==4)
end)
t('corrupted sampler clock rejected',function()
  now=905000;local orig=canon.sample
  canon.sample=function(unit,o)
    local r=orig(unit,o);r.time_ms=o.time_ms+1;return r
  end
  local r,e=capture()
  assert(not r and e=='sampler_timestamp_contract_drift')
  canon.sample=orig
end)
t('reset synchronizes both modules',function()
  assert(M.reset(canon));now=1000000
  local r=assert(capture());assert(r.sample_id==1 and r.time_ms==0)
end)
t('clock unavailable fail closed',function()
  _G.memreader_plus.elapsed_us=nil
  local r,e=capture();assert(not r and e=='memreader_plus_monotonic_api_unavailable')
end)
print('R50_MONOTONIC_MOCK_PASS '..n..'/'..n)
