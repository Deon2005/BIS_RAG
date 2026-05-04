import json
import pickle
import faiss
import numpy as np
import os
import sys
from sentence_transformers import SentenceTransformer

# 🔹 Get absolute project root path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_PATH = os.path.join(BASE_DIR, "data")

model = None
index = None
chunks = []
bm25 = None
is_initialized = False
init_failed = False

def init_retriever():
    global model, index, chunks, bm25, is_initialized, init_failed
    if is_initialized or init_failed:
        return is_initialized

    try:
        model = SentenceTransformer("BAAI/bge-small-en")
        
        index_path = os.path.join(DATA_PATH, "faiss.index")
        if not os.path.exists(index_path):
            init_failed = True
            return False
        index = faiss.read_index(index_path)

        chunks_path = os.path.join(DATA_PATH, "processed_chunks.json")
        if not os.path.exists(chunks_path):
            init_failed = True
            return False
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        bm25_path = os.path.join(DATA_PATH, "bm25.pkl")
        if not os.path.exists(bm25_path):
            init_failed = True
            return False
        with open(bm25_path, "rb") as f:
            bm25 = pickle.load(f)
            
        is_initialized = True
        return True
    except Exception as e:
        print(f"Retriever initialization error: {e}", file=sys.stderr)
        init_failed = True
        return False

# Initialize eagerly but safely
init_retriever()


# 🔹 Vector search
def vector_search(query, k=10):
    if index is None or index.ntotal == 0:
        return []
    emb = model.encode([query], normalize_embeddings=True)
    k = min(k, index.ntotal)
    if k == 0:
        return []
    _, indices = index.search(np.array(emb), k)
    return indices[0].tolist()


# 🔹 BM25 search
def bm25_search(query, k=10):
    if bm25 is None or bm25.corpus_size == 0:
        return []
    scores = bm25.get_scores(query.split())
    k = min(k, len(scores))
    if k == 0:
        return []
    return np.argsort(scores)[::-1][:k].tolist()


# 🔹 RRF Fusion
def rrf(results_list, k=60):
    scores = {}
    for results in results_list:
        for rank, idx in enumerate(results):
            if idx == -1:
                continue
            scores[idx] = scores.get(idx, 0) + 1 / (rank + k)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# 🔹 FINAL FUNCTION (used by inference.py)
def retrieve(query, top_k=5):
    try:
        if not is_initialized and not init_retriever():
            return ["UNKNOWN"]

        vec = vector_search(query, k=20)
        bm = bm25_search(query, k=20)

        fused = rrf([vec, bm])

        standard_scores = {}
        for idx, score in fused:
            if 0 <= idx < len(chunks):
                std = chunks[idx].get("standard_id", "UNKNOWN")
                standard_scores[std] = standard_scores.get(std, 0) + score

        ranked = sorted(standard_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for std, _ in ranked:
            if std not in results:
                results.append(std)
            if len(results) == top_k:
                break

        if len(results) == 0:
            return ["UNKNOWN"]

        return results

    except Exception as e:
        print(f"Retriever error: {e}", file=sys.stderr)
        return ["UNKNOWN"]