# CÉRÉBRON ΑΩ — MEMORY & DATA GOVERNANCE V1

Status: ARCHITECTURE POLICY / automatic external storage transport must be separately proven.

## Objective
Prevent continuous agents, Collatz, ChatGPT task agents, AI learning and simulator farms from saturating storage or contaminating validated memory.

## Memory classes
M0 EPHEMERAL: runner scratch, transient simulation frames, caches. TTL: end of run. Never memory.
M1 TRACE: compact run manifest, hashes, seed, config, metrics, errors. Keep compact and versioned.
M2 REPLAY: seed + simulator version + configuration + event log sufficient to regenerate bulk simulation. Preferred over retaining raw frames.
M3 WARM: compressed exceptional episodes and diagnostic samples. Bounded rolling retention.
M4 GOLD: validated examples admitted through provenance/dedup/audit gates. Small, immutable/versioned; candidate learning corpus.
M5 MODEL: weights/adapters/tokenizers and exact training manifests. Separate from simulation data.
M6 COLD BENCHMARK: sealed evaluation corpus; never mixed into training/GOLD.
M7 SCIENTIFIC EVIDENCE: proofs, reference cases, calibration evidence, F72/AFAH decisions; durable.

## Domain isolation
COLLATZ, AGORA/TASK-AGENTS, SIX-AI LEARNING, SIMULATION, SPACE-WORLD, AELYS/ELYRA, BENCHMARK and MODEL artifacts use separate namespaces. No automatic cross-domain promotion. Cross-domain reads require explicit manifest/provenance.

## Simulation rule
Do not retain continuous raw worlds by default. For each cycle store: cycle_id, farm, simulator/version, seed, config hash, parent/output hashes, summary metrics, rare/failure event references, replay recipe. Raw high-volume frames/sensor streams expire unless an event is selected for WARM/GOLD.

## Automatic access model
Farms write a small POINTER/MANIFEST, not bulk data, into the coordination plane. A storage adapter resolves the pointer to the external data plane. Reads are content-addressed by SHA and checked against namespace, schema and provenance before use. Missing/corrupt data => fail closed, never silently substitute another episode.

## Anti-drift gates
QUARANTINE -> schema -> provenance -> hash -> dedup -> domain isolation -> contamination check -> quality gate -> GOLD candidate -> F72/AFAH where required. Benchmark data has DENY_TRAINING=true. Simulation has SIMULATED=true until real-world evidence changes the epistemic status.

## Capacity policy
Budget by bytes/day, files/day, commits/day and requests/day, not only total GB. Each producer receives HARD_BUDGET, SOFT_WARNING and emergency STOP. When soft threshold is crossed: increase compression/sampling and retain only anomalies. At hard threshold: stop bulk persistence but keep minimal trace/replay manifests.

## Scheduling policy
Continuous workloads are separated into lanes: COLLATZ; AGORA/TASK; LEARNING; SIMULATION. Heavy lanes do not all write bulk artifacts every tick. Deterministic simulation should run without LLM calls when possible. AI is event-driven for contradiction, novelty, failure, plateau or GOLD candidacy.

## Retention defaults
TRACE: compact long-lived manifests.
RAW SIMULATION: 0-24h unless selected.
WARM: rolling bounded window.
GOLD: durable but curated.
MODEL: durable promoted versions; obsolete candidates pruned after rollback window.
BENCHMARK: durable sealed.
CACHE/ACTIONS artifacts: short retention; never primary memory.

## Required accounting
Every cycle reports bytes_generated, bytes_persisted, bytes_promoted_gold, files_created, API_requests, runtime_seconds, regeneration_cost_estimate, and retention_class. Daily controller aggregates per lane and system total.

## Fundamental rule
STORE THE MINIMUM INFORMATION NEEDED TO REPRODUCE, AUDIT OR LEARN. Regenerate deterministic bulk data from seed/config/version instead of archiving it.
