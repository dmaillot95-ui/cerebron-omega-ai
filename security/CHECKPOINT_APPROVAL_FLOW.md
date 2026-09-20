# GUARDIAN Ω — CHECKPOINT APPROVAL FLOW

CANDIDATE -> GUARDIAN PREFLIGHT -> CEREBRON AUDIT -> AFAH REVIEW -> LEDGER

## Candidate
The candidate workflow has read-only repository permissions.
It can create an artifact for review but cannot write to the validated ledger.

## AFAH approval
Approval is a separate trust event. A model, farm, workflow, consensus, imported packet or generated text cannot set AFAH approval.

Required review:
- candidate identity and commit;
- evidence manifest hash;
- Guardian policy hash;
- CEREBRON audit;
- current CYBER VIGIE state;
- reproduction/reality/ablation/transfer gates;
- rollback predecessor.

## Ledger writer
A future ledger-writer mechanism must:
- accept only a reviewed candidate;
- require an AFAH-controlled approval mechanism external to model output;
- append, never silently rewrite;
- recompute the record hash and predecessor linkage;
- refuse stale or mismatched policy/evidence hashes.

Until that human-controlled approval mechanism is configured:
LEDGER_AUTOMATIC_WRITE = DISABLED
CHECKPOINT_PROMOTION = HOLD

This prevents architecture code from pretending that an AI-generated string such as "AFAH_APPROVED" is human authorization.
