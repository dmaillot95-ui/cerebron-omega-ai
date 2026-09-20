# CÉRÉBRON ΑΩ — AGORA FARM/MENTOR BRIDGE
Version: 1.0
Date: 2026-09-20
Status: DESIGN_ACTIVE
Privacy: PRIVATE_BY_DEFAULT

## Two clocks
FARM CLOCK target: 5-minute internal learning/communication cycles where the farm workflow actually supports that cadence.
MENTOR CLOCK: M1 H:00, M2 H:12, M3 H:24, M4 H:36, M5 H:48.

The two clocks exchange checkpoint packets; they are not treated as independent evidence merely because they run at different times.

## Farm-side route
Primary infrastructure candidates:
- Farm 59 verified-learning: learning-gate and lesson qualification.
- Farm 66 knowledge-graph-vector-index: provenance/dependency/lesson indexing.
- Farm 67 cross-farm-communication: AGORA question/answer transport.
- Farm 68 autonomous-experiment-orchestrator: exercise/experiment routing.
- Farm 70 theorem-proof-engineering: proof-oriented training.
- Farm 71 scientific-reproduction: independent reproduction.
- Farm 72 reality-evidence-gate: evidence promotion gate.
- Farm 74 session-memory-encyclopedia: long-lived validated learning memory.

These farms are currently registry SCAFFOLDED/PLANNED where indicated. This document does NOT mark them operational.

## Five-minute farm packet
CYCLE_ID
TIMESTAMP
COLONY
RESOURCE_ID
TASK
LEVEL_L0_L8
INPUT_LESSON_IDS
ATTEMPT
CLAIMS
EVIDENCE_IDS
QUESTIONS_OUT
ANSWERS_IN
ERRORS
ANTI_ERROR_RULES
TRANSFER_TEST
AUDIT_STATUS
NEXT
PROVENANCE

## Mentor ingress
M1 reads latest valid farm checkpoints and teaches.
M2 evaluates novel transfer performance.
M3 attacks claims and learning.
M4 routes cross-colony questions.
M5 freezes the pedagogical checkpoint and recalibrates.

If a mentor cannot access a farm checkpoint, it records NON_ACCESSIBLE and must not fabricate activity.

## Mentor egress
Each mentor produces:
MENTOR_ID
CYCLE_WINDOW
COLONIES_TOUCHED
LESSONS
CORRECTIONS
QUESTIONS
ROLLBACKS
PROMOTION_CANDIDATES
NEXT_TASKS
EVIDENCE_LINEAGE

Farm-side orchestration may consume this packet only when actually available through implemented infrastructure.

## Auto-improvement gate
No self-improvement claim from activity count.
A change is retained only when:
1. it improves a novel/cold task;
2. provenance is intact;
3. audit passes;
4. Red Team does not expose a critical failure;
5. matched ablation supports incremental value;
6. no benchmark leakage is detected.

## Anti-loop
Repeated failure on the same concept:
FAIL1 -> correction
FAIL2 -> simpler prerequisite
FAIL3 -> alternate representation/teacher
FAIL4 -> HOLD + diagnostic
No infinite repetition.

## Difficulty controller
>=90% + Red Team PASS -> increase difficulty.
75-89% -> maintain level with novel transfer.
50-74% -> targeted correction.
<50% -> prerequisite rollback.
Critical hallucination/provenance failure -> immediate RED + rollback regardless of score.

## Cross-colony learning
Imported lesson != independent evidence.
Imported answer must retain SOURCE_LINEAGE.
Independent reproduction requires a clean reconstruction without the imported derivation.

## AFAH
AFAH remains final human authority. Automated loops may teach, test, route and recommend promotion; they do not override AFAH permissions or evidence gates.
