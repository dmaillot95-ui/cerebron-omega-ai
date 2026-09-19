#!/usr/bin/env python3
import math,json,pathlib
# B2 blind discovery: do not preload phi/sqrt2/sqrt3 as targets.
# 16 oriented unit circles: centers on two radii (1 and 2) at 8 directions k*pi/4.
circles=[]
for R in (1.0,2.0):
 for k in range(8):
  a=k*math.pi/4
  circles.append((R*math.cos(a),R*math.sin(a),1.0,R,k))
pts=[]
for i,c0 in enumerate(circles):
 x0,y0,r0,_,_=c0
 for j in range(i+1,len(circles)):
  x1,y1,r1,_,_=circles[j]; dx=x1-x0;dy=y1-y0;d=math.hypot(dx,dy)
  if d<1e-12 or d>r0+r1+1e-12 or d<abs(r0-r1)-1e-12: continue
  aa=(r0*r0-r1*r1+d*d)/(2*d); h2=r0*r0-aa*aa
  if h2 < -1e-10: continue
  h=math.sqrt(max(0,h2)); px=x0+aa*dx/d;py=y0+aa*dy/d
  for s in (-1,1):
   x=px+s*h*(-dy/d);y=py+s*h*(dx/d)
   pts.append((x,y,math.hypot(x,y),math.atan2(y,x)))
# blind cluster radial invariants
vals=sorted(p[2] for p in pts)
clusters=[]
for v in vals:
 if not clusters or abs(v-clusters[-1][-1])>1e-9: clusters.append([v])
 else: clusters[-1].append(v)
levels=[{"rho":sum(c)/len(c),"multiplicity":len(c)} for c in clusters]
# integer-relation-style recognition only AFTER discovery, against small radicals
recogn=[]
for q in levels:
 v=q["rho"]; candidates=[]
 for n in range(1,21):
  if abs(v-math.sqrt(n))<1e-9:candidates.append(f"sqrt({n})")
 for n in range(1,11):
  if abs(v*n-round(v*n))<1e-9:candidates.append(f"{round(v*n)}/{n}")
 recogn.append({**q,"posthoc_simple_forms":candidates})
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-B2-BLIND-16","circle_count":16,"intersection_events":len(pts),"blind_radial_levels":recogn,"method":"discover radii first; recognize simple forms only afterward","limitations":["16-circle architecture is a test hypothesis, not yet uniquely derived from user's construction","2D only; no physical interpretation","simple-form recognizer is deliberately narrow"],"next":"derive the user's exact 16-circle generator, then lift to SO(3) and compare invariants"}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/sphere-dor-b2.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
