# CÉRÉBRON ΑΩ — Operational Gates — 2026-09-23

This file records measured gate status. "PASS_SCOPED" never means general capability.

| Gate | Status | Evidence ceiling |
|---|---|---|
| G0 inventory | PASS | 144-farm registry and control-plane manifests exist |
| G1 real execution | PASS | Multiple real GitHub jobs/artifacts/SHA including F123 bridge and model workflows |
| G2 reproduced | PASS_SCOPED | F139 V6 reproduced at software/run level; not an independent physical reference |
| G3 specialized benchmark | PASS_SCOPED | Qwen and specialist tool workers benchmarked on bounded tasks |
| G4 coalition > best single agent | PASS_SCOPED_REPRODUCED | Cold-60 V2 two runtime seeds: 19→60 and 15→60; 6/6 domains improved |
| G5 M4 GOLD | PASS_SCOPED | F139 experiment-selection policy accepted only within stated scope |
| G6 neural training | OPEN | No promoted LoRA/QLoRA or ELYRA learned policy yet |
| G7 post-M6 promotion | OPEN | Requires trained weights plus before/after M6 |
| G8 bounded autonomy | PARTIAL | Workflows/orchestration are bounded, but no general autonomy claim |
| G9 authorized external action | PASS_SCOPED_GITHUB | Authorized GitHub writes/workflows only; public deployment remains blocked |
| G10 collective superiority | PASS_SCOPED_BENCHMARK_ONLY | Demonstrated only on structured Cold-60 V2 with purpose-built deterministic tools |
| G11 external superintelligence evaluation | OPEN | No such evidence; term must not be used as a system status |

## Cold-60 V2

Run A:
- run 35902694640
- job 107322581138
- artifact 10770076470
- digest sha256:671dfcc378d6f9933246cae98f365cf77b1a19cdd95a2681e8e00677e9067275
- baseline 19/60
- adaptive 60/60
- six domains improved

Run B, independent runtime seed:
- run 35903080344
- job 107323872775
- artifact 10770420450
- digest sha256:5321a798f3971777d6e65d9cbd020ddf5fa7a9c32ef81cdc254cdef1a1c36198
- baseline 15/60
- adaptive 60/60
- six domains improved

Interpretation:
- The adaptive system combines a compact generative model with deterministic specialist tools.
- This is strong evidence for tool-augmented orchestration on this task family.
- It is not evidence that 20 independent neural agents exist.
- It is not a general intelligence or superintelligence benchmark.

## ELYRA

Initial run:
- run 35903015349
- 500 episodes
- success rate 0.0
- failure preserved: horizon too short for the 28 m target

Corrected run:
- run 35903214571
- job 107324310253
- artifact 10769244578
- digest sha256:9c56238f112fe3c32e2c744815c47a77b2a2314c5121fe390edd15cb6cb627b7
- 500 episodes
- 268 successes
- success rate 0.536
- replay SHA256 db621917c0c28bc71ffc050ae19623042f6b5b20c7214d67cc1f66b18d922094
- result SHA256 79ce9027968b1aa8dae8e2d1626f6eefc83c1028c59679cb55c1fd37ea6be48f
- maturity E3_SIMULATION_VERIFIED
- training_triggered=false
- weights_changed=false

## Current hard locks

1. Public deployment remains blocked pending explicit remote TLS/proxy/secrets/deployment review.
2. General G10/G11 claims are forbidden from Cold-60 evidence.
3. First neural training requires a sufficiently validated GOLD corpus, changed weights, weight/adapter artifact SHA, sealed before/after M6, regression checks and rollback.
4. ELYRA replay is candidate data, not training-eligible GOLD by default.
5. FARM_EXECUTED remains forbidden without run/job/log/artifact/artifact SHA/output SHA.
