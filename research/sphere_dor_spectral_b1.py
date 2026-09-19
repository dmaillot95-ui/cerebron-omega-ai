#!/usr/bin/env python3
import math,json,pathlib
phi=(1+math.sqrt(5))/2
def cs(d): return 2*math.cos(math.radians(d))
def sn(d): return 2*math.sin(math.radians(d))
angles=range(0,360)
targets={"sqrt2":math.sqrt(2),"sqrt3":math.sqrt(3),"phi":phi,"invphi":1/phi}
hits=[]
for a in angles:
 for branch,fn in [("2cos",cs),("2sin",sn)]:
  v=fn(a)
  for name,t in targets.items():
   if abs(abs(v)-t)<1e-12:hits.append({"angle":a,"branch":branch,"value":v,"target":name})
# exact four-circle intersections: centers (±1,0),(0,±1), radius 1
centers=[(1,0),(-1,0),(0,1),(0,-1)]
ints=set()
for i,(x0,y0) in enumerate(centers):
 for x1,y1 in centers[i+1:]:
  dx,dy=x1-x0,y1-y0; d=math.hypot(dx,dy)
  if d>2 or d==0: continue
  mx,my=(x0+x1)/2,(y0+y1)/2; h=math.sqrt(max(0,1-d*d/4)); ux,uy=-dy/d,dx/d
  for s in (-1,1):ints.add((round(mx+s*h*ux,12),round(my+s*h*uy,12)))
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-SPECTRAL-MAP-B1","known_constant_hits":hits,"four_circle_intersections":sorted(ints),"intersection_radii":sorted(set(round(math.hypot(x,y),12) for x,y in ints)),"claims":["four base circles have nonzero intersections (±1,±1) at radius sqrt(2)","phi/sqrt2/sqrt3 hits are exact classical trigonometric special values"],"firewall":"No novelty claim. Search next for invariants not reducible to classical trigonometry."}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/spectral-map-b1.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
