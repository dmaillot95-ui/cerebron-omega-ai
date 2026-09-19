#!/usr/bin/env python3
import math,json,pathlib
# B3: lift angular families into 3D and test rotation-invariant quantities.
# No physical-field claim; purely geometric SO(3) experiment.
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def rotz(t,p): 
 c,s=math.cos(t),math.sin(t);x,y,z=p;return(c*x-s*y,s*x+c*y,z)
def roty(t,p):
 c,s=math.cos(t),math.sin(t);x,y,z=p;return(c*x+s*z,y,-s*x+c*z)
# seed: four tangent-circle centers embedded in xy; sample circle planes then rotate through beta
centers=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]
samples=[]
for ci,c in enumerate(centers):
 for deg in range(0,360,2):
  t=math.radians(deg)
  # circle in xy around center
  p=(c[0]+math.cos(t),c[1]+math.sin(t),0.0)
  for beta_deg in range(0,181,9):
   beta=math.radians(beta_deg);q=roty(beta,p);q=rotz(t/5,q)
   samples.append((ci,deg,beta_deg,q,norm(q)))
# radial levels are invariant under SO(3); discover clusters blindly
vals=sorted(s[4] for s in samples)
clusters=[]
for v in vals:
 if not clusters or abs(v-clusters[-1][-1])>1e-8: clusters.append([v])
 else: clusters[-1].append(v)
levels=[{"rho":sum(c)/len(c),"multiplicity":len(c)} for c in clusters]
# retain extrema/high degeneracy as candidate spectral events
events=sorted(levels,key=lambda q:(-q["multiplicity"],q["rho"]))[:30]
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-B3-SO3","sample_count":len(samples),"distinct_radial_levels":len(levels),"top_degenerate_levels":events,"verified_invariant":"Euclidean radius is unchanged by the applied SO(3) rotations","interpretation":"Any genuinely new spectral signature must use more than radius alone; test intersection topology, linking, winding and harmonic spectra next.","physics_status":"NONE — geometric model only"}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/sphere-dor-b3.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
