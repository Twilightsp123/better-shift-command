#!/usr/bin/env python3
"""Verify that the canonical native map matches current runtime source.

This is the migration guard for Phase 1. The JSON map becomes the address-pipeline
source of truth, but until C++ generation is introduced the current backend still
contains compiled-in constants. This checker prevents those two representations
from silently diverging.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "native_maps" / "wh3_9.0.1_6c104a63.json"
DEFAULT_CPP = ROOT / "src" / "native_bridge" / "src" / "platform_windows.cpp"
DEFAULT_HOST = ROOT / "src" / "native_bridge" / "src" / "bridge_host.cpp"


def fail(message: str) -> None:
    print("FAIL:", message)
    raise SystemExit(1)


def parse_backend(text: str) -> tuple[str, dict[str, tuple[int, str]], dict[str, tuple[int, str]]]:
    locked = re.search(r'constexpr const char\* exe_hash="([a-f0-9]{64})"', text)
    block = re.search(r"constexpr\s+Guard\s+guards\[\]\s*=\s*\{(.*?)\};", text, re.S)
    names_block = re.search(
        r"constexpr const char\* hook_names\[\]\s*=\s*\{(.*?)\};", text, re.S
    )
    if not locked or not block or not names_block:
        fail("backend anchor inventory not recognized")

    guards = re.findall(
        r'\{\s*(0x[0-9a-fA-F]+)\s*,\s*"([0-9a-fA-F]+)"\s*\}',
        block.group(1),
    )
    names = re.findall(r'"([^"]+)"', names_block.group(1))
    if len(guards) != 16 or len(names) != 16:
        fail(f"expected 16 core hooks, got {len(guards)} guards/{len(names)} names")

    core = {
        name: (int(rva, 16), guard.lower())
        for name, (rva, guard) in zip(names, guards)
    }

    optional: dict[str, tuple[int, str]] = {}
    for logical_name, symbol in (
        ("contact_pair", "contact_pair_guard"),
        ("smart_guard", "smart_guard_guard"),
    ):
        match = re.search(
            rf'constexpr\s+Guard\s+{symbol}\s*\{{\s*(0x[0-9a-fA-F]+)\s*,\s*"([0-9a-fA-F]+)"\s*\}}',
            text,
        )
        if not match:
            fail(f"missing {symbol}")
        optional[logical_name] = (int(match.group(1), 16), match.group(2).lower())

    return locked.group(1), core, optional


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--backend", type=Path, default=DEFAULT_CPP)
    parser.add_argument("--host", type=Path, default=DEFAULT_HOST)
    args = parser.parse_args()

    native_map = json.loads(args.map.read_text(encoding="utf-8"))
    backend = args.backend.read_text(encoding="utf-8")
    host = args.host.read_text(encoding="utf-8")
    exe_hash, source_core, source_optional = parse_backend(backend)

    if native_map.get("schema") != 1:
        fail("map schema != 1")
    if native_map.get("game", {}).get("sha256", "").lower() != exe_hash:
        fail("map EXE SHA differs from platform_windows.cpp")

    map_core = native_map.get("core", {})
    if set(map_core) != set(source_core):
        fail(f"core name set differs: map={sorted(map_core)} source={sorted(source_core)}")

    for name, (rva, guard) in source_core.items():
        spec = map_core[name]
        if int(spec["rva"], 0) != rva:
            fail(f"{name}: RVA differs")
        if spec["guard"].lower() != guard:
            fail(f"{name}: guard differs")
        if spec.get("required") is not True:
            fail(f"{name}: core site must be required=true")

    map_optional = native_map.get("optional", {})
    if set(map_optional) != set(source_optional):
        fail(
            f"optional name set differs: map={sorted(map_optional)} source={sorted(source_optional)}"
        )
    for name, (rva, guard) in source_optional.items():
        spec = map_optional[name]
        if int(spec["rva"], 0) != rva:
            fail(f"{name}: optional RVA differs")
        if spec["guard"].lower() != guard:
            fail(f"{name}: optional guard differs")
        if spec.get("required") is not False:
            fail(f"{name}: optional site must be required=false")

    derived = native_map.get("derived", {})
    move_vt = int(derived["full_move_vtable"]["rva"], 0)
    attack_vt = int(derived["attack_vtable"]["rva"], 0)
    expected_outcome = (
        f"f.kind==Kind::Move?0x{move_vt:08X}:0x{attack_vt:08X}"
    ).lower()
    compact_host = re.sub(r"\s+", "", host).lower()
    if expected_outcome not in compact_host:
        fail("Move/Attack outcome VTable pair differs from bridge_host.cpp")

    old_move = int(derived["simple_intercept_move_vtable"]["rva"], 0)
    if old_move == move_vt:
        fail("Simple/Intercept Move VTable must not equal top-level Full Move VTable")
    if derived["simple_intercept_move_vtable"].get("release_use") is not False:
        fail("Simple/Intercept Move VTable must remain release_use=false")

    print("PASS")
    print(f"map={native_map['map_id']}")
    print("core=16/16")
    print("optional=2/2")
    print("source_cpp=SYNC")
    print("outcome_vtables=SYNC")


if __name__ == "__main__":
    main()
