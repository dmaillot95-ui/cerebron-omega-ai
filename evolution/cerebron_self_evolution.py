#!/usr/bin/env python3
"""Native CEREBRON self-evolution primitives.

Conceptually inspired by MIT-licensed trace/evolution/evaluation projects
(NousResearch/hermes-agent-self-evolution, DSPy, lm-evaluation-harness),
but implemented here from scratch with Python stdlib only.

This module does NOT train weights. It provides deterministic dataset splitting,
decontamination, hard constraints, metric records, and Pareto selection.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def stable_split(record_id: str, train_pct: int = 60, val_pct: int = 20) -> str:
    if train_pct < 1 or val_pct < 1 or train_pct + val_pct >= 100:
        raise ValueError("invalid split percentages")
    bucket = int(hashlib.sha256(record_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < train_pct:
        return "train"
    if bucket < train_pct + val_pct:
        return "validation"
    return "holdout"

def token_ngrams(text: str, n: int = 5) -> set[tuple[str, ...]]:
    toks = normalize_text(text).split()
    if not toks:
        return set()
    if len(toks) < n:
        return {tuple(toks)}
    return {tuple(toks[i:i+n]) for i in range(len(toks)-n+1)}

def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

@dataclass(frozen=True)
class ContaminationMatch:
    candidate_id: str
    reference_id: str
    exact_hash: bool
    ngram_jaccard: float
    blocked: bool

def contamination_scan(
    candidates: Sequence[dict],
    references: Sequence[dict],
    ngram_size: int = 5,
    threshold: float = 0.80,
) -> list[ContaminationMatch]:
    refs=[]
    for r in references:
        norm=normalize_text(str(r["text"]))
        refs.append((str(r["id"]), sha256_text(norm), token_ngrams(norm, ngram_size)))
    out=[]
    for c in candidates:
        cnorm=normalize_text(str(c["text"]))
        chash=sha256_text(cnorm)
        cgrams=token_ngrams(cnorm, ngram_size)
        for rid,rhash,rgrams in refs:
            exact = chash == rhash
            sim = jaccard(cgrams, rgrams)
            if exact or sim >= threshold:
                out.append(ContaminationMatch(str(c["id"]), rid, exact, round(sim,6), True))
    return out

@dataclass
class ConstraintResult:
    passed: bool
    name: str
    detail: str

def validate_candidate(
    candidate: str,
    baseline: str,
    max_growth_ratio: float = 0.25,
    required_markers: Sequence[str] = (),
    forbidden_fragments: Sequence[str] = (),
) -> list[ConstraintResult]:
    results=[]
    results.append(ConstraintResult(bool(candidate.strip()), "non_empty", "candidate must contain content"))
    growth=(len(candidate)-len(baseline))/max(1,len(baseline))
    results.append(ConstraintResult(growth <= max_growth_ratio, "growth_limit", f"growth={growth:.4f} max={max_growth_ratio:.4f}"))
    for marker in required_markers:
        results.append(ConstraintResult(marker in candidate, "required_marker", marker))
    low=candidate.lower()
    for frag in forbidden_fragments:
        results.append(ConstraintResult(frag.lower() not in low, "forbidden_fragment", frag))
    return results

@dataclass(frozen=True)
class Fitness:
    candidate_id: str
    format_pass_rate: float
    role_fidelity: float
    cold_score: float
    transfer_score: float
    redteam_survival: float
    critical_regression_rate: float
    token_cost: float
    latency: float
    prompt_size: float

MAX_KEYS=("format_pass_rate","role_fidelity","cold_score","transfer_score","redteam_survival")
MIN_KEYS=("critical_regression_rate","token_cost","latency","prompt_size")

def dominates(a: Fitness, b: Fitness) -> bool:
    no_worse=True
    strictly=False
    for k in MAX_KEYS:
        av,bv=getattr(a,k),getattr(b,k)
        if av < bv: no_worse=False
        if av > bv: strictly=True
    for k in MIN_KEYS:
        av,bv=getattr(a,k),getattr(b,k)
        if av > bv: no_worse=False
        if av < bv: strictly=True
    return no_worse and strictly

def pareto_front(items: Sequence[Fitness]) -> list[Fitness]:
    front=[]
    for x in items:
        if any(y.candidate_id != x.candidate_id and dominates(y,x) for y in items):
            continue
        front.append(x)
    return sorted(front, key=lambda x:x.candidate_id)

def promotion_gate(candidate: Fitness, baseline: Fitness) -> tuple[bool,list[str]]:
    failures=[]
    if candidate.cold_score <= baseline.cold_score:
        failures.append("COLD_GAIN_NOT_POSITIVE")
    if candidate.transfer_score <= baseline.transfer_score:
        failures.append("TRANSFER_GAIN_NOT_POSITIVE")
    if candidate.redteam_survival < baseline.redteam_survival:
        failures.append("REDTEAM_WORSE")
    if candidate.critical_regression_rate > 0:
        failures.append("CRITICAL_REGRESSION")
    return (not failures, failures)

def selftest() -> dict:
    # Stable split must be deterministic and cover all partitions over fixture IDs.
    ids=[f"case-{i}" for i in range(200)]
    s1=[stable_split(x) for x in ids]
    s2=[stable_split(x) for x in ids]
    assert s1 == s2
    assert {"train","validation","holdout"}.issubset(set(s1))

    # Exact and near-duplicate contamination.
    refs=[{"id":"cold-1","text":"Simulation output is not physical validation of a subsystem."}]
    cands=[
        {"id":"train-exact","text":"Simulation output is not physical validation of a subsystem."},
        {"id":"train-safe","text":"A reversible adapter requires a distinct artifact hash after optimization."},
    ]
    matches=contamination_scan(cands,refs,ngram_size=3,threshold=0.75)
    assert any(m.candidate_id=="train-exact" and m.exact_hash for m in matches)
    assert not any(m.candidate_id=="train-safe" for m in matches)

    # Constraint gate.
    cr=validate_candidate(
        "FACTS\nUNKNOWN\nNEXT_TEST",
        "FACTS\nUNKNOWN",
        max_growth_ratio=1.0,
        required_markers=["FACTS","UNKNOWN","NEXT_TEST"],
        forbidden_fragments=["PATENTED"],
    )
    assert all(x.passed for x in cr)

    # Pareto and promotion.
    base=Fitness("base",.40,.40,.50,.50,.50,0,100,10,1000)
    good=Fitness("good",.90,.70,.60,.60,.55,0,95,9,980)
    cheap=Fitness("cheap",.70,.60,.55,.55,.50,0,50,5,700)
    bad=Fitness("bad",.95,.80,.70,.40,.70,.10,90,8,950)
    front=pareto_front([base,good,cheap,bad])
    assert "base" not in {x.candidate_id for x in front}
    ok,fail=promotion_gate(good,base)
    assert ok and not fail
    ok2,fail2=promotion_gate(bad,base)
    assert not ok2 and "TRANSFER_GAIN_NOT_POSITIVE" in fail2 and "CRITICAL_REGRESSION" in fail2

    return {
        "schema":"CEREBRON_SELF_EVOLUTION_SELFTEST_V1",
        "status":"PASS",
        "stable_split_counts":{k:s1.count(k) for k in ("train","validation","holdout")},
        "contamination_matches":[asdict(m) for m in matches],
        "pareto_front":[x.candidate_id for x in front],
        "promotion_good":"PASS",
        "promotion_bad_failures":fail2,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--output",default="artifacts/cerebron-self-evolution-selftest.json")
    args=ap.parse_args()
    if not args.selftest:
        raise SystemExit("Use --selftest")
    report=selftest()
    p=ROOT/args.output
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
