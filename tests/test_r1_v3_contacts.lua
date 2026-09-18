local C=assert(loadfile(assert(arg[1])))()
local p,f=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then p=p+1;print('PASS '..n)else f=f+1;print('FAIL '..n..' :: '..tostring(e))end end
local function ev(s,t,a,b,ea,eb,sa,sb)return {serial=s,tick_ms=t,uid_a=a,uid_b=b,entity_a=ea,entity_b=eb,active_a=sa~=nil,active_b=sb~=nil,active_engine_seq_a=sa,active_engine_seq_b=sb}end
T('consume advances exact string cursor',function()local c=C.new();local x,w=C.consume(c,{ev('1','100','10','20','1000','2000','77','88')},{gap=false,complete=true,next_after='1'});assert(w=='OK' and #x==1 and c.after=='1')end)
T('gap is fail closed',function()local c=C.new();local x,w=C.consume(c,{}, {gap=true,complete=false,next_after='0'});assert(x==nil and w=='JOURNAL_GAP' and c.after=='0')end)
T('serial reversal rejected',function()local c=C.new();local x,w=C.consume(c,{ev('2','100','10','20','1000','2000','77','88'),ev('1','110','10','20','1001','2001','77','88')},{gap=false,complete=true,next_after='2'});assert(x==nil and w=='SERIAL_NOT_STRICT')end)
T('tick reversal rejected across pages',function()local c=C.new();assert(C.consume(c,{ev('1','200','10','20','1000','2000','77','88')},{gap=false,complete=true,next_after='1'}));local x,w=C.consume(c,{ev('2','199','10','20','1001','2001','77','88')},{gap=false,complete=true,next_after='2'});assert(x==nil and w=='TICK_REVERSED')end)
T('attack match requires own cohort entity target and exact order',function()local e=ev('9','500','10','20','1000','2000','77','88');assert(C.match_for_attack(e,'10','20','77',{['1000']=true}));assert(not C.match_for_attack(e,'10','20','78',{['1000']=true}));assert(not C.match_for_attack(e,'10','21','77',{['1000']=true}));assert(not C.match_for_attack(e,'10','20','77',{['1001']=true}))end)
T('reverse pair orientation matches symmetrically',function()local e=ev('9','500','20','10','2000','1000','88','77');assert(C.match_for_attack(e,'10','20','77',{['1000']=true}))end)
print('TOTAL '..p..' PASS '..f..' FAIL');os.exit(f==0 and 0 or 1)
