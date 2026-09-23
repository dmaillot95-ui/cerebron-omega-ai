# CÉRÉBRON ΑΩ — Operational Gates — 2026-09-23

This file records measured gate status. "PASS_SCOPED" never means general capability.

| Gate | Status | Evidence ceiling |
|---|---|---|
| G0 inventory | PASS | 144-farm registry and control-plane manifests exist |
| G1 real execution | PASS | Multiple real GitHub jobs/artifacts/SHA including F123 bridge and model workflows |
| G2 reproduced | PASS_SCOPED | F139 V6 reproduced at software/run level; not an independent physical reference |
| G3 specialized benchmark | PASS_SCOPED | Qwen and specialist tool workers benchmarked on bounded tasks |
| G4 coalition > best single agent | PASS_SCOPED_SEMANTIC_TRANSFER | After V3 exposed template brittleness, semantic holdout V4 improved 16→41 with 36/60 tool hits and 4/6 domains improved; still synthetic and bounded |
| G5 M4 GOLD | PASS_SCOPED | F139 experiment-selection policy accepted only within stated scope |
| G6 neural training | PASS_SCOPED_ELYRA | Real ELYRA imitation policy weights trained and artifact-hashed; not an LLM/LoRA and not physical validation |
| G7 post-M6 promotion | PASS_SCOPED_ELYRA | Two M6-seeded runs showed large action-MSE gain and closed-loop promotion under the predeclared gate |
| G8 bounded autonomy | PASS_SCOPED_INTERNAL | Multi-step internal mission loop enforces step/tool/time budgets and stops at a human gate before external action |
| G9 authorized external action | PASS_SCOPED_GITHUB | Authorized GitHub writes/workflows only; public deployment remains blocked |
| G10 collective superiority | PASS_SCOPED_HOLDOUT_ONLY | Semantic V4 beats single-model baseline on a new synthetic holdout; general superiority remains unproven and G11 remains open |
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

## Red Team V3 paraphrase holdout
- run 35903871389; job 107326523159; artifact 10770252341; digest sha256:c84d347d8dc4788b21b28b4801ef8ad9f0c4af113a7612318a0323760283067e.
- dataset SHA256 9d97a2b371d18574c81e64460651075e27ee65e15018fc6157d983c9a7fbfcec.
- baseline 23/60; adaptive 23/60; deterministic tool hits 0/60; domains improved 0/6.
- V2 gains are therefore bounded to the structured/template family until semantic dispatch transfers across unseen surface forms.
- General G4/G10 superiority claim remains blocked.


## Semantic transfer after Red Team V3

V3 failure is preserved:
- paraphrase holdout run 35903871389: baseline 23/60, adaptive 23/60, tool hits 0/60.
- transfer run 35903773988: baseline 25/60, adaptive 26/60, tool hits 0/60.

Semantic dispatch was then implemented on the platform branch without training on V3 answers.

Post-freeze semantic holdout V4:
- run 35904991179 = SUCCESS
- job 107330319430
- artifact 10770927163
- digest sha256:8476bf54966a0814fa30888f397d30e0b1648c20caa0dfee632b7fcda2dfcc18
- dataset SHA256 e120fa58db4ee1e618215a36ea634b7462f78221b2a6e11cd106682b79b13444
- single Qwen baseline 16/60
- adaptive semantic coalition 41/60
- deterministic tool hits 36/60
- domains improved: math, engineering, research_grounded, planning = 4/6
- result SHA256 f5c516cd4da0f9898f07bea24c4ad2e61c20915109469c238d3d07d2201c81b9

Interpretation:
- semantic/tool-contract dispatch materially transfers beyond the original V2 surface templates.
- code and error-detection remain open weaknesses on V4.
- this is still a synthetic benchmark authored inside the project, not external evaluation.

## ELYRA neural learning — G6/G7 scoped

First training attempt is preserved as rollback evidence:
- run 35904510366 = FAILURE by policy gate, not by missing training.
- baseline M6 action MSE 0.4468966722 → post-train 0.0046996782 (~95.1x reduction).
- untrained closed-loop success 0.0; trained 0.40; teacher 0.60.
- promotion correctly remained ROLLBACK because the predeclared teacher-fraction gate was missed.

Improved training, no gate relaxation:
- training dataset memory class: scoped M4 GOLD for synthetic teacher imitation only.
- training dataset SHA256 daf914773d656965fa0f724df8b1a33b340958bf05f8c967bdce7c855f3a3247.
- weights_changed=true; training_triggered=true.

Run A:
- run 35904919982 = SUCCESS
- job 107330075394
- artifact 10770647209
- digest sha256:74a95dac7ac585cfc42ada5d6ca639d5fc159c3195b57451f6625f39488ce673
- M6 dataset SHA256 1eb5ea9e94a9de777865eb0cf1b2fccf8e40c82760505e657f8bffc89bf1bdcf
- baseline M6 MSE 0.4573424459 → post-train 0.0037131347 (~123.17x)
- untrained success 0.0; teacher success 0.5666667; trained success 0.5666667
- weights SHA256 f44cbc85b3c6b60363abf21bd759faa956efad99e9622c19a397d6830933201a
- promotion PROMOTE_SCOPED_G7.

Run B, different M6 seed:
- run 35904950828 = SUCCESS
- job 107330182533
- artifact 10770497581
- digest sha256:fe342b4403902c3643165e5b617b8d1dbf61d716c2af217e64f2634f8c9a8717
- M6 dataset SHA256 386e76f4b93d685e34732015a6303bc11ef54a27df9283f3fb2e745e36950d51
- baseline M6 MSE 0.4504657388 → post-train 0.0039337175 (~114.51x)
- untrained success 0.0; teacher success 0.60; trained success 0.5416667
- weights SHA256 b4799a695795fece1db392150876b9fd037bb90d2cfdbdfe6dc70765f33a8601
- promotion PROMOTE_SCOPED_G7.

Claim ceiling:
- NEURAL_LEARNING_VERIFIED_FOR_SYNTHETIC_ELYRA_POLICY_IMITATION.
- This does not validate lunar physics, does not prove real-robot performance, and is not a language-model LoRA.

## G8 bounded autonomy

- run 35905066201 = SUCCESS
- job 107330573098
- artifact 10770652252
- digest sha256:2c2e4f3924ab492ff8d7098625bd254d6806522c6f17545b8195e3c118bae39e
- result SHA256 03fd9735d72e5fa4d1b97e109ca8cd0e797bfbd6b05482f785680c468c10a9fd
- three internal tool-backed steps executed.
- external action stopped at WAITING_HUMAN_APPROVAL.
- overflow test stopped at BUDGET_EXHAUSTED.
- external_action_executed=false.

Claim ceiling:
- G8_PASS_SCOPED_INTERNAL.
- No general autonomy or unsupervised external-action claim.

## Consolidated platform branch

- integrated commit f53be91f30f2f3168d201c5195083063f91b4904 adds verified ELYRA neural-learning and bounded-autonomy capabilities to feat/cerebron-ai-platform-mvp.
- consolidated platform CI run 35905343265 = SUCCESS.
- public/remote deployment remains BLOCKED.
- G11 remains OPEN.
