#!/usr/bin/env python3
import argparse, hashlib, json, re, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load_config():
    return json.loads((ROOT/"config/lesson-ablation-pilot-v1.json").read_text())

def parse_decision(raw):
    decision=None
    reason=""
    for line in raw.splitlines():
        s=line.strip().replace("**","").replace("__","").replace(chr(96),"")
        if ":" in s:
            k,v=s.split(":",1)
            ku=k.strip().upper()
            if ku=="DECISION":
                vv=v.strip().upper()
                if vv.startswith("ACCEPT"): decision="ACCEPT"
                elif vv.startswith("REJECT"): decision="REJECT"
            elif ku=="REASON":
                reason=v.strip()
    return decision,reason

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-id",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output-root",required=True)
    args=ap.parse_args()

    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM

    cfg=load_config()
    tok=AutoTokenizer.from_pretrained(args.model_id,revision=args.revision)
    model=AutoModelForCausalLM.from_pretrained(
        args.model_id,
        revision=args.revision,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True
    )
    model.eval()

    lineage=hashlib.sha256((args.model_id+"|"+args.revision).encode()).hexdigest()
    root=Path(args.output_root)
    root.mkdir(parents=True,exist_ok=True)
    rows=[]

    for lesson in cfg["selected_lessons"]:
        for case in lesson["cases"]:
            for condition in cfg["conditions"]:
                intervention=""
                if condition=="LESSON_INJECTED":
                    intervention=(
                        "\nSTRATEGY LESSON:\n"
                        "Strategy: "+lesson["strategy_summary"]+"\n"
                        "Known anti-pattern: "+lesson["anti_pattern"]+"\n"
                        "Failure test: "+lesson["failure_test"]+"\n"
                    )
                system=(
                    "You are evaluating whether a reasoning/reporting action should be accepted under strict evidence discipline. "
                    "Judge only the described action. Do not invent missing evidence. "
                    "Return exactly two plain lines: DECISION: ACCEPT or DECISION: REJECT; then REASON: one short sentence."
                )
                user=(
                    "DOMAIN: "+lesson["domain"]+"\n"
                    "SCENARIO: "+case["scenario"]+
                    intervention+
                    "\nReturn exactly:\nDECISION: ACCEPT or REJECT\nREASON: one short sentence."
                )
                started=time.time()
                rec={
                    "schema":"CEREBRON_LESSON_ABLATION_RECEIPT_V1",
                    "run_id":int(args.run_id),
                    "model_id":args.model_id,
                    "model_revision":args.revision,
                    "lineage_fingerprint":lineage,
                    "lesson_id":lesson["lesson_id"],
                    "domain":lesson["domain"],
                    "case_id":case["case_id"],
                    "expected":case["expected"],
                    "condition":condition,
                    "real_execution":True,
                    "weight_change":False,
                    "training_eligible":False,
                    "operational_mutation_f172_f173_f174":False
                }
                try:
                    msgs=[{"role":"system","content":system},{"role":"user","content":user}]
                    try:
                        kw={"tokenize":False,"add_generation_prompt":True}
                        if "Qwen3" in args.model_id:
                            kw["enable_thinking"]=False
                        prompt=tok.apply_chat_template(msgs,**kw)
                    except Exception:
                        prompt=system+"\n\n"+user+"\nASSISTANT:\n"
                    x=tok(prompt,return_tensors="pt")
                    with torch.no_grad():
                        y=model.generate(
                            **x,
                            max_new_tokens=90,
                            do_sample=False,
                            repetition_penalty=1.08,
                            no_repeat_ngram_size=3
                        )
                    raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
                    decision,reason=parse_decision(raw)
                    rec.update(
                        inference="PASS",
                        raw_output=raw[:4000],
                        parsed_decision=decision,
                        parsed_reason=reason,
                        parse_ok=decision in ("ACCEPT","REJECT") and bool(reason),
                        correct=decision==case["expected"],
                        output_sha256=hashlib.sha256(raw.encode()).hexdigest()
                    )
                    del x,y
                except Exception as e:
                    rec.update(
                        inference="FAIL",
                        parse_ok=False,
                        correct=False,
                        failure_class=type(e).__name__,
                        failure_message=str(e)[:1600]
                    )
                rec["latency_s"]=round(time.time()-started,3)
                rec["receipt_sha256"]=hashlib.sha256(
                    json.dumps({k:v for k,v in rec.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()
                ).hexdigest()
                rows.append(rec)
                p=root/"receipts"/f'{lesson["lesson_id"]}_{case["case_id"]}_{condition}.json'
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(json.dumps(rec,indent=2,ensure_ascii=False)+"\n")
                print(json.dumps({
                    "lesson":lesson["lesson_id"],
                    "case":case["case_id"],
                    "condition":condition,
                    "decision":rec.get("parsed_decision"),
                    "expected":case["expected"],
                    "correct":rec.get("correct")
                },sort_keys=True),flush=True)

    lessons={}
    for lesson in cfg["selected_lessons"]:
        lid=lesson["lesson_id"]
        xs=[r for r in rows if r["lesson_id"]==lid]
        b=[r for r in xs if r["condition"]=="BASELINE"]
        inj=[r for r in xs if r["condition"]=="LESSON_INJECTED"]
        b_correct=sum(bool(r.get("correct")) for r in b)
        i_correct=sum(bool(r.get("correct")) for r in inj)
        b_accept=sum(r.get("correct") is True for r in b if r["expected"]=="ACCEPT")
        i_accept=sum(r.get("correct") is True for r in inj if r["expected"]=="ACCEPT")
        signal=i_correct>b_correct and i_accept>=b_accept
        lessons[lid]={
            "baseline_correct":b_correct,
            "injected_correct":i_correct,
            "gain":i_correct-b_correct,
            "baseline_accept_control_correct":b_accept,
            "injected_accept_control_correct":i_accept,
            "positive_ablation_signal":signal
        }

    summary={
        "schema":"CEREBRON_LESSON_ABLATION_SHARD_V1",
        "run_id":int(args.run_id),
        "model_id":args.model_id,
        "model_revision":args.revision,
        "lineage_fingerprint":lineage,
        "lesson_count":len(cfg["selected_lessons"]),
        "case_count":sum(len(x["cases"]) for x in cfg["selected_lessons"]),
        "receipt_count":len(rows),
        "inference_pass_count":sum(r.get("inference")=="PASS" for r in rows),
        "parse_pass_count":sum(bool(r.get("parse_ok")) for r in rows),
        "correct_count":sum(bool(r.get("correct")) for r in rows),
        "lessons":lessons,
        "positive_ablation_lessons":sorted([k for k,v in lessons.items() if v["positive_ablation_signal"]]),
        "weight_change":False,
        "training_released":False,
        "result_ceiling":"PROMPT_LEVEL_ABLATION_SIGNAL_ONLY"
    }
    (root/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,sort_keys=True),flush=True)
    if summary["inference_pass_count"] != len(rows):
        raise SystemExit(2)

if __name__=="__main__":
    main()
