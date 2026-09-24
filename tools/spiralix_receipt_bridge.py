#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

WORKER_PARENT={"SAPHEA-A":"SAPHEA","SAPHEA-B":"SAPHEA","SAPHEA-C":"SAPHEA","SPIRALION-A":"SPIRALION","ETHERION-A":"ETHERION","ELYSIUM-SMOL-AUDITOR":"ELYSIUM","OMEGA-QWEN-COUNTERAUDITOR":"F149-OMEGA"}
ROLE_SLOT={"SYSTEM_ARCHITECT":"A2_ANALYST","EVIDENCE_AUDITOR":"A4_AUDITOR","COUNTEREXAMPLE_HUNTER":"A5_COUNTER_AUDITOR","CONTINUITY_SYNTHESIZER":"A7_SYNTHESIZER","FORMAL_ANALYST":"A2_ANALYST","SEMANTIC_AUDITOR":"A4_AUDITOR","FORMAL_COUNTER_AUDITOR":"A5_COUNTER_AUDITOR"}
DEFAULT_SLOT={"SAPHEA":"A3_EXECUTOR","SPIRALION":"A7_SYNTHESIZER","ETHERION":"A2_ANALYST","ELYSIUM":"A4_AUDITOR","F149-OMEGA":"A5_COUNTER_AUDITOR"}

def endpoint_for(r):
    wid=r.get("worker_id") or r.get("auditor_id")
    parent=r.get("parent_ai") or WORKER_PARENT.get(wid)
    role=r.get("agora_role") or r.get("role_id") or r.get("role")
    if not parent: raise ValueError("PARENT_AI_UNRESOLVED")
    return f"{parent}:{ROLE_SLOT.get(role,DEFAULT_SLOT.get(parent,'A3_EXECUTOR'))}"

def bridge_receipt(receipt,target="AGORA",message_type="RESULT"):
    r=dict(receipt); source=endpoint_for(r)
    mission=str(r.get("mission_id") or r.get("run_id") or "UNSPECIFIED")
    natural=str(r.get("result") or r.get("audit_text") or r.get("raw_output") or r.get("failure_message") or "")
    snapshot={k:v for k,v in r.items() if not k.startswith("spiralix_")}
    deps=[]
    if r.get("model_id"): deps.append("model:"+str(r["model_id"]))
    if r.get("revision"): deps.append("revision:"+str(r["revision"]))
    if r.get("source_packet"): deps.append("packet:"+str(r["source_packet"]))
    env=make_envelope(source,target,mission,message_type,natural,problem_ref=str(r.get("problem_sha256") or r.get("task") or mission),evidence_level="E1" if r.get("llm_inference") else "E0",confidence=1.0 if r.get("inference")=="PASS" else 0.0,risk=0.4 if r.get("inference")=="PASS" else 0.8,unknowns=[] if r.get("inference")=="PASS" else ["execution_or_model_failure"],dependencies=deps,json_payload=snapshot,lineage_fingerprint=r.get("lineage_fingerprint"))
    if r.get("receipt_sha256"): r["pre_spiralix_receipt_sha256"]=r["receipt_sha256"]
    r["spiralix_source_endpoint"]=source
    r["spiralix_output_envelope"]=env
    r["spiralix_envelope_sha256"]=sha256_obj(env)
    r["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--receipt",required=True);ap.add_argument("--target",default="AGORA");ap.add_argument("--message-type",default="RESULT");args=ap.parse_args()
    p=Path(args.receipt);r=json.loads(p.read_text());out=bridge_receipt(r,args.target,args.message_type);p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":"PASS","source":out["spiralix_source_endpoint"],"envelope_sha256":out["spiralix_envelope_sha256"],"receipt_sha256":out["receipt_sha256"]},sort_keys=True))
if __name__=="__main__": main()
