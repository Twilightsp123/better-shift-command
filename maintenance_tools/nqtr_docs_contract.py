#!/usr/bin/env python3
"""Documentation-only NQTR migration, old-byte preservation and safe default read order."""
from pathlib import Path
import re, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
BASE="e711e716f2411599d75184618fc1ee5cb85bcd54"
def git(*args):
    p=subprocess.run(["git",*args],cwd=ROOT,capture_output=True,check=True)
    return p.stdout
def historical(path):
    return git("show",BASE+":"+path)
def check_file(src,dst):
    old=historical(src)
    new=(ROOT/dst).read_bytes()
    assert old==new,(src,"historical bytes changed")
    assert not (ROOT/src).exists(),(src,"obsolete document still in active location")
old_docs=[p.decode() for p in git("ls-tree","-r","--name-only",BASE,"docs/").splitlines()
          if p and b"/past_doc/" not in p and b"/current/" not in p]
root_docs=["README_FIRST.md","README.md","BUILD_WINDOWS.md","CHANGELOG.md","COREPATH_CHANGELOG.md"]
for path in old_docs:check_file(path,"docs/past_doc/"+path[5:])
for path in root_docs:
    assert historical(path)==(ROOT/"docs/past_doc/root"/path).read_bytes(),path
for path in root_docs[2:]:
    assert not (ROOT/path).exists(),(path,"old root doc not archived")
cur=ROOT/"docs/current"
names=["README.md","PRODUCT_CONTRACT.md","CURRENT_BASELINE.md","NATIVE_RESEARCH_MAP.md",
       "TARGET_ARCHITECTURE.md","IMPLEMENTATION_PLAN.md","VERIFICATION.md",
       "RISKS_AND_DECISIONS.md","MAINTENANCE_RULES.md"]
for name in names:
    p=cur/name
    assert p.is_file() and p.stat().st_size>=500,("missing or incomplete current",name)
start=(cur/"README.md").read_text(encoding="utf-8")
for name in names[1:]:
    assert f"]({name})" in start,("broken current navigation",name)
plan=(cur/"IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
for n in range(7):assert f"Stage {n}" in plan,("plan stage missing",n)
for name in ("README_FIRST.md","README.md","docs/README.md"):
    assert "docs/current" in (ROOT/name).read_text(encoding="utf-8"),name
archive_index=(ROOT/"docs/past_doc/README.md").read_text(encoding="utf-8")
assert archive_index.count("| docs/")>=len(old_docs)-2
assert len(old_docs)==54 and len(root_docs)==5,("baseline archive inventory changed",len(old_docs))
# The only permitted source-tree modifications in a docs-only migration are
# docs and two contracts that explicitly validate/pack the archived docs.
approved={"README_FIRST.md","README.md","BUILD_WINDOWS.md","CHANGELOG.md","COREPATH_CHANGELOG.md",
          "maintenance_tools/check_documentation_contract.py",
          "maintenance_tools/t2move_a/seal_h4_soft_902.py",
          "maintenance_tools/nqtr_docs_contract.py",".github/workflows/nqtr-docs.yml"}
changed=[p.decode() for p in git("diff","--name-only",BASE,"HEAD").splitlines()]
unexpected=[p for p in changed if not (p.startswith("docs/") or p in approved)]
assert not unexpected,("non-doc gameplay/code files changed",unexpected)
# Only link paths written in the active doc tree and top-level readmes must work;
# archived documentation keeps its original bytes, including original links.
for file in [ROOT/"README_FIRST.md",ROOT/"README.md",ROOT/"docs/README.md",*cur.glob("*.md")]:
    s=file.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)",s):
        if target.startswith(("http://","https://","#","mailto:")):continue
        clean=target.split("#",1)[0]
        if clean and not (file.parent/clean).exists():
            raise AssertionError((str(file.relative_to(ROOT)),"broken link",target))
print("PASS NQTR docs-only migration: 54 docs + 5 root docs original blobs byte-identical")
print("PASS NQTR current nav, 7-stage plan, links, no Native/Lua/gameplay modifications")
print("PASS NQTR historical source manifest and current-doc authority separation")
