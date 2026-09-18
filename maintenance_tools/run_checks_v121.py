#!/usr/bin/env python3
from pathlib import Path
import shutil,subprocess,sys,json,os
ROOT=Path(__file__).resolve().parents[1]
def lua_cmd():
    for n in ('lua5.1','texlua','lua5.3','lua'):
        p=shutil.which(n)
        if p:return [p]
    p=shutil.which('luatex');return [p,'--luaonly'] if p else None
def main():
    out=(ROOT/'validation_v121');out.mkdir(parents=True,exist_ok=True);L=lua_cmd()
    if not L:raise SystemExit('No Lua host found')
    jobs=[
      ('release_check.txt',[sys.executable,'maintenance_tools/check_release_v121.py']),
      ('evidence_wiring_audit.txt',[sys.executable,'maintenance_tools/audit_evidence_wiring.py']),
      ('gate.txt',L+['tests/test_gate.lua','source/fresh_engagement_gate.lua']),
      ('gate103.txt',L+['tests/test_gate_v103.lua','source/fresh_engagement_gate.lua']),
      ('gate104.txt',L+['tests/test_gate_v104.lua','source/fresh_engagement_gate.lua']),
      ('handoff.txt',L+['tests/test_r1_v3_handoff.lua','source/r1_v3_handoff.lua']),
      ('recovery.txt',L+['tests/test_r1_v3_recovery.lua','source/r1_v3_recovery.lua']),
      ('contacts.txt',L+['tests/test_r1_v3_contacts.lua','source/r1_v3_contacts.lua']),
      ('second_charge.txt',L+['tests/test_r1_v3_second_charge.lua','source/better_shift_command.lua','tests/fixture.lua']),
      ('center_b2.txt',L+['tests/test_center_phase_b2.lua','source/better_shift_command.lua','tests/fixture.lua']),
      ('blocks.txt',L+['tests/test_v104_blocks.lua','source/better_shift_command.lua','tests/fixture.lua']),
      ('contracts.txt',L+['tests/test_contracts_v104.lua','source/better_shift_command.lua','tests/fixture.lua']),
      ('regressions.txt',L+['tests/test_regressions_v104.lua','source/better_shift_command.lua','tests/fixture.lua']),
      ('v107.txt',L+['tests/test_v107_regressions.lua','source/better_shift_command.lua','tests/fixture.lua']),
      ('v109.txt',L+['tests/test_v109_regressions.lua','source/better_shift_command.lua','tests/fixture.lua']),
      ('exec_identity_v3.txt',L+['tests/test_exec_identity_v3.lua','source/better_shift_command.lua','tests/fixture.lua']),
      ('tools.txt',[sys.executable,'tests/test_tools.py']),
      ('reverse.txt',[sys.executable,'tests/test_reverse_inventory.py']),
      ('mutations.txt',[sys.executable,'steering_tests/test_mutations_sc5.py'])]
    env=dict(os.environ);results=[]
    for name,cmd in jobs:
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,env=env)
        (out/name).write_text('$ '+' '.join(cmd)+'\n'+r.stdout+r.stderr,encoding='utf-8')
        results.append({'name':name,'exit_code':r.returncode});print(name,'PASS' if r.returncode==0 else 'FAIL')
        if r.returncode:print(r.stdout+r.stderr)
    status='PASS' if all(x['exit_code']==0 for x in results) else 'FAIL'
    (out/'checks_result.json').write_text(json.dumps({'variant':'BetterShiftCommand_v1.2.1','status':status,'steps':results},indent=2)+'\n')
    raise SystemExit(0 if status=='PASS' else 1)
if __name__=='__main__':main()
