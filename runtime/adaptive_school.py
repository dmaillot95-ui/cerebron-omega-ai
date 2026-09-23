import argparse, hashlib, json, pathlib, datetime
ROOT=pathlib.Path("agora");ROOT.mkdir(exist_ok=True)
PROFILES=ROOT/"learning_profiles.json";OUT=pathlib.Path("artifacts/adaptive_lesson.json")
AIS=["SAPHEA","SPIRALION","ETHERION","HYPERION","ASTRION","METRION"]
def load():
    if PROFILES.exists():return json.loads(PROFILES.read_text())
    return {"schema":"CEREBRON_ADAPTIVE_SCHOOL_V1","profiles":{}}
def clamp(x):return max(0.0,min(1.0,x))
ap=argparse.ArgumentParser()
ap.add_argument("--ai",choices=AIS,required=True);ap.add_argument("--domain",required=True)
ap.add_argument("--result",choices=["PASS","FAIL","PARTIAL","CONTRADICTION"],required=True)
ap.add_argument("--difficulty",type=float,default=.5);ap.add_argument("--evidence",default="")
a=ap.parse_args();d=load();p=d["profiles"].setdefault(a.ai,{});q=p.setdefault(a.domain,{"mastery":0.5,"attempts":0,"passes":0,"failures":0,"contradictions":0})
q["attempts"]+=1
delta={"PASS":.06,"PARTIAL":.015,"FAIL":-.05,"CONTRADICTION":-.08}[a.result]
q["mastery"]=round(clamp(q["mastery"]+delta*(.5+clamp(a.difficulty))),4)
if a.result=="PASS":q["passes"]+=1
elif a.result=="CONTRADICTION":q["contradictions"]+=1
else:q["failures"]+=1
m=q["mastery"]
if a.result=="CONTRADICTION":kind="RED_TEAM_RECONCILIATION";nextdiff=max(.2,a.difficulty-.15)
elif m<.4:kind="REMEDIAL_LESSON";nextdiff=max(.2,a.difficulty-.1)
elif m<.7:kind="GUIDED_CHALLENGE";nextdiff=min(.8,a.difficulty+.05)
else:kind="TRANSFER_TEST";nextdiff=min(1.0,a.difficulty+.1)
lesson={"lesson_id":"LESSON:"+hashlib.sha256(f"{a.ai}|{a.domain}|{q['attempts']}|{kind}".encode()).hexdigest()[:20],"student":a.ai,"domain":a.domain,"kind":kind,"difficulty":round(nextdiff,2),"mastery":m,"teacher_sequence":["PEDAGOGUE","EXAMINER","RED_TEAM","CONNECTOR","SYNTHESIZER"],"evidence_ref":a.evidence,"rules":["NO_GOLD_AUTO_PROMOTION","NO_WEIGHT_UPDATE","UNAIDED_RETEST_REQUIRED","MEASURE_GAIN_BEFORE_PROMOTION"],"created_at":datetime.datetime.now(datetime.timezone.utc).isoformat()}
PROFILES.write_text(json.dumps(d,indent=2)+"\n");OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(lesson,indent=2)+"\n");print(json.dumps(lesson))
