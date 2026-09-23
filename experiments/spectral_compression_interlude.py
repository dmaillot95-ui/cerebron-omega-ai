import json,math,random,hashlib,pathlib
N=4096; random.seed(20260923)
# Orthogonal real Fourier basis implemented without dependencies.
def make(kind):
 if kind=="structured": return [1.2*math.sin(2*math.pi*7*n/N)+.7*math.cos(2*math.pi*31*n/N)+.25*math.sin(2*math.pi*113*n/N) for n in range(N)]
 if kind=="mixed": return [1.2*math.sin(2*math.pi*7*n/N)+.7*math.cos(2*math.pi*31*n/N)+.25*math.sin(2*math.pi*113*n/N)+.45*random.gauss(0,1) for n in range(N)]
 return [random.gauss(0,1) for _ in range(N)]
def coeffs(x):
 # Project only 256 candidate frequencies: enough to test sparse spectral structure cheaply.
 out=[]
 for k in range(1,257):
  c=2/N*sum(x[n]*math.cos(2*math.pi*k*n/N) for n in range(N)); s=2/N*sum(x[n]*math.sin(2*math.pi*k*n/N) for n in range(N)); out.append((c*c+s*s,k,c,s))
 return sorted(out,reverse=True)
def test(kind):
 x=make(kind); base=sum(v*v for v in x); cs=coeffs(x); K=41; keep=cs[:K]; y=[sum(c*math.cos(2*math.pi*k*n/N)+s*math.sin(2*math.pi*k*n/N) for _,k,c,s in keep) for n in range(N)]; err=sum((a-b)**2 for a,b in zip(x,y)); return {"kind":kind,"N":N,"kept_frequency_pairs":K,"candidate_pairs":256,"retained_energy_fraction":1-err/base,"relative_mse":err/base}
results=[test(k) for k in ("structured","mixed","random")]; out={"experiment":"spectral-sincos-compression-interlude-v1","results":results,"interpretation":"Sparse sin/cos compression is useful only when parameter vectors contain exploitable spectral structure; real-model weights must be tested before any claim.","status":"EXPERIMENT_EXECUTED"}; raw=json.dumps(out,sort_keys=True).encode();out["result_sha256"]=hashlib.sha256(raw).hexdigest();pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/spectral_compression_interlude.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out))
