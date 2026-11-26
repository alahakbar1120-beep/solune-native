"""Solune Cloud: bounded Groq proxy, no credentials in client or logs."""
import os, time, json, secrets, hmac, hashlib, threading, collections
from pathlib import Path
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
app=FastAPI(docs_url=None,redoc_url=None)
app.add_middleware(CORSMiddleware,allow_origins=["https://solune.local"],allow_methods=["GET","POST"],allow_headers=["Authorization","Content-Type"])
MODELS={"paper":"openai/gpt-oss-20b","marble":"qwen/qwen3.8-27b","opal":"openai/gpt-oss-120b"}
FRACTION={"free":.30,"pro":.60,"dev":1.0}
DAY_TOKENS=int(os.getenv("GROQ_DAY_TOKENS","200000"))
DAY_REQUESTS=int(os.getenv("GROQ_DAY_REQUESTS","1000"))
KEYS=[os.getenv(n,"").strip() for n in ("GROQ_API_KEY","GROQ_API_KEY_2","GROQ_API_KEY_3")]
PASSWORDS={p:os.getenv("SOLUNE_"+p.upper()+"_PASSWORD","") for p in ("pro","dev")}
SIGN=secrets.token_bytes(32)
lock=threading.RLock()
slots=threading.BoundedSemaphore(2)
ledger=collections.deque()
attempts=collections.deque()
status={i:{"configured":bool(k),"state":"not_checked" if k else "missing","models":{}} for i,k in enumerate(KEYS)}
active=next((i for i,k in enumerate(KEYS) if k),0)
def sign(plan):
    s=f"{plan}.{int(time.time())+43200}.{secrets.token_hex(8)}"
    return s+"."+hmac.new(SIGN,s.encode(),hashlib.sha256).hexdigest()
def tier(req):
    token=req.headers.get("Authorization","").removeprefix("Bearer ")
    if not token: return "free"
    try:
        p,exp,nonce,sig=token.split(".")
        base=".".join((p,exp,nonce))
        if p in FRACTION and int(exp)>time.time() and hmac.compare_digest(sig,hmac.new(SIGN,base.encode(),hashlib.sha256).hexdigest()): return p
    except (ValueError,TypeError): pass
    raise HTTPException(401,"Сессия истекла. Повторно активируйте тариф.")
def prune():
    now=time.time()
    while ledger and ledger[0]["at"]<now-86400: ledger.popleft()
def totals(model):
    rows=[r for r in ledger if r["model"]==model]
    return sum(r["tokens"] for r in rows),len(rows)
class Unlock(BaseModel):
    plan:str
    password:str=Field(max_length=200)
class Chat(BaseModel):
    model:str
    messages:list[dict]=Field(min_length=1,max_length=24)
    max_tokens:int=Field(default=256,ge=16,le=4096)
    stream:bool=True
    task:str="chat"
    depth:str="medium"
@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("index.html"),headers={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer"})
@app.get("/health")
def health(): return {"ok":True,"configured_keys":sum(bool(k) for k in KEYS)}
@app.post("/v1/unlock")
def unlock(q:Unlock):
    if q.plan=="free": return {"plan":"free","token":""}
    with lock:
        now=time.time()
        while attempts and attempts[0]<now-60: attempts.popleft()
        if len(attempts)>=12: raise HTTPException(429,"Слишком много попыток. Повторите через минуту.")
        attempts.append(now)
    expected=PASSWORDS.get(q.plan,"")
    if not expected or not hmac.compare_digest(q.password.encode(),expected.encode()): raise HTTPException(403,"Неверный пароль или тариф не настроен.")
    return {"plan":q.plan,"token":sign(q.plan)}
@app.get("/v1/usage")
def usage(req:Request):
    p=tier(req)
    with lock:
        prune()
        models={m:{"tokens_used":totals(m)[0],"requests_used":totals(m)[1],"tokens_limit":int(DAY_TOKENS*FRACTION[p]),"requests_limit":int(DAY_REQUESTS*FRACTION[p])} for m in MODELS}
        keys=[{"slot":i+1,"active":i==active,**v} for i,v in status.items()]
        # Copy under lock; no credentials ever included.
        return json.loads(json.dumps({"plan":p,"models":models,"keys":keys,"window":"rolling_24h","note":"Локальный учёт сервера с момента запуска. Заголовки Groq: запросы в сутки, токены в минуту. Квоты организаций не суммируются."}))
def rate_headers(r,slot,model):
    fields=("limit-requests","remaining-requests","reset-requests","limit-tokens","remaining-tokens","reset-tokens")
    with lock:
        status[slot]["state"]="rate_limited" if r.status_code==429 else "ok" if r.ok else "error"
        status[slot]["models"][model]={"observed_at":int(time.time()),**{x:r.headers.get("x-ratelimit-"+x) for x in fields},"retry_after":r.headers.get("retry-after")}
@app.post("/v1/chat/completions")
def chat(q:Chat, req:Request):
    global active
    plan=tier(req)
    if q.model not in MODELS or q.task not in ("chat","code","image","deep"): raise HTTPException(400,"Неизвестная модель или режим.")
    if plan=="free" and (q.model=="opal" or q.task in ("code","deep")): raise HTTPException(403,"Нужен Pro или Dev.")
    msgs=[]
    for m in q.messages:
        if m.get("role") not in ("system","user","assistant") or not isinstance(m.get("content"),str): raise HTTPException(400,"Некорректное сообщение.")
        msgs.append({"role":m["role"],"content":m["content"]})
    if sum(len(m["content"]) for m in msgs)>24000: raise HTTPException(413,"Контекст слишком длинный.")
    max_tokens=min(q.max_tokens,4096 if plan!="free" else 1536)
    # Conservative reservation, reconciled with actual provider usage.
    reserved=sum(len(m["content"].encode("utf-8"))+24 for m in msgs)+max_tokens+128
    if not slots.acquire(blocking=False): raise HTTPException(429,"Сервер занят, повторите позже.")
    entry=None
    upstream=None
    try:
        with lock:
            prune()
            used,count=totals(q.model)
            if used+reserved>DAY_TOKENS*FRACTION[plan] or count>=DAY_REQUESTS*FRACTION[plan]: raise HTTPException(429,"Дневной лимит тарифа исчерпан.")
            entry={"at":time.time(),"model":q.model,"tokens":reserved}
            ledger.append(entry)
            order=[active]+[i for i in range(len(KEYS)) if i!=active]
        payload={"model":MODELS[q.model],"messages":msgs,"max_completion_tokens":max_tokens,"stream":True}
        payload["reasoning_effort"]="low" if q.model=="paper" or q.depth=="low" else "high" if q.depth=="high" else "medium"
        for i in order:
            if not KEYS[i]: continue
            try:
                upstream=requests.post("https://api.groq.com/openai/v1/chat/completions",headers={"Authorization":"Bearer "+KEYS[i]},json=payload,stream=True,timeout=(10,90))
            except requests.RequestException:
                raise HTTPException(502,"Не удалось связаться с Groq.")
            if upstream.status_code==401:
                with lock: status[i]["state"]="invalid_key"
                upstream.close();upstream=None
                continue
            rate_headers(upstream,i,q.model)
            with lock: active=i
            break
        if upstream is None: raise HTTPException(503,"Нет рабочего ключа Groq. Проверьте секреты.")
        if upstream.status_code==429:
            retry=upstream.headers.get("retry-after","")
            raise HTTPException(429,"Лимит Groq исчерпан. Повторите позже.",headers={"Retry-After":retry} if retry else None)
        if not upstream.ok: raise HTTPException(502,f"Groq отклонил запрос (HTTP {upstream.status_code}).")
    except BaseException:
        if upstream is not None: upstream.close()
        with lock:
            if entry in ledger: ledger.remove(entry)
        slots.release()
        raise
    def output():
        actual=None
        try:
            for raw in upstream.iter_lines(chunk_size=64):
                if not raw.startswith(b"data:"): continue
                raw=raw[5:].strip()
                if raw==b"[DONE]": break
                try: item=json.loads(raw)
                except ValueError: continue
                u=item.get("usage") or (item.get("x_groq") or {}).get("usage")
                if u and isinstance(u.get("total_tokens"),int): actual=u["total_tokens"]
                choices=item.get("choices") or []
                if choices:
                    delta=choices[0].get("delta") or {}
                    text=delta.get("content")
                    if text: yield "data: "+json.dumps({"choices":[{"delta":{"content":text}}]},ensure_ascii=False)+"\n\n"
                    if choices[0].get("finish_reason")=="length":
                        yield "data: "+json.dumps({"truncated":True})+"\n\n"
            yield "data: [DONE]\n\n"
        except requests.RequestException:
            yield "data: "+json.dumps({"error":"Соединение с Groq прервано."},ensure_ascii=False)+"\n\n"
        finally:
            upstream.close()
            with lock:
                if actual is not None: entry["tokens"]=actual
            slots.release()
    return StreamingResponse(output(),media_type="text/event-stream",headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
