#!/usr/bin/env python3
"""Fail-closed documentation navigation/status contract for BSC maintenance handoffs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(msg: str) -> None:
    print("FAIL:", msg)
    raise SystemExit(1)


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        fail("missing required documentation file: " + rel)
    return p.read_text(encoding="utf-8")


required = [
    "README_FIRST.md",
    "docs/MAINTAINER_INDEX.md",
    "docs/ARCHITECTURE_STATUS_20260927.md",
    "docs/OPEN_ISSUES.md",
    "docs/ASSUMPTION_LEDGER.md",
    "docs/TEST_MATRIX.md",
    "docs/CURRENT_BUILD_MAP.md",
    "docs/DECISION_LOG.md",
    "docs/VERSION_LINEAGE.md",
    "docs/PROVENANCE.md",
    "docs/HISTORY_COVERAGE.md",
    "docs/DEVELOPMENT_HISTORY.md",
    "docs/MAINTENANCE_PROTOCOL.md",
]
for rel in required:
    read(rel)

first = read("README_FIRST.md")
for token in (
    "Mandatory reading order",
    "docs/MAINTAINER_INDEX.md",
    "History is not current authority",
    "1.2.2-corepath-rc8",
    "16 command/packet hooks",
    "QUARANTINED",
    "Windows VS2019 v142 x64 + MASM BuildOnly",
):
    if token not in first:
        fail("README_FIRST missing contract token: " + token)

index = read("docs/MAINTAINER_INDEX.md")
for token in (
    "Document authority",
    "Current-state docs",
    "Historical narrative",
    "Do not count ContactPair as the 17th mandatory hook",
    "Do not interpret one bare `RCx` label",
):
    if token not in index:
        fail("MAINTAINER_INDEX missing rule: " + token)

hist = read("docs/DEVELOPMENT_HISTORY.md")
for token in (
    "HISTORICAL DOCUMENT — NOT CURRENT AUTHORITY",
    "Upstream behavior release:** Better Shift Command `v1.2.2`",
    "BSC-CONV-RC1 / BSC-CONV-RC2",
    "历史上曾作为生产物理证据",
):
    if token not in hist:
        fail("DEVELOPMENT_HISTORY missing supersession marker: " + token)
if "## 5. R4 Evidence V3：验证过的物理证据" in hist:
    fail("stale R4 title still presents historical physical evidence as current proof")

lineage = read("docs/VERSION_LINEAGE.md")
for token in ("BSC-CONV-RC2", "NATIVE-MAP-RC7", "COREPATH-RC8", "SMARTGUARD-RC2"):
    if token not in lineage:
        fail("VERSION_LINEAGE missing disambiguation token: " + token)

issues = read("docs/OPEN_ISSUES.md")
for token in (
    "Windows v142 + MASM BuildOnly",
    "WH3 CorePath runtime smoke",
    "KNOWN / ACCEPTED FOR RC8",
    "not release blockers",
):
    if token not in issues:
        fail("OPEN_ISSUES missing current-state token: " + token)

ledger = read("docs/ASSUMPTION_LEDGER.md")
if "`Entity +0x18 = MovementComponent*` | **RETRACTED**" not in ledger:
    fail("Assumption ledger lost the retracted Entity+0x18 status")

matrix = read("docs/TEST_MATRIX.md")
for token in ("Windows VS2019 v142 + MASM | PENDING", "WH3 CorePath runtime smoke | PENDING"):
    if token not in matrix:
        fail("TEST_MATRIX lost pending gate: " + token)

prov = read("docs/PROVENANCE.md")
if "RC7_PREBUILD_ORIGINAL.zip" not in prov:
    fail("PROVENANCE does not point to nested RC5/RC6 history")

coverage = read("docs/HISTORY_COVERAGE.md")
for token in ("BSC R1 / R2 | WEAK", "BSC-CONV-RC1 / RC2 | SUMMARY ONLY", "NESTED evidence"):
    if token not in coverage:
        fail("HISTORY_COVERAGE missing known archive gap: " + token)

# Active documentation must not re-declare the old v1.2.1 baseline as current.
active_docs = [p for p in (ROOT / "docs").glob("*.md")] + [ROOT / "README.md", ROOT / "README_FIRST.md"]
for p in active_docs:
    t = p.read_text(encoding="utf-8")
    if "Release: Better Shift Command `v1.2.1`" in t or "**Release:** Better Shift Command `v1.2.1`" in t:
        fail("stale current v1.2.1 baseline in " + str(p.relative_to(ROOT)))

print("PASS: documentation contract; current-state authority, version disambiguation, archive gaps, and RC8 pending gates are explicit")
