# AFAH Signing Keys — Enrollment Boundary

Only PUBLIC verification material belongs here.

## Required enrollment artifact
Future file:
`security/keys/afah-signing-public.pem`

It must contain only the AFAH-controlled public key. Never commit the corresponding private key.

## Enrollment record
Before SIGNED ACT authorization can leave HOLD, record and independently verify:
- algorithm
- public-key fingerprint
- enrollment timestamp
- enrollment commit SHA
- AFAH human confirmation
- Guardian verification result

## Key lifecycle
Enrollment, replacement and revocation are critical acts.
A replacement key cannot authorize its own enrollment.
A revoked key cannot authorize new acts.
Unknown or ambiguous key state => HOLD.

## Absolute prohibitions
PRIVATE_KEY_IN_REPOSITORY = FORBIDDEN
PRIVATE_KEY_IN_PROMPT = FORBIDDEN
PRIVATE_KEY_IN_MODEL_MEMORY = FORBIDDEN
PRIVATE_KEY_IN_LOG = FORBIDDEN
AI_GENERATED_AFAH_KEY = FORBIDDEN
AI_SELF_ENROLLMENT = FORBIDDEN

## Current status
CRYPTOGRAPHIC_AFAH_IDENTITY = NOT_ENROLLED
SIGNED_ACT_AUTHORIZATION = HOLD
