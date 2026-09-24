# CEREBRON PI-SEARCH V1

## Purpose
PI-SEARCH is the shared search-space calculator for CEREBRON AIs. It combines deterministic angular coverage (PI-SWEEP) and reproducible Monte-Carlo sampling (PI-NEEDLE).

It is a search heuristic, not an oracle. Pi does not certify truth and the system does not claim that all answers are encoded in pi.

## Common flow
PROBLEM -> PI-SWEEP -> PI-NEEDLE -> candidate generation -> common scoring -> diversity filter -> local refinement -> ELYSIUM Red Team -> OMEGA evidence gate -> CEREBRON fusion.

## Shared defaults
- planar sweep: 16 directions over 0..2pi
- Monte-Carlo needles: 512
- spherical search: 32 directions
- local refinement: 9 samples around selected sectors
- reproducibility: task ID deterministically defines PI-NEEDLE seed

## Interpretation
An angle is a search direction/operator, not a truth value. Different AIs may answer the same angle differently. Agreement is not independent evidence.

## Runtime freeze
PI-SEARCH lives in tools/ and config/. It does not modify runtime/. Any AI that cannot execute the shared tool must state PI_SEARCH_UNAVAILABLE rather than simulate a run.

## Evidence
Every real PI-SEARCH execution should preserve task_id, seed, parameters, result SHA, candidate IDs, model/agent IDs, scores, rejected sectors, surviving sectors, and downstream audit receipts.

## Promotion
No candidate is promoted because it was found by PI-SWEEP or PI-NEEDLE. Promotion requires ordinary CEREBRON verification, falsification, reproduction where applicable, and CLAIM <= EVIDENCE.
