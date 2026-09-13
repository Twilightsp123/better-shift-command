# Failed Approaches — DO NOT REINTRODUCE

This file exists to prevent future maintainers or AI agents from repeating already-disproved ideas.

| Revoked idea | Why it looked plausible | Runtime contradiction / failure | Use instead |
|---|---|---|---|
| `+0x98 == Shift/RMB` | field varied between movement record types | width/record classification, not gesture semantics | native `is_queued` |
| `ordered_position()` = physical execution head | public API exposes an ordered destination | swept rapidly through future queued points while unit could not physically be there | actual unit position + execution geometry |
| one Move callback = one player gesture | callback appears when moving | Shift polyline produced N slots : N+1 callbacks; P0 has no target slot | native journal/action chronology |
| `RMB_OVERRIDE_LOCK` | suppress stale records after RMB | ignored Lua records did not cancel CA native queue; controller could lock permanently | external nonqueued replacement generation |
| `NATIVE_OVERRIDE_FENCE` | conservative protection after ambiguous replacement | false positives permanently disabled later valid routes | revision + journal generation semantics |
| callback-time replace pulse as authority | native bit really exists | pulse can be cleared by native update before Lua callback | durable accepted-order/revision evidence |
| Attack seen = whole program complete | Attack is a natural barrier | pN can appear in Journal much later; immutable freeze dropped real Shift tail | appendable active shadow timeline |
| fixed 30s Attack approach timeout | prevents stuck plans | long-distance pursuit can exceed 30s before first melee | wait while target/attack remains valid; diagnostics only |
| repeated escape Move spam | might force disengagement | risks animation/formation reset and fights CA steering | one verified pN dispatch; observe result |

Historical direct Attack queue/root hypotheses such as `root+0x88` generic queue and direct `root+0x1DB0` header were also revoked by runtime evidence. See the original project status archives for chronology.
