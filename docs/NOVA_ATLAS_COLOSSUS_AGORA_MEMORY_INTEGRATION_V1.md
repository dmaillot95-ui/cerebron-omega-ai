# NOVA / ATLAS / COLOSSUS — AGORA + MEMORY Ω integration V1

Date: 2026-09-26
Status: fail-closed, not trained, runtime muted.

## 1. Purpose

F176 NOVA, F177 ATLAS and F178 COLOSSUS are tri-core AI farms. Each contains three distinct model/weight slots intended to work in parallel:

`CORE_A || CORE_B || CORE_C -> INTERNAL_FUSION`

The tri-core structure is configuration only until three explicit models/revisions are assigned and a real trainer changes adapters/weights.

## 2. Functional roles

- NOVA: exploration, invention and representation synthesis.
- ATLAS: knowledge mapping, integration, memory continuity and transfer.
- COLOSSUS: difficult reasoning, verification and large-scale synthesis.

These roles are declared specialization targets, not evidence of capability.

## 3. AGORA integration

Reference: `config/greek-agora-training-v1.json`.

The master AGORA contract states that all real available AIs may participate, but AGORA output is teaching material, not automatic truth and not automatic neural training.

The five requested task roles are:

1. M1 PEDAGOGUE — explanations, exercises, curriculum candidates.
2. M2 EXAMINER — grading, gaps, corrections.
3. M3 RED_TEAM — counterexamples, regressions, leakage, false confidence.
4. M4 CONNECTOR — links validated lessons across AIs/farms/tools/memory.
5. M5 COACH — selects next exercises from measured weaknesses and information gain.

Repository verification did not establish that these five ChatGPT task roles execute an optimizer themselves. Therefore they may prepare/filter curriculum, but a neural-training claim still requires a real trainer run and changed weights/adapters.

## 4. Training flow

`AGORA -> role-specific curriculum -> audit/counter-audit -> dedup/provenance -> TRAIN source gate -> real trainer -> changed adapter/weights -> COLD -> TRANSFER -> RED/REGRESSION -> promote or rollback -> AGORA receipt`

Required proof for each core:

- pinned model revision;
- TRAIN dataset SHA;
- trainer config SHA;
- pre-training weight/adapter SHA;
- post-training weight/adapter SHA different from pre-training;
- run/receipt;
- COLD, TRANSFER and RED/REGRESSION results.

M6/COLD/TRANSFER/RED material is never training material.

## 5. MEMORY Ω

Registered memory farms:

- F114 Encyclopedic memory index
- F115 Vector semantic memory
- F116 Dedup knowledge fusion
- F117 Simulation replay memory
- F118 Gold knowledge library
- F119 Evidence scientific archive
- F120 Memory governor/freeze

Memory classes used by the tri-core AIs:

- M0 EPHEMERAL
- M1 TRACE
- M2 REPLAY
- M3 WARM
- M4 GOLD
- M5 MODEL
- M6 COLD BENCH — DENY_TRAINING
- M7 EVIDENCE

`MEMORY != TRAINING`: reading or writing memory does not mean neural weights changed.

## 6. Hugging Face boundary

The private Hugging Face MEMORY Ω path is now directly verified for F176 NOVA, F177 ATLAS and F178 COLOSSUS by workflow run `36246961870`.

The canary verified, for each identity, a private-repository write -> read -> SHA-256 equality check. The recorded state is `HF_DIRECT_VERIFIED_3_OF_3`; the evidence receipt is `receipts/p03/tricore-hf-m03/36246961870.json` and the registry extension is `config/all-ai-memory-matrix-tricore-extension-v1.json`.

This proves storage connectivity and integrity only. It does not prove neural training, model capability, or runtime activation. No paid provider may be enabled automatically.

## 7. Current state

NOVA / ATLAS / COLOSSUS:

- repositories exist;
- tri-core contracts exist;
- private Hugging Face memory write/read/SHA is verified 3/3;
- global memory-matrix extension is registered and gated;
- model slots are unassigned;
- `training_status = NOT_TRAINED`;
- `weights_changed = false`;
- `runtime_enabled = false`;
- `output_enabled = false`;
- `operational_state = MUTED_HOLD`.

They may be prepared for AGORA curriculum and MEMORY Ω routing while remaining silent. Actual training remains blocked until the model assignments and verified trainer backend exist.
