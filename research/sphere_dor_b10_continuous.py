#!/usr/bin/env python3
import sympy as s,json,pathlib
a,th=s.symbols('a th', positive=True, real=True)
# Equal circles radius a tangent at O; centers c1=a(1,0), c2=a(cos th,sin th).
# Nonzero intersection is c1+c2; radial norm:
rho=s.simplify(s.sqrt((a*(1+s.cos(th)))**2+(a*s.sin(th))**2))
rho2=s.trigsimp(rho**2)
# on 0<=th<=pi, rho=2a cos(th/2)
formula=2*a*s.cos(th/2)
events={}
for deg in [18,30,36,45,54,60,72,90,108,120,144]:
 q=s.simplify(formula.subs({a:1,th:s.pi*s.Rational(deg,180)}))
 events[str(deg)]={"rho":str(q),"rho_numeric":float(s.N(q,15))}
# Invert law: theta=2 acos(rho/(2a))
R=s.symbols('R', nonnegative=True)
out={"CEREBRON_VERSION":"C42.1","campaign":"SPHERE-DOR-B10-CONTINUOUS-INTERSECTION","exact_law":"rho(theta)=2*a*cos(theta/2), 0<=theta<=pi","squared_law":str(rho2),"inverse":"theta=2*acos(rho/(2*a))","events":events,"key_consequences":{"theta90":"rho=a*sqrt(2)","theta72":"rho=a*phi (because 2*cos36=phi)","theta60":"rho=a*sqrt(3)"},"structural_finding":"sqrt(2), phi, sqrt(3) are three samples of ONE continuous intersection-radius law, at center separations 90°,72°,60° respectively.","novelty_status":"Exact and useful unification, but the chord/intersection law itself is classical Euclidean geometry.","next":"B11 iterate the circle-intersection operator and classify closure spectra; test whether repeated projection creates nontrivial invariant beyond classical polygon/chord geometry."}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/sphere-dor-b10.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
