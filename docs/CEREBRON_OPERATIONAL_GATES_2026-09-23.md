# CÉRÉBRON ΑΩ — Operational Gates — 2026-09-23

This file records measured gate status. "PASS_SCOPED" never means general capability.

| Gate | Status | Evidence ceiling |
|---|---|---|
| G0 inventory | PASS | 144-farm registry and control-plane manifests exist |
| G1 real execution | PASS | Multiple real GitHub jobs/artifacts/SHA including F123 bridge and model workflows |
| G2 reproduced | PASS_SCOPED | F139 V6 reproduced at software/run level; not an independent physical reference |
| G3 specialized benchmark | PASS_SCOPED | Qwen and specialist tool workers benchmarked on bounded tasks |
| G4 coalition > best single agent | OPEN_OUTSIDE_TEMPLATE_FAMILY | Cold-60 V2 was 19→60 and 15→60, but transfer Red Team V3 was only 25→26 with 0 specialist-tool hits and 1/6 domains improved |
| G5 M4 GOLD | PASS_SCOPED | F139 experiment-selection policy accepted only within stated scope |
| G6 neural training | OPEN | No promoted LoRA/QLoRA or ELYRA learned policy yet |
| G7 post-M6 promotion | OPEN | Requires trained weights plus before/after M6 |
| G8 bounded autonomy | PARTIAL | Workflows/orchestration are bounded, but no general autonomy claim |
| G9 authorized external action | PASS_SCOPED_GITHUB | Authorized GitHub writes/workflows only; public deployment remains blocked |
| G10 collective superiority | OPEN | V2 tool-template gain did not transfer under parser-unseen reformulations; no general collective-superiority claim is allowed |
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


## Live operational core evidence
- F139 software/run reproduction B: run 35901349529, job 107318057554, artifact 10769451138, digest sha256:3c633424f84e082bb92e7907c79cc3224c62eb44d0878b933cbd3c9d4446af7c; S7 software/run reproduction only.
- Pure shared-model orchestration ablation: Qwen single 14/60 vs corrected coalition without tools 14/60 on Cold-60 V1. More logical roles alone did not improve accuracy.
- Tool-augmented Cold-60 V2 reproduced on two runtime seeds: 19→60 and 15→60, 6/6 domains improved. Scope remains structured task-family performance.
- Live adaptive coalition integration commit f17929990e92038a1a2678effb867c27a1371d52; live test commit a2bfaaeaa4a4c7cc9b2a8f60ad1a202b92f34042; CI 35903451187 SUCCESS.
- Cockpit coalition/evidence display commit c5d3347a725e59c9a43a11d6dd39d04be0167e01; CI 35903534095 SUCCESS.
- Specialist safety/regression tests commit 4aaf0dad7dca4d395544cdbaa11cc96e85cdcd5d; CI 35903257778 SUCCESS.
- Local core status: OPERATIONAL_SCOPED. Remote/public deployment: BLOCKED.


## Cold-60 V3 Transfer Red Team — downgrade evidence

- Dedicated branch: feat/cerebron-cold60-redteam-v3
- Commit: eaf87cf87b5aa8f0de3a7cf35c1874dd18511fec
- Run: 35903773988 = SUCCESS
- Job: 107326190245
- Artifact: 10770645736
- Artifact digest: sha256:27a37328a6a9e09b27e2d733aa20c77b3f2c26787f6a6264bc68141f6fc9585e
- Runtime seed: 35903773988
- Single Qwen baseline: 25/60
- Adaptive coalition: 26/60
- Deterministic specialist-tool hits: 0/60
- Domains improved: code only = 1/6
- criterion_4_of_6 = false
- Transfer gap from V2 adaptive 60/60 = 0.5666666666666667
- Result SHA256: 9c01b869f09d265725517a219a2b5175c3ebbd76d34c57cb331337336a816ca8

Interpretation:
- V2 proves that CEREBRON can orchestrate purpose-built deterministic workers extremely well when task surface forms match their contracts.
- V3 shows that the current trigger layer is brittle to semantically equivalent reformulation.
- This is a router/parser generalization failure, not a failure of the entire CEREBRON architecture.
- Next gate is to replace brittle surface-pattern routing with semantic/tool-contract routing and then rerun V3 unchanged.
- V3 remains sealed and deny_training=true. Do not train on its answers.
