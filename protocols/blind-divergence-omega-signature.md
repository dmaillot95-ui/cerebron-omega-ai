# CÉRÉBRON ΑΩ — Blind Divergence / Independent Convergence / Ω Signature

Status: ACTIVE DESIGN RULE
Date: 2026-09-20

## Purpose
Allow multiple farms/colonies to receive the same mission while preserving independent search trajectories long enough to measure genuine convergence.

## Protocol
1. SAME MISSION — distribute the identical frozen problem statement.
2. BLIND DIVERGENCE — colonies do not read peer conclusions during the exploration window.
3. 15 CYCLES — default divergence window. Each cycle records hypotheses, derivations, failures, counterexamples and evidence IDs.
4. LOCAL FREEZE — each colony freezes its result before seeing peer work.
5. CONVERGENCE MAP — cluster equivalent conclusions and identify materially different derivations.
6. DEPENDENCY AUDIT — shared premises, datasets, prompts, models, code and prior lemmas reduce independence weight.
7. COUNTER-AUDIT — dedicated adversarial colonies try to break each convergent claim.
8. INDEPENDENT REPRODUCTION — reconstruct selected claims without the originating derivation.
9. Ω SIGNATURE — assign a convergence signature only after audit and reproduction.
10. FUSION — validated knowledge enters AGORA/Memory; unresolved contradictions become new missions.

## Core rule
CONSENSUS != PROOF.
Repeated answers sharing one evidence lineage count as one lineage, not many independent confirmations.

## Measurements
- DIVERSITY
- INDEPENDENCE
- REPRODUCIBILITY
- CONTRADICTION_RATE
- FALSIFICATION_SURVIVAL
- TRANSFER
- COST
- LATENCY
- EVIDENCE_LEVEL E0..E8

## SPIRALIX result packet
TASK -> HYP -> CLAIM -> EVID -> FAIL -> RED -> REPRO -> SYNTH -> FREEZE -> OMEGA_SIGNATURE -> LESSON -> NEXT

## Ω Signature record
For every candidate convergence store:
- claim_id
- participating colonies/farms
- evidence lineages
- derivation fingerprints
- shared dependencies
- independent dependencies
- audit result
- counter-audit result
- reproduction result
- evidence level
- unresolved unknowns
- next falsification test

## Learning loop
Validated convergence -> AGORA lesson -> novel exercises -> cold benchmark -> before/after comparison.
A lesson is retained as training knowledge only when it survives the evidence gates. Failed paths go to GRAVEYARD with the failure cause and reusable anti-error rule.

## Privacy
PRIVATE BY DEFAULT. No public exposure of CÉRÉBRON, SAPHEA MICRO, AGORA internals, private datasets, prompts, keys or memories without explicit AFAH authorization.
