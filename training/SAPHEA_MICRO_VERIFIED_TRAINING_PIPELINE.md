# CÉRÉBRON ΑΩ — SAPHEA MICRO VERIFIED TRAINING PIPELINE
Version: 1.0
Date: 2026-09-20
Status: DESIGN_ACTIVE

## Objective
Convert validated colony work into training material for future SAPHEA MICRO while preventing unverified claims, duplicated evidence, and benchmark leakage from becoming training truth.

## Pipeline
COLONIES
-> BLIND DIVERGENCE
-> LOCAL FREEZE
-> OMEGA SIGNATURE
-> AUDIT / COUNTER-AUDIT / REPRODUCTION
-> GOLD DATASET CANDIDATES
-> DATA HYGIENE
-> TRAIN / VALIDATION / COLD TEST SPLIT
-> SAPHEA MICRO TRAINING
-> BLIND BENCHMARK
-> RED TEAM
-> ABLATION
-> PROMOTE OR ROLLBACK
-> AGORA LESSON / MEMORY

## Admission gates for GOLD candidates
A sample is eligible only if it has:
- exact task statement;
- final answer or exact mathematical claim;
- evidence/proof object when applicable;
- provenance and dependency IDs;
- audit result;
- counter-audit result;
- reproduction status;
- explicit status: PROVED | VERIFIED | COMPUTED | REFUTED | OPEN;
- no hidden promotion of COMPUTED/CANDIDATE to PROVED.

## Negative curriculum
Keep useful failures separately:
- false lemmas;
- invalid quantifier jumps;
- circular arguments;
- shared-evidence false consensus;
- failed counterexamples;
- arithmetic/indexing errors;
- benchmark overfitting.
Each failure stores CAUSE -> COUNTEREXAMPLE -> CORRECTION -> ANTI_ERROR_RULE.

## Data separation
Never train on the cold benchmark.
Maintain immutable IDs for:
TRAIN
VALIDATION
COLD_TEST
RED_TEAM_HOLDOUT
TRANSFER_TEST

Deduplicate by semantic claim, derivation lineage, source dependency and near-duplicate prompt/answer pairs.

## Promotion rule
A trained SAPHEA generation is NOT promoted because training loss improves.
Promotion requires measurable improvement on unseen tasks with no unacceptable regression.

Required comparisons:
- baseline vs candidate;
- accuracy/correctness;
- proof validity where applicable;
- calibration;
- reproducibility;
- transfer;
- hallucination/error rate;
- cost;
- latency.

ABLATION BEFORE ADDITION.
TRANSFER BEFORE GENERALITY.
CLAIM <= EVIDENCE.

## Collatz curriculum seed
Current Collatz farms may contribute examples only after evidence classification.
Preserve:
- N<=4 audited closure as historical verified material.
- N=5/N=6 remain non-GOLD unless complete proof objects are recovered and independently re-audited.
- arbitrary N remains OPEN unless a universal proof passes formal audit.
- finite computation is labeled COMPUTED, never PROVED.

Candidate lessons:
- H-coupling derivation/audit;
- H-log identity checking;
- 3-adic lifting and residue towers;
- lower Diophantine gap;
- rotation-difference identities;
- counterexample search;
- dependency auditing;
- distinguishing local constraints from arbitrary-N closure.

## Generation passport
Every SAPHEA MICRO generation stores:
model/base
dataset_version
training_method
hyperparameters
training_compute
benchmark_version
cold_scores
red_team_scores
ablations
known_regressions
promotion_status
rollback_target

## Promotion statuses
EXPERIMENTAL -> CANDIDATE -> VALIDATED -> PROMOTED
or
EXPERIMENTAL/CANDIDATE -> REJECTED

## Safety / privacy
PRIVATE BY DEFAULT.
No private prompts, API keys, secrets, personal data, or restricted repository material enters a training corpus without explicit authorization and provenance.
