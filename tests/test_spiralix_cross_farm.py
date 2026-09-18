#!/usr/bin/env python3
"""SPIRALIX cross-farm routing semantics test.
E2 software/interface evidence only: no claim of live cross-repository delivery.
"""
import copy
from tools.glyph_router import encode, verify, route, decode

CASES = [
 ("collatz","reason","cerebron-collatz-theory-farm"),
 ("struct","calculate","cerebron-farm-51-architecton-struct"),
 ("thermal","simulate","cerebron-farm-53-architecton-thermal"),
 ("metrology","measure","cerebron-farm-58-architecton-metrology"),
 ("learn","evaluate","cerebron-farm-59-verified-learning"),
 ("hardware","design","cerebron-farm-60-hardware-architecture"),
 ("cross-farm","route","cerebron-farm-67-cross-farm-communication"),
 ("theorem","prove","cerebron-farm-70-theorem-proof-engineering"),
 ("evidence-gate","audit","cerebron-farm-72-reality-evidence-gate"),
 ("integration","qualify","cerebron-farm-73-system-integration-qualification"),
]

def packet(domain, task):
    return encode(domain,"cross-farm-interface-validation","deterministic-route-hash-decode","E2","VERIFY","high",task,{"claim":"transport/routing semantics only"})

def main():
    for domain,task,target in CASES:
        p=packet(domain,task)
        ok,status=verify(p)
        assert ok and status=="VERIFIED"
        r=route(p)
        assert r["status"]=="ROUTED" and r["farm"]==target, (domain,r,target)
        assert "SPIRALIX-OMEGA" in decode(p)
    bad=packet("collatz","reason")
    bad=copy.deepcopy(bad); bad["payload"]["claim"]="tampered"
    ok,status=verify(bad)
    assert not ok and status=="HASH_MISMATCH"
    assert route(bad)["status"]=="REJECTED"
    unknown=packet("unmapped-domain","unmapped-task")
    assert route(unknown)["status"]=="UNKNOWN"
    print("VERIFIED: cross-farm routing semantics; cases=%d; tamper-rejection=PASS; unknown-route=PASS" % len(CASES))

if __name__=="__main__":
    main()
