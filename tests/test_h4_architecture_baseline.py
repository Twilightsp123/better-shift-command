#!/usr/bin/env python3
"""Lock archived H4 code by native Git blob SHA-1; never modify release runtime."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/"archive/h4_soft_speed_20261009/ARCHITECTURE_LOCK.json").read_text(encoding="utf-8"))
assert manifest["stage"]=="H4_SPEED_FIRST_SOFT_WAYPOINT_ARCHITECTURE_FROZEN"
assert manifest["main_release_code_change"] is False
for rel,expected in manifest["archived_files"].items():
    data=(root/rel).read_bytes()
    hash=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    assert hash==expected["git_blob_sha1"],f"frozen H4 drift: {rel}: {hash}"
a=(root/"archive/h4_soft_speed_20261009/source/better_shift_command.lua").read_bytes()
b=(root/"archive/h4_soft_speed_20261009/src/better_shift_command.lua").read_bytes()
assert a==b,"H4 archived controller mirrors must be identical"
for marker in (b"function R1.H4SoftCornerCredit",b"H4_SOFT_WAYPOINT_ACCEPTED",
               b"H4_SOFT_CORNER_COMMITTED",b"H2_ROUTE_ISSUE_BLOCKED",
               b"NATIVE_FUTURE_OVERRUN",b"TRANSITION_EDGE_COMMITTED"):
    assert marker in a,marker
active=(root/"source/better_shift_command.lua").read_bytes()
assert b"function R1.H4SoftCornerCredit" not in active, "Main production source unexpectedly promoted"
print("PASS: H4 complete archived source, mirrors and Git blob hashes frozen; main runtime not promoted")
