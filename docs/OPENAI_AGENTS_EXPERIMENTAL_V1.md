# CÉRÉBRON ΑΩ — OpenAI Agents API experimental bridge V1

Status: PREPARED / DISABLED / ZERO-SPEND / NO NETWORK CALLS

## Purpose

This branch maps CÉRÉBRON roles onto the OpenAI Agents API architecture without enabling paid execution.

The official API currently exposes durable agent sessions at:

- POST https://api.openai.com/v1/agents/sessions
- Header: OpenAI-Beta: agents=v1

The managed harness can maintain sessions, compact context, recover work, use tools and coordinate subagents.

## CÉRÉBRON mapping

- CÉRÉBRON: coordinator.
- SAPHEA: execution selector/router.
- SPIRALION: continuity/checkpoint specialist.
- ETHERION: hard R&D specialist.
- HYPERION: alternative-hypothesis specialist.
- AFAH: final evidence-policy gate outside candidate self-review.

Subagent count is NOT independent evidence.

## Model IDs pinned from current official docs

- high difficulty candidate: gpt-6-astra
- coordinator candidate: gpt-5.6-sol
- high-volume candidate: gpt-5.6-luna

Do not use gpt-6-sol or gpt-6-luna unless those exact API IDs become officially documented.

## Hard zero-spend gate

Default configuration requires:

- enabled=false
- max_spend_usd=0
- no OPENAI_API_KEY required by CI
- no hosted sandbox
- MCP disabled
- web search disabled
- no paid model invocation
- no automatic activation
- max 5 subagents if the experiment is ever explicitly unlocked

Unlocking a future executable bridge requires explicit user authorization, an external project spend limit, runtime-only secrets, a nonzero user-approved budget, a model allowlist and a new audit checkpoint.

## Evidence rules

REALITY > COHERENCE  
EVIDENCE > CONFIDENCE  
CLAIM <= EVIDENCE  
VERIFY BEFORE COMMIT  
SIMULATION != TEST  
AGENT COUNT != INTELLIGENCE  
WORKFLOW SUCCESS != SCIENTIFIC SUCCESS

Every future session must persist session ID, model ID, input hash, output hash, tool-call provenance and artifact SHA when artifacts exist.

## Current claim ceiling

This branch proves only that CÉRÉBRON has a statically validated integration contract for the Agents API.

It does NOT prove:

- that an Agents API call was executed;
- that a paid model was invoked;
- that subagents ran;
- that MCP was connected;
- that the integration improves CÉRÉBRON;
- that multiple subagents are independent evidence.
