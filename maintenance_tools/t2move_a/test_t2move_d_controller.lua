-- T2-MOVE-D real controller zero-permission observation fixtures.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(name,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..name)else fail=fail+1;print('FAIL '..name..' '..tostring(e))end end
local function order_v3(f,u)
 local r=f.evidence_record;if not r or r.unit_uid~=u then return nil,'NO_ORDER' end
 return {schema=3,epoch='1',unit_uid=u,unit_lifetime=r.unit_lifetime,complete=true,active=true,known=true,
 accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
end
local function mk()
 local f=F({cold_idle=true,debug_source=true,no_calibration=true,width=20,native_order_evidence_v3=order_v3})
 f:start();f.unit.idle=false;f.unit.moving=true
 local m=f:emit('MOVE',false,100,0)
 local n=f:emit('MOVE',true,200,0)
 f.evidence_record=m
 return f,m,n
end
local function warm(f)
 f:tick(100,0,0);f:tick(200,30,0);f:tick(300,50,0);f:tick(400,70,0)
end
T('D-RT00 exact-current MOVE records non-authoritative geometry proof',function()
 local f=mk();warm(f)
 assert(f:has('T2MOVE_D_SHADOW_CAPTURE'),'D observer must record exact-current MOVE evidence')
 assert(f:has('authoritative=false'),'D evidence never authorizes transitions')
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'),'no Native MOVE adopt from D evidence')
end)
T('D-RT01 exact-current MOVE proof may support isolated E Native adoption',function()
 local f,m,n=mk();warm(f)
 f.evidence_record=n
 f:tick(500,72,0)
 assert(f:has('NATIVE_SUCCESSOR_ADOPTED'),'E must use valid previous proof')
 assert(f:has('TRANSITION_EDGE_COMMITTED'),'E must use existing T1.6 commit')
end)
T('D-RT02 no pre-promotion evidence on cold start',function()
 local f=mk();f:tick(100,10,0)
 assert(not f:has('T2MOVE_D_SHADOW_CAPTURE'),'insufficient G1/geometry cannot certify')
end)
print('TOTAL '..pass..' PASS '..fail..' FAIL')
os.exit(fail==0 and 0 or 1)
