# MCT Policy Schema D1.1

Status: **APPROVED SCHEMA; T1H HIDDEN SCAFFOLD IMPLEMENTED; NO MCT UI REGISTERED**

Runtime stage: `BSC-TPOL-T1H`

The public schema is defined now so later MCT wiring does not require another gameplay rewrite. T1H intentionally does **not** call `get_mct()`, does not register an MCT mod, and creates no visible settings page. The current runtime takes an immutable built-in snapshot.

## 1. User-facing model for the future MCT page

The eventual page should lead with one movement-behavior preset:

```text
Behavior Preset
  Smooth   (default / recommended)
  Balanced
  Precise
  Custom
```

Presets control bounded transition timing/precision. `Minimum Engagement Time` is intentionally a direct time control rather than an abstract priority score.

## 2. Options and exact meaning

| Key | EN label | 中文标签 | Range | Default | T1H runtime status | Exact meaning |
|---|---|---|---:|---:|---|---|
| `behavior_preset` | Behavior Preset | 行为预设 | enum | Smooth | snapshot only | Chooses bundled bounded movement-transition preferences. It never changes hard invariants. |
| `movement_cornering` | Movement Cornering | 移动转向提前量 | 0–100 | 85 | reserved | How early a legal **MOVE→MOVE** successor may be handed to CA inside the existing steering/corner caps. Higher = more continuous cornering; lower = closer adherence to the current waypoint before handoff. |
| `attack_handoff` | Attack Handoff | 攻击衔接提前量 | 0–100 | 80 | reserved | Size of the legal **MOVE→ATTACK** terminal handoff window. Higher = Attack may be issued earlier before CA arrival braking; lower = require the Move to get closer to semantic completion. Prior route debt and target identity remain hard requirements. |
| `route_fidelity` | Route Fidelity | 路径点遵循程度 | 0–100 | 45 | reserved | How strongly soft waypoint/debt logic prefers passing close to the drawn waypoint. Higher = tighter route adherence; lower = treat intermediate points more as navigation guidance when the trajectory still preserves the route. It can never skip a canonical action. |
| `native_successor_tolerance` | Native Successor Tolerance | 原生提前执行容忍度 | 0–100 | 85 | reserved | Width of the bounded **adopt-only hysteresis band**. Higher = if CA is already executing the exact immediate successor slightly before Lua would issue it, BSC is more willing to adopt instead of rollback. It never permits `i+2` skips or target mismatch. |
| `engagement_hold_seconds` | Minimum Engagement Time | 最低交战持续时间 | 0.5–10.0 s, step 0.5 | **3.0 s** | **wired** | Minimum amount of **verified eligible engagement time** required after Attack has genuinely engaged its intended target before a following Exit Move can become eligible. Approach/chase time does not count. Observation gaps and non-eligible intervals do not count. |
| `disengage_priority` | Disengage Priority | 脱战移动优先度 | 0–100 | 80 | reserved | Once Minimum Engagement Time and the Exit semantic prerequisites are satisfied, controls how aggressively BSC pushes the Exit Move / bounded anti-stick recovery. It does **not** shorten the minimum engagement timer. |

### Why `Attack Commitment` was removed

The earlier D1 draft used a vague `attack_commitment` 0–100 slider. That mixes two distinct questions:

1. **How long must the unit actually fight before Exit is allowed?** → direct seconds (`engagement_hold_seconds`).
2. **After Exit is allowed, how aggressively should BSC enforce disengagement?** → `disengage_priority`.

D1.1 keeps them separate so the UI matches player intent.

## 3. Presets

Presets currently apply only to bounded transition preferences. `engagement_hold_seconds` remains an independent direct setting and defaults to 3.0 seconds for every preset unless the player changes it.

| Setting | Smooth | Balanced | Precise |
|---|---:|---:|---:|
| Movement Cornering | 85 | 65 | 35 |
| Attack Handoff | 80 | 60 | 25 |
| Route Fidelity | 45 | 65 | 90 |
| Native Successor Tolerance | 85 | 65 | 35 |
| Disengage Priority | 80 | 65 | 55 |
| Minimum Engagement Time | 3.0 s | 3.0 s | 3.0 s |

`Smooth` is the product default because BSC exists to remove avoidable stop/start behavior while keeping command semantics intact.

## 4. Minimum Engagement Time contract

Current runtime baseline used `CFG.attack_hold_ms = 3000`. T1H routes that same value through the hidden policy profile:

```text
engagement_hold_seconds = 3.0
→ engagement_hold_ms = 3000
→ CFG.attack_hold_ms = 3000
```

The timer is **not** “seconds since the Attack order was clicked.” It is accumulated only while the existing engagement evidence says the intended target is actually eligible for hold credit.

The lower bound is 0.5 seconds rather than 0 because current hold logic must observe at least a positive eligible interval before completing the Attack semantic episode.

## 5. Future mapping rule

0–100 values map only into bounded policy ranges. They must never become arbitrary raw distances, retry counts, or Native proof switches.

```text
movement_cornering
  → bounded Move→Move early-handoff scale

attack_handoff
  → terminal Move→Attack issue window + bounded progress requirement

route_fidelity
  → waypoint corridor / soft-debt grace inside hard caps

native_successor_tolerance
  → adopt-window minus issue-window hysteresis slack

engagement_hold_seconds
  → exact bounded eligible engagement requirement (milliseconds internally)

disengage_priority
  → bounded Exit response/reassert timings after eligibility
```

## 6. Forbidden MCT controls

MCT must never expose controls to:

- skip canonical intermediate actions;
- allow Attack target mismatch;
- disable manual RMB/REPLACE authority;
- accept unknown/noncanonical Native execution;
- disable revision/ACK/engine-sequence proof;
- create unlimited SC5/SC6 retries;
- promote quarantined Entity/Component/ContactPair evidence;
- modify hook addresses/guards.

## 7. Battle snapshot rule

When visible MCT is implemented, settings are read once at battle initialization and compiled into one immutable `PolicyProfile`. Mid-battle UI changes take effect only next battle.

Fallback on missing/broken MCT:

```text
profile = built_in_smooth
engagement_hold_seconds = 3.0
source = DEFAULT_FAIL_SAFE
```

T1H intentionally uses the equivalent source label `BUILTIN_HIDDEN` and exposes no settings UI.
