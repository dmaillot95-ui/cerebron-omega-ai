import json
from simulation.visual_canary import simulate

def test_visual_canary_is_deterministic():
    a=simulate("TEST",6)
    b=simulate("TEST",6)
    assert a==b
    assert len(a["frames"])==6
    assert a["physical_model_claimed"] is False
    assert a["physical_validation_claimed"] is False
    assert len(a["result_sha256"])==64

def test_visual_canary_changes_with_steps():
    a=simulate("TEST",6)
    b=simulate("TEST",7)
    assert a["result_sha256"]!=b["result_sha256"]
