#!/usr/bin/env python3
"""R77 original-WH3 exact-EXE static guard only. No game process, Hook or patch."""
from pathlib import Path
import hashlib,json,struct,subprocess,re,sys
HERE=Path(__file__).resolve().parent
BASE=0x140000000
class Drift(ValueError):pass
def verify(path,m,check_disassembly=False):
 path=Path(path);data=path.read_bytes()
 if len(data)!=m["size"] or hashlib.sha256(data).hexdigest()!=m["sha256"]:
  raise Drift("EXACT_SHA_FAIL_CLOSED")
 if data[:2]!=b"MZ":raise Drift("MZ")
 p=struct.unpack_from("<I",data,0x3c)[0]
 if not 0x40<=p<0x1000 or data[p:p+4]!=b"PE\0\0":raise Drift("PE")
 if struct.unpack_from("<H",data,p+4)[0]!=0x8664 or struct.unpack_from("<H",data,p+24)[0]!=0x20b:raise Drift("AMD64")
 if struct.unpack_from("<Q",data,p+48)[0]!=BASE:raise Drift("IMAGEBASE")
 n=struct.unpack_from("<H",data,p+6)[0];opt=struct.unpack_from("<H",data,p+20)[0];ss=[]
 for j in range(n):
  o=p+24+opt+j*40
  _,r,size,raw=struct.unpack_from("<IIII",data,o+8)
  if raw+size>len(data):raise Drift("SECTION")
  ss.append((r,size,raw))
 def read(r,size):
  for start,length,raw in ss:
   if start<=r and r+size<=start+length:return data[raw+r-start:raw+r-start+size]
  raise Drift("RVA")
 edata,esize=struct.unpack_from("<II",data,p+24+112+3*8)
 funcs={}
 for i in range(esize//12):
  a,b,u=struct.unpack("<III",read(edata+12*i,12))
  funcs[a]=b
 for name,(a,b) in m["function_ranges"].items():
  if funcs.get(int(a,16))!=int(b,16):raise Drift("UNWIND_"+name)
 for site,item in m["pins"].items():
  r=int(site,16);by=bytes.fromhex(item["hex"]);a,b=m["function_ranges"][item["owner"]]
  if not (int(a,16)<=r and r+len(by)<=int(b,16)):raise Drift("OWNER_"+site)
  if read(r,len(by))!=by:raise Drift("OPCODE_"+site)
 for site,target in m["e8"].items():
  r=int(site,16);b=read(r,5)
  if b[0]!=0xe8 or r+5+struct.unpack_from("<i",b,1)[0]!=int(target,16):
   raise Drift("CALL_"+site)
 v=int(m["member_vtable"],16)+0x368
 if struct.unpack("<Q",read(v,8))[0]!=BASE+int(m["member_receiver"],16):
  raise Drift("MEMBER_TYPE")
 req={"030da52e":"4c8b99300b0000","030da556":"41ff5248",
      "030da561":"488b4728","030da565":"4c8d0476","030da569":"49c1e004",
      "030da572":"4c03442440","030da57c":"488b1cf0",
      "030da583":"450fb74822","030da59b":"ff9068030000",
      "030da5a1":"ffc6","030da5a3":"3b7724"}
 for a,h in req.items():
  if m["pins"][a]["hex"]!=h:raise Drift("INDEX_PAIR_"+a)
 if check_disassembly:
  rgx=re.compile(r"^\s*([0-9a-f]{8,16}):\s*((?:[0-9a-f]{2}\s+)+)\s+(.+?)\s*$",re.I)
  for owner,(a,b) in m["function_ranges"].items():
   raw=subprocess.check_output(["objdump","-d","-M","intel",
      f"--start-address={BASE+int(a,16)}",f"--stop-address={BASE+int(b,16)}",str(path)],text=True)
   starts={}
   for line in raw.splitlines():
    q=rgx.match(line)
    if q:starts[int(q.group(1),16)-BASE]=bytes.fromhex(q.group(2))
   for k,item in m["pins"].items():
    if item["owner"]==owner and starts.get(int(k,16))!=bytes.fromhex(item["hex"]):
     raise Drift("NOT_REAL_INSTRUCTION_START_"+k)
 return {"evidence":"CURRENT_EXE_STATIC_ONLY","opcode_sites":len(m["pins"]),"e8":len(m["e8"]),
   "unwind_functions":3,"member_vtable_slots":1,
   "index_pairing_in_conditional_A_fanout":True,
   "original_shift_A_branch_observed":False,"member_world_goal_verified":False,
   "native_gameplay_patch_authorized":False}
if __name__=="__main__":
 try:
  m=json.loads((HERE/"r77_slot_pins.json").read_text())
  print(json.dumps(verify(sys.argv[1],m,check_disassembly=True),indent=2))
 except (IndexError,OSError,ValueError,subprocess.CalledProcessError,struct.error) as e:
  print("FAIL_CLOSED",str(e));sys.exit(2)
