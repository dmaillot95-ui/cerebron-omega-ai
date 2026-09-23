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

## Progress after checkpoint creation
- PhysicsNeMo runtime corrected and verified: run 35864199488 SUCCESS, version 2.2.2, artifact 10752545024, result SHA c262668e75bba6cf3c483d95eb540a01961e310ab5863aa4b7a7b01b144dfca0.
- PhysicsNeMo real model forward pass V2: run 35865674566 SUCCESS, artifact 10751648203, result SHA 60b9d813e8f098e64d753f6696e6a7566e6337ec454d8cb92efce97c4cdaf1db.
- PhysicsNeMo compressible-flow V3: run 35866592008 SUCCESS; 257 Mach points 0-5, 1200 epochs, MAE 5.223882e-4, MSE 5.570676e-7, max abs error 0.00444126; artifact 10751544524; SHA e9351fd14144a72619dea6c6da24fc6324643c368f31d395080f37b472644354.
- OTF024 PhysicsNeMo is BENCHMARKED, not VALIDATED.
- Warp V3: run 35866776553 SUCCESS; 4096 x 1000 = 4,096,000 updates; x error 9.09517e-6 m, v error 3.30877e-9 m/s vs analytic oscillator; artifact 10751879409; SHA 1d0abd62991cbfdcf794e5785812b1df5fde38d5533a58abe028e3e459f2c78c.
- PhysicsNeMo V4 normal-shock Rankine-Hugoniot benchmark launched: code commit 6d9155b1e88e836cda6bb5b242f061700cef572f, workflow commit 783b9df8657bbea895a782c5fa2771933e1882a8, run 35867031558 IN PROGRESS at this update. Verify before claim.
- Tool Fabric evidence consolidation commit: 772fde763ff980fe1605a1b62f20594c7ccfdf81.

## Newton F139 progress
- Newton 1.6.0 runtime canary SUCCESS: run 35867267961, job 107201940154, artifact 10753005951, result SHA 0cd013b36efb4aa34623baf04d6b32376aab4cd8d0d5f62b23adff5583d5b543. Runtime only.
- Newton+Warp lunar ballistic V2 SUCCESS: run 35868432958, artifact 10753332014, 4,096,000 updates, position error 0.003291378 m after 2s, velocity error 2.78598e-5 m/s, result SHA 2a1ba8a56265ee46d93156f7a3d0b17c7f14cf1644ac77d658c49211be71ff52. This is NOT native Newton contact evidence.
- Newton API probe SUCCESS: run 35868628617; exposed Model, ModelBuilder, Contacts, CollisionPipeline-compatible API path and solvers.
- Native Newton contact V3 created: code commit 764dafe0f0682be04c2dedb896a2d43b27f44f2a; workflow commit b6991ee0075903aaccd8524908884320eba3168b; run 35869399793 IN PROGRESS at this update. Verify before claim or Tool Fabric promotion.
