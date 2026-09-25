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
