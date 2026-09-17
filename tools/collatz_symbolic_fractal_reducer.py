#!/usr/bin/env python3
import argparse,json,math,hashlib
from pathlib import Path

CACHE=Path('cache/collatz-symbolic-cache.json')

def load_cache():
    if CACHE.exists():
        try:return json.loads(CACHE.read_text())
        except:pass
    return {}

def save_cache(c):
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    CACHE.write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')

def key(u,r,h,m2,m3):
    return f'u={u}|r={r}|h={h}|m2={m2}|m3={m3}'

def reduce_case(u,r,h,m2=16,m3=27,cache=None):
    cache=cache if cache is not None else {}
    k=key(u,r,h,m2,m3)
    if k in cache:
        out=dict(cache[k]); out['cache_hit']=True; return out
    # symbolic stage: keep powers factorized and use modular/log filters before exact products
    mult_saved=0; exact_mult=0; filtered=[]
    # parity/mod-6 filter
    if h%2==0 or h%3!=2:
        filtered.append('h_not_5_mod_6'); mult_saved+=4
    # 3-adic compatibility h == -4^-r mod 3^u, guarded for tractable u
    mod3u=3**u
    inv4r=pow(pow(4,r,mod3u),-1,mod3u)
    if h%mod3u != (-inv4r)%mod3u:
        filtered.append('3_adic_incompatible'); mult_saved+=4
    # logarithmic gap sign; avoids building 4^r and 3^(u+r)
    eta=(u+r)*math.log(3.0)-(u+2*r)*math.log(2.0)
    log_class='lhs3_dominant' if eta>0 else 'lhs2_dominant_or_equal'
    mult_saved+=2
    # modular H-factorization checks
    lhs_mod2=(pow(3,u,m2)*(h%m2)-1)%m2
    if lhs_mod2!=0 and m2>=4:
        filtered.append('h_factor_mod2_fail'); mult_saved+=2
    # exact arithmetic only for survivors
    exact=None
    if not filtered:
        a=(1<<(u+2*r))*h
        b=(3**(u+r))*h
        exact={'pow2_term':a,'pow3_term':b,'difference':a-b}
        exact_mult+=2
    out={'u':u,'r':r,'h':h,'filtered':filtered,'survives':not filtered,'log_class':log_class,
         'multiplications_saved_estimate':mult_saved,'exact_multiplications':exact_mult,'exact':exact,
         'cache_hit':False}
    cache[k]=out
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--max-u',type=int,default=8); ap.add_argument('--max-r',type=int,default=12); ap.add_argument('--h-max',type=int,default=199)
    a=ap.parse_args(); c=load_cache(); rows=[]
    for u in range(1,a.max_u+1):
      for r in range(1,a.max_r+1):
        for h in range(5,a.h_max+1,6):
          rows.append(reduce_case(u,r,h,cache=c))
    save_cache(c)
    total=len(rows); survivors=sum(x['survives'] for x in rows); saved=sum(x['multiplications_saved_estimate'] for x in rows); exact=sum(x['exact_multiplications'] for x in rows); hits=sum(x['cache_hit'] for x in rows)
    summary={'cases':total,'filtered_before_exact':total-survivors,'survivors':survivors,'filter_rate':round((total-survivors)/total,6) if total else 0,
             'multiplications_saved_estimate':saved,'exact_multiplications_executed':exact,'cache_hits':hits,'cache_size':len(c),
             'claim_note':'Saved-multiplication count is an operation-accounting estimate for this reducer, not a proof-speedup claim.'}
    Path('out').mkdir(exist_ok=True); Path('out/symbolic-reducer-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
if __name__=='__main__': main()
