# CÉRÉBRON MODEL GATEWAY
Version: 1.0
Status: DESIGNED_NOT_CONNECTED

## Purpose
One central model gateway serves farms and SAPHEA MICRO without copying neural-network weights into the 74 Git repositories.

## Route
FARM / COLONY -> MODEL GATEWAY -> APPROVED PROVIDER -> MODEL + OPTIONAL ADAPTER -> EXECUTION -> EVIDENCE/METRICS -> AGORA.

## Storage separation
GitHub: orchestration, configuration, immutable model references, hashes, recipes, metrics, compact checkpoints and validated memory.
External model store: base weights, adapters/LoRA and large model artifacts.
Compute runner: temporary execution/training cache only.

## Model identity
Every usable model record must contain:
provider
model_id
immutable_revision
license
task/capability
weight_location
runtime requirements
context limit when known
quantization when applicable
cost class
availability
benchmark IDs
audit status

Never use a floating model reference as reproducible evidence when an immutable revision can be recorded.

## Adapter strategy
Prefer a shared validated base model plus small specialized adapters when benchmark evidence shows this is sufficient.
ADAPTER != NEW INDEPENDENT BASE MODEL.
Every adapter records base_model_id, base_revision, training_dataset lineage, recipe, metrics and digest.

## Farm request
A farm requests capability; it does not own a copy of the weights.
The gateway selects only among actually registered/available resources.
If none exists, return UNAVAILABLE. Never simulate a model.

## Memory
F66 may index model/evidence relationships.
F74 may retain validated model-selection and training history.
Neither should duplicate large weight files.

## Security
Tokens/credentials are never stored in repository files.
Provider access is read from approved secret storage at runtime.
Downloaded weights must not be committed by workflows.

## Promotion
DISCOVER -> IDENTIFY -> LICENSE/CAPABILITY CHECK -> BASELINE -> COLD BENCHMARK -> AUDIT -> RED TEAM -> ABLATION -> TRANSFER -> APPROVE/BIND.

## Current truth
The gateway architecture now exists, but no Hugging Face connection or model availability is claimed until a real provider connection and model discovery run succeeds.
