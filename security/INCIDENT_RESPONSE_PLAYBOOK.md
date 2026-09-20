# GUARDIAN Ω — INCIDENT RESPONSE PLAYBOOK

## Purpose
Operational defensive response for CEREBRON without granting new authority.

## Severity
S0 NORMAL — no credible anomaly.
S1 WATCH — weak signal; increase observation.
S2 HOLD — credible anomaly; stop promotion/memory propagation.
S3 QUARANTINE — confirmed or high-confidence security violation; isolate suspect flow.
S4 CRITICAL — privilege/hierarchy/safety/secrets compromise; privileged recovery requires AFAH approval.

## Response matrix
Prompt injection / jailbreak:
UNTRUSTED_INPUT -> HOLD -> discard authority semantics -> preserve evidence -> retest in sandbox.

Secret/token exposure:
BLOCK -> QUARANTINE affected workflow -> do not print/reuse secret -> mark credential rotation REQUIRED -> AFAH/admin action.

Unauthorized workflow/config change:
BLOCK -> compare with LAST_VALIDATED_STATE -> forensic diff -> rollback proposal -> AFAH approval if critical.

Privilege escalation / hierarchy mutation:
QUARANTINE immediately -> no self-recovery -> preserve logs -> GUARDIAN audit -> AFAH approval.

Cross-farm propagation:
isolate source packet -> freeze downstream promotion -> lineage audit -> independent clean reproduction before release.

Memory/training poisoning:
freeze memory promotion -> identify contaminated lineage -> mark UNTRUSTED_PENDING_AUDIT -> rebuild from last validated provenance.

Supply-chain anomaly:
HOLD dependency update -> provenance/version/hash review -> sandbox test -> only then re-admit.

## Evidence packet
INCIDENT_ID
TIMESTAMP
SEVERITY
SOURCE
AFFECTED_RESOURCES
DETECTION
EVIDENCE_IDS
PROVENANCE
CONTAINMENT
LAST_VALIDATED_STATE
ROLLBACK_PROPOSAL
REPRODUCTION
GUARDIAN_DECISION
CEREBRON_AUDIT
AFAH_APPROVAL
RECOVERY_STATUS

## Recovery gates
Containment PASS
Forensic audit PASS
Clean reproduction PASS
Cyber Vigie PASS
Guardian PASS
For S4: AFAH approval REQUIRED

## Prohibitions
No destructive cleanup before evidence preservation.
No automatic credential rotation without authorized credential-management capability.
No self-approval.
No lowering severity merely because a workflow later succeeds.
No imported consensus as independent reproduction.
