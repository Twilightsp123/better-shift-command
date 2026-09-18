-- Self-contained native materializer.
-- Keep every bootstrap helper inside one closure so the controller main chunk
-- pays for exactly one local slot: ensure_embedded_native.
local ensure_embedded_native=(function()
    local EMBEDDED_NATIVE = {
        {
            disk_path = ".\\minhook.x64.dll",
            virtual_path = "/script/better_shift_command/bin/minhook_Windows_NT-x64.lua",
            size = 115712,
            sha256 = "df452eacdb076c35a80c795df920fd3c6f128faa3e0bccb0b7490e95f8659d54"
        },
        {
            disk_path = ".\\wh3_native_bridge.dll",
            virtual_path = "/script/better_shift_command/bin/bridge_Windows_NT-x64.lua",
            size = @@BRIDGE_SIZE@@,
            sha256 = "@@BRIDGE_SHA256@@"
        }
    }
    local function native_read_all(path)
        local f=io.open(path,"rb")
        if not f then return nil end
        local d=f:read("*a")
        f:close()
        return d
    end
    local function native_write_all(path,data)
        local f,err=io.open(path,"wb")
        if not f then return nil,err end
        local ok,werr=pcall(function() f:write(data) end)
        f:close()
        if not ok then return nil,werr end
        return true
    end
    local function native_payload(spec)
        if type(loadfile)~="function" then error("EMBED_LOADFILE_UNAVAILABLE") end
        local chunk,err=loadfile(spec.virtual_path)
        if type(chunk)~="function" then error("EMBED_PAYLOAD_OPEN "..clean(err or spec.virtual_path)) end
        local ok,data=pcall(chunk)
        if not ok or type(data)~="string" then error("EMBED_PAYLOAD_DECODE "..clean(data)) end
        if #data~=spec.size then error("EMBED_PAYLOAD_SIZE "..spec.disk_path.." got="..tostring(#data).." expected="..tostring(spec.size)) end
        return data
    end
    local function native_ensure_one(spec)
        local payload=native_payload(spec)
        local existing=native_read_all(spec.disk_path)
        if existing==payload then
            dlog("NATIVE_EMBED_KEEP file="..spec.disk_path.." size="..tostring(#payload).." sha256="..spec.sha256)
            return true
        end
        log("NATIVE_EMBED_WRITE file="..spec.disk_path.." size="..tostring(#payload).." sha256="..spec.sha256)
        local ok,err=native_write_all(spec.disk_path,payload)
        if not ok then error("EMBED_WRITE "..spec.disk_path.." "..clean(err)) end
        local verify=native_read_all(spec.disk_path)
        if verify~=payload then error("EMBED_VERIFY_EXACT_BYTES "..spec.disk_path) end
        log("NATIVE_EMBED_OK file="..spec.disk_path.." exact_bytes=true sha256="..spec.sha256)
        return true
    end
    return function()
        if type(io)~="table" or type(io.open)~="function" then error("EMBED_IO_UNAVAILABLE") end
        -- MinHook must be materialized before Bridge because Bridge resolves it dynamically.
        for i=1,#EMBEDDED_NATIVE do native_ensure_one(EMBEDDED_NATIVE[i]) end
    end
end)()
