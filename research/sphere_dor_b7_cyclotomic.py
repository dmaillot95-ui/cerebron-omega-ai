#!/usr/bin/env python3
import sympy as s,json,pathlib
x=s.symbols('x')
rows=[]
for n in range(3,31):
 lam=2*s.cos(s.pi/n)
 p=s.Poly(s.minpoly(lam,x),x)
 # Chebyshev closure: T_n(lam/2)=cos(pi)=-1
 closure=s.simplify(s.chebyshevt(n,lam/2)+1)
 rows.append({"n":n,"lambda":str(s.simplify(lam)),"degree":p.degree(),"minpoly":str(p.as_expr()),"chebyshev_closure":str(closure)})
# recurrence for traces of powers of an SO(2) rotation: a_0=2,a_1=lambda,a_{k+1}=lambda*a_k-a_{k-1}
L=s.symbols('L'); seq=[s.Integer(2),L]
for k in range(1,10):seq.append(s.expand(L*seq[-1]-seq[-2]))
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-B7-CYCLOTOMIC-CHEBYSHEV","family":"lambda_n=2*cos(pi/n)","rows":rows,"trace_recurrence":[str(q) for q in seq],"exact_closure":"T_n(lambda_n/2)+1=0","interpretation":"The observed sqrt(2), phi, sqrt(3) belong to the trace spectrum of finite planar rotations; all n generate algebraic values governed by cyclotomic/Chebyshev structure.","novelty_status":"Classical structure. Candidate novelty, if any, must be in the user's circle-composition geometry or a new invariant derived from it.","next":"B8 build composition graph using lambda_n as edge/scale labels and search for invariant cycles not implied by Chebyshev closure."}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/sphere-dor-b7.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
