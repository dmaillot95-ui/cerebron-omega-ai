# CÉRÉBRON Memory Fabric
Status: DESIGNED_NOT_RUNTIME_VALIDATED

Memory is separated from model weights.

- Working memory: temporary, per colony.
- Validated memory: versioned records catalogued by F74 and related/indexed by F66.
- Parametric memory: model weights and LoRA/adapters in the approved external private model store once authenticated.

A colony namespace is provisioned lazily on its first validated write. This avoids creating 62 empty databases.

## Write path
COLONY -> provenance/evidence/audit gate -> F74 validated record -> F66 relation/index entry.

## Read path
COLONY -> F66 lookup -> F74 record -> referenced evidence/artifact.

## Rules
No secret is memory.
No large neural-network weights are committed as memory.
A model output is not validated memory by itself.
Imported/shared ancestry is recorded.
Memory updates are versioned and reversible.
F74 must not be called operational until a real write/read/recall test passes.
