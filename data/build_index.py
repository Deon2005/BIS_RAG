import json
import pickle
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

DATA_DIR = os.path.abspath(os.path.dirname(__file__))

model = SentenceTransformer("BAAI/bge-small-en")

def build():
    chunks_path = os.path.join(DATA_DIR, "processed_chunks.json")
    if not os.path.exists(chunks_path):
        print(f"{chunks_path} not found. Run chunker.py first.")
        return

    with open(chunks_path, encoding="utf-8") as f:
        chunks = json.load(f)

    if not chunks:
        print("No chunks to process.")
        return

    texts = [c["text"] for c in chunks]

    # 🔹 FAISS
    embeddings = model.encode(texts, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings))

    # 🔹 BM25
    tokenized = [t.split() for t in texts]
    bm25 = BM25Okapi(tokenized)

    # Save
    faiss.write_index(index, os.path.join(DATA_DIR, "faiss.index"))

    with open(os.path.join(DATA_DIR, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)

    print("Indexes built")


if __name__ == "__main__":
    build()