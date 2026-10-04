#!/usr/bin/env python3
"""Verify canonical JSON -> generated C++ runtime map synchronization."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_native_header import render


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "native_maps" / "wh3_9.0.1_6c104a63.json"
DEFAULT_GENERATED = ROOT / "src" / "native_bridge" / "include" / "wh3" / "generated_native_map.hpp"
DEFAULT_CPP = ROOT / "src" / "native_bridge" / "src" / "platform_windows.cpp"
DEFAULT_HOST = ROOT / "src" / "native_bridge" / "src" / "bridge_host.cpp"


def fail(message: str) -> None:
    print("FAIL:", message)
    raise SystemExit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", type=Path, default=DEFAULT_MAP)
    ap.add_argument("--generated", type=Path, default=DEFAULT_GENERATED)
    ap.add_argument("--backend", type=Path, default=DEFAULT_CPP)
    ap.add_argument("--host", type=Path, default=DEFAULT_HOST)
    args = ap.parse_args()

    native_map = json.loads(args.map.read_text(encoding="utf-8"))
    generated = args.generated.read_text(encoding="utf-8")
    backend = args.backend.read_text(encoding="utf-8")
    host = args.host.read_text(encoding="utf-8")

    if native_map.get("schema") != 1:
        fail("map schema != 1")
    if len(native_map.get("core", {})) != 16:
        fail("canonical map must contain exactly 16 core hooks")
    if set(native_map.get("optional", {})) != {"contact_pair", "smart_guard"}:
        fail("optional site set drift")
    if generated != render(native_map):
        fail("generated_native_map.hpp is stale")

    for token in (
        '#include "wh3/generated_native_map.hpp"',
        "native_map::kExeSha256",
        "native_map::kCoreGuards",
        "native_map::kHookNames",
        "native_map::kContactPairGuard",
        "native_map::kSmartGuardGuard",
        "native_map::kMapId",
    ):
        if token not in backend:
            fail("backend missing generated-map binding: " + token)

    for forbidden in (
        "constexpr Guard guards[]={",
        "constexpr const char* hook_names[]={",
        'constexpr const char* exe_hash="',
    ):
        if forbidden in backend:
            fail("backend still owns duplicate native-map constant: " + forbidden)

    for token in (
        '#include "wh3/generated_native_map.hpp"',
        "native_map::kFullMoveVTable",
        "native_map::kAttackVTable",
    ):
        if token not in host:
            fail("bridge host missing generated-map binding: " + token)

    derived = native_map["derived"]
    full_move = int(derived["full_move_vtable"]["rva"], 0)
    simple_move = int(derived["simple_intercept_move_vtable"]["rva"], 0)
    if full_move == simple_move:
        fail("Full Move and Simple/Intercept Move VTables must differ")
    if derived["simple_intercept_move_vtable"].get("release_use") is not False:
        fail("Simple/Intercept Move VTable must remain release_use=false")

    print("PASS")
    print(f"map={native_map['map_id']}")
    print("core=16/16")
    print("optional=2/2")
    print("generated_header=SYNC")
    print("runtime_sources=JSON_BACKED")


if __name__ == "__main__":
    main()
