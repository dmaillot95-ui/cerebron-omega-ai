#!/usr/bin/env python3
import sympy as s,json,pathlib
# B9 exact intersection-field audit for the four primitive polar circles.
x,y=s.symbols('x y', real=True)
circles=[
 s.expand((x-1)**2+y**2-1),s.expand((x+1)**2+y**2-1),
 s.expand(x**2+(y-1)**2-1),s.expand(x**2+(y+1)**2-1)]
sols=set()
for i in range(4):
 for j in range(i+1,4):
  for q in s.solve([circles[i],circles[j]],[x,y], dict=True):
   sols.add((s.simplify(q[x]),s.simplify(q[y])))
pts=sorted([(str(a),str(b),str(s.simplify(s.sqrt(a*a+b*b)))) for a,b in sols])
# General adjacent cardinal circles radius a, centers (a,0),(0,a): derive nonzero intersection.
a=s.symbols('a', positive=True)
gen=s.solve([(x-a)**2+y**2-a**2,x**2+(y-a)**2-a**2],[x,y],dict=True)
# Circle family r=2cos(theta) has Cartesian polynomial x^2+y^2-2x=0; rotated by alpha:
alpha=s.symbols('alpha', real=True)
rot=s.expand(x**2+y**2-2*(x*s.cos(alpha)+y*s.sin(alpha)))
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-B9-EXACT-INTERSECTION","primitive_intersections":pts,"general_adjacent_solution":[{str(k):str(s.simplify(v)) for k,v in q.items()} for q in gen],"rotated_circle_equation":str(rot),"theorem_candidate":"For two equal circles of radius a tangent at O with orthogonal center vectors, the second intersection is the vector sum of the centers and has norm a*sqrt(2).","status":"DERIVED; elementary Euclidean geometry, not novel.","next":"B10 replace orthogonal angle pi/2 by arbitrary alpha. Derive second-intersection radius as a function of alpha and map spectral constants across alpha."}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/sphere-dor-b9.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
