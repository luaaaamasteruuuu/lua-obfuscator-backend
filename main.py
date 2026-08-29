from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random, time, sys, os, traceback

sys.path.insert(0, os.path.dirname(__file__))
from obfuscate import obfuscate

app = FastAPI(title="LUOB", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ObfuscateIn(BaseModel):
    source: str
    seed: int | None = None
    antitamper: bool = False

class ObfuscateOut(BaseModel):
    output: str
    seed: int
    elapsed_ms: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/obfuscate", response_model=ObfuscateOut)
def obfuscate_endpoint(req: ObfuscateIn):
    if not req.source.strip():
        raise HTTPException(400, "source empty")
    seed = req.seed or random.randint(0, 2**32-1)
    t0 = time.perf_counter()
    try:
        result = obfuscate(req.source, seed=seed, antitamper=req.antitamper)
    except Exception as e:
        raise HTTPException(500, str(e))
    return ObfuscateOut(output=result, seed=seed, elapsed_ms=round((time.perf_counter()-t0)*1000, 2))