#!/usr/bin/env python3
import argparse, json, math
from itertools import product

try:
    import sympy as sp
except Exception:
    sp = None
try:
    from z3 import Int, Solver, sat
except Exception:
    Int = Solver = sat = None
try:
    import networkx as nx
except Exception:
    nx = None


def symbolic_identity(max_r=10):
    rows=[]
    for r in range(1,max_r+1):
        # Verify 4^r z_r = 3^r z_0 + 2(4^r-3^r) for z_{k+1}=(3 z_k+2)/4
        z0=sp.symbols('z0', integer=True) if sp else None
        if sp:
            z=z0
            for _ in range(r):
                z=(3*z+2)/4
            residual=sp.simplify(4**r*z-(3**r*z0+2*(4**r-3**r)))
            ok=(residual==0)
        else:
            ok=None
        rows.append({'r':r,'identity_verified':ok})
    return {'worker':'sympy','claim_level':'FINITE_SYMBOLIC_VERIFICATION','rows':rows}


def modular_scan(umax=8,rmax=30,hmax=500):
    hits=[]
    for u in range(1,umax+1):
        mod=3**u
        for r in range(1,rmax+1):
            target=(-pow(pow(4,r,mod),-1,mod))%mod
            hs=[h for h in range(1,hmax+1,2) if h%mod==target]
            if hs:
                hits.append({'u':u,'r':r,'h_min':hs[0],'count_le_hmax':len(hs)})
    return {'worker':'modular','claim_level':'FINITE_ENUMERATION','umax':umax,'rmax':rmax,'hmax':hmax,'hits':hits}


def z3_hcoupling(umax=7,rmax=8,hmax=1000):
    if Solver is None:
        return {'worker':'z3','claim_level':'UNAVAILABLE','error':'z3-solver unavailable'}
    sols=[]
    # bounded exact search for one H-coupling transition
    for u in range(1,umax+1):
        for rj in range(1,rmax+1):
            for rn in range(1,rmax+1):
                hj=Int('hj'); hn=Int('hn')
                s=Solver()
                s.add(hj>=1,hj<=hmax,hn>=1,hn<=hmax,hj%2==1,hn%2==1)
                s.add((2**(u+2*rn))*hn - (3**(u+rj))*hj == 3**u-2**u)
                if s.check()==sat:
                    m=s.model()
                    sols.append({'u_next':u,'r_j':rj,'r_next':rn,'h_j':m[hj].as_long(),'h_next':m[hn].as_long()})
    return {'worker':'z3','claim_level':'BOUNDED_SAT_SEARCH','bounds':{'u':umax,'r':rmax,'h':hmax},'solutions':sols}


def graph_transitions(umax=5,rmax=6,hmax=300):
    if nx is None:
        return {'worker':'graph','claim_level':'UNAVAILABLE','error':'networkx unavailable'}
    G=nx.DiGraph()
    states=[]
    for u in range(1,umax+1):
        mod=3**u
        for r in range(1,rmax+1):
            target=(-pow(pow(4,r,mod),-1,mod))%mod
            for h in range(1,hmax+1,2):
                if h%mod==target:
                    states.append((u,r,h)); G.add_node((u,r,h))
    # bounded transition relation: exact H-coupling with u_next from destination state
    for a in states:
        ua,ra,ha=a
        for b in states:
            ub,rb,hb=b
            if (2**(ub+2*rb))*hb - (3**(ub+ra))*ha == 3**ub-2**ub:
                G.add_edge(a,b)
    cyc=list(nx.simple_cycles(G))
    return {'worker':'graph','claim_level':'FINITE_GRAPH_SEARCH','bounds':{'u':umax,'r':rmax,'h':hmax},'nodes':G.number_of_nodes(),'edges':G.number_of_edges(),'cycles_count':len(cyc),'cycles_preview':[list(map(list,c)) for c in cyc[:20]]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--worker',choices=['sympy','modular','z3','graph'],required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    fn={'sympy':symbolic_identity,'modular':modular_scan,'z3':z3_hcoupling,'graph':graph_transitions}[a.worker]
    result=fn()
    result['rule']='Finite computation is evidence, not a universal Collatz proof.'
    with open(a.out,'w') as f: json.dump(result,f,indent=2)
    print(json.dumps({k:result.get(k) for k in ('worker','claim_level','nodes','edges','cycles_count')}))

if __name__=='__main__': main()
