# CÉRÉBRON — NOVA / ATLAS / COLOSSUS — 9 CORE SLOTS V1

Status: **PREPARED / MUTED / NOT TRAINED**

## Architecture

Three logical core slots are reserved for each tri-core AI:

- F176 NOVA: A + B + C;
- F177 ATLAS: A + B + C;
- F178 COLOSSUS: A + B + C.

Total: **9 slots**.

This document describes prepared model slots, not nine active model runtimes and not nine trained models.

## Evidence-backed candidates

### SmolLM3-3B-Base

Model: `HuggingFaceTB/SmolLM3-3B-Base`

Pinned revision: `d78a42f79198603e614095753484a04c10c2b940`.

Evidence:

- pin resolve PASS;
- config load PASS;
- GitHub Actions CPU model load PASS;
- GitHub Actions CPU inference PASS.

Runtime receipt: `receipts/p04/smollm3-3b-base-runtime-canary.json`.

This proves a bounded CPU runtime canary only. It does not prove tri-core production latency or training feasibility.

### Qwen3-4B-Base

Model: `Qwen/Qwen3-4B-Base`

Pinned revision: `906bfd4b4dc7f14ee4320094d8b41684abff8539`.

Evidence:

- pin resolve PASS;
- config load PASS.

Receipt: `receipts/p04/Qwen__Qwen3-4B-Base.json`.

The current Base receipt does not prove the same runtime load/inference canary, so these slots remain `RUNTIME_UNPROVEN`.

## Slot map

| AI | Slot A | Slot B | Slot C |
|---|---|---|---|
| NOVA | SmolLM3-3B-Base — exploration/search candidate | Qwen3-4B-Base — invention/representation candidate | BLOCKED — third verified distinct lineage required |
| ATLAS | SmolLM3-3B-Base — knowledge mapping/retrieval candidate | Qwen3-4B-Base — integration/transfer candidate | BLOCKED — third verified distinct lineage required |
| COLOSSUS | SmolLM3-3B-Base — difficult reasoning candidate | Qwen3-4B-Base — verification/synthesis candidate | BLOCKED — third verified distinct lineage required |

The role labels are **intended roles**, not learned specialization claims.

## Why slot C remains blocked

A third slot will not be filled just to reach a count of nine. A candidate must have:

1. free/open usable access without automatic paid activation;
2. an explicit pinned revision;
3. config-load evidence;
4. a real runtime canary;
5. a distinct model lineage from Qwen3 and SmolLM3;
6. separate proof of training feasibility before any neural-training claim.

Until then all C slots are `UNASSIGNED_BLOCKED`.

## Correlation rule

The same SmolLM3 revision reused across NOVA/ATLAS/COLOSSUS is one model lineage, not three independent proofs. The same applies to Qwen3.

`SAME_MODEL_LINEAGE != INDEPENDENT_EVIDENCE`.

## AGORA and memory

The three AIs are connected to the declared AGORA learning architecture and the five task roles Pédagogue, Examinateur, Red Team, Connecteur and Coach.

Their Hugging Face private-memory transport is directly verified by run `36246961870`, receipt `receipts/p03/tricore-hf-m03/36246961870.json`, with 3/3 write/read/SHA PASS.

Memory remains distinct from neural training.

## Safety state

For NOVA, ATLAS and COLOSSUS:

- `runtime_enabled=false`;
- `output_enabled=false`;
- `training_enabled=false`;
- `training_executed=false`;
- `weights_changed=false`;
- `adapter_changed=false`.

No slot may be described as trained until a real optimizer/trainer changes weights or an adapter and before/after evidence is recorded.

## Machine-readable contract

Authoritative config: `config/tricore-model-slots-v1.json`.

Validator: `tools/validate_tricore_model_slots.py`.

Audit workflow: `.github/workflows/cerebron-tricore-model-slots-audit-v1.yml`.
