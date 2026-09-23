# CÉRÉBRON ΑΩ — RELAY CHECKPOINT — 2026-09-23

## Purpose
Machine-readable human relay checkpoint for the next ChatGPT session. Continue; do not restart.

## Master state
- Master repo: dmaillot95-ui/cerebron-omega-ai
- Farm registry: config/farms.json v2.20; cap 144; no farm above 144.
- NVIDIA tools are shared engines, not farms.
- Open Tool Fabric: config/open-tool-fabric-v1.json.
- Epistemic rules: REALITY>COHERENCE; EVIDENCE>CONFIDENCE; CLAIM<=EVIDENCE; VERIFY BEFORE COMMIT; SIMULATION!=TEST; WORKFLOW SUCCESS!=SCIENTIFIC SUCCESS.

## F123-F144
All 22 farms have real S4 engine evidence. V2 reference-suite pass is complete after F143 corrected rerun.
F143 initial V2 failure was an incorrect acceptance threshold; calculation was correct. Corrected run 35863193847 passed: CBE 905 kg, with margins 1066 kg, margin 161 kg = 17.790055%.
Do not promote registry above S4 without explicit maturity audit.

## NVIDIA
OTF023 NVIDIA Warp: BENCHMARKED.
- F140 real Warp 1.17.0 reproduction run 35863323220: Bond number delta vs Python 3.363109270237974e-11; artifact 10751212890; result SHA a5694ce0079b8bf64dc5fc9f5c7d980dc89dd11fafe511d4008e30f73009565a.
- F140 dynamic Warp V2 run 35863637690: 2048 elements x 500 steps = 1,024,000 updates; CPU because GitHub runner has no CUDA driver; artifact 10750729687; result SHA 07517c81f3e595c8654d88e3e0095be00ba220103c33a009fc7a0b6023f5949f.
- Scope remains numerical simulation, not physical validation.

OTF024 NVIDIA PhysicsNeMo:
- First run 35863721541 failed because PyPI package physicsnemo is a sentinel. Correct package is nvidia-physicsnemo; imports remain import physicsnemo.
- Workflow corrected commit 2f758c4ae29a965316f5c18d2ee7d56f447d30c0.
- Corrected run 35864199488 is IN PROGRESS at checkpoint creation. VERIFY its final status before any claim.

OTF025 Newton and OTF026 NVIDIA Isaac Lab remain DISCOVERED only. Do not claim execution.

## Immediate continuation order
1. Verify PhysicsNeMo run 35864199488, logs, artifact, version and SHA.
2. If success: record OTF024 as BENCHMARKED only after a real numerical PhysicsNeMo workload, not merely import. If import only, record runtime available and create physics workload.
3. If failure: diagnose from logs, preserve trace, fix minimally.
4. Move from toy/reference equations toward real external scientific engines and independent reproduction; avoid stacking formula canaries.
5. Highest value: F127 external CFD/thermochemistry; F131 radiation transport/reference data; F132 real space-weather data/tool; F137 POPPY/HCIPy; F138 ISIS; F123 already has poliastro external reproduction.
6. Integrate Newton/Isaac only where useful for robotics/contact/assembly; no new farm.
7. Keep F72/AFAH blocked until evidence gates are genuinely met.

## Relay rule
Never simulate an agent/farm/tool execution. A run exists only if GitHub run/log/artifact evidence exists. Preserve failed attempts as evidence. Use minimal useful coalition, not all 144 farms by default.
