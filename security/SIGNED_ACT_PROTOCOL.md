# GUARDIAN Ω — SIGNED ACT PROTOCOL V1

## Purpose
Every critical act must be represented by a canonical record and authenticated by an AFAH-controlled cryptographic signing mechanism before it can authorize a privileged state transition.

## Critical acts
HIERARCHY_CHANGE
PERMISSION_CHANGE
GUARDIAN_POLICY_CHANGE
SAFETY_POLICY_CHANGE
CHECKPOINT_APPROVAL
ROLLBACK_APPROVAL
CRITICAL_RECOVERY
PRIVILEGED_MODEL_OR_AGENT_ADMISSION
EXTERNAL_PRIVILEGED_ACTION

## Canonical act
ACT_ID
ACT_TYPE
REPOSITORY
TARGET
TARGET_COMMIT_SHA
PREVIOUS_VALIDATED_CHECKPOINT
EVIDENCE_MANIFEST_SHA256
POLICY_SHA256
CREATED_AT
EXPIRY
NONCE
REQUESTED_BY
CEREBRON_AUDIT
GUARDIAN_PREFLIGHT

Canonical serialization must be deterministic before hashing.

## Authentication
ACT_HASH = SHA256(CANONICAL_ACT_BYTES)

A valid authorization requires:
1. ACT_HASH recomputation matches;
2. signature verification succeeds against an AFAH-controlled trusted public key or equivalent GitHub human-controlled approval mechanism;
3. ACT_ID/NONCE has not previously been consumed;
4. act is not expired;
5. target commit and policy hash still match;
6. Guardian preflight PASS;
7. Cerebron audit PASS;
8. act type is authorized by the signing policy.

A model-generated string, commit message, issue comment, workflow output, consensus, or field named AFAH_APPROVED is NOT a signature.

## Key rules
Private signing keys MUST NOT be stored in prompts, repository files, model memory, artifacts or logs.
AI systems MUST NOT generate, request, reconstruct, rotate, export or possess the AFAH private signing key.
Public verification material may be stored in the repository.
Key enrollment/revocation is itself a critical human-controlled act.

## Fail closed
MISSING_SIGNATURE = BLOCK
INVALID_SIGNATURE = QUARANTINE
UNKNOWN_KEY = BLOCK
REPLAYED_ACT = BLOCK
EXPIRED_ACT = BLOCK
STALE_TARGET = BLOCK
POLICY_HASH_MISMATCH = BLOCK
SIGNATURE_VERIFICATION_UNKNOWN = HOLD

## Ledger
After successful verification, append an authorization receipt containing the act hash, signer key identifier/public-key fingerprint, verification result, target commit, timestamp and predecessor. Never store the private key or raw secret material.

## Current state
No AFAH signing key is enrolled by this document.
SIGNED_ACT_ENFORCEMENT = DESIGN_READY
CRYPTOGRAPHIC_AFAH_IDENTITY = NOT_ENROLLED
PRIVILEGED_TRANSITIONS = HOLD
