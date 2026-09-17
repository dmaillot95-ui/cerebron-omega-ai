#!/usr/bin/env python3
import json, os, time, random, requests
from datetime import datetime, timezone

PROMPT=os.getenv('CEREBRON_PROMPT','Return one concise mathematical observation about the Collatz checkpoint. Distinguish ESTABLISHED from CONJECTURAL. Do not claim a proof.')
TIMEOUT=int(os.getenv('CEREBRON_TIMEOUT','45'))


def post(url, headers, payload):
    t=time.time()
    try:
        r=requests.post(url,headers=headers,json=payload,timeout=TIMEOUT)
        latency=round(time.time()-t,3)
        text=r.text[:12000]
        return r.status_code, text, latency
    except Exception as e:
        return 0, repr(e), round(time.time()-t,3)


def openai_compat(name,url,key,model):
    if not key: return {'provider':name,'status':'SKIPPED_NO_KEY'}
    code,text,lat=post(url,{'Authorization':f'Bearer {key}','Content-Type':'application/json'},
                       {'model':model,'messages':[{'role':'user','content':PROMPT}],'temperature':0.1,'max_tokens':500})
    out={'provider':name,'http_status':code,'latency_seconds':lat,'model':model}
    try:
        j=json.loads(text); out['response']=j['choices'][0]['message']['content']; out['success']=bool(out['response'].strip())
    except Exception:
        out['success']=False; out['error_excerpt']=text[:800]
    return out


def gemini():
    key=os.getenv('GEMINI_API_KEY')
    if not key:return {'provider':'gemini_free','status':'SKIPPED_NO_KEY'}
    model=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
    code,text,lat=post(url,{'Content-Type':'application/json'},{'contents':[{'parts':[{'text':PROMPT}]}],'generationConfig':{'temperature':0.1,'maxOutputTokens':500}})
    out={'provider':'gemini_free','http_status':code,'latency_seconds':lat,'model':model}
    try:
        j=json.loads(text); out['response']=j['candidates'][0]['content']['parts'][0]['text']; out['success']=bool(out['response'].strip())
    except Exception:
        out['success']=False; out['error_excerpt']=text[:800]
    return out


def cohere():
    key=os.getenv('COHERE_API_KEY')
    if not key:return {'provider':'cohere_trial','status':'SKIPPED_NO_KEY'}
    model=os.getenv('COHERE_MODEL','command-a-03-2025')
    code,text,lat=post('https://api.cohere.com/v2/chat',{'Authorization':f'Bearer {key}','Content-Type':'application/json'},
                       {'model':model,'messages':[{'role':'user','content':PROMPT}],'temperature':0.1,'max_tokens':500})
    out={'provider':'cohere_trial','http_status':code,'latency_seconds':lat,'model':model}
    try:
        j=json.loads(text); out['response']=j['message']['content'][0]['text']; out['success']=bool(out['response'].strip())
    except Exception:
        out['success']=False; out['error_excerpt']=text[:800]
    return out


def cloudflare():
    token=os.getenv('CLOUDFLARE_API_TOKEN'); account=os.getenv('CLOUDFLARE_ACCOUNT_ID')
    if not token or not account:return {'provider':'cloudflare_workers_ai_free','status':'SKIPPED_NO_KEY'}
    model=os.getenv('CLOUDFLARE_MODEL','@cf/google/gemma-4-26b-a4b-it')
    url=f'https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}'
    code,text,lat=post(url,{'Authorization':f'Bearer {token}','Content-Type':'application/json'},{'messages':[{'role':'user','content':PROMPT}],'max_tokens':500})
    out={'provider':'cloudflare_workers_ai_free','http_status':code,'latency_seconds':lat,'model':model}
    try:
        j=json.loads(text); resp=(j.get('result') or {}).get('response') or ''; out['response']=resp; out['success']=bool(resp.strip())
    except Exception:
        out['success']=False; out['error_excerpt']=text[:800]
    return out


def main():
    providers=[
      lambda: openai_compat('openrouter_free','https://openrouter.ai/api/v1/chat/completions',os.getenv('OPENROUTER_API_KEY'),'openrouter/free'),
      lambda: openai_compat('groq_free','https://api.groq.com/openai/v1/chat/completions',os.getenv('GROQ_API_KEY'),os.getenv('GROQ_MODEL','openai/gpt-oss-20b')),
      lambda: openai_compat('mistral_free','https://api.mistral.ai/v1/chat/completions',os.getenv('MISTRAL_API_KEY'),os.getenv('MISTRAL_MODEL','mistral-small-latest')),
      lambda: openai_compat('cerebras_free','https://api.cerebras.ai/v1/chat/completions',os.getenv('CEREBRAS_API_KEY'),os.getenv('CEREBRAS_MODEL','gpt-oss-120b')),
      gemini, cohere, cloudflare
    ]
    results=[]
    for fn in providers:
        time.sleep(random.uniform(.15,.45))
        results.append(fn())
    successes=[r for r in results if r.get('success')]
    out={'schema':'cerebron-global-provider-probe-v1','timestamp':datetime.now(timezone.utc).isoformat(),
         'success_count':len(successes),'tested_count':sum(1 for r in results if not str(r.get('status','')).startswith('SKIPPED')),
         'results':results,'rule':'A successful HTTP/model response is not a validated scientific result.'}
    os.makedirs('out',exist_ok=True)
    open('out/global-ai-provider-probe.json','w').write(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps({'success_count':out['success_count'],'tested_count':out['tested_count'],
                      'providers':[{k:r.get(k) for k in ('provider','success','status','http_status','latency_seconds')} for r in results]}))

if __name__=='__main__': main()
