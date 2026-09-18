#!/usr/bin/env python3
import json,math,hashlib
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def reduce_tree(items,base=2):
 if base<2: raise ValueError("base >=2")
 if not items or len(items)>4096: raise ValueError("1..4096 items")
 level=[{"refs":[x],"hash":digest([x]),"contradictions":[]} for x in items]; levels=[level]
 while len(level)>1:
  nxt=[]
  for i in range(0,len(level),base):
   g=level[i:i+base]
   refs=[r for n in g for r in n["refs"]]
   contradictions=[c for n in g for c in n.get("contradictions",[])]
   nxt.append({"refs":refs,"hash":digest([n["hash"] for n in g]),"contradictions":contradictions})
  level=nxt;levels.append(level)
 return {"base":base,"input_count":len(items),"depth":len(levels)-1,"levels":levels,"root":levels[-1][0]}
if __name__=="__main__":
 r=reduce_tree([f"R{i}" for i in range(64)],2)
 assert r["depth"]==6 and len(r["root"]["refs"])==64
 r["levels"][0][0]["contradictions"].append("C1")
 r2=reduce_tree([{"id":"R0","contradiction":"C1"},"R1"],2)
 assert len(r2["root"]["refs"])==2
 print(json.dumps({"status":"VERIFIED","input_count":64,"base":2,"depth":6,"root_hash":r["root"]["hash"],"claim":"hierarchical reduction protocol test only"}))
