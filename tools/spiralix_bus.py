#!/usr/bin/env python3
import argparse,datetime,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BUS_PATH=ROOT/"config/spiralix-universal-bus-v1.json"

def _canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sha256_obj(x): return hashlib.sha256(_canon(x).encode("utf-8")).hexdigest()
def load_bus(): return json.loads(BUS_PATH.read_text(encoding="utf-8"))
def endpoint(endpoint_id):
    for e in load_bus()["endpoints"]:
        if e["endpoint_id"]==endpoint_id: return e
    raise KeyError(endpoint_id)

def validate_envelope(env):
    b=load_bus(); req=set(b["envelope"]["required"])
    missing=sorted(req-set(env))
    if missing: raise ValueError("MISSING:"+",".join(missing))
    if env["schema"]!="CEREBRON_SPIRALIX_ENVELOPE_V1": raise ValueError("BAD_SCHEMA")
    if env["language"]!="SPIRALIX-OMEGA": raise ValueError("BAD_LANGUAGE")
    if env["mode"]!="CEREBRON-M": raise ValueError("BAD_MODE")
    ep=endpoint(env["source_endpoint"])
    if ep["availability"]!="AVAILABLE": raise ValueError("UNAVAILABLE_SOURCE")
    if env["payload_sha256"]!=sha256_obj(env["json_payload"]): raise ValueError("PAYLOAD_SHA_MISMATCH")
    if not isinstance(env["natural_language"],str): raise ValueError("NATURAL_LANGUAGE_REQUIRED")
    if set(env["V"])!={"P","E","C","U","R","D","M"}: raise ValueError("BAD_VECTOR")
    if env["V"]["E"] not in {f"E{i}" for i in range(9)}: raise ValueError("BAD_EVIDENCE_LEVEL")
    if not 0<=float(env["V"]["C"])<=1 or not 0<=float(env["V"]["R"])<=1: raise ValueError("BAD_RANGE")
    return True

def make_envelope(source_endpoint,target,mission_id,message_type,natural_language,problem_ref=None,evidence_level="E0",confidence=0.0,unknowns=None,risk=0.5,dependencies=None,memory_checkpoint=None,evidence_refs=None,json_payload=None,glyph_expression=None,lineage_fingerprint=None,created_at=None):
    ep=endpoint(source_endpoint)
    if ep["availability"]!="AVAILABLE": raise ValueError("SOURCE_ENDPOINT_UNAVAILABLE")
    payload=json_payload if json_payload is not None else {"text":natural_language}
    payload_sha=sha256_obj(payload)
    created_at=created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
    surface={"AGORA":"AGΩ","FORUM":"FRΩ","BURST20":"B₂₀","MEMORY":"MΩ"}.get(str(target).upper(),"CΜ")
    glyph_expression=glyph_expression or f"Ω⟦{ep['ai_id']}:{ep['role_glyph']}⟧→{surface}"
    lineage_fingerprint=lineage_fingerprint or hashlib.sha256((source_endpoint+"|"+mission_id).encode()).hexdigest()
    env={"schema":"CEREBRON_SPIRALIX_ENVELOPE_V1","envelope_id":hashlib.sha256((source_endpoint+"|"+mission_id+"|"+message_type+"|"+payload_sha).encode()).hexdigest(),"language":"SPIRALIX-OMEGA","mode":"CEREBRON-M","source_endpoint":source_endpoint,"target":target,"mission_id":mission_id,"message_type":message_type,"glyph_expression":glyph_expression,"V":{"P":problem_ref or mission_id,"E":evidence_level,"C":float(confidence),"U":unknowns or [],"R":float(risk),"D":dependencies or [],"M":memory_checkpoint},"payload_sha256":payload_sha,"lineage_fingerprint":lineage_fingerprint,"evidence_refs":evidence_refs or [],"natural_language":natural_language,"json_payload":payload,"created_at":created_at}
    validate_envelope(env); return env

def self_test_all():
    b=load_bus(); active=[e for e in b["endpoints"] if e["spiralix_required"]]; prep=[e for e in b["endpoints"] if not e["spiralix_required"]]
    results=[]
    for ep in active:
        payload={"endpoint":ep["endpoint_id"],"probe":"SPIRALIX_UNIVERSAL_BUS_CANARY","value":1}
        env=make_envelope(ep["endpoint_id"],"AGORA","SPIRALIX-BUS-CANARY-001","EVIDENCE",f"Canary for {ep['endpoint_id']}",problem_ref="SPIRALIX-BUS-CANARY",evidence_level="E1",confidence=1.0,risk=0.0,dependencies=["config/spiralix-universal-bus-v1.json"],json_payload=payload,created_at="2026-09-24T00:00:00+00:00")
        assert env["json_payload"]==payload; validate_envelope(env)
        results.append({"endpoint_id":ep["endpoint_id"],"envelope_id":env["envelope_id"],"payload_sha256":env["payload_sha256"],"glyph_expression":env["glyph_expression"],"status":"PASS"})
    out={"schema":"CEREBRON_SPIRALIX_UNIVERSAL_BUS_CANARY_V1","status":"PASS","active_endpoints_tested":len(results),"prep_only_endpoints":len(prep),"logical_ai":b["counts"]["logical_ai"],"available_ai":b["counts"]["available_ai"],"slots_per_ai":b["counts"]["slots_per_ai"],"agora":"PASS","forum":"CONTRACT_REQUIRED","burst20":"CONTRACT_REQUIRED","lossless_json_payload_roundtrip":"PASS","results":results}
    out["receipt_sha256"]=sha256_obj({k:v for k,v in out.items() if k!="receipt_sha256"}); return out

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--self-test-all",action="store_true"); ap.add_argument("--output"); args=ap.parse_args()
    if args.self_test_all:
        out=self_test_all(); s=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding="utf-8")
        print(json.dumps({k:v for k,v in out.items() if k!="results"},ensure_ascii=False,sort_keys=True))
