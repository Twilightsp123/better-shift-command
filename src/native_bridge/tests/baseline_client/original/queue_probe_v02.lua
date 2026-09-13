out("[BRIDGE_OBSERVER_V02] ENTER")

local function safe_log(msg)
    local line = "[BRIDGE_OBSERVER_V02] " .. tostring(msg)
    local b = rawget(_G, "bm")
    if b and type(rawget(b, "out")) == "function" then
        b:out(line)
    elseif rawget(_G, "out") ~= nil then
        local out_fn = rawget(_G, "out")
        local ok = pcall(out_fn, line)
        if not ok then
            print(line)
        end
    else
        print(line)
    end
end

safe_log("LUA=" .. tostring(_VERSION))

if _VERSION ~= "Lua 5.1" then
    safe_log("FAIL WRONG_LUA_VERSION")
    return
end

if type(package) ~= "table" or type(package.loadlib) ~= "function" then
    safe_log("FAIL PACKAGE_LOADLIB_UNAVAILABLE")
    return
end

local dll_path = rawget(_G, "WH3_NATIVE_BRIDGE_DLL") or ".\\wh3_native_bridge.dll"
safe_log("LOADLIB " .. tostring(dll_path))

local loader, load_err = package.loadlib(dll_path, "luaopen_wh3_native_bridge")
if type(loader) ~= "function" then
    safe_log("FAIL LOADLIB " .. tostring(load_err))
    return
end

local ok_init, bridge = pcall(loader)
if not ok_init or type(bridge) ~= "table" then
    safe_log("FAIL INIT " .. tostring(bridge))
    return
end

-- 1. ABI Verification
local ok_ver, version = pcall(bridge.version)
if not ok_ver or version ~= "0.1.1-observer-floatabi" then
    safe_log("FAIL VERSION " .. tostring(version))
    return
end
safe_log("VERSION " .. tostring(version))

local ok_id, max_u32, over_float = pcall(bridge.exact_id_probe)
if not ok_id or type(max_u32) ~= "string" or max_u32 ~= "4294967295" or over_float ~= "16777217" then
    safe_log("FAIL EXACT_ID_PROBE")
    return
end

-- 2. Start Observer Engine (Observer Mode ONLY)
-- Strict boundary: Observer records accepted native orders; DOES NOT alter logic, DOES NOT reject orders, DOES NOT issue orders.
local ok_obs, obs_err = bridge.start_observer(true)
if not ok_obs then
    safe_log("FAIL START_OBSERVER " .. tostring(obs_err))
    return
end
safe_log("OBSERVER_HOOKS_ACTIVE")

local ok_caps, caps = pcall(bridge.capabilities)
if ok_caps and type(caps) == "table" then
    safe_log("CAPS observer_hooks_installed=" .. tostring(caps.observer_hooks_installed) .. " host_lua_number=" .. tostring(caps.host_lua_number))
end

-- 3. Register Battle Lifecycle Callbacks
local active_epoch = nil
local last_read_serial = 0
local total_orders_observed = 0

local function format_order(ord)
    if type(ord) ~= "table" then return tostring(ord) end
    local otype = tostring(ord.order_type or "UNKNOWN")
    local queued = tostring(ord.is_queued)
    local uid = tostring(ord.unit_uid or "?")
    local src = tostring(ord.source or "UNKNOWN")
    local rev = tostring(ord.unit_revision or "?")
    local seq = tostring(ord.engine_seq or "?")
    local cmd_id = tostring(ord.command_id or "?")
    local issue_id = tostring(ord.script_issue_id or "?")
    local pos = ""
    if ord.dest_x ~= nil then
        pos = string.format(" dst=(%.1f,%.1f,%.1f)", ord.dest_x or 0, ord.dest_y or 0, ord.dest_z or 0)
    end
    local target = ""
    if ord.target_uid ~= nil and ord.target_uid ~= "0" and ord.target_uid ~= "" then
        target = string.format(" tgt_uid=%s tgt_root=%s", tostring(ord.target_uid), tostring(ord.target_root or "0"))
    end
    return string.format("cmd_id=%s issue_id=%s type=%s src=%s queued=%s uid=%s rev=%s seq=%s%s%s",
        cmd_id, issue_id, otype, src, queued, uid, rev, seq, pos, target)
end

local function poll_journal_records()
    if not active_epoch or not bridge.read_journal then return end
    local records, meta = bridge.read_journal(active_epoch, last_read_serial, 64)
    if type(records) == "table" and #records > 0 then
        for i = 1, #records do
            local ord = records[i]
            total_orders_observed = total_orders_observed + 1
            safe_log(string.format("[ORDER_OBSERVED #%d] %s", total_orders_observed, format_order(ord)))
            if ord.serial and ord.serial > last_read_serial then
                last_read_serial = ord.serial
            end
        end
    end
end

local function on_battle_start()
    local session_id = "session_" .. tostring(os.date("%Y%m%d_%H%M%S"))
    local ok_begin, epoch = bridge.begin_battle(session_id)
    if ok_begin then
        active_epoch = epoch
        last_read_serial = 0
        total_orders_observed = 0
        safe_log(string.format("BATTLE_STARTED epoch=%s session=%s", tostring(epoch), session_id))
    else
        safe_log("FAIL BEGIN_BATTLE " .. tostring(epoch))
    end
end

local function on_battle_end()
    if active_epoch and bridge.end_battle then
        local ok_end, res = bridge.end_battle(active_epoch)
        safe_log("BATTLE_ENDED epoch=" .. tostring(active_epoch) .. " res=" .. tostring(res) .. " total_observed=" .. tostring(total_orders_observed))
        active_epoch = nil
    end
end

local bm_obj = rawget(_G, "bm")
if bm_obj then
    if type(bm_obj.register_phase_change_callback) == "function" then
        bm_obj:register_phase_change_callback("Deployment", function()
            on_battle_start()
        end)
        bm_obj:register_phase_change_callback("Conflict", function()
            if not active_epoch then
                on_battle_start()
            end
        end)
    else
        on_battle_start()
    end

    if type(bm_obj.repeat_real_callback) == "function" then
        bm_obj:repeat_real_callback(function()
            poll_journal_records()
        end, 200, "ObserverJournalPoller")
    end
else
    on_battle_start()
end

_G.wh3_bridge = bridge
safe_log("OBSERVER_V02_READY_WAITING_FOR_ORDERS")
