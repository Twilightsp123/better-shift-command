out("[BRIDGE_OBSERVER_V041] ENTER")

-- Client for the byte-locked v0.5.0 integrated candidate.
-- Observes by default. NEVER arms or issues a native command automatically.
-- Exact uint32 values remain decimal STRINGS, including epoch and cursor.
local TAG = "[BRIDGE_OBSERVER_V041] "
local TIMER_KEY = "WH3ObserverV041Journal"
local PAGE_SIZE, MAX_PAGES_PER_TICK = 64, 8
local b = nil

-- WH3 mod chunks may inherit engine globals through their Lua environment.
-- Direct global lookup follows that environment; rawget(_G, ...) may bypass it.
local function resolve_out()
    local ok, value = pcall(function() return out end)
    if ok and type(value) == "function" then return value end
    return nil
end
local function resolve_battle_manager()
    local ok, value = pcall(function() return bm end)
    if ok and value ~= nil then return value end
    return nil
end
local function log(message)
    local line = TAG .. tostring(message)
    local f = resolve_out()
    if f then
        local ok = pcall(f, line)
        if ok then return true end
    end
    local manager = b or resolve_battle_manager()
    if manager then
        local ok_method, method = pcall(function() return manager.out end)
        if ok_method and type(method) == "function" then
            local ok = pcall(method, manager, line)
            if ok then return true end
        end
    end
    local ok_print, print_fn = pcall(function() return print end)
    if ok_print and type(print_fn) == "function" then pcall(print_fn, line) end
    return false
end

-- Strict, canonical u32, without converting a complete identifier to number.
local function is_u32(s)
    return type(s) == "string" and #s > 0 and #s <= 10
        and not s:find("[^0-9]")
        and (#s == 1 or s:sub(1, 1) ~= "0")
        and (#s < 10 or s <= "4294967295")
end
local function cmp(a, c)
    if #a ~= #c then return #a < #c and -1 or 1 end
    if a == c then return 0 end
    return a < c and -1 or 1
end
-- Used for client counters only, never for guessing native sequence IDs.
local function increment(s)
    local t, carry = {}, 1
    for i = #s, 1, -1 do
        local digit = string.byte(s, i) - 48 + carry
        if digit == 10 then digit, carry = 0, 1 else carry = 0 end
        t[i] = string.char(digit + 48)
    end
    return (carry == 1 and "1" or "") .. table.concat(t)
end
local function finite(n)
    return type(n) == "number" and n == n and n > -math.huge and n < math.huge
end
local function clean(s)
    if s == nil then return "nil" end
    return (tostring(s):gsub("[%c]", "?"))
end

if _VERSION ~= "Lua 5.1" then log("FAIL WRONG_LUA_VERSION " .. clean(_VERSION)); return end
b = resolve_battle_manager()
if not b then log("FAIL BATTLE_MANAGER_UNAVAILABLE_AT_LOAD"); return end
local previous = __WH3_OBSERVER_V041_CLIENT
if previous and previous.bm == b then
    log("DUPLICATE_ENTRY_IGNORED")
    return
end
if not b or type(b.register_phase_change_callback) ~= "function"
    or type(b.repeat_real_callback) ~= "function"
    or type(b.remove_real_callback) ~= "function" then
    log("FAIL BATTLE_MANAGER_CALLBACK_API_MISSING"); return
end
if type(package) ~= "table" or type(package.loadlib) ~= "function" then
    log("FAIL PACKAGE_LOADLIB_UNAVAILABLE"); return
end

local path = ".\\wh3_native_bridge.dll"
local path_ok, path_override = pcall(function() return WH3_NATIVE_BRIDGE_DLL end)
if path_ok and type(path_override) == "string" and path_override ~= "" then path = path_override end
local loaded, loader, load_error = pcall(package.loadlib, path, "luaopen_wh3_native_bridge")
if not loaded or type(loader) ~= "function" then
    log("FAIL LOADLIB " .. clean(loaded and load_error or loader)); return
end
local initialized, bridge, init_error = pcall(loader)
if not initialized or type(bridge) ~= "table" then
    log("FAIL INIT " .. clean(initialized and init_error or bridge)); return
end
for _, name in ipairs({"version", "number_abi_probe", "exact_id_probe", "capabilities",
    "get_status", "start_observer", "begin_battle", "end_battle", "read_journal", "acknowledge"}) do
    if type(bridge[name]) ~= "function" then log("FAIL MISSING_API " .. name); return end
end

local ok, version = pcall(bridge.version)
if not ok or version ~= "0.5.0-attack-native-token" then
    log("FAIL VERSION " .. clean(version)); return
end
local number_ok, a, c = pcall(bridge.number_abi_probe)
if not number_ok or type(a) ~= "number" or type(c) ~= "number" or a ~= 16777215 or c ~= 1.5 then
    log("FAIL NUMBER_ABI"); return
end
local id_ok, max_id, above_float = pcall(bridge.exact_id_probe)
if not id_ok or not is_u32(max_id) or not is_u32(above_float)
    or max_id ~= "4294967295" or above_float ~= "16777217" then
    log("FAIL EXACT_ID_ABI"); return
end
log("ABI_OK version=" .. version .. " ids=decimal_string")

local function caps_read()
    local success, caps, err = pcall(bridge.capabilities)
    if not success or type(caps) ~= "table" then
        return nil, "CAPABILITIES " .. clean(success and err or caps)
    end
    if caps.host_lua_number ~= "float32" or caps.host_lua_number_bytes ~= 4 then
        return nil, "CAPABILITIES_ABI"
    end
    -- Ready/path samples are diagnostics, not a release qualification.
    if type(caps.exact_source) ~= "boolean" or caps.verified_issue ~= false
        or caps.controller_connected ~= false or caps.complete_command_batch ~= false
        or caps.release_approved ~= false then
        return nil, "CAPABILITIES_NOT_EXPECTED_OBSERVER_BASELINE"
    end
    return caps
end
local caps, cap_err = caps_read()
if not caps then log("FAIL " .. cap_err); return end

local state = {bm=b, epoch=nil, cursor="0", records="0", gaps="0", failed=false,
    stopped=false, timer=false, poll_busy=false, started=false, waiting_ticks=0, newest="0"}
__WH3_OBSERVER_V041_CLIENT = state
-- Stop any old client closure if a new battle manager is created in the same VM.
if previous and previous.bm ~= b and type(previous.stop) == "function" then
    previous.stop("REPLACED_BY_NEW_BATTLE_MANAGER")
end

local function remove_timer()
    if state.timer then
        state.timer = false
        local success, err = pcall(b.remove_real_callback, b, TIMER_KEY)
        if not success then log("CLEANUP_TIMER_ERROR " .. clean(err)) end
    end
end
local function close_session(reason)
    local epoch = state.epoch
    state.epoch = nil
    if epoch then
        local success, result, err = pcall(bridge.end_battle, epoch)
        log("BATTLE_ENDED epoch=" .. epoch .. " reason=" .. reason
            .. " result=" .. clean(result) .. " records=" .. state.records .. " gaps=" .. state.gaps)
        if not success or result ~= true then
            state.failed = true
            log("CLEANUP_END_ERROR " .. clean(success and err or result))
        end
    end
end
local function fail(reason)
    if state.failed or state.stopped then return end
    state.failed = true
    log("FAIL " .. reason)
    remove_timer()
    close_session("CLIENT_FAULT")
end

-- Every field below is read as returned; no player/AI/source inference.
local function format_order(ord)
    local fields = {"epoch", "serial", "status", "order_type", "source", "command_id",
        "script_issue_id", "unit_uid", "unit_revision", "engine_seq", "engine_seq_valid",
        "is_queued", "flags_valid_mask", "batch_index", "batch_total",
        "dest_x", "dest_y", "dest_z", "target_uid", "target_root",
        "raw70", "raw71", "raw72", "raw78", "halt_flags"}
    local text = {}
    for i = 1, #fields do
        local key = fields[i]
        text[#text + 1] = key .. "=" .. clean(ord[key])
    end
    return table.concat(text, " ")
end

local function validate_page(records, meta)
    if type(records) ~= "table" or type(meta) ~= "table" then return nil, "READ_RETURN_SHAPE" end
    if not is_u32(meta.epoch) or meta.epoch ~= state.epoch then return nil, "READ_EPOCH_MISMATCH" end
    for _, key in ipairs({"oldest_serial", "newest_serial", "next_after", "dropped"}) do
        if not is_u32(meta[key]) then return nil, "META_ID_TYPE_" .. key end
    end
    if type(meta.overrun) ~= "boolean" or type(meta.complete) ~= "boolean"
        or type(meta.error) ~= "string" or type(meta.journal_fault) ~= "string" then
        return nil, "META_STATUS_TYPES"
    end
    if meta.journal_fault ~= "Ok" and meta.journal_fault ~= "" then
        return nil, "JOURNAL_FAULT_" .. clean(meta.journal_fault)
    end
    if meta.error ~= "Ok" and meta.error ~= "" and not (meta.overrun and meta.error == "Overrun") then
        return nil, "READ_ERROR_" .. clean(meta.error)
    end
    if not meta.complete and not meta.overrun then return nil, "INCOMPLETE_NATIVE_READ" end
    local count = meta.count
    if type(count) ~= "number" or count < 0 or count > PAGE_SIZE or count ~= math.floor(count)
        or #records ~= count then return nil, "READ_COUNT_MISMATCH" end
    local actual = 0
    for k in pairs(records) do
        if type(k) ~= "number" or k < 1 or k > count or k ~= math.floor(k) then
            return nil, "READ_NON_ARRAY"
        end
        actual = actual + 1
    end
    if actual ~= count then return nil, "READ_SPARSE_ARRAY" end
    if cmp(meta.next_after, state.cursor) < 0 or cmp(meta.next_after, meta.newest_serial) > 0 then
        return nil, "CURSOR_METADATA_RANGE"
    end
    local last = state.cursor
    for i = 1, count do
        local ord = records[i]
        if type(ord) ~= "table" then return nil, "RECORD_NOT_TABLE" end
        for _, key in ipairs({"epoch", "serial", "command_id", "script_issue_id", "unit_uid",
            "unit_revision", "engine_seq", "flags_valid_mask"}) do
            if not is_u32(ord[key]) then return nil, "RECORD_ID_TYPE_" .. key end
        end
        if ord.epoch ~= state.epoch then return nil, "RECORD_EPOCH_MISMATCH" end
        if cmp(ord.serial, last) <= 0 or cmp(ord.serial, meta.newest_serial) > 0 then
            return nil, "RECORD_SERIAL_ORDER"
        end
        if type(ord.engine_seq_valid) ~= "boolean" or type(ord.status) ~= "string"
            or type(ord.source) ~= "string" or type(ord.order_type) ~= "string" then
            return nil, "RECORD_STATUS_TYPES"
        end
        if ord.is_queued ~= nil and type(ord.is_queued) ~= "boolean" then return nil, "QUEUED_TYPE" end
        for _, key in ipairs({"dest_x", "dest_y", "dest_z"}) do
            if ord[key] ~= nil and not finite(ord[key]) then return nil, "GEOMETRY_TYPE_" .. key end
        end
        if ord.target_uid ~= nil and not is_u32(ord.target_uid) then return nil, "TARGET_UID_TYPE" end
        if ord.target_root ~= nil and type(ord.target_root) ~= "string" then return nil, "TARGET_ROOT_TYPE" end
        last = ord.serial
    end
    if count > 0 and meta.next_after ~= last then return nil, "NEXT_AFTER_NOT_LAST_RETURNED" end
    if count == 0 and meta.next_after ~= state.cursor then return nil, "EMPTY_PAGE_CURSOR_ADVANCE" end
    return count
end

local function drain(max_pages)
    for page = 1, max_pages do
        if state.failed or state.stopped or not state.epoch then return end
        local success, records, meta = pcall(bridge.read_journal, state.epoch, state.cursor, PAGE_SIZE)
        if not success then fail("READ_EXCEPTION " .. clean(records)); return end
        if records == nil then fail("READ_NATIVE " .. clean(meta)); return end
        local count, err = validate_page(records, meta)
        if not count then fail(err); return end
        -- Overrun never silently becomes 'no new orders' or a clean acceptance.
        if meta.overrun then
            state.gaps = increment(state.gaps)
            log("JOURNAL_GAP epoch=" .. state.epoch .. " after=" .. state.cursor
                .. " oldest=" .. meta.oldest_serial .. " newest=" .. meta.newest_serial
                .. " dropped=" .. meta.dropped .. " policy=OBSERVE_RETAINED_ONLY")
        end
        for i = 1, count do
            state.records = increment(state.records)
            log("ORDER_OBSERVED index=" .. state.records .. " " .. format_order(records[i]))
        end
        -- NEVER advance to newest_serial: there may be unread pages before it.
        state.cursor, state.newest = meta.next_after, meta.newest_serial
        if count > 0 then
            local ack_ok, ack_result, ack_err = pcall(bridge.acknowledge, state.epoch, state.cursor)
            if not ack_ok or ack_result ~= true then
                fail("ACKNOWLEDGE " .. clean(ack_ok and ack_err or ack_result)); return
            end
        end
        if count == 0 then
            state.waiting_ticks = state.waiting_ticks + 1
            if state.records == "0" and (state.waiting_ticks == 1 or state.waiting_ticks % 50 == 0) then
                log("WAITING_NATIVE_RECORDS epoch=" .. state.epoch .. " after=" .. state.cursor)
            end
            return
        end
        state.waiting_ticks = 0
        if cmp(state.cursor, meta.newest_serial) >= 0 then return end
        if page == max_pages then
            log("BACKLOG_DEFERRED epoch=" .. state.epoch .. " after=" .. state.cursor
                .. " newest=" .. meta.newest_serial)
        end
    end
end
local function poll()
    if state.poll_busy or state.failed or state.stopped or not state.epoch then return end
    state.poll_busy = true
    local success, err = pcall(drain, MAX_PAGES_PER_TICK)
    state.poll_busy = false
    if not success then fail("POLL_EXCEPTION " .. clean(err)); return end
    if state.epoch and not state.failed then
        local st_ok, st = pcall(bridge.get_status)
        if not st_ok or type(st) ~= "table" then fail("STATUS_READ_FAILED"); return end
        local key = clean(st.adapter_error) .. ":" .. clean(st.move_path_observed) .. ":" .. clean(st.attack_path_observed)
        if key ~= state.last_adapter_status then
            state.last_adapter_status = key
            log("ADAPTER_STATUS reason=" .. clean(st.adapter_error)
                .. " move_path=" .. clean(st.move_path_observed) .. " attack_path=" .. clean(st.attack_path_observed)
                .. " release_approved=false")
        end
    end
end

local function start_session()
    if state.failed or state.stopped or state.started then return end
    state.started = true
    -- The DLL itself returns epoch_string OR nil,error. It does NOT return true,epoch.
    local success, epoch, err = pcall(bridge.begin_battle, "wh3_observer_v041_" .. tostring(b))
    if not success or not is_u32(epoch) or epoch == "0" then
        fail("BEGIN_BATTLE " .. clean(success and err or epoch)); return
    end
    state.epoch, state.cursor = epoch, "0"
    local status_ok, status, status_err = pcall(bridge.get_status)
    if not status_ok or type(status) ~= "table" or status.recording ~= true or status.epoch ~= epoch then
        fail("BEGIN_STATUS " .. clean(status_ok and status_err or status)); return
    end
    log("BATTLE_STARTED epoch=" .. epoch .. " after=0 recording=true")
    state.timer = true
    local registered, regerr = pcall(b.repeat_real_callback, b, poll, 200, TIMER_KEY)
    if not registered then fail("REGISTER_TIMER " .. clean(regerr)); return end
    poll()
end
local function stop(reason)
    if state.stopped then return end
    if state.epoch and not state.failed then poll() end
    if state.epoch and not state.failed and cmp(state.cursor, state.newest) < 0 then
        log("FINAL_BACKLOG_UNREAD epoch=" .. state.epoch .. " after=" .. state.cursor
            .. " newest=" .. state.newest .. " capture_complete=false")
    end
    state.stopped = true
    remove_timer()
    close_session(reason or "COMPLETE")
end
state.stop = stop

-- Explicit start; no hidden hook installation in DLL load/self-test.
local started_ok, started, start_error = pcall(bridge.start_observer, true)
if not started_ok or started ~= true then
    fail("START_OBSERVER " .. clean(started_ok and start_error or started)); return
end
caps, cap_err = caps_read()
if not caps or caps.observer_hooks_installed ~= true or caps.queued_from_native_entry ~= true then
    fail(cap_err or "HOOK_CAPABILITY_NOT_ACTIVE"); return
end
log("HOOKS_ACTIVE observer_hooks_installed=" .. clean(caps.observer_hooks_installed)
    .. " exact_source=" .. clean(caps.exact_source) .. " verified_issue=" .. clean(caps.verified_issue))
wh3_bridge = bridge

for _, phase in ipairs({"Deployment", "Deployed"}) do
    local registered, err = pcall(b.register_phase_change_callback, b, phase, start_session)
    if not registered then fail("REGISTER_PHASE " .. phase .. " " .. clean(err)); return end
end
local registered, err = pcall(b.register_phase_change_callback, b, "Complete", function() stop("COMPLETE") end)
if not registered then fail("REGISTER_COMPLETE " .. clean(err)); return end

-- Mod reload/late initialization: do not wait for a phase that already passed.
if type(b.get_current_phase_name) == "function" then
    local phase_ok, phase = pcall(b.get_current_phase_name, b)
    if not phase_ok then fail("GET_PHASE " .. clean(phase)); return end
    if phase == "Deployment" or phase == "Deployed" or phase == "VictoryCountdown" then start_session()
    elseif phase == "Complete" then stop("ALREADY_COMPLETE") end
end
if not state.failed and not state.stopped then log("CLIENT_READY_WAITING_FOR_NATIVE_RECORDS")
log("RELEASE_APPROVED=false AUTO_COMMANDS=false") end
