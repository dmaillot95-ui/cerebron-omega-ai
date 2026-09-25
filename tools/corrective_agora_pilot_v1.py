#!/usr/bin/env python3
import argparse, hashlib, json, time, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["ATTEMPT","ASSUMPTIONS","EVIDENCE_NEEDED","COUNTEREXAMPLE_OR_LIMIT","CONFIDENCE","UNKNOWN"]

def parse(raw):
    out = {}
    cur = None
    aliases = {x:x for x in LABELS}
    aliases["EVIDENCE NEEDED"] = "EVIDENCE_NEEDED"
    aliases["COUNTEREXAMPLE OR LIMIT"] = "COUNTEREXAMPLE_OR_LIMIT"
    for line in raw.splitlines():
        s = line.strip().replace("**","").replace("__","").replace(chr(96),"").replace("：",":")
        if not s:
            continue
        if ":" in s:
            h,v = s.split(":",1)
            k = aliases.get(h.strip().upper())
            if k:
                cur = k
                out[k] = v.strip()
                continue
        if cur:
            out[cur] = (out[cur] + " " + s).strip()
    return out

def load_task(target):
    out = ROOT / "artifacts/corrective_curriculum_g1_tasks.json"
    if not out.exists():
        subprocess.check_call([sys.executable, str(ROOT / "tools/build_corrective_curriculum_g1_tasks.py")])
    pack = json.loads(out.read_text())
    tid = "G1-" + target + "-01"
    return next(x for x in pack["tasks"] if x["task_id"] == tid)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True)
    ap.add_argument("--model-id", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--output-root", required=True)
    a = ap.parse_args()
    targets = [x.strip() for x in a.targets.split(",") if x.strip()]
    if not targets:
        raise SystemExit("NO_TARGETS")

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    tok = AutoTokenizer.from_pretrained(a.model_id, revision=a.revision)
    model = AutoModelForCausalLM.from_pretrained(
        a.model_id,
        revision=a.revision,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True
    )
    model.eval()
    lineage = hashlib.sha256((a.model_id + "|" + a.revision).encode()).hexdigest()
    rows = []

    for target in targets:
        task = load_task(target)
        system = (
            "You are a candidate teacher for CEREBRON target AI " + target + ". "
            "Stay inside the supplied corrective axis. You are not an independent proof source. "
            "Do not claim that memory is training, simulation is physical validation, or consensus is evidence. "
            "Your output is a candidate AGORA lesson and must be auditable."
        )
        user = (
            "TASK_ID: " + task["task_id"] + "\n"
            "CORRECTIVE_AXIS: " + task["corrective_axis"] + "\n"
            "INSTRUCTION: " + task["instruction"] + "\n"
            "SPECIALIZATION_TAGS: " + ", ".join(task.get("specialization_tags",[])) + "\n\n"
            "Return exactly six plain lines:\n"
            "ATTEMPT: propose the useful solution or teaching example.\n"
            "ASSUMPTIONS: list the assumptions that must hold.\n"
            "EVIDENCE_NEEDED: state what would verify the lesson.\n"
            "COUNTEREXAMPLE_OR_LIMIT: state one failure case or scope limit.\n"
            "CONFIDENCE: give LOW, MEDIUM, or HIGH with a short reason.\n"
            "UNKNOWN: state what remains unresolved."
        )
        started = time.time()
        rec = {
            "schema":"CEREBRON_CORRECTIVE_AGORA_PILOT_RECEIPT_V1",
            "run_id":int(a.run_id),
            "target_ai":target,
            "task_id":task["task_id"],
            "task_sha256":task["task_sha256"],
            "corrective_axis":task["corrective_axis"],
            "model_id":a.model_id,
            "model_revision":a.revision,
            "lineage_fingerprint":lineage,
            "real_execution":True,
            "llm_inference":False,
            "training_eligible":False,
            "independent_evidence":False,
            "operational_mutation_f172_f173_f174":False
        }
        try:
            msgs = [{"role":"system","content":system},{"role":"user","content":user}]
            try:
                kw = {"tokenize":False,"add_generation_prompt":True}
                if "Qwen3" in a.model_id:
                    kw["enable_thinking"] = False
                prompt = tok.apply_chat_template(msgs, **kw)
            except Exception:
                prompt = system + "\n\n" + user + "\nASSISTANT:\n"
            x = tok(prompt, return_tensors="pt")
            with torch.no_grad():
                y = model.generate(
                    **x,
                    max_new_tokens=220,
                    do_sample=False,
                    repetition_penalty=1.12,
                    no_repeat_ngram_size=4
                )
            raw = tok.decode(y[0][x["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            parsed = parse(raw)
            rec.update(
                llm_inference=True,
                inference="PASS",
                raw_output=raw[:9000],
                parsed=parsed,
                parse_ok=all(parsed.get(k) for k in LABELS),
                output_sha256=hashlib.sha256(raw.encode()).hexdigest()
            )
            del x, y
        except Exception as e:
            rec.update(
                inference="FAIL",
                parse_ok=False,
                failure_class=type(e).__name__,
                failure_message=str(e)[:2000]
            )
        rec["latency_s"] = round(time.time() - started, 3)
        rec["receipt_sha256"] = hashlib.sha256(
            json.dumps({k:v for k,v in rec.items() if k != "receipt_sha256"}, sort_keys=True, default=str).encode()
        ).hexdigest()
        p = Path(a.output_root) / target / "receipt.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        rows.append(rec)
        print(json.dumps({
            "target":target,
            "model":a.model_id,
            "inference":rec.get("inference"),
            "parse_ok":rec.get("parse_ok")
        }, sort_keys=True), flush=True)

    summary = {
        "schema":"CEREBRON_CORRECTIVE_AGORA_PILOT_SHARD_V1",
        "run_id":int(a.run_id),
        "model_id":a.model_id,
        "model_revision":a.revision,
        "lineage_fingerprint":lineage,
        "requested":targets,
        "receipt_count":len(rows),
        "inference_pass_count":sum(r.get("inference") == "PASS" for r in rows),
        "parse_pass_count":sum(bool(r.get("parse_ok")) for r in rows),
        "training_released":False,
        "independent_evidence_count":0
    }
    Path(a.output_root).mkdir(parents=True, exist_ok=True)
    (Path(a.output_root) / "_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)
    if summary["inference_pass_count"] != len(targets):
        raise SystemExit(2)

if __name__ == "__main__":
    main()
