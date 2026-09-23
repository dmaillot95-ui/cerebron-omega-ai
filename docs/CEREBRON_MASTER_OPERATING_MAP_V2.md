# CÉRÉBRON ΑΩ — MASTER OPERATING MAP V2

Date: 2026-09-23
Registry: 120 farms
Purpose: single operational sheet explaining how ChatGPT, CÉRÉBRON, AI identities, Hugging Face inference, farms, memories, simulations, evidence and embodied agents cooperate.

## 0 — Reality boundary
A repository is not an AI. A prompt role is not independent weights. A workflow success is not scientific proof. A simulation is not a physical test. Stored data is not learned knowledge. CLAIM <= EVIDENCE.

## 1 — Entry and command layer
CHATGPT / GPT-5.6 Sol is the interactive entry point in the present ChatGPT session. CÉRÉBRON is the orchestration architecture: parse mission, inspect checkpoint, select minimal useful coalition, route, collect, deduplicate, audit, return result and checkpoint.

## 2 — Named AI layer
SAPHEA: execution/specialists.
SPIRALION: cumulative reasoning and continuity.
ETHERION: difficult R&D.
HYPERION: exploration/divergence.
AFAH: final audit/fusion layer.
CÉRÉBRON: orchestration/routing.
AÉLYS: humanoid conversational identity/interface; no consciousness claim.
ELYRA: embodied digital humanoid/avatar; F113 executes reduced embodied simulation interfaces.

Current six core policy identities have demonstrated real inference canaries on the pinned SmolLM3-3B base where recorded, but shared base/policy prompting does not establish independent neural models. AÉLYS/ELYRA are architectural identities/interfaces until separate model weights and benchmarks demonstrate otherwise.

## 3 — Hugging Face AI workers
The system may fan out up to 20 inference roles when a workflow actually invokes them. Count EXECUTED calls, not configured roles. Each result must record provider/model/revision when available, mission fingerprint, source fingerprint, output hash and execution status. Twenty calls using the same model/data are not twenty independent proofs.

HF private storage is reserved for curated GOLD datasets, selected memory, manifests and promoted model/adapters. It is not the raw simulation dump.

## 4 — Farm layer
Registry contains F001-F120. Farms are capabilities/repositories, not automatically autonomous neural agents. CÉRÉBRON routes only the useful subset.

Protected/special groups include Collatz F01-F07; research/evidence including F08/F33/F35/F37/F72; core/orchestration including F76; robotics F77-F78/F107; simulators F79-F100; SPACE WORLD F101-F110; humanoid/cognition F111-F113; MEMORY Ω F114-F120. Existing specialist farms outside these ranges remain addressable from the registry.

## 5 — AÉLYS / ELYRA
AÉLYS -> dialogue/identity -> F112 cognitive-process laboratory -> action request -> F113 ELYRA body -> simulated world -> observations/consequences -> F112 revision -> memory/audit. F111 handles head/face/gaze/expression simulation. F90 and F101-F110 provide candidate worlds. F92 benchmarks, F95 injects failures, F97 supports causal experiments, F107 supports robot workforce interactions.

## 6 — MEMORY Ω F114-F120
F114 ENCYCLOPEDIC INDEX: stable IDs, domain/book/chapter/concept hierarchy, SPIRALIX glyph references and summaries.
F115 VECTOR SEMANTIC MEMORY: semantic retrieval and nearest-neighbour candidate detection; vector similarity alone never merges evidence.
F116 DEDUP/FUSION: SHA exact dedup, near-duplicate review, dependency tracking, contradiction preservation and controlled fusion.
F117 SIMULATION REPLAY: seeds, simulator versions, configs, checkpoints, rare events and replay recipes; prefer regeneration over raw retention.
F118 GOLD LIBRARY: validated curated knowledge/training candidates only; versioned and immutable once released.
F119 EVIDENCE ARCHIVE: sources, proofs, calibration, tests, contradictions, F72/AFAH decisions and provenance.
F120 MEMORY GOVERNOR/FREEZE: quotas, TTL, compression, pruning, namespace isolation, DRAIN/CHECKPOINT/FREEZE/RESUME.

## 7 — Memory classes
M0 EPHEMERAL runner/cache -> delete after run.
M1 TRACE -> compact manifests/hashes/metrics.
M2 REPLAY -> seed+config+version sufficient to regenerate.
M3 WARM -> bounded exceptional episodes.
M4 GOLD -> curated validated memory.
M5 MODEL -> weights/adapters/training manifests.
M6 COLD BENCHMARK -> sealed; DENY_TRAINING.
M7 EVIDENCE -> durable scientific/proof/calibration record.

Namespaces isolate COLLATZ, AGORA_TASKS, SIX_AI, SIMULATION, SPACE_WORLD, AELYS_ELYRA, GOLD, MODELS, COLD_BENCHMARK and EVIDENCE.

## 8 — Memory addressing and anti-duplication
Canonical object identity: NAMESPACE:CLASS:SHA256. Knowledge layer additionally carries stable concept ID + SPIRALIX glyph + semantic vector + provenance links. Before write: schema -> provenance -> SHA -> exact dedup -> semantic candidate search -> contradiction/dependency test -> retention class -> budget -> admit/reject. Never overwrite contradictory evidence merely because embeddings are similar.

## 9 — Storage planes
GitHub: CONTROL PLANE — code, registry, workflows, compact manifests, indexes, checkpoints and selected evidence.
HF private: CURATED PLANE — GOLD, selected datasets, promoted adapters/models and compact manifests.
External object storage candidates: DATA PLANE for WARM/REPLAY bulk only after account, credentials, quota and zero-paid-overage guards are explicitly configured and tested.
Raw deterministic simulation streams should normally expire; retain replay recipe instead.

## 10 — Simulation data lifecycle
SIMULATOR -> local ephemeral raw -> metrics/events -> F116 dedup -> F117 replay manifest -> F114/F115 index -> exceptional WARM or validated GOLD -> F119 evidence when scientifically relevant. Routine frames expire. Rare failures, discoveries and irreproducible events may be retained selectively.

## 11 — Learning lifecycle
Result -> quarantine -> provenance/dedup -> validated memory -> versioned dataset -> actual training -> adapter/weights -> cold benchmark -> transfer -> ablation -> regression -> F72 -> AFAH -> promote/rollback. Prompt changes and memory retrieval do not count as neural training.

## 12 — Evidence lifecycle
RESULT -> HASH/PROVENANCE -> DEDUP -> DEPENDENCY GRAPH -> REPRODUCTION -> ALTERNATIVE METHOD -> RED TEAM -> AUDIT -> COUNTER-AUDIT -> REGRESSION GUARD -> F72 -> AFAH -> VALIDATED / RED / OPEN / REJECT.

## 13 — Continuous workload scheduler
Separate lanes: COLLATZ; AGORA/TASK agents; LEARNING; SIMULATION/SPACE WORLD; MEMORY maintenance. Deterministic work avoids LLM calls. AI is event-driven on novelty, contradiction, invariant failure, plateau, recovery or GOLD candidacy. Backpressure prevents overlapping heavy cycles.

## 14 — Quota and saturation control
Each cycle accounts bytes_generated, bytes_persisted, bytes_gold, files, API requests and runtime. Policy: 70% warn; 80% compress/sample; 90% stop raw persistence; 95% DRAIN -> CHECKPOINT -> FREEZE. Free-tier numbers are external facts and must be rechecked before provisioning; never infer extra quota merely from adding repositories.

## 15 — Global FREEZE
RUN -> DRAIN -> stop new cycles -> settle/cancel active writes -> CHECKPOINT -> hash/verify -> disable recurring writes -> READ_ONLY/FROZEN. Freeze covers simulations, ELYRA, AGORA, Collatz automation, learning, GOLD promotion and memory mutation. Resume requires checkpoint verification and idempotent continuation.

## 16 — End-to-end target
USER -> ChatGPT -> CÉRÉBRON -> minimal coalition of named AI/HF roles/farms -> research/calculation/simulation -> MEMORY Ω -> RED TEAM/AUDIT -> F72 -> AFAH -> response -> validated memory -> optional learning -> benchmark -> checkpoint.

## 17 — Non-negotiable controls
REALITY > COHERENCE
EVIDENCE > CONFIDENCE
CLAIM <= EVIDENCE
VERIFY BEFORE COMMIT
ABLATION BEFORE ADDITION
TRANSFER BEFORE GENERALITY
CALCULATION != PROOF
SIMULATION != TEST
WORKFLOW SUCCESS != SCIENTIFIC SUCCESS
CONSENSUS != TRUTH
MEMORY != LEARNING
STORAGE != TRAINING
