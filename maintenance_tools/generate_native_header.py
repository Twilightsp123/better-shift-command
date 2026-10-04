#!/usr/bin/env python3
"""Render the runtime C++ native-map header from one canonical JSON map."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def cpp_hex(value: str | int) -> str:
    n = value if isinstance(value, int) else int(value, 0)
    return f"0x{n:08X}"


def render(native_map: dict) -> str:
    core = native_map["core"]
    if len(core) != 16:
        raise ValueError("runtime map requires exactly 16 mandatory core hooks")
    optional = native_map["optional"]
    for name in ("contact_pair", "smart_guard"):
        if name not in optional:
            raise ValueError(f"missing optional site: {name}")

    lines = [
        "#pragma once",
        "// GENERATED FILE. Edit native_maps/*.json, then regenerate.",
        "#include <array>",
        "#include <cstdint>",
        "",
        "namespace wh3 {",
        "namespace native_map {",
        "",
        "struct GuardSpec {",
        "    std::uintptr_t rva;",
        "    const char* bytes;",
        "};",
        "",
        f'inline constexpr char kMapId[] = "{native_map["map_id"]}";',
        f'inline constexpr char kExeSha256[] = "{native_map["game"]["sha256"]}";',
        "",
        "inline constexpr std::array<GuardSpec, 16> kCoreGuards{{",
    ]
    for spec in core.values():
        lines.append(f'    GuardSpec{{{cpp_hex(spec["rva"])}, "{spec["guard"]}"}},')
    lines += [
        "}};",
        "",
        "inline constexpr std::array<const char*, 16> kHookNames{{",
    ]
    for name in core:
        lines.append(f'    "{name}",')
    lines += [
        "}};",
        "",
        f'inline constexpr GuardSpec kContactPairGuard{{{cpp_hex(optional["contact_pair"]["rva"])}, "{optional["contact_pair"]["guard"]}"}};',
        f'inline constexpr GuardSpec kSmartGuardGuard{{{cpp_hex(optional["smart_guard"]["rva"])}, "{optional["smart_guard"]["guard"]}"}};',
        "",
        f'inline constexpr std::uintptr_t kFullMoveVTable = {cpp_hex(native_map["derived"]["full_move_vtable"]["rva"])};',
        f'inline constexpr std::uintptr_t kSimpleInterceptMoveVTable = {cpp_hex(native_map["derived"]["simple_intercept_move_vtable"]["rva"])};',
        f'inline constexpr std::uintptr_t kAttackVTable = {cpp_hex(native_map["derived"]["attack_vtable"]["rva"])};',
        "",
        "} // namespace native_map",
        "} // namespace wh3",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    native_map = json.loads(args.map.read_text(encoding="utf-8"))
    rendered = render(native_map)
    if args.check:
        current = args.out.read_text(encoding="utf-8") if args.out.exists() else ""
        if current != rendered:
            raise SystemExit("GENERATED_NATIVE_MAP_STALE")
        print("PASS")
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
