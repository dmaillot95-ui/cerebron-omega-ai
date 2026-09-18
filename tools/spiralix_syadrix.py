#!/usr/bin/env python3
"""SYADRIX Ω: lossless-first dedup/correlation layer."""
import json,hashlib
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sha(x): return hashlib.sha256(canon(x).encode()).hexdigest()
def ingest(records):
    source_bank={}; refs=[]; contradictions=[]
    for r in records:
        body={k:v for k,v in r.items() if k!="record_id"}
        h=sha(body)
        source_bank.setdefault(h,body)
        refs.append({"record_id":r.get("record_id"),"sha256":h,"dependencies":sorted(set(r.get("dependencies",[])))})
    by_claim={}
    for h,r in source_bank.items(): by_claim.setdefault(r.get("subject",""),[]).append((h,r))
    for subject,items in by_claim.items():
        claims={canon(r.get("claim")) for _,r in items}
        if len(claims)>1: contradictions.append({"subject":subject,"source_hashes":[h for h,_ in items]})
    return {"source_bank":source_bank,"references":refs,"contradictions":contradictions,
            "raw_count":len(records),"unique_count":len(source_bank),"exact_duplicates":len(records)-len(source_bank)}
def synthesize(index):
    return {"status":"CONTRADICTORY" if index["contradictions"] else "SUPPORTED",
            "unique_sources":index["unique_count"],"exact_duplicates_removed_from_working_set":index["exact_duplicates"],
            "source_hashes":sorted(index["source_bank"]),"contradictions":index["contradictions"]}
if __name__=="__main__":
    rows=[
      {"record_id":"a","subject":"X","claim":"p","dependencies":["D1"],"value":42},
      {"record_id":"b","subject":"X","claim":"p","dependencies":["D1"],"value":42},
      {"record_id":"c","subject":"X","claim":"not-p","dependencies":["D2"],"value":43}]
    idx=ingest(rows); s=synthesize(idx)
    assert idx["raw_count"]==3 and idx["unique_count"]==2 and idx["exact_duplicates"]==1
    assert s["status"]=="CONTRADICTORY" and len(s["source_hashes"])==2
    print(json.dumps({"status":"VERIFIED","index":{k:v for k,v in idx.items() if k!="source_bank"},"synthesis":s,"claim":"compression/dedup protocol test only"}))
