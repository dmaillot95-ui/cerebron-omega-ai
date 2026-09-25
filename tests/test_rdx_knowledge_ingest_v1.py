import json
from runtime.rdx_knowledge_ingest_v1 import validate_record

def base_record():
    return {
        "schema":"RDX_ATOMIC_RECORD_V1",
        "rdx_id":"RDX-CANARY-001",
        "object_id":"CLAIM-001",
        "object_type":"CLAIM",
        "content":"Synthetic canary claim used only to test routing.",
        "provenance":{
            "source_ids":["SRC-CANARY-001"],
            "origin":"CEREBRON_OWNED_SYNTHETIC",
            "producer":"F152"
        },
        "rights":{"class":"OWNED","shared_training_allowed":True},
        "validated":True,
        "dedup_pass":True,
        "license_origin_pass":True,
        "m6_contamination":False,
        "afah_pass":True
    }

def test_owned_rdx_is_memory_but_not_gold_while_f72_fails():
    out=validate_record(base_record())
    assert out["memory"]["admissible"] is True
    assert out["memory"]["shared"] is True
    assert out["memory"]["rag_available"] is True
    assert out["gold"]["eligible"] is False
    assert out["training"]["eligible"] is False
    assert "F72" in out["gold"]["blockers"]
    assert out["training"]["weights_changed"] is False

def test_m6_contamination_fails_closed():
    r=base_record(); r["m6_contamination"]=True
    out=validate_record(r)
    assert out["memory"]["admissible"] is False
    assert out["training"]["eligible"] is False
    assert "M6_CLEAN" in out["gold"]["blockers"]

def test_client_private_is_tenant_only_and_not_shared_train_by_default():
    r=base_record()
    r["rights"]={"class":"CLIENT_PRIVATE","tenant_id":"TENANT-CANARY","shared_training_allowed":False}
    out=validate_record(r)
    assert out["memory"]["admissible"] is True
    assert out["memory"]["shared"] is False
    assert out["memory"]["tenant_only"] is True
    assert out["training"]["eligible"] is False
    assert "RIGHTS_TRAINING" in out["gold"]["blockers"]
