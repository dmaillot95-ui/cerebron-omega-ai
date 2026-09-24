#!/usr/bin/env python3
import argparse,glob,hashlib,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--input-glob",required=True);ap.add_argument("--run-id",required=True);ap.add_argument("--output",required=True);args=ap.parse_args()
    rec=sorted([json.loads(Path(fn).read_text()) for fn in glob.glob(args.input_glob,recursive=True)],key=lambda x:x["worker_id"])
    executed=sum(bool(x.get("llm_inference") and x.get("inference")=="PASS") for x in rec);valid=sum(bool(x.get("contract_valid")) for x in rec);no_drift=sum(bool(x.get("no_drift")) for x in rec);spiralix=sum(bool(x.get("spiralix_envelope_sha256") and x.get("spiralix_source_endpoint")) for x in rec);hashes={x.get("result_sha256") for x in rec if x.get("result_sha256")}
    out={"schema":"CEREBRON_M11_S5_V2_SCORE_V2","run_id":args.run_id,"executed_workers":executed,"contract_valid_workers":valid,"no_drift_workers":no_drift,"spiralix_valid_workers":spiralix,"unique_result_sha256":len(hashes),"workers":rec,"v1_baseline":{"executed_workers":5,"unique_results":5,"semantic_status":"HOLD_DUE_TO_DRIFT","drift_workers":3,"instruction_echo_proxy_workers":4},"v2_pass_gate":"5_EXECUTED_AND_5_CONTRACT_VALID_AND_5_NO_DRIFT_AND_5_SPIRALIX","v2_pass":executed==5 and valid==5 and no_drift==5 and spiralix==5,"gold_status":"DENY_PENDING_SEMANTIC_AUDIT","scale_5_to_10":"HOLD_PENDING_V2_AUDIT"}
    text=f"M11 V2 score: executed={executed}, valid={valid}, no_drift={no_drift}, spiralix={spiralix}, unique={len(hashes)}"
    env=make_envelope("SPIRALION:A7_SYNTHESIZER","AGORA","C80-M11-S5-V2-001","SYNTHESIS",text,problem_ref="268482a63cb1616367e9c0e2d2204f8c1b82cb00e60b8be28dacf9fcae81f230",evidence_level="E1",confidence=1.0 if out["v2_pass"] else 0.5,risk=0.2 if out["v2_pass"] else 0.6,dependencies=[x.get("spiralix_envelope_sha256") for x in rec if x.get("spiralix_envelope_sha256")],json_payload={k:v for k,v in out.items() if k!="workers"})
    out["spiralix_synthesis_envelope"]=env;out["spiralix_synthesis_envelope_sha256"]=sha256_obj(env);out["score_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in out.items() if k!="score_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({k:out[k] for k in ["executed_workers","contract_valid_workers","no_drift_workers","spiralix_valid_workers","unique_result_sha256","v2_pass","gold_status","scale_5_to_10","spiralix_synthesis_envelope_sha256"]},sort_keys=True))
if __name__=="__main__": main()
