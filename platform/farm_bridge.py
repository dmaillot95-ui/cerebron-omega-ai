from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

API="https://api.github.com"
OWNER="dmaillot95-ui"
PILOTS={
    123:{
        "repo":"cerebron-farm-123-mission-design-navigation",
        "workflow":"control-plane-bridge-v1.yml",
        "operations":{"hohmann_reference"},
    }
}

class FarmBridgeError(RuntimeError):
    pass

def canonical_sha(value)->str:
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def _token()->str:
    token=os.getenv("CEREBRON_GITHUB_TOKEN","").strip()
    if not token:
        raise FarmBridgeError("GITHUB_TOKEN_UNAVAILABLE")
    return token

def _request(method:str,path:str,payload=None):
    body=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(API+path,data=body,method=method)
    req.add_header("Accept","application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version","2022-11-28")
    req.add_header("Authorization","Bearer "+_token())
    if body is not None:
        req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read()
            return json.loads(raw or b"{}")
    except urllib.error.HTTPError as exc:
        detail=exc.read().decode(errors="replace")[:500]
        raise FarmBridgeError(f"GITHUB_HTTP_{exc.code}:{detail}") from exc

def submit(farm_id:int,operation:str,payload:dict,mission_id:str,task_id:str)->dict:
    spec=PILOTS.get(int(farm_id))
    if not spec:
        raise FarmBridgeError("FARM_BRIDGE_NOT_CONFIGURED")
    if operation not in spec["operations"]:
        raise FarmBridgeError("OPERATION_NOT_ALLOWED")
    core={
        "mission_id":mission_id,
        "task_id":task_id,
        "farm_id":int(farm_id),
        "operation":operation,
        "payload":payload,
        "requested_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    }
    core["input_sha"]=canonical_sha(core)
    repo=spec["repo"]
    nonce=uuid.uuid4().hex[:12]
    path=f"bridge/requests/{mission_id}-{task_id}-{nonce}.json"
    content=base64.b64encode((json.dumps(core,indent=2)+"\n").encode()).decode()
    created=_request("PUT",f"/repos/{OWNER}/{repo}/contents/{path}",{
        "message":f"CEREBRON bridge request {mission_id}/{task_id}",
        "content":content,
        "branch":"main",
    })
    commit_sha=created.get("commit",{}).get("sha")
    if not commit_sha:
        raise FarmBridgeError("REQUEST_COMMIT_SHA_MISSING")
    return {
        "protocol":"CEREBRON_FARM_BRIDGE_V1",
        "farm_id":farm_id,
        "repo":f"{OWNER}/{repo}",
        "workflow":spec["workflow"],
        "request_path":path,
        "request_commit_sha":commit_sha,
        "input_sha":core["input_sha"],
        "status":"REQUEST_COMMITTED",
    }

def collect(farm_id:int,commit_sha:str,timeout_s:int=180)->dict:
    spec=PILOTS.get(int(farm_id))
    if not spec:
        raise FarmBridgeError("FARM_BRIDGE_NOT_CONFIGURED")
    repo=spec["repo"]; deadline=time.time()+timeout_s
    run=None
    while time.time()<deadline:
        data=_request("GET",f"/repos/{OWNER}/{repo}/actions/runs?head_sha={urllib.parse.quote(commit_sha)}&per_page=20")
        matches=[r for r in data.get("workflow_runs",[]) if r.get("path","").endswith(spec["workflow"])]
        if matches:
            run=matches[0]
            if run.get("status")=="completed":
                break
        time.sleep(3)
    if not run:
        raise FarmBridgeError("WORKFLOW_RUN_NOT_FOUND")
    if run.get("status")!="completed":
        raise FarmBridgeError("WORKFLOW_TIMEOUT")
    if run.get("conclusion")!="success":
        raise FarmBridgeError("WORKFLOW_FAILED")
    run_id=run["id"]
    jobs=_request("GET",f"/repos/{OWNER}/{repo}/actions/runs/{run_id}/jobs?per_page=20").get("jobs",[])
    ok=[j for j in jobs if j.get("conclusion")=="success"]
    if not ok:
        raise FarmBridgeError("SUCCESS_JOB_MISSING")
    artifacts=_request("GET",f"/repos/{OWNER}/{repo}/actions/runs/{run_id}/artifacts?per_page=20").get("artifacts",[])
    if not artifacts:
        raise FarmBridgeError("ARTIFACT_MISSING")
    art=artifacts[0]
    digest=art.get("digest")
    if not digest:
        raise FarmBridgeError("ARTIFACT_SHA_MISSING")
    return {
        "protocol":"CEREBRON_FARM_BRIDGE_V1",
        "farm_id":farm_id,
        "status":"FARM_EXECUTED",
        "run_id":run_id,
        "job_id":ok[0]["id"],
        "artifact_id":art["id"],
        "artifact_sha":digest,
        "head_sha":commit_sha,
        "engine":"farm-workflow",
        "limitations":["artifact metadata verified; scientific validity remains bounded by the farm workload"],
    }
