# AFAH KEY ENROLLMENT STATUS

## Verified state

Repository secret `AFAH_SIGNING_PRIVATE_KEY` is configured.

Public verification material is enrolled at:
`security/keys/afah-signing-public.pem`

Public-key SHA-256 fingerprint:
`44632c148985a7dbfdb4602887b6fde0d1d007537845e80c353703db3b0988bf`

Cryptographic challenge:
- workflow: `AFAH Cryptographic Challenge`
- run: `35517096408`
- tested commit: `603e967c3531fea23f7f67869e35273ed2ae1ae9`
- result: PASS

The challenge proves that the private key currently stored in the GitHub Actions secret matches the enrolled public key.

## Security state

PUBLIC_KEY_ENROLLED = TRUE
KEYPAIR_MATCH_VERIFIED = TRUE
CRYPTOGRAPHIC_AFAH_IDENTITY = KEYPAIR_VERIFIED
SIGNED_ACT_AUTHORIZATION = HOLD
HUMAN_INTENT_GATE_VERIFIED = FALSE

## Boundary

Keypair consistency is not equivalent to proof of human intent for a future privileged act.

The private key is available to workflows explicitly granted access to the repository secret. Therefore no workflow, model, farm, CEREBRON component or GitHub Action may treat possession of the secret alone as AFAH approval.

Critical state transitions remain HOLD until the human-controlled GitHub approval boundary or an equivalent non-delegable authorization mechanism is independently verified.

PRIVATE_KEY_IN_REPOSITORY = FORBIDDEN
PRIVATE_KEY_IN_LOG = FORBIDDEN
MODEL_SELF_APPROVAL = FORBIDDEN
WORKFLOW_SELF_APPROVAL = FORBIDDEN
