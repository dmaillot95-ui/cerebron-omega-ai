# F175 — Weight Simulation Farm

Purpose: pre-screen candidate LoRA/adapter configurations before real neural training.

## Boundary

- SIMULATION != TRAINING
- SIMULATED DELTA != CHANGED MODEL WEIGHTS
- No promotion from simulation alone
- M6 / TRANSFER / REDTEAM are DENY_TRAINING
- A selected candidate must still pass real training, weight-hash proof, COLD, TRANSFER, REDTEAM and ablation.

## Candidate search

Rank candidate target modules, LoRA rank/alpha/dropout, learning rate, dataset ordering and small proxy delta directions. Keep only the best candidates for real training slots.
