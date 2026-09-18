#!/usr/bin/env python3
import re,json
PAT=re.compile(r"^Ω\^(\d+)\[([^\]]+)\]$")
def expand(s):
 m=PAT.match(s.strip())
 if not m: raise ValueError("invalid SPIRALIX exponent")
 n=int(m.group(1)); targets=[x.strip() for x in m.group(2).split(",") if x.strip()]
 if n<1 or n>64: raise ValueError("expansion limit")
 if n!=len(targets): raise ValueError("exponent must equal explicit target count")
 return [{"ordinal":i+1,"target":t,"real_task_required":True} for i,t in enumerate(targets)]
if __name__=="__main__":
 x=expand("Ω^3[F1,F3,F34]")
 assert [i["target"] for i in x]==["F1","F3","F34"]
 try: expand("Ω^5[F1,F3]")
 except ValueError: pass
 else: raise AssertionError("phantom multiplication accepted")
 print(json.dumps({"status":"VERIFIED","expanded":x,"claim":"notation expansion test only"},ensure_ascii=False))
