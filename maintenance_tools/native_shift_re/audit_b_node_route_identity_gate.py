#!/usr/bin/env python3
"""Exact original WH3 9.0.3: B route-node converter and reference invalidation.

SHA-pinned read-only proof. Tracks the *real* RDX = &node+0x20 across
0x0311BE18 -> no-unwind leaf 0x03037A48 and into 0x030FDA9C.
Separates B node list manager+0x2D0 from other manager+0x2F8 list,
and three neighboring but DIFFERENT B-family task vtables.
This does not prove a real Shift instance used the branch or fix crowding.
"""
import argparse, json, re, shutil, struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
PINS={int(a,16):bytes.fromhex(b) for a,b in (ln.split() for ln in """
0311BE1C 8b4148
0311BE1F 83f8ff
0311BE22 751b
0311BE24 488b01
0311BE2C 488b4108
0311BE30 488b80100a0000
0311BE37 488bc8
0311BE3A e809bcf1ff
0311BE3F 4883c428
03037A48 488b8198000000
03037A4F 4885c0
03037A52 740d
03037A54 83780400
03037A58 7507
03037A5A 8b81a4000000
03037A60 c3
03037A61 8b8184010000
03037A67 c3
03128EA8 488bbbf0010000
03128F1D e8524fffff
03129031 488bbbd0020000
03129055 488b7718
03129059 44396704
03129078 44386708
0312907C 7524
0312907E 488d5720
03129082 488bca
03129085 e88e2dffff
0312908A 85c0
0312908C 7414
0312908E 488d4b18
03129092 e8054afdff
03129097 48894770
0312909B 4103ed
0312909E 44886f08
031290A2 44386f08
031290C0 488bbb88020000
031291A4 e82b0cfeff
03121A25 6683630800
03121A39 c7430401000000
03121A40 e8a7affcff
03121A45 4883637000
03121A91 488d4f18
03121A95 488d5320
03121A99 e8febffdff
03121A9E 48894370
03121AA2 c6430801
03121B29 4c8b87d8020000
03121B3B 48896c2420
03121B40 e8cbaffcff
03121B4B 4883bfd0020000
03121B55 488987d0020000
03121B6B 488987d8020000
030ECB2E 66c741080100
030ECB34 4c894110
030ECB41 488b4c2478
030ECB4B 4c894b70
030ECB66 488b9158010000
030ECB98 e847160100
030ECBA2 48894370
03281408 4053
03281411 488b4958
03281426 e819000000
03281444 4053
03281454 488b4958
0328145D 80790800
03281469 488b4970
0328146D e8aed5e5ff
03281472 84c0
03281476 488b4358
0328147D 014804
03281480 4883635800
03281485 488b4320
0328148C 4883632000
03281497 48837b5800
0328149E 488b4320
032814A7 4883b858010000
032814AF 7466
032814B1 488d542420
032814FB e8bc05eaff
03281500 48894358
03281504 c6436000
0328150A e8a104eaff
0328150F 48894358
030DEA2A 4883797800
030DEA34 488b7910
030DEA38 8b410c
030DEA44 488b0f
030DEA4B 488b01
030DEA4E 4c8b4810
030DEA55 488b9060010000
030DEA5C 41ffd1
030DEA5F 483b4378
030DEA63 7521
030DEA79 32c0
030DEA86 b001
03109DEF 483991f8020000
03109E17 4c8b7270
03109E20 498b5e08
03109E24 498bce
03109E2C 488b8620030000
03109E33 498906
03109E36 4c89b620030000
03109E45 488bcf
0328153D 488b4178
03281554 488b4070
0328155D 488b5118
032815CA 488bc8
032815D1 488b01
030FDAC7 488b0a
030FDAEA f30f10773c
030FDB02 498bce
030FDB08 e8bff50100
03263ACF 488d0552c68700
""".strip().splitlines())}
# Extra original EXE guards for route-object +0x78 writer / consumer
PINS.update({int(a,16):bytes.fromhex(b) for a,b in (ln.split() for ln in """
030FE1F3 488bf9
030FE206 4c8bd0
030FE272 e8653dfcff
030FE277 488bf8
030FE280 488d5318
030FE284 488bcf
030FE287 e8cc95fcff
030FE28C 488b5b08
030FE290 4885db
030FE293 75eb
030FE29A 488bc7
030C7868 83790c00
030C786F 488bd9
030C788C e8774b0500
030C7895 488d5358
030C78AA 488b8860010000
030C78B1 e8d2570600
030C78BE 488d4818
030C78C5 ff5210
030C78C8 3c01
030C78CC 488b4740
030C78D0 48894378
030C78D4 488bce
030C78D7 e8a8910000
030C78EA e845db25fe
""".strip().splitlines())})
PINS[0x030C78CA]=bytes.fromhex('7508')
LEAF=(0x03037A48,0x03037A68)
CALLS={
 0x03128F1D:0x0311DE74,
 0x03129085:0x0311BE18,
 0x03129092:0x030FDA9C,
 0x0311BE3A:0x03037A48,
 0x03121A99:0x030FDA9C,
 0x030ECB98:0x030FE1E4,
 0x03281426:0x03281444,
 0x0328146D:0x030DEA20,
 0x032814FB:0x03121ABC,
 0x0328150A:0x031219B0,
 0x031291A4:0x03109DD4,
 0x030FE272:0x030C1FDC, 0x030FE287:0x030C7858,
 0x030C788C:0x0311C408, 0x030C78B1:0x0312D088,
 0x030C78D7:0x030D0A84, 0x030C78EA:0x01325434,
}
TYPED_TASK_SLOTS={
 0x03AE00E8+0x10:0x03281520,
 0x03AE0108+0x10:0x03281600,
 0x03AE0128+0x10:0x03281408,
}
BRANCHES={
 0x0312907C:0x031290A2,
 0x0312908C:0x031290A2,
 0x03281474:0x03281493,
 0x032814AF:0x03281517,
 0x030DEA63:0x030DEA86,
 0x032814F9:0x0328150A,
 0x030C78CA:0x030C78D4,
 0x030FE293:0x030FE280,
}
LEAF_RET=(0x03037A60,0x03037A67)

def opcode_starts(pe):
 if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
 cache={}
 for site,expected in PINS.items():
  if pe.read(site,len(expected),True)!=expected:
   raise ValueError('NATIVE_OPCODE_CHANGED:'+hex(site))
  owner=pe.function(site)
  if owner is None and LEAF[0]<=site<LEAF[1]:owner=LEAF
  if owner is None:raise ValueError('UNVERIFIED_FUNCTION_BOUNDARY:'+hex(site))
  if owner not in cache:
   body=pe.disasm(owner[0],owner[1]-owner[0])
   cache[owner]={int(m.group(1),16):m.group(2).strip() for line in body.splitlines()
    if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+([^\n]*)',line))}
  if site not in cache[owner]:raise ValueError('MID_INSTRUCTION:'+hex(site))
 return cache

def read_branch_target(pe,site):
 raw=pe.read(site,2,True)
 if raw[0] not in (0x72,0x74,0x75):raise ValueError('EXPECTED_SHORT_JCC:'+hex(site))
 return site+2+struct.unpack_from('<b',raw,1)[0]

def _assert_rdx_survival(val_ops,leaf_ops,post_ops):
 """Conservatively forbid ANY RDX/EDX/DX/DL access/call in these bodies.

 The validator has one expected E8 to the separately checked leaf.
 We don't rely on ABI volatility assumptions or the existing PIN subset.
 """
 rd=re.compile(r'\b(?:rdx|edx|dx|dl)\b',re.I)
 for ins in (val_ops+leaf_ops+post_ops):
  if rd.search(ins):raise ValueError('RDX_PROPAGATION_UNPROVEN:'+ins)
 if any(re.search(r'\bcall\b|\bjmp\s+QWORD\b',i,re.I) for i in leaf_ops):
  raise ValueError('TYPE_VALIDATION_LEAF_NOT_LEAF')
 if sum(bool(re.search(r'\bcall\b',x,re.I)) for x in val_ops)!=1:
  raise ValueError('VALIDATOR_GAINED_CALL')
 if any(re.search(r'\bcall\b',x,re.I) for x in post_ops):
  raise ValueError('BETWEEN_VALIDATOR_AND_CONVERTER_HAS_CALL')
 return True

def rdx_provenance(pe, cache):
 # Pinned contiguous true leaf with TWO ret instructions and no calls.
 # Full decoded bodies matter because x64 calls may clobber RDX.
 validator=cache[pe.function(0x0311BE18)]
 leaf=cache[LEAF]
 manager=cache[pe.function(0x03129085)]
 val_ops=[asm for at,asm in validator.items() if 0x0311BE18<=at<0x0311BE44]
 leaf_ops=[asm for at,asm in leaf.items() if LEAF[0]<=at<LEAF[1]]
 post_ops=[asm for at,asm in manager.items() if 0x0312908A<=at<0x03129092]
 if tuple(at for at in LEAF_RET if leaf.get(at)!='ret'):
  raise ValueError('UNWIND_FREE_LEAF_RET_DRIFT')
 _assert_rdx_survival(val_ops,leaf_ops,post_ops)
 if pe.read(0x0312907E,4,True)!=bytes.fromhex('488d5720'):
  raise ValueError('NODE_SUBOBJECT_LEA_MISSING')
 if pe.read(0x030FDAC7,3,True)!=bytes.fromhex('488b0a'):
  raise ValueError('CONVERTER_NOT_READING_RDX')
 # The converter must not clobber RDX before its first dereference.
 conv=cache[pe.function(0x030FDAC7)]
 pre_read=[ins for at,ins in conv.items() if 0x030FDA9C<=at<0x030FDAC7]
 if any(re.search(r'\b(?:rdx|edx|dx|dl|call)\b',ins,re.I) for ins in pre_read):
  raise ValueError('CONVERTER_RDX_PRE_READ_CHANGED')
 return len(val_ops),len(leaf_ops),len(post_ops)

def synthetic_branch(*,big_task_ref, existing_node, old_subtask, reference_changed, node_valid=True, checkpoint_checked=False):
 """Bounded native-condition illustration; not a physical motion simulation."""
 big=bool(big_task_ref); node=bool(existing_node); checked=bool(checkpoint_checked)
 if big and node and node_valid and not checked:
  if reference_changed:
   node=False;big=False
  else:
   checked=True
 if node:return 'RETAIN_EXISTING_NODE'
 if big and not old_subtask:return 'WAIT_FOR_OLD_SUBTASK'
 return 'CREATE_TASK_AWARE_NODE' if big else 'CREATE_GENERIC_NODE'

def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  if pe.sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH')
  cache=opcode_starts(pe)
  for site,target in CALLS.items():
   data=pe.read(site,5,True)
   if data[0]!=0xe8 or site+5+struct.unpack_from('<i',data,1)[0]!=target:
    raise ValueError('CALL_TARGET_CHANGED:'+hex(site))
  for site,target in BRANCHES.items():
   if read_branch_target(pe,site)!=target:raise ValueError('CONDITION_TARGET_CHANGED:'+hex(site))
  for slot,target in TYPED_TASK_SLOTS.items():
   ptr=struct.unpack('<Q',pe.read(slot,8))[0]
   if ptr!=pe.base+target:raise ValueError('OTHER_TASK_VTABLE_MIXED:'+hex(slot))
  at=0x03263ACF
  lea=pe.read(at,7,True)
  if lea[:3]!=bytes.fromhex('488d05') or at+7+struct.unpack_from('<i',lea,3)[0]!=0x03AE0128:
   raise ValueError('THIRD_SUBCLASS_CONSTRUCTOR_CHANGED')
  # All three vtable +0x10 slots resolve to DIFFERENT functions.
  if len(set(TYPED_TASK_SLOTS.values()))!=3:raise ValueError('VTABLE_TYPE_COLLAPSE')
  val_count,leaf_count,post_count=rdx_provenance(pe,cache)
  # This is a DIFFERENT linked list, with +0x70 a structurally similar field;
  # it cannot be silently substituted for B node list manager+0x2D0.
  if PINS[0x03129031]!=bytes.fromhex('488bbbd0020000') or PINS[0x031290C0]!=bytes.fromhex('488bbb88020000'):
   raise ValueError('MANAGER_LINKED_LIST_TYPE_COLLAPSED')
  if PINS[0x03109DEF]!=bytes.fromhex('483991f8020000'):
   raise ValueError('RETIREMENT_DIFFERENT_LIST_COLLAPSED')
  return dict(schema='bsc.n1.exact_B_node_rdx_converter_and_ref_invalidation.v1',
   original_exe_sha256=pe.sha,proof='EXACT_ORIGINAL_EXE_STATIC',
   opcode_instruction_starts=len(PINS),unwind_or_explicit_leaf_owners=len(cache),
   direct_calls=len(CALLS),checked_JCC_destinations=len(BRANCHES),
   distinct_typed_vtable_slots=len(TYPED_TASK_SLOTS),
   validator_instruction_count=val_count,pinned_leaf_instruction_count=leaf_count,
   between_calls_instructions=post_count,
   rdx_retained_after_validator_on_checked_path=True,
   converter_argument='&node+0x20, NOT pointer to bigTask+0x160',
   converter_result='node+0x70; flag node+0x08=1',
   big_task_aware_node_flag='constructor 0x030ECB10 sets node+0x08=1',
   common_node_flag='constructor 0x031219B0 initially node+0x08=0',
   task_aware_valid_node_skips_manager_converter=True,
   B_aux_ref_check='0x03281444 uses aux+0x58 -> node+0x70 -> 0x030DEA20',
   node_route_ref_writer='0x030FE1E4 -> 0x030C7858; after native +0x10 gate route+0x78 = derived ref',
   node_route_ref_provenance='0x030FE1E4 keeps returned geometry object in RDI; child append call uses RCX=RDI and returns RDI',
   B_reference_lifecycle='route+0x78 constructed conditionally, later compared against route child virtual lookup',
   checked_conversion_writer_consumer_same_object_type=True,
   B_aux_on_reference_mismatch='drop node and big task refs; next creation can select generic node',
   reference_checker_compares='computed route lookup against route+0x78',
   reference_checker_vtable_plus160_is_method_pointer_NOT_task_field=True,
   other_2F8_list_retirement_is_NOT_B_2D0_node_consumption=True,
   sibling_0x03281520_reads_different_typed_task_route=True,
   B_node70_to_motor_goal_proven=False,player_SHIFT_instance_branch_proven=False,
   physical_crowding_cause_proven=False,native_patch_authorized=False)
 finally:pe.close()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error('NEVER_OVERWRITE_EXE')
 r=audit(a.exe)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('PASS',r['opcode_instruction_starts'],'native opcodes,',r['direct_calls'],'E8,',r['distinct_typed_vtable_slots'],'typed vtables; NO PATCH')
