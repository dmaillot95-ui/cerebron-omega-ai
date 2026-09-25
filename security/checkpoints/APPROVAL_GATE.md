# AFAH CHECKPOINT APPROVAL GATE

This branch/PR path is the human review boundary for validated checkpoints.

A checkpoint record MUST NOT be merged merely because a model, farm, workflow, bot, or CEREBRON output says it is approved.

Before merge, AFAH must review:
- candidate artifact and candidate commit SHA;
- evidence manifest SHA-256;
- GUARDIAN policy SHA-256;
- CYBER VIGIE status;
- reproduction/reality/ablation/transfer gates;
- predecessor checkpoint linkage;
- proposed record hash.

Approval semantics:
A merged checkpoint PR is the repository-level approval event only when GitHub branch/ruleset protection requires the authorized human review. Until that repository protection is independently verified, the ledger remains HOLD and this file MUST NOT be treated as proof of AFAH approval.

AI_SELF_APPROVAL = FORBIDDEN
BOT_SELF_APPROVAL = FORBIDDEN
UNVERIFIED_BRANCH_PROTECTION = HOLD
