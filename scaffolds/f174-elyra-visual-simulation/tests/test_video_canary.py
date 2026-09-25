from pathlib import Path
from render.video_canary import generate

def test_frame_sequence_is_deterministic(tmp_path: Path):
    a=tmp_path/"a"
    b=tmp_path/"b"
    ha=generate(a,8)
    hb=generate(b,8)
    assert ha==hb
    assert len(list(a.glob("frame_*.ppm")))==8
    assert len(ha)==64

def test_different_frame_count_changes_sequence(tmp_path: Path):
    ha=generate(tmp_path/"a",8)
    hb=generate(tmp_path/"b",9)
    assert ha!=hb
