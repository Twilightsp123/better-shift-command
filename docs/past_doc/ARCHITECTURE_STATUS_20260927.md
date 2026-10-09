# Architecture Status — CorePath RC8

## Release-critical flow

`player command → native Move/Attack capture → canonical Lua action/block → SC1–SC4 route logic → verified native issue/ACK → active-order execution identity → SC6 reconcile → CA locomotion`

Attack observation/hold continues to use FEG from supported battle-unit APIs/geometry. SC5 recovery requires exact current Exit MOVE identity, positive live contact/proximity, low speed, bounded no-progress time, and the shared bounded recovery budget.

## Quarantined flow

`BattleUnit-like physical root → member array → historically named Entity → Component/Alive → ContactPair`

This source remains for diagnostic research and historical reproducibility. It does not authorize, block, or complete production CorePath actions.

## Hook tiers

Mandatory 16: Move, Attack, allocator, halt, Lua Move, Lua Attack, publish Move, publish Attack, writer begin/finalize, copy, stage, Move handler, Attack handler, selection, free.

Optional static sites: ContactPair and Smart Guard. Both are staged disabled in RC8.

## Lifecycle

The bridge DLL is pinned. Normal battle stop ends the bridge session but leaves observer hooks available for later battles. Desktop quit triggers `stop_observer()`, which queue-disables hooks and applies the disable without removing hooks, unloading MinHook, freeing trampolines, or unloading the pinned bridge.
