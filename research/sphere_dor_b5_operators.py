#!/usr/bin/env python3
import math,cmath,json,pathlib
# B5 operator funnel. Blindly compare structural complexity generated from primitive z(theta).
N=720
ts=[2*math.pi*n/N for n in range(N)]
base=[2*math.cos(t)*cmath.exp(1j*t) for t in ts]
ops={}
ops["identity"]=base
ops["square_complex"]=[z*z for z in base]
ops["golden_rotation"]=[z*cmath.exp(1j*math.pi/5) for z in base]
ops["quarter_rotation"]=[z*1j for z in base]
ops["inversion"]=[1/z if abs(z)>1e-9 else complex(float("nan"),0) for z in base]
ops["product_shift36"]=[base[n]*base[(n+N//10)%N] for n in range(N)]
ops["sum_shift36"]=[base[n]+base[(n+N//10)%N] for n in range(N)]
def signature(arr):
 good=[z for z in arr if math.isfinite(z.real) and math.isfinite(z.imag)]
 radii=[abs(z) for z in good]
 # winding around origin where defined
 arg=[cmath.phase(z) for z in good if abs(z)>1e-8]
 unwrap=0.0
 for a,b in zip(arg,arg[1:]):
  d=b-a
  if d>math.pi:d-=2*math.pi
  if d<-math.pi:d+=2*math.pi
  unwrap+=d
 # occupancy angular/radial bins as crude complexity measure
 cells=set()
 for z in good:
  a=(cmath.phase(z)+math.pi)/(2*math.pi)
  rr=min(abs(z),8)/8
  cells.add((int(a*72)%72,min(39,int(rr*40))))
 return {"finite":len(good),"rho_min":min(radii),"rho_max":max(radii),"winding_approx":unwrap/(2*math.pi),"occupied_cells":len(cells)}
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-B5-OPERATOR-FUNNEL","operators":{k:signature(v) for k,v in ops.items()},"selection_rule":"Prefer operators that create new topology/spectral structure without fitted constants; reject mere rigid rotations as information-neutral.","warning":"This does not yet compare to the user's video image or prove the user's exact composition rule.","next":"B6 derive algebraic recurrence and search invariant polynomial / closure conditions for surviving operators."}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/sphere-dor-b5.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
