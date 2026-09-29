# Version and artifact naming policy

## Formal Mod version

The current formal project version is:

`v1.3.0`

The Mod uses normal semantic release numbers only. Do not append maintenance-stage strings to the formal version.

Good:

- `v1.3.0`
- `v1.3.1`
- `v1.4.0`

Not acceptable as formal versions:

- `1.3.0-corepath-rc8`
- `1.3.0-tpol-t1h`
- `1.3.0-movevtfix`

Those labels may still appear in internal history/provenance records where they identify a specific maintenance experiment or Native build.

## Steam pack filename

The canonical Steam/install artifact filename is fixed as:

`zzz_better_shift_command_steam.pack`

Do not rename the public pack when the Mod version changes.

## Runtime/log version

The Lua controller reports `1.3.0` and run ID `V1_3_0`.

Native Bridge may retain an independent internal ABI/build identifier such as:

`1.0.17-corepath-wh3-6c104-movevtfix`

This string is a binary compatibility/build provenance ID. It is not the Mod version and must not be presented as such in release notes or Steam-facing text.

## Internal maintenance labels

Labels such as these remain valid only for engineering history:

- `COREPATH-RC8`
- `NATIVE-MAP-RC7`
- `BSC-TPOL-D1`
- `BSC-TPOL-T1H`

They must always be described as a stream/stage, not a release version.
