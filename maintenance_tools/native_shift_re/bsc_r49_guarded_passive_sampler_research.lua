-- BSC R49 RESEARCH ONLY. Do not auto-load, register callbacks, patch code, or ship as gameplay mod.
-- Tested against an offline API mock, NOT tested inside Warhammer III.
-- This is a bounded sequential sample, never an engine-level atomic snapshot.
local M = {}
local BUILD = '6acec6f4'
local MAX_MEN, MAX_ROWS, MAX_IDS = 500, 32, 4096
local MAX_GAP_MS, MAX_READ_US = 250, 5000
local TICK_RVA, GATE_RVA = 0x03086f04, 0x03087378
local MEMBER_VTABLE, MEMBER_UPDATE = 0x03912950, 0x030592bc
local TICK_BYTES = string.char(0x48,0x8b,0xc4,0x48,0x89,0x58,0x10)
local GATE_BYTES = string.char(0x44,0x38,0xbf,0xf8,0x06,0,0,0x75,0x09,
                               0x44,0x38,0xbf,0,0x06,0,0,0x75,0x5c)
local ACTIONS = {
    {'derpy_walk_a_vtable',0x03919350},
    {'derpy_walk_b_vtable',0x03ae2400},
    {'b2_special_action_vtable',0x039199f8},
    {'b2_general_action_vtable',0x03919b28},
    {'other_move_action_vtable',0x03ae1928},
    {'state16_cached_vector_vtable',0x03ae22d0},
    {'melee_action_vtable',0x03ad24b8},
}
-- Local only: raw pointer strings, roster bytes and epoch identities are never returned.
local context = {unit_key=nil, token=nil, epoch=0, last_roster=nil,
                 last_array=nil, last_sample_id=nil, last_time_ms=nil,
                 seen={}, next_id=0}
local busy=false

local function addr(mr, base, rva)
    local lo = rva % 0x10000
    return mr.add(mr.add(base, rva-lo), lo)
end
local function positive_integer(v, max)
    return type(v)=='number' and v==math.floor(v) and v>=0 and v<=max
end
local function good_number(v)
    return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge
end
local function ptr_ok(mr, ptr)
    return ptr~=nil and ptr~=false and not mr.is_null(ptr)
end
local function image_info(mr)
    local base=mr.base
    local hdr=mr.read_uint16(base,0x3c)
    if mr.read_uint16(base,0x3e)~=0 or hdr<0x40 or hdr>0x1000 then
        return nil,'invalid_pe_header_offset'
    end
    if mr.read(base,hdr,4)~='PE\0\0' or mr.read_uint16(base,hdr+0x18)~=0x20b then
        return nil,'invalid_pe_x64_header'
    end
    local timestamp=string.format('%04x%04x',mr.read_uint16(base,hdr+10),mr.read_uint16(base,hdr+8))
    if timestamp~=BUILD then return nil,'game_build_mismatch' end
    -- Read SizeOfImage in exact halves. Never pass the full image RVA as one game float.
    local low, high=mr.read_uint16(base,hdr+0x50),mr.read_uint16(base,hdr+0x52)
    if high==0 or high>0x1000 then return nil,'invalid_image_size' end
    local finish=mr.add(mr.add(base,high*0x10000),low)
    return {base=base,finish=finish,lo=mr.tostring(base),hi=mr.tostring(finish)}
end
local function verify_read_contract(mr)
    for _,name in ipairs({'read','read_original','hook_info','read_pointer','read_uint8',
        'read_uint16','read_int32','read_float','ud_topointer','ticks','elapsed_us',
        'eq','is_null','add','tostring'}) do
        if type(mr[name])~='function' then return nil,'missing_memreader_api_'..name end
    end
    if not ptr_ok(mr,mr.base) then return nil,'missing_image_base' end
    return true
end
local function check_live_code(mr,image)
    local tick,gate=addr(mr,image.base,TICK_RVA),addr(mr,image.base,GATE_RVA)
    for _,entry in ipairs({{tick,TICK_BYTES,'member_tick'},{gate,GATE_BYTES,'queued_gate'}}) do
        local h=mr.hook_info(entry[1])
        if h and h.kind and h.kind~='none' then return nil,entry[3]..'_hook_or_cave_present' end
        if mr.read_original(entry[1],0,#entry[2])~=entry[2] or
           mr.read(entry[1],0,#entry[2])~=entry[2] then
           return nil,entry[3]..'_original_or_live_bytes_drift'
        end
    end
    local vt=addr(mr,image.base,MEMBER_VTABLE)
    if not mr.eq(mr.read_pointer(vt,0x18),tick) or
       not mr.eq(mr.read_pointer(vt,0x20),addr(mr,image.base,MEMBER_UPDATE)) then
        return nil,'member_vtable_methods_mismatch'
    end
    return true
end
local function indices(n,limit,opts)
    local result={}
    if opts.mode=='window' then
        local first=opts.start_index
        if not positive_integer(first,n) or first<1 then return nil,'bad_start_index' end
        for i=first,math.min(n,first+limit-1) do result[#result+1]=i end
    else
        local count=math.min(n,limit)
        for i=0,count-1 do
            result[#result+1]=(count==1 and 1 or 1+math.floor(i*(n-1)/(count-1)))
        end
    end
    return result
end
local function action_label(mr,value,image)
    if not ptr_ok(mr,value) then return 'none_or_unknown' end
    for _,a in ipairs(ACTIONS) do
        if mr.eq(value,addr(mr,image.base,a[2])) then return a[1] end
    end
    return 'unknown_action_vtable'
end
local function identity_key(mr,ptr)
    local key=mr.tostring(ptr)
    if type(key)~='string' or #key<12 then error('bad_pointer_format') end
    return key
end
local function valid_opts(opts)
    if type(opts)~='table' then return nil,'invalid_opts' end
    if not positive_integer(opts.sample_id,16777215) or not positive_integer(opts.time_ms,16777215) then
        return nil,'invalid_sample_id_or_time_ms'
    end
    local token=opts.unit_token
    if type(token)~='string' or #token<1 or #token>80 or
       token:match('^0[xX]') or token:match('^%x%x%x%x%x%x%x%x%x%x%x%x$') then
        return nil,'invalid_anonymous_unit_token'
    end
    if opts.mode~=nil and opts.mode~='window' and opts.mode~='stride' then return nil,'invalid_selection_mode' end
    local limit=opts.max_rows or 16
    if not positive_integer(limit,MAX_ROWS) or limit<1 then return nil,'invalid_max_rows' end
    return {unit_token=token,sample_id=opts.sample_id,time_ms=opts.time_ms,
            mode=opts.mode or 'stride',max_rows=limit,start_index=opts.start_index}
end
local function sample_inner(mr,unit,options)
    local opts,err=valid_opts(options)
    if not opts then return nil,err end
    if _G.memreader_plus_release~='0_13_0' then return nil,'memreader_release_unverified' end
    local ok,reason=verify_read_contract(mr)
    if not ok then return nil,reason end
    local image,why=image_info(mr)
    if not image then return nil,why end
    ok,reason=check_live_code(mr,image)
    if not ok then return nil,reason end
    if type(unit)~='userdata' or type(unit.number_of_men_alive)~='function' then
        return nil,'not_battle_unit_userdata'
    end
    local interface=mr.ud_topointer(unit)
    if not ptr_ok(mr,interface) then return nil,'no_battle_unit_interface' end
    local obj=mr.read_pointer(interface,8)
    if not ptr_ok(mr,obj) then return nil,'no_unit_object' end
    local key=identity_key(mr,obj)
    if context.unit_key and (context.unit_key~=key or context.token~=opts.unit_token) then
        return nil,'one_unit_per_session_call_reset_before_new_unit'
    end
    if context.last_sample_id and (opts.sample_id<=context.last_sample_id or
       opts.time_ms<=context.last_time_ms) then
        return nil,'non_monotonic_sample_clock'
    end
    local began=mr.ticks() -- uint64 typed value, never converted or used in arithmetic
    local alive=unit:number_of_men_alive()
    local n=mr.read_int32(obj,0xa4)
    if not positive_integer(n,MAX_MEN) or n<1 or n~=alive then return nil,'member_count_mismatch' end
    local array=mr.read_pointer(obj,0xa8)
    if not ptr_ok(mr,array) then return nil,'member_array_missing' end
    -- Every roster pointer, including unsampled members, checked before & after.
    local roster=mr.read(array,0,n*8)
    if type(roster)~='string' or #roster~=n*8 then return nil,'short_roster_read' end
    -- A complete active roster must contain unique, non-null 64-bit pointers.
    -- This catches partially rebuilt arrays before following any member pointers.
    local roster_ids={}
    for i=1,n do
        local item=roster:sub((i-1)*8+1,i*8)
        if item=='\0\0\0\0\0\0\0\0' then return nil,'null_roster_pointer' end
        if roster_ids[item] then return nil,'duplicate_roster_pointer' end
        roster_ids[item]=true
    end
    local chosen,selection_err=indices(n,opts.max_rows,opts)
    if not chosen then return nil,selection_err end
    local rows,before,keys={},{},{}
    local ordinary=addr(mr,image.base,MEMBER_VTABLE)
    for _,index in ipairs(chosen) do
        local member=mr.read_pointer(array,(index-1)*8)
        if not ptr_ok(mr,member) then return nil,'missing_selected_member' end
        local klass=mr.read_pointer(member,0)
        if not ptr_ok(mr,klass) then return nil,'missing_member_vtable' end
        local class_addr=mr.tostring(klass)
        if class_addr<image.lo or class_addr>=image.hi then return nil,'member_vtable_outside_exe' end
        local is_ordinary=mr.eq(klass,ordinary)
        local px,py,pz=mr.read_float(member,0x88),mr.read_float(member,0x8c),mr.read_float(member,0x90)
        if not (good_number(px) and good_number(py) and good_number(pz)) then
            return nil,'invalid_member_position'
        end
        local k=identity_key(mr,member)
        before[#before+1]={ptr=member,class=klass,index=index}
        keys[#keys+1]=k
        local row={member_index=index,position_xyz={px,py,pz},
                   member_type=is_ordinary and 'ordinary_exact_vtable' or 'unknown_position_only',
                   action='not_typed',goal_has_reference=false,
                   read_offset_us=mr.elapsed_us(began)}
        if is_ordinary then
            local action_before=mr.read_pointer(member,0x330)
            local f_before=mr.read_uint8(member,0x108)
            local p0,p1,p2=mr.read_float(member,0x1e0),mr.read_float(member,0x1e4),mr.read_float(member,0x1e8)
            local dx,dy,dz=mr.read_float(member,0x13c),mr.read_float(member,0x140),mr.read_float(member,0x144)
            local vx,vz=mr.read_float(member,0xe0),mr.read_float(member,0xe8)
            if not(good_number(p0) and good_number(p1) and good_number(p2) and
                    good_number(dx) and good_number(dy) and good_number(dz) and
                    good_number(vx) and good_number(vz)) then
                return nil,'invalid_member_motion_or_goal'
            end
            local ref=mr.read_pointer(member,0x1f0)
            row.action=action_label(mr,action_before,image)
            row.stored_goal_xz={p0,p2}
            row.goal_has_reference=ptr_ok(mr,ref)
            row.pending_delta_xyz={dx,dy,dz}
            row.motion_xz={vx,vz}
            row.flags_108=f_before
            row.flags_155=mr.read_uint8(member,0x155)
            row.action_state_324=mr.read_int32(member,0x324)
            row.action_done_340=mr.read_uint8(member,0x340)
            if f_before~=mr.read_uint8(member,0x108) or
               not mr.eq(action_before,mr.read_pointer(member,0x330)) then
                return nil,'member_action_changed_mid_sample'
            end
        end
        rows[#rows+1]=row
    end
    if mr.read_int32(obj,0xa4)~=n or unit:number_of_men_alive()~=n or
       not mr.eq(array,mr.read_pointer(obj,0xa8)) then
        return nil,'unit_roster_owner_changed_during_read'
    end
    local after_roster=mr.read(array,0,n*8)
    if roster~=after_roster then return nil,'full_member_roster_changed_during_read' end
    for _,b in ipairs(before) do
        local member=mr.read_pointer(array,(b.index-1)*8)
        if not mr.eq(member,b.ptr) or not mr.eq(mr.read_pointer(member,0),b.class) then
            return nil,'selected_member_identity_changed_during_read'
        end
    end
    local duration=mr.elapsed_us(began)
    if not good_number(duration) or duration<0 or duration>MAX_READ_US then
        return nil,'sample_read_budget_exceeded'
    end
    local next_epoch=context.epoch
    local new_epoch=not context.last_roster or context.last_roster~=roster or
        context.last_array~=identity_key(mr,array) or
        context.last_time_ms and opts.time_ms-context.last_time_ms>MAX_GAP_MS
    if new_epoch then next_epoch=next_epoch+1 end
    local id_map={}
    if next_epoch==context.epoch then
        for k,v in pairs(context.seen) do id_map[k]=v end
    end
    local next_id=next_epoch==context.epoch and context.next_id or 0
    for i,row in ipairs(rows) do
        local id=id_map[keys[i]]
        if not id then
            next_id=next_id+1
            if next_id>MAX_IDS then return nil,'identity_budget_exceeded' end
            id='m'..tostring(next_epoch)..'_'..tostring(next_id)
            id_map[keys[i]]=id
        end
        row.member_id=id
    end
    -- Do not commit sample state before every read and budget guard passes.
    context.unit_key=key;context.token=opts.unit_token
    context.epoch=next_epoch;context.last_roster=roster
    context.last_array=identity_key(mr,array)
    context.last_sample_id=opts.sample_id;context.last_time_ms=opts.time_ms
    context.seen=id_map;context.next_id=next_id
    return {schema='bsc.n1.passive_member_snapshot.v1',build=BUILD,
            unit_token=opts.unit_token,sample_id=opts.sample_id,time_ms=opts.time_ms,
            member_count=n,sampled_count=#rows,rows=rows,
            roster_epoch=next_epoch,read_duration_us=duration,
            read_budget_us=MAX_READ_US,roster_bytes_checked=n*8,
            inventory_stable=true,intra_sample_full_roster_stable=true,
            sample_type='sequential-not-atomic',member_selection=opts.mode,
            all_member_types_typed=not (function()
                for _,r in ipairs(rows) do if r.member_type~='ordinary_exact_vtable' then return true end end
                return false
            end)(),
            cross_snapshot_lifetime_proven=false,world_goal_frame_consistency_proven=false,
            native_patch_authorized=false}
end
function M.sample(unit,opts)
    if busy then return nil,'reentrant_snapshot_rejected' end
    local mr=rawget(_G,'memreader_plus')
    if not mr then return nil,'memreader_plus_not_loaded' end
    busy=true
    local ok,a,b=pcall(sample_inner,mr,unit,opts)
    busy=false
    -- Never return the raw native exception: it could include a process pointer.
    if not ok then return nil,'guarded_read_error' end
    return a,b
end
function M.reset()
    if busy then return nil,'reentrant_snapshot_rejected' end
    context={unit_key=nil,token=nil,epoch=0,last_roster=nil,last_array=nil,
             last_sample_id=nil,last_time_ms=nil,seen={},next_id=0}
    return true
end
return M
