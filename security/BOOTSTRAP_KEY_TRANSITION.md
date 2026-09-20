# AFAH BOOTSTRAP KEY TRANSITION

## Verified bootstrap state
A GitHub Actions bootstrap run successfully generated an AFAH Ed25519 keypair artifact.
The bootstrap artifact is temporary and is NOT itself an authorization.

## Required transition
1. AFAH downloads the bootstrap artifact.
2. AFAH stores AFAH_PRIVATE_KEY.pem privately.
3. AFAH replaces repository secret AFAH_SIGNING_PRIVATE_KEY with the complete private PEM.
4. AFAH runs AFAH Public Key Enrollment.
5. Enrollment derives only the public key and fingerprint.
6. Guardian verifies public material before signed-act authorization can progress.

## Fail closed
BOOTSTRAP_RUN_SUCCESS != KEY_ENROLLMENT
ARTIFACT_EXISTS != AFAH_POSSESSION_CONFIRMED
SECRET_NAME_EXISTS != VALID_PRIVATE_KEY
PUBLIC_KEY_ABSENT = HOLD
SIGNATURE_TEST_NOT_PASSED = HOLD

## Security
Never commit or print AFAH_PRIVATE_KEY.pem.
Never place it in AGORA, SAPHEIDE, model memory, prompts, issues, PRs, artifacts after bootstrap, or logs.
The temporary bootstrap artifact should be deleted/allowed to expire after AFAH has securely retained the key and completed enrollment.

## Next validation
A challenge/response signature test must be performed after public-key enrollment:
random challenge -> sign with repository secret -> verify with enrolled public key.
No privileged act is enabled merely by successful key derivation.
