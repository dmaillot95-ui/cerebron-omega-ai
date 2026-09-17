#!/usr/bin/env python3
import json, os, time, requests, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

PROMPT=os.getenv('CEREBRON_PROMPT','Return one concise, verifiable answer. Separate established facts from uncertainty. CLAIM<=EVIDENCE.')
TIMEOUT=int(os.getenv('CEREBRON_TIMEOUT','45'))
MAX_TOKENS=int(os.getenv('CEREBRON_MAX_TOKENS','700'))


def post(url, headers, payload):
    t=time.time()
    try:
        r=requests.post(url,headers=headers,json=payload,timeout=TIMEOUT)
        return r.status_code, r.text[:20000], round(time.time()-t,3)
    except Exception as e:
        return 0, repr(e), round(time.time()-t,3)


def quality_gate(text):
    s=(text or '').strip()
    if not s: return {'pass':False,'score':0,'reasons':['empty']}
    score=0; reasons=[]
    n=len(s)
    if n>=80: score+=1
    else: reasons.append('too_short')
    if n<=12000: score+=1
    else: reasons.append('too_long')
    if not re.search(r'(?i)\b(i cannot|as an ai language model|cannot assist)\b',s): score+=1
    else: reasons.append('refusal_or_meta')
    if re.search(r'\d|because|therefore|if|however|uncertain|established|evidence|verify',s,re.I): score+=1
    else: reasons.append('low_reasoning_signal')
    return {'pass':score>=3,'score':score,'reasons':reasons}


def openai_compat(name,url,key,model):
    if not key: return {'provider':name,'status':'SKIPPED_NO_KEY','success':False}
    code,text,lat=post(url,{'Authorization':f'Bearer {key}','Content-Type':'application/json'},
                       {'model':model,'messages':[{'role':'user','content':PROMPT}],'temperature':0.1,'max_tokens':MAX_TOKENS})
    out={'provider':name,'http_status':code,'latency_seconds':lat,'model':model}
    try:
        j=json.loads(text); resp=j['choices'][0]['message']['content']; out['response']=resp; out['success']=bool(resp.strip())
    except Exception:
        out['success']=False; out['error_excerpt']=text[:1000]
    if out.get('success'): out['quality']=quality_gate(out['response'])
    return out


def gemini():
    key=os.getenv('GEMINI_API_KEY')
    if not key:return {'provider':'gemini_free','status':'SKIPPED_NO_KEY','success':False}
    model=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
    code,text,lat=post(url,{'Content-Type':'application/json'},{'contents':[{'parts':[{'text':PROMPT}]}],'generationConfig':{'temperature':0.1,'maxOutputTokens':MAX_TOKENS}})
    out={'provider':'gemini_free','http_status':code,'latency_seconds':lat,'model':model}
    try:
        j=json.loads(text); resp=j['candidates'][0]['content']['parts'][0]['text']; out['response']=resp; out['success']=bool(resp.strip())
    except Exception:
        out['success']=False; out['error_excerpt']=text[:1000]
    if out.get('success'): out['quality']=quality_gate(out['response'])
    return out


def cohere():
    key=os.getenv('COHERE_API_KEY')
    if not key:return {'provider':'cohere_trial','status':'SKIPPED_NO_KEY','success':False}
    model=os.getenv('COHERE_MODEL','command-a-03-2025')
    code,text,lat=post('https://api.cohere.com/v2/chat',{'Authorization':f'Bearer {key}','Content-Type':'application/json'},
                       {'model':model,'messages':[{'role':'user','content':PROMPT}],'temperature':0.1,'max_tokens':MAX_TOKENS})
    out={'provider':'cohere_trial','http_status':code,'latency_seconds':lat,'model':model}
    try:
        j=json.loads(text); resp=j['message']['content'][0]['text']; out['response']=resp; out['success']=bool(resp.strip())
    except Exception:
        out['success']=False; out['error_excerpt']=text[:1000]
    if out.get('success'): out['quality']=quality_gate(out['response'])
    return out


def cloudflare():
    token=os.getenv('CLOUDFLARE_API_TOKEN'); account=os.getenv('CLOUDFLARE_ACCOUNT_ID')
    if not token or not account:return {'provider':'cloudflare_workers_ai_free','status':'SKIPPED_NO_KEY','success':False}
    model=os.getenv('CLOUDFLARE_MODEL','@cf/google/gemma-4-26b-a4b-it')
    url=f'https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}'
    code,text,lat=post(url,{'Authorization':f'Bearer {token}','Content-Type':'application/json'},{'messages':[{'role':'user','content':PROMPT}],'max_tokens':MAX_TOKENS})
    out={'provider':'cloudflare_workers_ai_free','http_status':code,'latency_seconds':lat,'model':model}
    try:
        j=json.loads(text); resp=(j.get('result') or {}).get('response') or ''; out['response']=resp; out['success']=bool(resp.strip())
    except Exception:
        out['success']=False; out['error_excerpt']=text[:1000]
    if out.get('success'): out['quality']=quality_gate(out['response'])
    return out


def main():
    providers=[
      lambda: openai_compat('openrouter_free','https://openrouter.ai/api/v1/chat/completions',os.getenv('OPENROUTER_API_KEY'),os.getenv('OPENROUTER_MODEL','openrouter/free')),
      lambda: openai_compat('groq_free','https://api.groq.com/openai/v1/chat/completions',os.getenv('GROQ_API_KEY'),os.getenv('GROQ_MODEL','openai/gpt-oss-20b')),
      lambda: openai_compat('mistral_free','https://api.mistral.ai/v1/chat/completions',os.getenv('MISTRAL_API_KEY'),os.getenv('MISTRAL_MODEL','mistral-small-latest')),
      lambda: openai_compat('cerebras_free','https://api.cerebras.ai/v1/chat/completions',os.getenv('CEREBRAS_API_KEY'),os.getenv('CEREBRAS_MODEL','gpt-oss-120b')),
      gemini, cohere, cloudflare
    ]
    results=[]
    with ThreadPoolExecutor(max_workers=len(providers)) as ex:
        futs=[ex.submit(fn) for fn in providers]
        for fut in as_completed(futs):
            try: results.append(fut.result())
            except Exception as e: results.append({'provider':'unknown','success':False,'error':repr(e)})
    results.sort(key=lambda r:r.get('provider',''))
    configured=[r for r in results if r.get('status')!='SKIPPED_NO_KEY']
    successes=[r for r in results if r.get('success')]
    quality=[r for r in successes if (r.get('quality') or {}).get('pass')]
    out={
      'schema':'cerebron-global-multimodel-router-v2',
      'timestamp':datetime.now(timezone.utc).isoformat(),
      'configured_count':len(configured),
      'success_count':len(successes),
      'quality_pass_count':len(quality),
      'providers_total':len(results),
      'results':results,
      'fusion_candidates':[{'provider':r['provider'],'model':r.get('model'),'response':r.get('response')} for r in quality],
      'rules':['REALITY>COHERENCE','EVIDENCE>CONFIDENCE','CLAIM<=EVIDENCE','HTTP_SUCCESS!=VALIDATED_RESULT']
    }
    os.makedirs('out',exist_ok=True)
    with open('out/global-ai-provider-probe.json','w',encoding='utf-8') as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps({'configured_count':len(configured),'success_count':len(successes),'quality_pass_count':len(quality),
                      'providers':[{'provider':r.get('provider'),'success':r.get('success'),'status':r.get('status'),'http_status':r.get('http_status'),'quality':(r.get('quality') or {}).get('pass')} for r in results]}))

if __name__=='__main__': main()
