#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
mission=json.loads((R/"config/m11-s5-v2-mission-v1.json").read_text())
contract=json.loads((R/"config/role-diverse-prompt-contract-v2.json").read_text())
calc=hashlib.sha256(mission["problem_text"].encode()).hexdigest()
assert mission["problem_sha256"]==calc
assert mission["status"]=="PREPARED_NOT_TRIGGERED"
assert mission["runtime_changed"] is False
assert len(mission["workers"])==5
assert len({w["worker_id"] for w in mission["workers"]})==5
assert len({w["role_id"] for w in mission["workers"]})==5
assert contract["runtime_changed"] is False
for rule in [
 "DO_NOT_REPLACE_THE_PROBLEM_WITH_AN_EXAMPLE",
 "DO_NOT_INVENT_A_DIFFERENT_CLAIM",
 "DO_NOT_ECHO_INSTRUCTIONS_AS_THE_RESULT",
 "ANSWER_ONLY_THE_EXACT_PROBLEM_TEXT"
]:
    assert rule in contract["hard_prompt_rules"]
assert mission["gold_status"]=="DENY_UNTIL_POSTRUN_AUDIT"
assert mission["scale_status"]=="5_TO_10_DENY_UNTIL_V2_BEATS_V1"
print(json.dumps({
 "status":"PASS",
 "problem_sha256":calc,
 "workers":5,
 "roles":5,
 "runtime_changed":False,
 "gold":"DENY_UNTIL_POSTRUN_AUDIT",
 "scale_5_to_10":"DENY_UNTIL_V2_BEATS_V1"
},sort_keys=True))
