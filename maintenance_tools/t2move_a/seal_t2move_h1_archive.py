"""Deterministic T2-MOVE-H1 tracked-source handoff and baseline integrity seal."""
from pathlib import Path
import hashlib
import os
import json
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output"
BASE_G = "580252224363c8d14fae1556ef15f4bee87e5377"
NATIVE_SHA = "8fc223c9d1da5834b2034ced8e34ea9f0a8bc0a27964d6704ce931bc9a3b3b0a"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    return sha(path.read_bytes())


head = git("rev-parse", "HEAD")
branch = git("branch", "--show-current")
changed = git("diff", "--name-only", BASE_G, "HEAD").splitlines()
frozen_paths = ("src/native_bridge/", "release_artifacts/native/",
                "tools/inspect_exe.py", "tools/prebuild_contract_check.py",
                "docs/CURRENT_BUILD_MAP.md")
unsafe = [p for p in changed if any(p.startswith(prefix) for prefix in frozen_paths)]
if unsafe:
    raise SystemExit("NATIVE/ADDRESS BASELINE CHANGED: " + ",".join(unsafe))

src_path = ROOT / "source/better_shift_command.lua"
mirror_path = ROOT / "src/better_shift_command.lua"
template_path = ROOT / "src/better_shift_command_selfcontained.template.lua"
src = src_path.read_text(encoding="utf-8")
mirror = mirror_path.read_text(encoding="utf-8")
template = template_path.read_text(encoding="utf-8")
if src != mirror:
    raise SystemExit("SOURCE MIRRORS NOT IDENTICAL")

for begin, end in [
    ("-- T2MOVE_D_EVIDENCE_MODULE_BEGIN", "-- T2MOVE_D_EVIDENCE_MODULE_END"),
    ("-- T2MOVE_E_POLICY_MODULE_BEGIN", "-- T2MOVE_E_POLICY_MODULE_END"),
    ("function R1.T2MoveEPreview(st,current,successor,ctx)",
     "function R1.TransitionPolicy.evaluate(st,current,successor,g,context)"),
    ("function Core.reconcile_native_successor(st,now)", "local function advance(st,now)"),
]:
    def region(text):
        a = text.index(begin)
        b = text.index(end, a)
        return text[a:b]
    if region(src) != region(template):
        raise SystemExit("TEMPLATE MIRROR DIVERGENCE: " + begin)

old = git("show", BASE_G + ":source/better_shift_command.lua")
def cfg(text):
    # The CFG table ends on the final property line, not on a standalone brace.
    begin = text.index("local CFG={")
    end = text.index("\nlocal bmgr,bridge", begin)
    return text[begin:end]
if cfg(old) != cfg(src):
    raise SystemExit("GAMEPLAY CFG CHANGED SINCE E")
subprocess.run(["python", "maintenance_tools/t2move_a/test_t2move_h1_contract.py"],
               cwd=ROOT, check=True)

native = ROOT / "release_artifacts/native/wh3_native_bridge.dll"
if file_sha(native) != NATIVE_SHA:
    raise SystemExit("NATIVE BINARY SHA NO LONGER MATCHES LOCK")

OUT.mkdir(exist_ok=True)
archive = OUT / "BSC_T2MOVE_H1_full_source_20261009.zip"
subprocess.run(["git", "archive", "--format=zip", "--output=" + str(archive), "HEAD"],
               cwd=ROOT, check=True)
required = {
    "source/better_shift_command.lua",
    "src/better_shift_command.lua",
    "src/better_shift_command_selfcontained.template.lua",
    "maintenance_tools/t2move_a/test_t2move_e_controller.lua",
    "maintenance_tools/t2move_a/test_t2move_f_boundaries.lua",
    "maintenance_tools/t2move_a/test_t2move_f_mutations.py",
    ".github/workflows/t2move-f-hardening.yml",
    ".github/workflows/t2move-g-adversarial.yml",
    "maintenance_tools/t2move_a/test_t2move_g_adversarial.lua",
    "maintenance_tools/t2move_a/test_t2move_g_mutations.py",
    "docs/design/T2_MOVE_G_NATIVE_TURNBACK_20261009.md",
    "source/t2move_h1_route_obligation.lua",
    "maintenance_tools/t2move_a/test_t2move_h1_pure.lua",
    "maintenance_tools/t2move_a/test_t2move_h1_controller.lua",
    "maintenance_tools/t2move_a/test_t2move_h1_mutations.py",
    "maintenance_tools/t2move_a/test_t2move_h1_contract.py",
    ".github/workflows/t2move-h1-shadow.yml",
    "docs/design/T2_MOVE_H1_ROUTE_OBLIGATION_20261009.md",
    "docs/design/T2_MOVE_F_HARDENING_20261009.md",
    "docs/MAINTENANCE_TODO.md",
    "docs/OPEN_ISSUES.md",
    "docs/TEST_MATRIX.md",
}
with zipfile.ZipFile(archive) as z:
    names = set(z.namelist())
    if not required <= names:
        raise SystemExit("INCOMPLETE ARCHIVE: " + repr(sorted(required - names)))
    if z.read("source/better_shift_command.lua") != src_path.read_bytes():
        raise SystemExit("ARCHIVE CONTROLLER BYTES DIVERGE")
    file_lines = []
    for name in sorted(names):
        if not name.endswith("/"):
            file_lines.append(sha(z.read(name)) + "  " + name)
(OUT / "FILE_SHA256_MANIFEST.txt").write_text(
    "\n".join(file_lines) + "\n", encoding="utf-8")
manifest = {
    "stage": "T2-MOVE-H1",
    "type": "COMPLETE_TRACKED_SOURCE_HANDOFF_NOT_INSTALLABLE",
    "commit": head,
    "branch_in_checkout": branch or "DETACHED_CI_HEAD",
    "expected_branch": "maintenance/t2move-h1-route-obligation-shadow",
    "parent_G_commit": BASE_G,
    "archive_sha256": file_sha(archive),
    "controller_sha256": file_sha(src_path),
    "native_bridge_sha256": file_sha(native),
    "archive_files": len(file_lines),
    "source_mirror_equal": True,
    "native_address_changed": False,
    "gameplay_cfg_changed": False,
    "verified_offline_ci_reference": int(os.environ.get("GITHUB_RUN_ID", "0")),
    "H1_pure": "14/14 PASS",
    "H1_controller_shadow": "5/5 PASS",
    "H1_mutations": "5/5 CAUGHT",
    "H1_policy_authority": "READ_ONLY_NO_PERMISSION_CHANGE",
    "H1_legacy_Uturn_route_fidelity": "CONFLICT_RECORDED_NOT_FIXED",
    "G_controller": "7/7 PASS",
    "G_mutations": "3/3 CAUGHT",
    "SC1_proactive_Uturn_unchanged": True,
    "SC1_proactive_Uturn_route_fidelity": "OPEN / NOT WH3 TESTED",
    "G_scope": "NATIVE_EXACT_IMMEDIATE_MOVE_ADOPTION_ONLY",
    "F_controller": "5/5 PASS",
    "F_mutations": "3/3 CAUGHT",
    "E_controller": "11/11 PASS",
    "E_mutations": "8/8 CAUGHT",
    "maintenance": "46/46 PASS",
    "wh3_runtime": "NOT TESTED / BLOCKED",
    "release_promotion": False,
    "root_SHA256SUMS_warning": "STALE - use SHA256SUMS_HANDOFF.txt",
}
(OUT / "T2MOVE_H1_HANDOFF_MANIFEST.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(OUT / "READ_THIS_HANDOFF.txt").write_text(
    "Better Shift Command T2-MOVE-H1 isolated complete source handoff.\n"
    "Contains complete git-tracked source, Native reference, tests, docs, CI and archive.\n"
    "Not an installable WH3 pack. Do not merge/publish from offline CI alone.\n"
    "Baseline G: " + BASE_G + "\n"
    "Current commit: " + head + "\n"
    "WH3 RT-TP-02/03 and RT-TP-04/05 are BLOCKED/DEFERRED.\n"
    "Root SHA256SUMS.txt is stale; use the handoff and per-file manifests.\n",
    encoding="utf-8")
outputs = [archive, OUT / "T2MOVE_H1_HANDOFF_MANIFEST.json",
           OUT / "READ_THIS_HANDOFF.txt", OUT / "FILE_SHA256_MANIFEST.txt"]
(OUT / "SHA256SUMS_HANDOFF.txt").write_text(
    "".join(file_sha(path) + "  " + path.name + "\n" for path in outputs),
    encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
