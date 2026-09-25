from runtime.rdx_rd_handoff_v1 import validate

def sample():
    return {
      "schema":"CEREBRON_RDX_RD_HANDOFF_V1",
      "handoff_id":"HANDOFF-CANARY-001",
      "project_id":"S01",
      "producer":{"session_role":"R&D_EXECUTION_PLANE","farm_id_or_null":None,"ai_or_model":"CANARY","role":"TEST","mission":"schema test"},
      "canonical_ids":["RESULT-CANARY-001","TEST-CANARY-001"],
      "artifacts":[{"artifact_id":"ART-CANARY","kind":"receipt","sha256":"a"*64,"location":"synthetic://canary","visibility":"PRIVATE"}],
      "sources":[{"source_id":"SRC-CANARY-001","origin":"OWNED_SYNTHETIC","citation_or_location":"synthetic://source","rights_status":"ALLOWED"}],
      "executions":[{"exec_id":"EXEC-CANARY-001","status":"PASS","input_refs":["SRC-CANARY-001"],"output_refs":["RESULT-CANARY-001"],"artifact_refs":["ART-CANARY"]}],
      "claims":[{"claim_id":"CLAIM-CANARY-001","text":"Synthetic canary only","evidence_refs":["RESULT-CANARY-001"],"limitations":["NOT_REAL_RD"],"evidence_level":"E1"}],
      "dedup":{"status":"PASS"},
      "rights":{"shared_training_allowed":True,"train_valid_split_ready":True,"m6_exclusion_e2e":True},
      "human_review":{"complete":True},
      "open_work":[],
      "m6_contamination":False,
      "transfer":{"status":"PASS"},
      "ablation":{"status":"PASS"},
      "afah_review":{"status":"PASS"}
    }

def test_candidate_stops_before_gold_while_global_f72_fails():
    out=validate(sample())
    assert out["memory_ingest_ready"] is True
    assert out["f72_review_candidate"] is True
    assert out["m4_gold_eligible"] is False
    assert out["training_eligible"] is False
    assert "F72_GLOBAL_PASS" in out["blockers"]

def test_open_work_blocks_f72_candidate():
    s=sample(); s["open_work"]=["VERIFY_REAL_WORLD"]
    out=validate(s)
    assert out["memory_ingest_ready"] is True
    assert out["f72_review_candidate"] is False
    assert "OPEN_WORK_EMPTY" in out["blockers"]

def test_unknown_rights_block_training_candidate():
    s=sample(); s["sources"][0]["rights_status"]="UNKNOWN"; s["rights"]["shared_training_allowed"]=False
    out=validate(s)
    assert out["f72_review_candidate"] is False
    assert "SOURCE_RIGHTS_CLEAR_FOR_TRAINING" in out["blockers"]

def test_m6_contamination_blocks_memory_and_training():
    s=sample(); s["m6_contamination"]=True
    out=validate(s)
    assert out["memory_ingest_ready"] is False
    assert out["training_eligible"] is False
    assert "M6_CLEAN" in out["blockers"]
