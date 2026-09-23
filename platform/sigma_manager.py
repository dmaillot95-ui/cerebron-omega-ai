from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time

from generative_backend import GenerativeBackendError, MODEL_ID, REVISION, generate
from huggingface_memory import status as hf_status

ROOT = pathlib.Path(__file__).resolve().parent.parent
COUNCIL_PATH = ROOT / "config" / "sigma-executive-council-v1.json"

ROLE_PROMPTS = {
    "SAPHEA": "Act as SAPHEA: identify the minimum useful specialist capabilities and executable steps.",
    "SPIRALION": "Act as SPIRALION: recover continuity, checkpoints, negative memory, contradictions and what must not be repeated.",
    "ETHERION": "Act as ETHERION: analyze the hard science, mathematics and falsifiable technical reasoning.",
    "HYPERION": "Act as HYPERION: generate materially different hypotheses, alternatives and failure explanations.",
    "ASTRION": "Act as ASTRION: analyze space/aerospace implications, constraints and mission-level consequences when relevant.",
    "METRION": "Act as METRION: produce engineering calculations, simulation needs, validation gates and measurable outputs.",
    "AFAH": "Act as AFAH: audit evidence, dependencies, overclaims, contradictions and set the maximum justified claim.",
    "AELYS": "Act as AELYS: organize the result for the human, expose decisions, uncertainties and required arbitration clearly.",
}

KEYWORDS = {
    "ASTRION": ("space","orbital","orbit","lunar","moon","mars","rocket","aerospace","satellite","spatial"),
    "METRION": ("engineer","engineering","calculate","calculation","simulation","mechanic","power","force","thermal","structure"),
    "ETHERION": ("proof","theorem","math","science","physics","equation","collatz","research"),
    "HYPERION": ("alternative","hypothesis","invent","novel","different","diverge","idea"),
    "SPIRALION": ("checkpoint","continue","memory","previous","resume","history","contradiction"),
    "AFAH": ("audit","verify","evidence","claim","red team","risk","validate"),
    "AELYS": ("explain","present","dialogue","user","decision","communicate"),
    "SAPHEA": ("tool","farm","specialist","execute","workflow","agent"),
}


def _sha(value) -> str:
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def council() -> dict:
    return json.loads(COUNCIL_PATH.read_text(encoding="utf-8"))


def select_delegates(prompt: str, full_council: bool=False) -> list[str]:
    cfg=council()
    roles=[d["role"] for d in cfg["delegates"]]
    if full_council:
        return roles
    p=prompt.lower()
    selected=["SAPHEA","AFAH","AELYS"]
    for role,words in KEYWORDS.items():
        if any(w in p for w in words) and role not in selected:
            selected.append(role)
    if len(selected)<4:
        selected.insert(1,"ETHERION")
    return [r for r in roles if r in selected]


def status() -> dict:
    cfg=council()
    return {
        "schema":"SIGMA_PLATFORM_MANAGER_STATUS_V1",
        "name":"SIGMA",
        "farm_id":74,
        "platform_manager":True,
        "council_seats":cfg["seat_count"],
        "selection_policy":cfg["selection_policy"],
        "shared_general_model":{"model_id":MODEL_ID,"revision":REVISION},
        "independent_general_neural_models":1,
        "elyra":"SEPARATE_TRAINED_POLICY_CAPABILITY",
        "huggingface_memory":hf_status(),
        "claim_ceiling":"ORCHESTRATED_MULTI_ROLE_INFERENCE_NOT_EIGHT_INDEPENDENT_MODELS",
    }


def execute(prompt: str, full_council: bool=False, max_new_tokens: int=120) -> dict:
    prompt=str(prompt).strip()
    if not prompt:
        raise ValueError("SIGMA_PROMPT_REQUIRED")
    started=time.perf_counter()
    roles=select_delegates(prompt,full_council)
    outputs=[]
    for role in roles:
        role_prompt=(
            ROLE_PROMPTS[role]
            + "\nMission from SIGMA: " + prompt
            + "\nReturn a compact contribution. Do not claim tools or evidence not actually executed."
        )
        try:
            result=generate(role_prompt,max_new_tokens=max_new_tokens)
            outputs.append({
                "role":role,
                "status":"EXECUTED",
                "model_id":result["model_id"],
                "revision":result["revision"],
                "output":result["generation"],
                "output_sha":result["output_sha"],
                "neural_independence":"SHARED_QWEN_CORRELATED",
            })
        except GenerativeBackendError as exc:
            outputs.append({
                "role":role,
                "status":"NON_EXECUTED",
                "error":str(exc),
                "neural_independence":"NOT_APPLICABLE",
            })

    executed=[o for o in outputs if o["status"]=="EXECUTED"]
    fusion=None
    if executed:
        transcript="\n\n".join(f"[{o['role']}] {o['output']}" for o in executed)
        fusion_prompt=(
            "You are SIGMA, the platform-native manager of CEREBRON. "
            "Fuse the following correlated role contributions without inventing independent consensus. "
            "Preserve disagreements, evidence limits and next executable actions.\n\n"
            + transcript
            + "\n\nOriginal mission: " + prompt
        )
        try:
            fr=generate(fusion_prompt,max_new_tokens=max_new_tokens)
            fusion={
                "status":"EXECUTED",
                "generation":fr["generation"],
                "output_sha":fr["output_sha"],
                "model_id":fr["model_id"],
                "revision":fr["revision"],
            }
        except GenerativeBackendError as exc:
            fusion={"status":"NON_EXECUTED","error":str(exc)}

    core={
        "schema":"SIGMA_EXECUTION_V1",
        "farm_id":74,
        "mode":"FULL_COUNCIL_8" if full_council else "MINIMAL_USEFUL_COALITION",
        "selected_roles":roles,
        "role_results":outputs,
        "fusion":fusion,
        "independent_general_neural_models":1,
        "shared_dependency":f"{MODEL_ID}@{REVISION}",
        "huggingface_memory_status":hf_status(),
        "elapsed_s":round(time.perf_counter()-started,3),
        "claim_ceiling":"ORCHESTRATED_MULTI_ROLE_INFERENCE_NOT_INDEPENDENT_MULTI_MODEL_CONSENSUS",
    }
    core["result_sha256"]=_sha(core)
    return core
