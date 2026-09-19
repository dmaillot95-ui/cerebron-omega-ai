#!/usr/bin/env python3
import math,cmath,json,pathlib
# B4 harmonic/topological probe of the exact four base polar branches.
N=4096
branches={"2cos":lambda t:2*math.cos(t),"-2cos":lambda t:-2*math.cos(t),"2sin":lambda t:2*math.sin(t),"-2sin":lambda t:-2*math.sin(t)}
def dft_peaks(z,maxk=32):
 out=[]
 for k in range(maxk+1):
  c=sum(z[n]*cmath.exp(-2j*math.pi*k*n/N) for n in range(N))/N
  if abs(c)>1e-8: out.append((k,abs(c)))
 return sorted(out,key=lambda x:-x[1])[:10]
res={}
for name,f in branches.items():
 z=[]
 for n in range(N):
  t=2*math.pi*n/N;r=f(t);z.append(r*cmath.exp(1j*t))
 res[name]={"harmonic_peaks":dft_peaks(z)}
# exact intersection graph known analytically for centers cardinal radius1
vertices=[(0,0),(1,1),(1,-1),(-1,1),(-1,-1)]
radii=sorted(set(round(math.hypot(x,y),12) for x,y in vertices))
# golden 36-degree rotation matrix trace and 45 diagonal retained as known controls
controls={"trace_R_pi_over_5":2*math.cos(math.pi/5),"diag_radius":math.sqrt(2),"cos30_scaled":2*math.cos(math.pi/6)}
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-B4-HARMONIC-TOPOLOGY","N":N,"branches":res,"intersection_graph_vertices":vertices,"radial_strata":radii,"controls":controls,"finding":"The four primitive polar circles are low-order harmonic objects; complexity/new invariants cannot come from the primitive circles alone. It must arise from the user's composition/iteration/lift rule.","next":"infer/test composition operators: union, Minkowski sum/product, complex multiplication, inversion, rotations; rank by whether they reproduce the target rosette without parameter fitting.","novelty_status":"OPEN; no new theorem claimed"}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/sphere-dor-b4.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
