#!/usr/bin/env python3
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FB=json.loads((ROOT/'memory/failure-bank-v1.json').read_text())
ROLES={
 'BETA':('problem contract','Extract assumptions, constraints, evidence ceiling and falsifiable acceptance criteria.'),
 'GAMMA':('causal mechanism','Explain the causal chain from root cause to observed failure and identify a discriminating test.'),
 'EPSILON':('robustness uncertainty','Identify sensitivity, uncertainty and transfer risks; propose a robustness check.'),
 'ZETA':('optimization efficiency','Propose the lowest-cost repair that preserves evidence quality and state what must not be optimized away.'),
 'ETA':('temporal dynamics','Reconstruct the state transition before/failure/repair/retest and identify the next temporal checkpoint.')
}
VARIANTS=['DIAGNOSE','FALSIFY','REPAIR','TRANSFER']
MIN=32
entries=[e for e in FB.get('entries',[]) if e.get('FAILURE_ID') and e.get('ROOT_CAUSE')]
entries.sort(key=lambda e:e['FAILURE_ID'])
assert entries, 'failure bank empty'
out={'schema':'CEREBRON_WAVE4_CANDIDATE_CURRICULUM_V1','status':'CANDIDATE_NOT_RELEASED','source':'memory/failure-bank-v1.json','source_sha256':hashlib.sha256((ROOT/'memory/failure-bank-v1.json').read_bytes()).hexdigest(),'roles':{},'training_released':False,'training_executed':False,'weights_changed':False}
for role,(focus,instruction) in ROLES.items():
    rows=[]
    i=0
    while len(rows)<40:
        e=entries[i%len(entries)]; variant=VARIANTS[(i//len(entries))%len(VARIANTS)]
        fid=e['FAILURE_ID']
        prompt=(f'ROLE={role}; TASK={variant}; FOCUS={focus}. Failure evidence: ID={fid}; class={e.get("FAILURE_CLASS")}; signature={e.get("FAILURE_SIGNATURE")}; root_cause={e.get("ROOT_CAUSE")}; impact={e.get("IMPACT")}; scope={e.get("SCOPE")}; repair_status={e.get("REPAIR_STATUS")}; transfer_risk={e.get("TRANSFER_RISK")}. {instruction} Preserve uncertainty and cite the failure ID. Do not claim more than the evidence.')
        rid=hashlib.sha256((role+'|'+fid+'|'+variant).encode()).hexdigest()
        row={'record_id':rid,'role':role,'split':'CANDIDATE','validation_status':'UNVALIDATED','task_variant':variant,'source_id':fid,'provenance':{'failure_id':fid,'evidence_refs':e.get('EVIDENCE_REFS',[]),'source_sha256':out['source_sha256']},'prompt':prompt,'target_answer':None,'training_eligible':False}
        if rid not in {r['record_id'] for r in rows}: rows.append(row)
        i+=1
        if i>len(entries)*len(VARIANTS)*2: break
    out['roles'][role]={'count':len(rows),'records':rows,'meets_candidate_minimum':len(rows)>=MIN}
assert all(v['count']>=MIN for v in out['roles'].values())
out['total_records']=sum(v['count'] for v in out['roles'].values())
out['dataset_sha256']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
p=ROOT/'artifacts/wave4-candidate-curriculum-v1.json'; p.parent.mkdir(exist_ok=True); p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':out['status'],'counts':{k:v['count'] for k,v in out['roles'].items()},'total_records':out['total_records'],'dataset_sha256':out['dataset_sha256']}))
