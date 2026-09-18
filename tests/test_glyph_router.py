from tools.glyph_router import encode,verify,route,decode

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
