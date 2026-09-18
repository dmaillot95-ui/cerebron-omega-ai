import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"tools"/"glyph_router.py"
S=importlib.util.spec_from_file_location("glyph_router",P)
M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
encode,verify,route,decode=M.encode,M.verify,M.route,M.decode

def test_roundtrip_collatz():
    x=encode("collatz","cycle closure","symbolic","E2","VERIFY","high","reason",{"finite":True})
    assert verify(x)==(True,"VERIFIED")
    assert route(x)["farm"]=="cerebron-collatz-theory-farm"
    assert "cycle closure" in decode(x)

def test_tamper_rejected():
    x=encode("thermal","balance","fourier","E2","VERIFY","normal","calculate")
    x["vector"]["objective"]="tampered"
    assert verify(x)[0] is False
    assert route(x)["status"]=="REJECTED"
