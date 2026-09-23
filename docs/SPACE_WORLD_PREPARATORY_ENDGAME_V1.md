# CÉRÉBRON SPACE WORLD — PREPARATORY ENDGAME V1

Status: PREPARATORY PLAN / DO NOT CLAIM EXECUTION.

## Phase A — Reality and protocol
1. Verify F93-F95 runs/artifacts.
2. Verify F96-F100 repository/workflow maturity.
3. Keep F101-F110 registry/repository identity immutable.
4. Validate SPACE_STATE_V1 schema, hash-chain and replay rules.
5. Define cycle IDs, deterministic seeds, parent SHA and failure semantics.

## Phase B — Shared world
6. Implement F101 environment-state generator.
7. Implement F102 construction-plan consumer/producer.
8. Implement F103 lunar city reduced reference model.
9. Implement F104 Mars city reduced reference model.
10. Implement F105 industrial/material-flow model.
11. Implement F106 energy-grid reduced model; nuclear is system-level simulation only until qualified engine/reference data exists.
12. Implement F107 robot workforce task/state model.
13. Implement F108 ISRU/resource flow model.
14. Implement F109 logistics/inventory model.
15. Implement F110 fusion/checkpoint/residual generator.

## Phase C — Data and memory
16. Event packet schema + content-addressed hashes.
17. HOT/WARM/GOLD/COLD retention policy.
18. Deduplicate identical trajectories.
19. Keep seed/config/version/summary for reproducible regeneration.
20. Never mix cold benchmark data with training corpus.
21. Add quota/size guards before any recurring schedule.

## Phase D — E2E qualification
22. Run one manual deterministic F101→F110 cycle.
23. Replay same seed and require identical canonical hashes where deterministic.
24. Inject one missing/corrupt packet and require fail-closed behavior.
25. Run alternate seed and require changed world state.
26. Cross-check conservation/inventory/energy invariants.
27. F33 Red Team.
28. F35 replication.
29. F37 experiment design.
30. F72 evidence gate.
31. AFAH synthesis.
32. Only after PASS: enable recurring cadence.

## Phase E — 5-minute operation
33. Prefer one coordinator heartbeat every 5 minutes over ten independent cron storms.
34. Coordinator assigns logical slot/cycle and triggers only required farms.
35. Idempotency: duplicate cycle ID must not duplicate state.
36. Backpressure: if previous cycle unfinished, HOLD/SKIP rather than overlap.
37. Quota guard and emergency STOP.
38. Persist compact checkpoint after each completed cycle.
39. Periodic GOLD curator; raw bulk expires unless explicitly retained.

## Phase F — scientific growth
40. Replace toy models progressively with verified open-source engines/reference cases.
41. Calibrate each domain before scientific use.
42. Couple F93 multiphysics, F94 optimization, F95 failure, F96 worlds, F97 causal experiments, F98 scientist, F99 invention, F100 arena.
43. Measure whether larger coalitions beat smaller ones at comparable budget via F91/F92.
44. Promote learning only after cold/transfer/ablation/regression evidence.

## Handoff invariants
REALITY>COHERENCE
EVIDENCE>CONFIDENCE
CLAIM<=EVIDENCE
SIMULATION!=TEST
WORKFLOW_SUCCESS!=SCIENTIFIC_VALIDATION
MEMORY!=LEARNING
G0 immutable
F01-F07 protected
No paid services without explicit approval
No recurring 5-minute loop until E2E + quota guards PASS
