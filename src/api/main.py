"""
BIS RAG — FastAPI application entry point.
"""
from fastapi import FastAPI
from pydantic import BaseModel

from src.api.pipeline import run_pipeline

app = FastAPI(
    title="BIS RAG API",
    description="Retrieval-Augmented Generation over BIS documents.",
    version="0.1.0",
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    rationale: str
    hallucination_score: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    result = run_pipeline(request.query)
    return QueryResponse(**result)
