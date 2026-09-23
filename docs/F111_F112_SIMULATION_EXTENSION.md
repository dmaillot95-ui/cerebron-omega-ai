# CÉRÉBRON F111/F112 — simulation extension

Status: PLANNED_REPOSITORY_REQUIRED

## F111 Humanoid Head & Face Simulator
Scope: ocular gaze, eyelids, jaw, facial actuation, synthetic-skin deformation interfaces, neck/head kinematics, sensor/actuator timing, expression trajectories, safe mechatronic limits.
Reference inspiration: user-provided Galika visual only; do not infer hidden construction from appearance.
Required gates: geometry/kinematics -> actuator model -> ocular reference tests -> timing/replay -> fault injection -> physical calibration before physical claims.

## F112 Cognitive / Thought Simulator
Scope: observable computational reasoning processes only: working-memory state, competing hypotheses, evidence retrieval, attention allocation, planning, tool routing, contradiction detection, revision, red-team branch, convergence and uncertainty.
Explicit non-claim: does not simulate or establish consciousness, subjective experience, sentience, or human-equivalent cognition.

### Minimal state
problem_state -> observations -> working_memory -> hypothesis_set -> evidence_links -> candidate_actions -> critic/red_team -> revision -> decision_state -> residual_unknowns

### Measurements
accuracy, evidence coverage, contradiction recovery, calibration, compute/tool cost, latency, branch diversity, convergence stability, transfer score.

### Coupling
F112 may request experiments from simulator farms; results return as evidence. F111 may act as a humanoid interface/embodiment simulator. Neither is evidence of consciousness.

CLAIM <= EVIDENCE. SIMULATION != TEST. WORKFLOW SUCCESS != SCIENTIFIC VALIDATION.
