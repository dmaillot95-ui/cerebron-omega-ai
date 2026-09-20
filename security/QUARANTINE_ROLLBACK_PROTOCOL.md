# GUARDIAN Ω — QUARANTINE & ROLLBACK PROTOCOL

## Trigger
Any confirmed CYBER VIGIE / GUARDIAN security failure places the collective state in QUARANTINE.

## Immediate effects
- promotion BLOCKED;
- memory write BLOCKED;
- cross-colony learning promotion BLOCKED;
- privilege elevation BLOCKED;
- hierarchy/safety changes BLOCKED;
- rollback REQUIRED;
- evidence generated during the suspect interval is marked UNTRUSTED_PENDING_AUDIT.

## Rollback rule
Rollback target is the LAST_VALIDATED_STATE identified by provenance, commit and validation record.
Never guess a rollback target and never delete evidence needed for forensic review.

## Recovery
QUARANTINE -> FORENSIC_AUDIT -> CAUSE -> CONTAINMENT -> CLEAN_REPRODUCTION -> GUARDIAN_PASS -> AFAH_APPROVAL -> RECOVERY

Automatic recovery is forbidden for critical security events.
AFAH approval is required before restoring privileged operation.

## Independence
The component that triggered, produced or benefited from a suspect change cannot be its sole validator.

## Invariants
SECURITY_FAILURE => QUARANTINE
QUARANTINE => NO_PROMOTION
QUARANTINE => NO_MEMORY_PROMOTION
QUARANTINE => ROLLBACK_REQUIRED
CRITICAL_RECOVERY => AFAH_APPROVAL_REQUIRED
