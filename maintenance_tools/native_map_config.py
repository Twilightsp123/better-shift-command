#!/usr/bin/env python3
"""Resolve the promoted canonical native map from native_maps/CURRENT."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POINTER = ROOT / "native_maps" / "CURRENT"


def current_map_path(root: Path = ROOT) -> Path:
    pointer = root / "native_maps" / "CURRENT"
    rel = pointer.read_text(encoding="utf-8").strip()
    if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        raise ValueError("invalid native_maps/CURRENT pointer")
    path = (root / "native_maps" / rel).resolve()
    maps_root = (root / "native_maps").resolve()
    if maps_root not in path.parents:
        raise ValueError("CURRENT escapes native_maps")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path
