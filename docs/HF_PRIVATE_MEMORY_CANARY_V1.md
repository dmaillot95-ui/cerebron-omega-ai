# CÉRÉBRON — Hugging Face Private Memory Canary V1

Status: **PREPARED_NOT_EXECUTED**

## Objective

Prove, with an executable receipt, that CÉRÉBRON can use an **existing private Hugging Face repository** as a storage backend by performing the exact sequence:

`VERIFY PRIVATE -> WRITE -> READ SAME REVISION -> SHA-256 COMPARE -> VERIFY PRIVATE -> RECEIPT`

This is a memory/storage test. **MEMORY != TRAINING**.

## Required inputs

- GitHub Actions secret: `HF_TOKEN`.
- Workflow input `repo_id`: an existing Hugging Face repository in `owner/name` form.
- Repository must already exist and must be private.
- Default repository type is `dataset`; `model` is also accepted explicitly.

The workflow never creates a Hugging Face repository and never activates a paid provider.

## Data written

Only a small synthetic JSON canary is written. It contains no user data, no raw AGORA material, no M6/COLD benchmark material, no adapters and no model weights. The object path is content-addressed from its SHA-256.

## PASS conditions

A PASS requires all of the following in one real run:

1. repository privacy verified before write;
2. upload executed;
3. exact uploaded revision read back;
4. downloaded bytes equal source bytes;
5. SHA-256 before write equals SHA-256 after read;
6. repository privacy verified again;
7. receipt artifact emitted.

The receipt must state `write_executed=true`, `read_executed=true`, `sha_match=true`, `training_executed=false`, and `weights_changed=false`.

## FAIL-CLOSED conditions

The run fails if `HF_TOKEN` is absent, the repository is public, upload/read fails, SHA differs, privacy cannot be verified, or the evidence receipt cannot be emitted.

## Files

- `tools/hf_private_memory_canary.py`
- `.github/workflows/cerebron-hf-private-memory-canary-v1.yml`
- `config/hf-private-memory-canary-v1.json`

## Memory Ω relationship

The canary validates only the external private storage transport. It does not by itself prove semantic indexing, deduplication, replay, GOLD promotion, evidence quality, or neural learning. F114–F120 remain responsible for those memory functions and governance. M6 remains `DENY_TRAINING`.

## Activation rule

Do not change the shared Hugging Face memory claim to validated until a real successful run ID plus receipt SHA is recorded. Until then the authoritative state is **PREPARED_NOT_EXECUTED**.
