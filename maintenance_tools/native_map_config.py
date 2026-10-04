#!/usr/bin/env python3
"""Resolve promoted and staged-candidate native maps from pointer files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _map_path(pointer_name: str, root: Path = ROOT) -> Path:
    pointer = root / "native_maps" / pointer_name
    rel = pointer.read_text(encoding="utf-8").strip()
    if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        raise ValueError(f"invalid native_maps/{pointer_name} pointer")
    path = (root / "native_maps" / rel).resolve()
    maps_root = (root / "native_maps").resolve()
    if maps_root not in path.parents:
        raise ValueError(f"{pointer_name} escapes native_maps")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path

def current_map_path(root: Path = ROOT) -> Path:
    return _map_path("CURRENT", root)

def candidate_map_path(root: Path = ROOT) -> Path:
    return _map_path("CANDIDATE", root)
