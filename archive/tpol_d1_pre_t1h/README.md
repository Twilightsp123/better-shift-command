# Better Shift Command — Transition Policy Architecture D1

This is a **design/maintenance handoff**, not an install-ready release.

Runtime source is the corrected CorePath RC8 Move-VTable baseline. The new `BSC-TPOL-D1` transition architecture is documented but **not implemented** in this archive.

Start with `README_FIRST.md`.

Core design goal:

> Preserve canonical command meaning while choosing the smoothest legal handoff by default; expose bounded timing/precision preferences through MCT without making hard invariants configurable.
