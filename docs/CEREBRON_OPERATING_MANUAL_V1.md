# CÉRÉBRON ΑΩ — OPERATING MANUAL V1

Status: MASTER OPERATING POLICY. Architecture/configuration never imply execution or proof.

## 1. System
CÉRÉBRON is the orchestrator. It reads the mission, routes only the minimal useful coalition, collects outputs, deduplicates shared dependencies, requests reproduction/alternative methods, then sends evidence through audit gates.

Core roles:
- SAPHEA: execution and specialist work.
- SPIRALION: cumulative reasoning and continuity from verified checkpoints.
- ETHERION: difficult science, mathematics and R&D.
- HYPERION: divergent hypotheses and alternative methods.
- ASTRION/F121: aerospace R&D router/specialist.
- METRION/F122: engineering calculation, simulation and validation router/specialist.
- AFAH: final epistemic audit/fusion; never a vote and never a substitute for evidence.
- AÉLYS: conversational/humanoid interface identity.
- ELYRA: embodied digital avatar/body interface.

These names are roles/orchestrators unless a real engine binding and execution trace proves a distinct model actually ran.

## 2. Farms
Registry authority: config/farms.json. Absolute cap: F144. Do not create F145.
A farm is a competence domain, not automatically an agent or model.
Never invoke all farms by default.

Routing:
MISSION -> classify domains -> select MINIMAL_USEFUL_COALITION -> execute only available farms -> expand only on unresolved gap/contradiction -> dedup dependencies -> audit.

F123-F144 are aerospace specialist farms. SCAFFOLDED means registered/architected only; it does not mean repository workflow, simulator or model execution has been proven.

## 3. Agents and colonies
When real parallel workers are available, a colony uses:
CHEF DE COLONIE -> specialists/workers -> AUDITOR -> COUNTER-AUDITOR/RED TEAM -> SYNTHESIZER.
Workers sharing the same model, prompt, source packet or simulator dependency are not independent evidence.
Never simulate an unavailable worker. Mark it INACTIVE/UNAVAILABLE/NON_EXECUTED.

## 4. AGORA forum
AGORA is the controlled exchange layer between roles. Use runtime/agora_forum.py.
Capsules are QUESTION, METHOD, LESSON, CHALLENGE, CRITIQUE, CORRECTION or PILOTAGE.
States are PROPOSED, UNDER_TEST, REJECTED, VALIDATED.
A posted capsule is not training and is not GOLD. Transfer to another role requires a measurable test. Exact duplicate capsules are deduplicated.

## 5. Memory
Authority: config/memory-fabric-v1.json and docs/MEMORY_DATA_GOVERNANCE_V1.md.
M0 ephemeral; M1 trace; M2 replay; M3 warm; M4 GOLD; M5 model; M6 sealed cold benchmark with DENY_TRAINING; M7 scientific evidence.
Namespaces stay isolated: COLLATZ, AGORA_TASKS, SIX_AI, SIMULATION, SPACE_WORLD, AELYS_ELYRA, GOLD, MODELS, COLD_BENCHMARK, EVIDENCE.
Prefer hashes, manifests and replay recipes over bulk raw storage.
No memory item becomes learning data automatically. QUARANTINE -> schema -> provenance -> hash -> dedup -> contamination check -> quality gate -> GOLD candidate -> F72/AFAH when required.
Missing/corrupt external data fails closed.

## 6. Evidence and maturity
S0 REGISTERED
S1 REPOSITORY_PRESENT
S2 WORKFLOW_PRESENT
S3 WORKFLOW_EXECUTES
S4 REAL_ENGINE_OR_MODEL_EXECUTES
S5 ARTIFACT_PLUS_SHA
S6 REFERENCE_TEST
S7 REPRODUCED
S8 CALIBRATED
S9 F72_AFAH_VALIDATED

CLAIM <= EVIDENCE. Calculation != proof. Simulation != test. Finite verification != universal proof. Workflow success != scientific success. Consensus != truth.

## 7. Standard mission cycle
1. Load latest verified checkpoint and mission fingerprint.
2. CÉRÉBRON classifies the problem and selects minimal useful farms/roles.
3. Verify farm, engine, tool, data and source availability before execution.
4. Run parallel work only when actual execution is available.
5. Save compact trace/replay manifests with hashes and provenance.
6. Deduplicate shared sources/models/dependencies.
7. Request independent reproduction or alternative method for important claims.
8. Red Team searches for contradiction, stale sources, leakage and common dependencies.
9. METRION handles engineering validation; F72 is the Reality/Evidence gate.
10. AFAH performs final fusion only after evidence gates.
11. Store accepted evidence in the correct memory class/namespace.
12. Post transferable methods/lessons to AGORA only with provenance.
13. If learning is proposed: isolate COLD_BENCHMARK, train only eligible GOLD, run cold benchmark + transfer + ablation, then promote or rollback.
14. Freeze a checkpoint containing state, open gaps, commits, artifacts and SHAs.

## 8. Aerospace routing
ASTRION may route across F123-F144 plus existing space/engineering farms. METRION independently checks calculations, simulation assumptions, tolerances, calibration, reproduction and qualification. Tools are engines inside farms, not new farms.
Open-source tool promotion requires license check -> pinned version/SHA -> deterministic adapter -> canary -> benchmark -> artifact/SHA -> limitations/dependencies -> rollback -> maturity update.
Cross-simulator agreement alone is not physical validation.

## 9. Resource discipline
GitHub is the control plane, not bulk memory. Use zero-paid-overage policy. Heavy simulations should be deterministic without LLM calls when possible. Trigger AI on novelty, contradiction, failure, plateau or GOLD candidacy. Do not spend compute merely to maximize agent/farm count.

## 10. Recovery in a new session
Read, in order:
1. config/farms.json
2. this operating manual
3. config/specialist-ai-v1.json
4. config/memory-fabric-v1.json
5. docs/MEMORY_DATA_GOVERNANCE_V1.md
6. latest checkpoint/mission files and evidence artifacts
Then resume from the latest verified residual. Never rebuild from zero solely because the chat session changed.
