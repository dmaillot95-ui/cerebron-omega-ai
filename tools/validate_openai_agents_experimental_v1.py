#!/usr/bin/env python3
from __future__ import annotations
import json, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=ROOT/"config/openai-agents-experimental-v1.json"

def fail(msg):
    print(f"FAIL_CLOSED: {msg}")
    raise SystemExit(2)

def main():
    d=json.loads(CFG.read_text())
    if d.get("schema")!="CEREBRON_OPENAI_AGENTS_EXPERIMENTAL_V1":
        fail("schema")
    if d.get("enabled") is not False:
        fail("enabled_must_be_false")
    cost=d.get("cost_gate",{})
    if cost.get("max_spend_usd")!=0:
        fail("max_spend_usd_must_be_zero")
    if cost.get("auto_paid_activation") is not False:
        fail("auto_paid_activation_must_be_false")
    if cost.get("fail_closed") is not True:
        fail("cost_gate_must_fail_closed")
    api=d.get("api",{})
    if api.get("endpoint")!="https://api.openai.com/v1/agents/sessions":
        fail("agents_endpoint_drift")
    if api.get("beta_header")!="OpenAI-Beta: agents=v1":
        fail("beta_header_drift")
    models=d.get("model_policy",{})
    allowed={models.get("coordinator_default"),models.get("high_difficulty_candidate"),models.get("high_volume_candidate")}
    expected={"gpt-5.6-sol","gpt-6-astra","gpt-5.6-luna"}
    if allowed!=expected:
        fail(f"model_allowlist_drift:{sorted(x for x in allowed if x)}")
    ma=d.get("multi_agent",{})
    n=ma.get("max_concurrent_subagents")
    if not isinstance(n,int) or n<1 or n>5:
        fail("subagent_limit_must_be_1_to_5")
    if ma.get("count_as_independent_evidence") is not False:
        fail("subagents_cannot_count_as_independent_evidence")
    env=d.get("environment",{})
    if env.get("default",{}).get("type")!="none":
        fail("default_environment_must_be_none")
    if env.get("optional_self_hosted",{}).get("allowed") is not False:
        fail("self_hosted_must_be_locked")
    tools=d.get("tools",{})
    if tools.get("mcp",{}).get("enabled") is not False:
        fail("mcp_must_be_disabled")
    if tools.get("web_search") is not False:
        fail("web_search_must_be_disabled")
    prohibited=set(d.get("prohibited_by_default",[]))
    required={
      "NETWORK_CALL_TO_OPENAI_AGENTS_API",
      "OPENAI_HOSTED_SANDBOX",
      "PAID_MODEL_INVOCATION",
      "SECRET_COMMIT",
      "AUTO_SCALE_ABOVE_5",
      "COUNT_SUBAGENTS_AS_INDEPENDENT_EVIDENCE",
      "AUTO_PROMOTION_FROM_AGENT_CONSENSUS"
    }
    if not required.issubset(prohibited):
        fail("prohibited_defaults_incomplete")
    print(json.dumps({
      "schema":d["schema"],
      "status":"PASS_ZERO_SPEND_STATIC_CONTRACT",
      "enabled":d["enabled"],
      "max_spend_usd":cost["max_spend_usd"],
      "models":sorted(allowed),
      "max_concurrent_subagents":n,
      "network_calls_executed":0,
      "paid_calls_executed":0
    },sort_keys=True))

if __name__=="__main__":
    main()
