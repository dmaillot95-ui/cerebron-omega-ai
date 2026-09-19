#!/usr/bin/env python3
import math,json,pathlib
# B8 composition graph: spectral labels lambda_n on circle-derived transformations.
# Search cycles first, then compare with classical angle-addition/Chebyshev predictions.
nodes=list(range(3,31))
lam={n:2*math.cos(math.pi/n) for n in nodes}
edges=[]
# operations motivated by geometry: complement, doubling/halving when integer, golden 36° shifts encoded as angle sums
for n in nodes:
 for m in nodes:
  # product-to-sum residual: lambda_n lambda_m = 2cos(a+b)+2cos(a-b)
  a=math.pi/n;b=math.pi/m
  rhs=2*math.cos(a+b)+2*math.cos(a-b)
  res=lam[n]*lam[m]-rhs
  if abs(res)<1e-12: edges.append({"n":n,"m":m,"type":"product_to_sum","residual":res})
# detect near coincidences among pair sums/products without preloaded constants
events=[]
for i,n in enumerate(nodes):
 for m in nodes[i:]:
  vals={"sum":lam[n]+lam[m],"product":lam[n]*lam[m],"difference":abs(lam[n]-lam[m])}
  for op,v in vals.items():
   for k in nodes:
    if abs(v-lam[k])<1e-10:
     events.append({"n":n,"m":m,"op":op,"k":k,"value":v})
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-B8-COMPOSITION-GRAPH","nodes":len(nodes),"identity_edges":len(edges),"blind_closure_events":events,"finding":"All product-to-sum closures tested are explained by classical trigonometric angle addition. Any listed lambda closure is therefore a candidate only until symbolic reduction excludes those identities.","novelty_gate":"No event is novel unless it survives symbolic reduction against trig/Chebyshev/cyclotomic identities.","next":"B9 derive exact user's circle composition from r=±2sin/cos and test intersection-generated values against the cyclotomic field."}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/sphere-dor-b8.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
