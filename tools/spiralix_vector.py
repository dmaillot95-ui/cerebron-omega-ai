#!/usr/bin/env python3
"""SPIRALIX-VECTOR v1: deterministic evidence-aware packets.
This layer structures/routs results; it does not claim semantic truth or proof.
"""
import hashlib, json, math
from collections import Counter

def digest(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def tokens(text):
    return [x.lower() for x in __import__("re").findall(r"[A-Za-zÀ-ÿ0-9_]+", text or "")]

def lexical_vector(text):
    """Dependency-free sparse baseline. Replace only after ablation beats it."""
    return Counter(tokens(text))

def cosine(a,b):
    common=set(a)&set(b)
    num=sum(a[k]*b[k] for k in common)
    da=math.sqrt(sum(v*v for v in a.values())); db=math.sqrt(sum(v*v for v in b.values()))
    return num/(da*db) if da and db else 0.0

def packet(packet_id, source_colony, task_id, text, evidence_level="E0",
           confidence=0.0, unknowns=None, risk=0.5, dependencies=None,
           memory_checkpoint=None, evidence_refs=None):
    return {
      "schema":"spiralix-vector-packet-v1","packet_id":packet_id,
      "source_colony":source_colony,"task_id":task_id,"text_digest":digest(text),
      "V":{"P":task_id,"E":evidence_level,"C":float(confidence),
           "U":unknowns or [],"R":float(risk),"D":dependencies or [],
           "M":memory_checkpoint},
      "evidence_refs":evidence_refs or [],
      "dependency_fingerprint":digest(json.dumps(sorted(dependencies or []))),
      "text":text
    }

def compare(a,b, similarity_threshold=0.82):
    sim=cosine(lexical_vector(a.get("text","")),lexical_vector(b.get("text","")))
    shared=sorted(set(a["V"].get("D",[])) & set(b["V"].get("D",[])))
    same_task=a["task_id"]==b["task_id"]
    return {
      "a":a["packet_id"],"b":b["packet_id"],"similarity":round(sim,6),
      "same_task":same_task,"shared_dependencies":shared,
      "possible_duplicate":bool(same_task and sim>=similarity_threshold),
      "independent_evidence":bool(not shared and a["source_colony"]!=b["source_colony"]),
      "rule":"SIMILARITY_NE_PROOF"
    }

def route(comparison):
    if comparison["shared_dependencies"]:
        return "DEPENDENCY_AUDIT"
    if comparison["possible_duplicate"]:
        return "DEDUP_AUDIT"
    if comparison["same_task"] and comparison["similarity"] < 0.35:
        return "CONTRADICTION_OR_DIVERGENCE_REDTEAM"
    return "STANDARD_AUDIT"

def self_test():
    a=packet("A","C03","T1","A cycle requires exact valuation equality and closure.","E2",.7,dependencies=["SRC1"])
    b=packet("B","C12","T1","Exact valuation equality and closure are required for a cycle.","E2",.7,dependencies=["SRC1"])
    c=compare(a,b)
    assert c["shared_dependencies"]==["SRC1"]
    assert c["independent_evidence"] is False
    assert route(c)=="DEPENDENCY_AUDIT"
    return {"status":"PASS","comparison":c,"route":route(c),
            "claim":"deterministic packet/comparison self-test only"}

if __name__=="__main__":
    print(json.dumps(self_test(),ensure_ascii=False,indent=2))
