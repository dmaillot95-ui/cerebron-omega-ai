#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def load(p): return json.loads((R/p).read_text())
def main():
    contract=load("config/cerebron-knowledge-banks-v1.json")
    lesson=load("memory/lesson-bank-v1.json")
    failure=load("memory/failure-bank-v1.json")
    contradiction=load("memory/contradiction-bank-v1.json")
    unknown=load("memory/unknown-bank-v1.json")
    dep=load("memory/dependency-graph-v1.json")
    transfer=load("memory/transfer-bank-v1.json")
    dual=load("config/cerebron-dual-core-contract-v1.json")
    latest=load("checkpoints/CEREBRON_80_LATEST_V2.json")
    s10=load("receipts/workers/s10-marginal-gain-36042832474.json")
    gh=load("memory/gvl-learning-history.json")
    assert contract["schema"]=="CEREBRON_KNOWLEDGE_BANKS_V1"
    assert lesson["schema"]=="CEREBRON_LESSON_BANK_V1"
    assert len(failure["entries"])>=4
    assert all(x["WINNER"]=="NONE" for x in contradiction["entries"])
    assert all(x["CLASS"] in {"U1","U2","U3","U4","U5"} for x in unknown["entries"])
    assert dep["groups"][0]["independent_evidence_count"]==0
    assert any(x["TRANSFER_ID"]=="TR-GVL-C2-B3" and x["TG"]>0 for x in transfer["entries"])
    assert dual["verified_assignments"]==[]
    assert s10["executed_count"]==10 and s10["unique_lineage_fingerprints"]==1
    assert s10["independent_evidence_count"]==0 and s10["scale_decision"]=="STAY_AT_5"
    assert latest["current_state"]["s10"]["scale_decision"]=="STAY_AT_5"
    assert gh["current_claim"]=="GEOMETRIC_GROWTH_NOT_DEMONSTRATED"
    assert gh["positive_consecutive_held_out_ratios"]==1
    out={"schema":"CEREBRON_KNOWLEDGE_BANKS_GUARD_V1","status":"PASS",
         "lesson_entries":len(lesson["entries"]),"failure_entries":len(failure["entries"]),
         "contradiction_entries":len(contradiction["entries"]),"unknown_entries":len(unknown["entries"]),
         "transfer_entries":len(transfer["entries"]),"s10_scale":"STAY_AT_5",
         "geometric_gate":"1_OF_4","dual_core_assignments_verified":0}
    out["sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p=R/"receipts/guards/knowledge-banks-guard-v1.json";p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
