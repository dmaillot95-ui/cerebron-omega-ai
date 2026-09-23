from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
PLATFORM=ROOT/"platform"
sys.path.insert(0,str(PLATFORM))

from coalition_tools import execute as coalition_execute
from farm_bridge import PILOTS
from generative_backend import MODEL_ID, REVISION, status as generative_status
from mission_engine import ARTIFACTS, create_mission, rows, sha256_bytes
from role_runtime import ELYRA_EVIDENCE

OUT=PLATFORM/"artifacts"/"operational-acceptance-v1.json"


def gh_json(url: str) -> dict:
    token=os.getenv("GH_TOKEN","").strip()
    headers={"Accept":"application/vnd.github+json","User-Agent":"cerebron-operational-acceptance-v1"}
    if token:
        headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=20) as response:
        return json.loads(response.read())


def gate(name, passed, evidence, limitation=None):
    return {
        "name":name,
        "passed":bool(passed),
        "evidence":evidence,
        "limitation":limitation,
    }


def wait_mission(mission_id: str):
    for _ in range(150):
        row=rows("SELECT * FROM missions WHERE mission_id=?",(mission_id,))[0]
        if row["status"] in {"COMPLETED","FAILED"}:
            return row
        time.sleep(0.03)
    raise RuntimeError("MISSION_TIMEOUT")


def main():
    gates=[]

    farms=json.loads((ROOT/"config"/"farms.json").read_text())["farms"]
    ids=[f["id"] for f in farms]
    gates.append(gate(
        "registry_144_integrity",
        len(farms)==144 and ids==list(range(1,145)) and len({f["repo"] for f in farms})==144,
        {"count":len(farms),"min_id":min(ids),"max_id":max(ids)},
    ))

    op=json.loads((ROOT/"config"/"operational-status-v1.json").read_text())
    control=json.loads((ROOT/"config"/"platform-control-plane-v1.json").read_text())
    gates.append(gate(
        "control_plane_invariants",
        op["status"] in {"OPERATIONAL_SCOPED_LOCAL","OPERATIONAL_SCOPED_LOCAL_VERIFIED"}
        and control["farm_count_effect"]==0
        and control["farm_cap"]==144
        and op["public_remote_deployment"]=="BLOCKED"
        and op["gates"]["G11"]["status"]=="OPEN",
        {
            "status":op["status"],"farm_count_effect":control["farm_count_effect"],
            "farm_cap":control["farm_cap"],"remote":op["public_remote_deployment"],
            "G11":op["gates"]["G11"]["status"],
        },
        "Local scoped operation only; public deployment and G11 are outside this acceptance.",
    ))

    mission=create_mission("Concevoir un rover lunaire autonome et calculer sa traction",owner_id="acceptance-v1")
    m=wait_mission(mission["mission_id"])
    ev=rows("SELECT * FROM evidence WHERE mission_id=?",(mission["mission_id"],))
    artifact_ok=False
    if ev:
        artifact=ARTIFACTS/pathlib.Path(ev[0]["source"]).name
        artifact_ok=artifact.exists() and sha256_bytes(artifact.read_bytes())==ev[0]["sha"]
    gates.append(gate(
        "local_mission_evidence",
        m["status"]=="COMPLETED" and bool(ev) and artifact_ok,
        {"mission_id":mission["mission_id"],"status":m["status"],"evidence_count":len(ev),"artifact_sha_verified":artifact_ok},
    ))

    samples=[
        ("Return only the number. Compute: 17*23","391"),
        ("Evaluate this Python expression and answer only with the value: (7+5)*2","24"),
        ("Mass 10 kg; acceleration 2 m/s^2. Compute force using mass times acceleration. One number only.","20"),
        ("DATA: alpha=0.25; beta=0.75; gamma=1.50. Using only DATA, give beta.","0.75"),
        ("Choose only A, B, or C. Constraints: X first; Y before Z. Options: A=Y,X,Z; B=X,Z,Y; C=X,Y,Z.","C"),
        ("One arithmetic statement is incorrect. Return only its label. A: 2+2=4; B: 3*3=8; C: 10/2=5","B"),
    ]
    results=[]
    for prompt,expected in samples:
        r=coalition_execute(prompt)
        answer=str(r.get("answer") or "").strip().rstrip(".")
        results.append({"answer":answer,"expected":expected,"mode":r.get("execution_mode"),"pass":answer.lower()==expected.lower()})
    gates.append(gate(
        "semantic_minimal_coalition_six_domains",
        all(r["pass"] for r in results),
        {"passed":sum(int(r["pass"]) for r in results),"total":len(results),"results":results},
        "Deterministic/tool-backed samples are bounded capabilities, not independent neural agents.",
    ))

    gates.append(gate(
        "farm_bridge_contract",
        123 in PILOTS and "hohmann_reference" in PILOTS[123]["operations"],
        {"pilot_farm":123,"workflow":PILOTS[123]["workflow"],"operations":sorted(PILOTS[123]["operations"])},
    ))

    gen=generative_status()
    gates.append(gate(
        "generative_backend_registered",
        gen["model_id"]==MODEL_ID and gen["revision"]==REVISION and gen["benchmark_evidence"]["score"]==5,
        {"model_id":gen["model_id"],"revision":gen["revision"],"runtime_status":gen["status"],"smoke_score":gen["benchmark_evidence"]["score"]},
        "Backend is fail-closed/disabled unless the runtime enable flag and dependencies are present.",
    ))

    external=[
        ("farm_bridge_real_run","https://api.github.com/repos/dmaillot95-ui/cerebron-farm-123-mission-design-navigation/actions/runs/35897592604"),
        ("qwen_backend_e2e","https://api.github.com/repos/dmaillot95-ui/cerebron-omega-ai/actions/runs/35900659814"),
        ("agora_gold","https://api.github.com/repos/dmaillot95-ui/cerebron-omega-ai/actions/runs/35900931011"),
        ("f139_reproduction","https://api.github.com/repos/dmaillot95-ui/cerebron-farm-139-regolith-geotechnics/actions/runs/35901349529"),
        ("elyra_independent_audit","https://api.github.com/repos/dmaillot95-ui/cerebron-omega-ai/actions/runs/35905952407"),
        ("bounded_autonomy","https://api.github.com/repos/dmaillot95-ui/cerebron-omega-ai/actions/runs/35905066201"),
        ("semantic_v5","https://api.github.com/repos/dmaillot95-ui/cerebron-omega-ai/actions/runs/35905965573"),
        ("remote_security_gate","https://api.github.com/repos/dmaillot95-ui/cerebron-omega-ai/actions/runs/35906185960"),
    ]
    for name,url in external:
        d=gh_json(url)
        gates.append(gate(name,d.get("status")=="completed" and d.get("conclusion")=="success",
                          {"run_id":d.get("id"),"status":d.get("status"),"conclusion":d.get("conclusion"),"head_sha":d.get("head_sha")}))

    gates.append(gate(
        "elyra_model_evidence_pinned",
        len(ELYRA_EVIDENCE["weights_sha256"])==64
        and ELYRA_EVIDENCE["training_run"]==35904950828
        and ELYRA_EVIDENCE["audit_run"]==35905952407,
        ELYRA_EVIDENCE,
        "Synthetic rover-policy model only; not a Control Plane language model and not physical validation.",
    ))

    passed=sum(int(g["passed"]) for g in gates)
    total=len(gates)
    score=round(100.0*passed/total,2)
    report={
        "schema":"CEREBRON_OPERATIONAL_ACCEPTANCE_V1",
        "scope":"LOCAL_SCOPED_OPERATIONAL_CORE",
        "status":"ACCEPTED_100_PERCENT_SCOPED_LOCAL" if passed==total else "NOT_FULLY_ACCEPTED",
        "passed":passed,
        "total":total,
        "score_percent":score,
        "gates":gates,
        "excluded_from_score":[
            "public_remote_deployment",
            "G11 external superintelligence evaluation",
            "physical validation of simulated science",
            "general intelligence or AGI claim",
        ],
        "terminology":"INTELLIGENCE_COLLECTIVE_ORCHESTREE_A_CAPACITE_MESUREE",
    }
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    report["result_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"passed":passed,"total":total,"score_percent":score,"result_sha256":report["result_sha256"]}))
    raise SystemExit(0 if passed==total else 1)


if __name__=="__main__":
    main()
