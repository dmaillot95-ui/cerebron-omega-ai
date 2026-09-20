# CÉRÉBRON ΑΩ — FIRST WAVE COLONY BENCHMARK
Version: 1.0
Date: 2026-09-20
Status: READY_FOR_EXECUTION

## Purpose
Measure whether a real assigned model/resource creates specialist value before any colony is promoted.

## Candidates
SIGMA
ARGUS
ANTITHESIS
REPLICA
BENCHMARK
MEMORIA
CHEMIA
MATERIA
MOTORIS
INDUSTRIA

## Protocol
For each candidate:
1. Record exact model/resource identity and version.
2. Freeze a baseline without the candidate colony.
3. Run the same task with the candidate routed.
4. Keep COLD_TEST and RED_TEAM_HOLDOUT unseen.
5. Audit outputs and provenance.
6. Run counter-audit.
7. Reproduce strongest claim independently where applicable.
8. Measure incremental value.
9. Perform ablation: remove candidate and repeat matched evaluation.
10. Promote only if gain survives audit and ablation.

## Common metrics
correctness
calibration
evidence_quality
reproducibility
independence
transfer
contradiction_rate
hallucination_error_rate
cost
latency

## Specialist test families
SIGMA: exact proof checking, quantifiers, lemma composition.
ARGUS: seeded mathematical/logical/data errors.
ANTITHESIS: adversarial attacks against plausible claims.
REPLICA: cold reconstruction from minimal evidence packet.
BENCHMARK: leakage detection, matched evaluation, scoring consistency.
MEMORIA: retrieval with provenance, contradiction preservation, no source invention.
CHEMIA: stoichiometry, thermodynamics, kinetics, structure-property reasoning, analytical interpretation.
MATERIA: phase/property reasoning, fatigue/corrosion tradeoffs, composites, manufacturing-property links.
MOTORIS: electric/thermal motor and propulsion calculations, efficiency/thermal/mechanical tradeoffs.
INDUSTRIA: process design, throughput, bottlenecks, reliability, quality, industrialization.

## Promotion gates
EXPERIMENTAL requires a real assigned resource plus baseline.
VALIDATED requires measurable cold-test specialist gain, audit, no leakage.
ACTIVE requires validated gain, routing rule, cost/latency record and rollback target.

## Evidence rule
A high score alone is insufficient. Preserve test IDs, outputs, evidence lineage, audit verdicts and ablation result.

## Current state
No candidate is promoted by this document.
Execution status remains determined by config/colonies.json and real benchmark artifacts.
