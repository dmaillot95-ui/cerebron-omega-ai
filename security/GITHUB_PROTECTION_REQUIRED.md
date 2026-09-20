# GUARDIAN Ω — REQUIRED GITHUB PROTECTION

Status: REQUIRED / NOT YET VERIFIED
Repository: dmaillot95-ui/cerebron-omega-ai
Protected target: main

## Required human-controlled repository controls
Configure a GitHub ruleset or equivalent branch protection for main with:
- require pull request before merge;
- require approving review;
- dismiss stale approvals when new commits are pushed;
- require conversation resolution;
- block force pushes;
- block branch deletion;
- do not allow workflows/bots to bypass the rule;
- restrict bypass to the AFAH-controlled administrator account only, if GitHub plan/settings permit;
- protect changes under security/**, config/**, .github/workflows/** and checkpoint ledger through CODEOWNERS/review policy where supported.

## Critical files
/security/GUARDIAN_OMEGA_POLICY.md
/security/LAST_VALIDATED_STATE_PROTOCOL.md
/security/QUARANTINE_ROLLBACK_PROTOCOL.md
/security/checkpoints/**
/config/**
/.github/workflows/**

## Fail-closed rule
Until repository protection is independently verified:
HUMAN_GATE_VERIFIED = FALSE
LEDGER_AUTOMATIC_WRITE = DISABLED
CHECKPOINT_PROMOTION = HOLD
PRIVILEGED_RECOVERY = BLOCKED

No model output may change these states to TRUE/PASS.

## Verification evidence
Record:
- ruleset/protection identifier;
- enforcement status;
- target branch;
- required approvals;
- bypass actors;
- verification timestamp;
- verifier identity/source.

A documentation file is not proof that GitHub protection is active.
