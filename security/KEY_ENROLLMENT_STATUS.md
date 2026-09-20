# AFAH KEY ENROLLMENT STATUS

User reports that repository secret `AFAH_SIGNING_PRIVATE_KEY` has been configured.

This statement does NOT expose, read, or verify the secret value.

## Security state
PRIVATE_KEY_READ_BY_AI = FALSE
PRIVATE_KEY_VALUE_LOGGED = FALSE
SECRET_PRESENCE_REPORTED_BY_AFAH = TRUE
PUBLIC_KEY_ENROLLED = FALSE
CRYPTOGRAPHIC_AFAH_IDENTITY = NOT_YET_VERIFIED
SIGNED_ACT_AUTHORIZATION = HOLD

## Next gate
A public verification key must be derived/provided through a trusted human-controlled process and committed as:
`security/keys/afah-signing-public.pem`

The private key must never be echoed, uploaded as an artifact, committed, or printed in workflow logs.
