# GUARDIAN Ω — LAST VALIDATED STATE

Purpose: provide a deterministic rollback anchor that an AI cannot self-declare as trusted.

## Record
A validated-state record MUST contain:
- checkpoint_id
- commit_sha
- created_at
- source_state_id
- evidence_manifest_hash
- policy_hash
- guardian_decision
- cerebron_audit
- afah_approval
- previous_checkpoint_id

## Promotion rule
A candidate state may become LAST_VALIDATED_STATE only when:
1. CYBER_VIGIE is PASS/NORMAL;
2. reproduction PASS;
3. reality gate PASS;
4. ablation PASS;
5. transfer PASS;
6. GUARDIAN policy invariants are intact;
7. CEREBRON audit is PASS;
8. AFAH approval is explicitly recorded.

No model-generated text, consensus, workflow success, age, score, or repetition can substitute for item 8.

## Integrity
The record uses SHA-256 hashes for evidence and policy manifests.
A hash proves byte-level integrity only; it does not prove truth.
The Git commit SHA and previous_checkpoint_id form an auditable chain.

## Rollback
On QUARANTINE, privileged promotion/memory writes stop.
Rollback may target only the most recent record satisfying this protocol.
If no validated record exists: HOLD, do not invent a target.

## Authority
AI_CAN_PROPOSE_CHECKPOINT = TRUE
AI_CAN_SELF_APPROVE_CHECKPOINT = FALSE
AFAH_APPROVAL_REQUIRED = TRUE
UNKNOWN_ROLLBACK_TARGET = HOLD
