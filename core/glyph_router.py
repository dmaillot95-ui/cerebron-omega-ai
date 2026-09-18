import json, math, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
GLYPHS=ROOT/'config'/'glyph-vector.json'
FARMS=ROOT/'config'/'farms.json'
DOMAIN_HINTS={'C':[1,2,3,4,5,6,7,9,33,34,35,39,42],'Φ':[10,36,37,34],'S':[15,13,16,32,36,37,42],'E':[14,13,16,31,36,37],'I':[16,13,32,36,37,42],'M':[11,13,16,32,36,37],'R':[13,16,17,18,32,36,37],'A':[18,41,42,44,45,34,35],'X':[8,33,34,35,38,39,40,42,43,44,45]}
METHOD_HINTS={'Θ':[9,34,35],'Δ':[9,36,34],'Σ':[43,38,40,42],'Χ':[33,34,35],'F':[34,35,38],'V':[34,35,41],'D':[20,40,34],'P':[32,23,22],'L':[8,48,34],'₃A':[3,9,34],'H':[1,3,9,34],'MAX':[1,2,4,6,7],'L→G':[2,4,6,7,34,38]}
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def tokenize(expr):
 g=load(GLYPHS)['glyphs']; return [k for k in sorted(g,key=len,reverse=True) if k in expr]
def route_glyph(expr,max_farms=16):
 reg=load(FARMS); by={f['id']:f for f in reg['farms']}; toks=tokenize(expr); scores={}
 for t in toks:
  for rank,i in enumerate(DOMAIN_HINTS.get(t,[])+METHOD_HINTS.get(t,[])):
   scores[i]=scores.get(i,0)+max(1,20-rank)
 ranked=sorted(scores.items(),key=lambda x:(-x[1],x[0]))
 return {'expression':expr,'tokens':toks,'selected_farms':[by[i]|{'vector_score':s} for i,s in ranked[:max_farms] if i in by],'rules':load(GLYPHS)['rules']}
if __name__=='__main__':
 import sys; print(json.dumps(route_glyph(' '.join(sys.argv[1:])),ensure_ascii=False,indent=2))
