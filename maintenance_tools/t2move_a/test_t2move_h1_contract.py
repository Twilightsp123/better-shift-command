"""T2-MOVE-H1 source-preservation contract against sealed G.
The H1 shadow must not accidentally change actionable route/transaction logic.
"""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
G="580252224363c8d14fae1556ef15f4bee87e5377"
def git(*a):
    return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def section(s,a,b):
    assert a in s and b in s,(a,b)
    return s.split(a,1)[1].split(b,1)[0]
s=(ROOT/"source/better_shift_command.lua").read_text(encoding="utf-8")
mir=(ROOT/"src/better_shift_command.lua").read_text(encoding="utf-8")
tpl=(ROOT/"src/better_shift_command_selfcontained.template.lua").read_text(encoding="utf-8")
pure=(ROOT/"source/t2move_h1_route_obligation.lua").read_text(encoding="utf-8")
assert s==mir,"source/src mirrors diverged"
for a,b in [
 ("-- T2MOVE_H1_SHADOW_MODULE_BEGIN","-- T2MOVE_H1_SHADOW_MODULE_END"),
 ("function R1.H1ShadowObserve(","-- T1.6 Transition Transaction."),
 ("function R1.T2MoveEPreview(","function R1.TransitionPolicy.evaluate("),
 ("function Core.reconcile_native_successor(","local function advance(st,now)")
]:
    assert section(s,a,b)==section(tpl,a,b),("template region diverged",a)
assert pure in s,"standalone H1 implementation differs from embedded controller"
old=git("show",G+":source/better_shift_command.lua")
for a,b in [
 ("local CFG={","\nlocal bmgr,bridge"),
 ("local function route_handoff_ready(","-- T1.6 Transition Transaction."),
 ("function Core.commit_transition_edge(","function Core.observe_move_completion(")
]:
    legacy=section(old,a,b)
    if a=="local function route_handoff_ready(":
        h1_begin="-- H1 is read-only."
        now=section(s,a,h1_begin)
    else:now=section(s,a,b)
    assert legacy==now,("frozen authority differs",a)
changed=git("diff","--name-only",G,"HEAD").splitlines()
for forbidden in ("src/native_bridge/","release_artifacts/native/","docs/CURRENT_BUILD_MAP.md"):
    assert not any(f.startswith(forbidden) for f in changed),("native/address altered",forbidden)
for needle in (
 'R1.H1ShadowObserve(st,cur,nexta,"ISSUE",now,decision)',
 'local h1=R1.H1ShadowObserve(st,cur,nexta,"CURRENT",now,decision)',
 'cert.h1_shadow=h1',
 'H1_SHADOW_ADOPT',
 "authoritative=false"
):
    assert needle in s,("missing shadow proof",needle)
print("PASS H1 preserves G CFG, SC1 route policy, T1.6 commit, Native layer and mirrors")
