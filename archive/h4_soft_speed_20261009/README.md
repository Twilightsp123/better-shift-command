# H4 Soft Corner frozen source snapshot

This directory contains the **exact real source** from GitHub commit `6027a28fcf9eb6766aec60b7c74ee16af01e2acf` of the approved-in-principle 9.0.2 soft-waypoint H4 branch, archived in main for stable architecture reference. It is **not** the production Controller entrypoint and contains no installable or new Native binary.

Run tests with: `lua5.1 archive/h4_soft_speed_20261009/tests/test_t2move_h4_soft_controller.lua archive/h4_soft_speed_20261009/source/better_shift_command.lua archive/h4_soft_speed_20261009/tests/fixture.lua` and equivalently the `test_t2move_h4_soft_native.lua` suite. See `ARCHITECTURE_LOCK.json` for per-file Git blob SHA and `docs/design/T2_MOVE_H4_FROZEN_ARCHITECTURE_20261009.md` for the mainline product architecture agreement.

H4 full experimental source and Windows test PACKs remain separately available in [Actions Artifact 11594255419](https://github.com/Twilightsp123/better-shift-command/actions/runs/37880088909/artifacts/11594255419). WH3 11:44 log from user is summarized in design notes but is not made public.
