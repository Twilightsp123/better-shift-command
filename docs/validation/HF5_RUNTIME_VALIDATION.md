# HF5 Runtime Validation Summary

Date: 2026-09-13
Controller: P2B-HF5 / 0.2.5
Authoritative result archive: `WH3_Controller_P2B_Result_69ec469bbff5440d.zip` (retained in the complete project handoff, not required in normal Git checkout).

Schema-4 re-analysis records:

```text
runtime_logic_pass=true
controller_runtime_validated=true
phase1_pass=true
phase2_pass=true
attack_first_chain_pass=true
physical_disengagement_pass=true
missing=[]
failures=[]
chronology_errors=[]
```

Runtime-confirmed behavior includes Move->Move, Move->Attack, append after takeover, sampled target-specific melee hold, Attack->pN ACK, physical separation evidence, Attack-first adoption, and ordinary RMB cancellation during Attack/Hold.

The Bridge proof boundary remains conservative: runtime success does not rewrite global provenance flags into universal exact-source proof.
