# Continuous neural training releases

Only new, explicitly audited training releases belong here.

A release is eligible only when:
- `training_released=true`
- `continuous_training_eligible=true`
- a dataset/release SHA is recorded
- train data excludes M6, transfer, red-team and adversarial answers
- closed Wave1/Wave2 roles are not reused unless `materially_new_data_or_method=true`
- any dispatch workflow is explicitly named and reviewed

An empty directory means the controller remains active but performs no neural training.

## Current execution state — 2026-09-26

No eligible neural-training release is registered yet. The controller remains fail-closed and keeps up to 4 slots available. Do not convert scaffolds, AGORA output, memory, prompts, or unvalidated RDX material into `training_released=true`.

Next admissible release must provide, at minimum: role-specific train split, pinned base model/revision, dataset SHA-256, explicit M6/transfer/red exclusion, cold benchmark split, transfer split, red-team split, and a reviewed dispatch workflow.
