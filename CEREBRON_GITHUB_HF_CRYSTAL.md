# CÉRÉBRON ΑΩ — CRISTAL GITHUB × HUGGING FACE
Version: 1.0
Authority: AFAH
Status: OPERATING RULE

## 1. Purpose
GitHub is the public/non-sensitive control plane. Hugging Face PRIVATE is the persistent data plane.
Every CÉRÉBRON component must be reconstructible from a minimal GitHub state plus its authorized private Hugging Face state.

## 2. Absolute privacy rule
PRIVATE BY DEFAULT.
Never put private prompts, private memories, private datasets, secrets, tokens, private adapters, derived weights, or confidential payloads in public GitHub repositories.
GitHub stores only code, schemas, routing, audit records and opaque non-sensitive pointers.
Private payloads go to authorized private Hugging Face repositories.
Secrets remain GitHub Actions secrets or equivalent secret stores and are never copied into memory.

## 3. CRISTAL rule
Every durable change follows:
READ VERIFIED STATE → LOCK VERSION → EXECUTE → CLASSIFY → AUDIT → HASH → WRITE PRIVATE STATE → READ-BACK → VERIFY HASH → WRITE OPAQUE POINTER → INDEX → COMMIT → BROADCAST.
Changes must be traced, testable, auditable and reversible.
UNKNOWN=DENY. CLAIM<=EVIDENCE.

## 4. Minimum memory retained for every created AI / SAPHEA MICRO
Each real AI receives its own namespace:
colony/{COLONY_ID}/agents/{AGENT_ID}/

Retain only the minimum useful state:
- immutable identity: colony, agent/SAPHEA role, model ID and pinned revision;
- mission and root objective;
- current verified checkpoint;
- active assumptions;
- validated methods/skills actually useful to its role;
- falsified paths and important failures;
- open contradictions;
- smallest remaining gap and current bottleneck;
- next decisive test;
- evidence/provenance references and dependency fingerprint;
- benchmark/ablation/transfer results;
- last validated memory generation;
- rollback point;
- adapter/LoRA/derived-weight reference only when training produced measured validated gain.

Do not accumulate raw conversation history by default. Compress before accumulation.

## 5. Three distinct states
WORKING MEMORY: temporary, local to execution, not trusted.
VALIDATED MEMORY: private HF object after provenance/audit gates.
PARAMETRIC MEMORY: private adapter/LoRA/derived weights; never equate it with validated knowledge.

MEMORY != LEARNING.
TRAINING != PROOF.
SAME MODEL+PROMPT+DATA != INDEPENDENT EVIDENCE.

## 6. Hugging Face private layout
cerebron-omega/cerebron-private-memory:
- colony/{COLONY_ID}/shared/
- colony/{COLONY_ID}/agents/{AGENT_ID}/memory/
- colony/{COLONY_ID}/agents/{AGENT_ID}/checkpoints/
- colony/{COLONY_ID}/agents/{AGENT_ID}/skills/
- colony/{COLONY_ID}/audit/

Derived trained artifacts belong in an authorized PRIVATE HF repository/namespace and are referenced by immutable revision/digest.

## 7. GitHub minimum state
For each AI GitHub keeps only:
- agent ID and role;
- colony ID;
- provider/model ID and immutable revision when non-sensitive;
- HF opaque object reference when non-sensitive;
- SHA-256/digest;
- evidence/audit status;
- generation/version;
- rollback pointer;
- timestamps/workflow/run IDs where applicable.
No private payload is duplicated into GitHub.

F66 = index/relations.
F74 = validated memory catalog/pointers.
HF PRIVATE = actual private memory and trained artifacts.

## 8. Recall
AI → colony router → F66 → F74 → authorized HF PRIVATE object → SHA-256 verification → minimum relevant retrieval → AI context.
Retrieve only what the mission needs.

## 9. Write
AI candidate memory → classify → reject secrets → provenance → audit/counter-audit when required → compress → hash → HF PRIVATE write → authenticated read-back → digest verification → F74 opaque catalog pointer → F66 index → recall test.
A failed gate leaves the candidate unpromoted.

## 10. Training
Do not train merely because data exists.
Training requires a defined deficit and baseline.
BASELINE → TRAIN/ADAPTER → COLD BENCHMARK → AUDIT → RED TEAM → ABLATION → TRANSFER.
Promote G(n+1) only if measured gain survives gates. Otherwise rollback to G(n).

## 11. Colony isolation and sharing
Each colony keeps its own learned memory and agent namespaces.
Cross-colony knowledge is imported with provenance and is never counted as independent reproduction.
Shared validated lessons are routed through F66/F74/AGORA, not copied blindly into every agent.

## 12. Concurrency
One HF channel per colony execution.
Global ceiling: 20 simultaneous colony HF slots.
Excess requests queue. Use adaptive backoff. Concurrency never weakens audit or privacy gates.

## 13. Lifecycle
INACTIVE → EXPERIMENTAL → VALIDATED → ACTIVE.
No AI/colony is announced as active without a real bound resource and benchmark evidence.
No simulated agent counts as execution.

## 14. AFAH authority
AFAH remains final authority.
No model, farm, colony, chief, workflow or AGORA process may self-promote privileges, weaken GUARDIAN, publish private artifacts, or override AFAH authorization.

## 15. Operational invariant
GITHUB = MINIMUM CONTROL STATE.
HUGGING FACE PRIVATE = DURABLE PRIVATE MEMORY + APPROVED TRAINING ARTIFACTS.
AGENT CONTEXT = MINIMUM RELEVANT RECALL.
CRISTAL = TRACE + HASH + AUDIT + ROLLBACK.
