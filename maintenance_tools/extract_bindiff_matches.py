#!/usr/bin/env python3
"""Extract old->new native anchor function matches from a BinDiff SQLite file.

The parser discovers the function table schema at runtime so it remains tolerant
of minor BinDiff database schema changes. BinExport should use "Subtract
Imagebase" so addresses are directly comparable to BSC RVAs.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def _columns(db: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in db.execute(f'PRAGMA table_info("{table}")')]


def _choose_function_table(db: sqlite3.Connection) -> tuple[str, dict[str, str]]:
    tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for table in tables:
        cols = _columns(db, table)
        lower = {c.lower(): c for c in cols}
        a1 = lower.get("address1") or lower.get("primary_address")
        a2 = lower.get("address2") or lower.get("secondary_address")
        if not a1 or not a2:
            continue
        mapping = {"address1": a1, "address2": a2}
        for logical in ("similarity", "confidence", "name1", "name2"):
            if logical in lower:
                mapping[logical] = lower[logical]
        return table, mapping
    raise ValueError("could not discover BinDiff function match table")


def extract(db_path: Path, native_map: dict) -> dict:
    old_by_rva = {int(spec["rva"], 0): name for name, spec in native_map["core"].items()}
    db = sqlite3.connect(str(db_path))
    try:
        table, cols = _choose_function_table(db)
        selected = [cols["address1"], cols["address2"]]
        optional = [key for key in ("similarity", "confidence", "name1", "name2") if key in cols]
        selected += [cols[key] for key in optional]
        query = "SELECT " + ",".join('"%s"' % x for x in selected) + f' FROM "{table}"'
        rows = []
        for raw in db.execute(query):
            primary = int(raw[0])
            if primary not in old_by_rva:
                continue
            item = {
                "anchor": old_by_rva[primary],
                "baseline_rva": f"0x{primary:08X}",
                "candidate_rva": f"0x{int(raw[1]):08X}",
            }
            for idx, key in enumerate(optional, 2):
                value = raw[idx]
                item[key] = value
            rows.append(item)
        return {
            "schema": 1,
            "tool": "extract_bindiff_matches",
            "database": str(db_path),
            "function_table": table,
            "matches": sorted(rows, key=lambda x: x["anchor"]),
        }
    finally:
        db.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bindiff-db", required=True, type=Path)
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    native_map = json.loads(args.map.read_text(encoding="utf-8"))
    result = extract(args.bindiff_db, native_map)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"matches": len(result["matches"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
