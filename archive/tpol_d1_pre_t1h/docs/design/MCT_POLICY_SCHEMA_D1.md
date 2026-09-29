# MCT Policy Schema D1

Status: **DESIGN ONLY — values are policy defaults, not yet wired to runtime.**

## 1. User-facing model

The normal page should lead with one preset:

```text
Behavior Preset
  Smooth   (default / recommended)
  Balanced
  Precise
  Custom
```

Selecting a preset fills the advanced controls. Editing any advanced control changes the displayed preset to `Custom`.

The UI should describe behavior, not internal SC numbers or raw meter/millisecond constants.

## 2. Proposed options

| Key | EN label | 中文标签 | Range | Default Smooth | Meaning |
|---|---|---|---:|---:|---|
| `behavior_preset` | Behavior Preset | 行为预设 | enum | Smooth | preset selector |
| `movement_cornering` | Movement Cornering | 移动转向提前量 | 0–100 | 85 | earlier/later Move→Move handoff inside safe caps |
| `attack_handoff` | Attack Handoff | 攻击衔接提前量 | 0–100 | 80 | size of legal Move→Attack issue window |
| `route_fidelity` | Route Fidelity | 路径点遵循程度 | 0–100 | 45 | strictness of waypoint corridor/debt preservation |
| `native_successor_tolerance` | Native Successor Tolerance | 原生提前执行容忍度 | 0–100 | 85 | width of adopt-only hysteresis band |
| `attack_commitment` | Attack Commitment | 攻击执行坚持度 | 0–100 | 55 | later-stage bounded FEG/Attack→Exit timing preference |
| `disengage_priority` | Disengage Priority | 脱战移动优先度 | 0–100 | 80 | later-stage bounded Exit responsiveness preference |

## 3. Presets

| Setting | Smooth | Balanced | Precise |
|---|---:|---:|---:|
| Movement Cornering | 85 | 65 | 35 |
| Attack Handoff | 80 | 60 | 25 |
| Route Fidelity | 45 | 65 | 90 |
| Native Successor Tolerance | 85 | 65 | 35 |
| Attack Commitment | 55 | 65 | 80 |
| Disengage Priority | 80 | 65 | 55 |

`Smooth` is the product default because the purpose of BSC is to remove avoidable stop/start behavior while keeping command semantics intact.

## 4. Mapping rule

MCT values must map only into bounded policy ranges. They must never become arbitrary raw distances or retry counts.

Example design mappings for implementation review:

```text
movement_cornering
  → route corner early fraction / bounded lookahead scale

attack_handoff
  → terminal Attack window scale
  → minimum current-leg progress inside a bounded range

route_fidelity
  → waypoint corridor tolerance / soft-debt grace inside hard caps

native_successor_tolerance
  → adopt_window - issue_window hysteresis slack

attack_commitment
  → bounded FEG commitment timing range (later phase)

disengage_priority
  → bounded Exit response/reassert timing range (later phase)
```

The exact conversion constants are implementation-stage values and require regression tests. The public 0–100 schema is stable even if the internal safe mapping is tuned later.

## 5. Forbidden MCT controls

The following must never be exposed as user-tunable switches/sliders:

- skip canonical intermediate action;
- allow target mismatch;
- disable manual RMB cancel;
- accept unknown/noncanonical Native execution;
- disable revision/ACK/engine-sequence validation;
- unlimited SC5/SC6 retries;
- ContactPair/Entity evidence promotion;
- hook address/guard behavior.

## 6. Battle snapshot rule

MCT values are compiled into one immutable `PolicyProfile` at battle initialization. No mid-battle slider change may alter rules for an already-active canonical generation.

Fallback when MCT is missing or errors:

```text
profile = built_in_smooth
source = DEFAULT_FAIL_SAFE
```

The Mod must remain functional without MCT installed.

## 7. Logging

At battle start log one compact line:

```text
POLICY_PROFILE source=MCT preset=SMOOTH corner=85 attack=80 fidelity=45 native_tol=85 commit=55 disengage=80
```

Do not log every raw derived threshold unless debug telemetry is enabled.
