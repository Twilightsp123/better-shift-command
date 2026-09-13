# Predictive Move Handoff

HF5 preserves the v6.5 locomotion kernel: actual dispatch origin, short-window median speed, angle-scaled lead/cap, formation-scale lookahead, progress gate, proximity handling and brake fallback. The purpose is to hand the next target to CA while the unit is still moving so CA steering performs the turn.

Key design rule: **do not replace CA locomotion with a custom facing solver.**

Historical tuned envelope includes roughly 30m straight to 45m U-turn angle lead, speed lead capped around 10m, formation lookahead, 12m floor and 50m cap. Exact release code is authoritative.
