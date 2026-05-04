"""
BIS RAG — FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.pipeline import run_pipeline

app = FastAPI(
    title="BIS RAG API",
    description="Retrieval-Augmented Generation over BIS documents.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root() -> dict:
    return {"status": "ok"}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/recommend")
def recommend(request: QueryRequest) -> dict:
    result = run_pipeline(request.query)
    
    frontend_results = []
    for s in result.get("standards_detail", []):
        frontend_results.append({
            "id": s.get("standard_code", ""),
            "title": s.get("title", ""),
            "rationale": s.get("rationale", ""),
            "category": s.get("category", ""),
            "snippet": s.get("snippet", ""),
            "score": s.get("score", 0.0)
        })
        
    return {"results": frontend_results}
