import os
import json
import argparse
import pickle
import re
import fitz  # PyMuPDF
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_PATH = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_PATH, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    print(f"Reading PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    full_text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        full_text += page.get_text("text") + "\n\n"
    return full_text

def create_chunks(text, words_per_chunk=300, overlap=50):
    words = text.split()
    chunks = []
    
    # Try to find an overarching standard code if the document is primarily one standard
    # e.g., IS 456, IS 269.
    
    for i in range(0, len(words), words_per_chunk - overlap):
        chunk_words = words[i:i + words_per_chunk]
        if not chunk_words:
            break
        chunk_text = " ".join(chunk_words)
        
        # Try to find a standard code mentioned in this chunk
        pattern = r'(IS\s*\d+(?:\s*\(Part\s*\d+\))?(?::\s*\d{4})?)'
        matches = re.findall(pattern, chunk_text, re.IGNORECASE)
        
        # Default if none found
        std_code = "UNKNOWN"
        if matches:
            # Clean up the match (e.g., "IS 269 : 1989" -> "IS 269:1989")
            std_code = matches[0].strip().replace(" :", ":").replace(": ", ":")
        
        chunks.append({
            "standard_code": std_code,
            "text": chunk_text,
            "category": "Extracted from PDF",
            "confidence": 1.0 # Base confidence
        })
    print(f"Created {len(chunks)} chunks.")
    return chunks

def build_indices(chunks):
    print("Loading SentenceTransformer model (BAAI/bge-small-en)...")
    model = SentenceTransformer("BAAI/bge-small-en")
    
    print("Embedding chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    
    print("Building FAISS index...")
    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d) # Inner product since embeddings are normalized
    index.add(np.array(embeddings))
    
    faiss_path = os.path.join(DATA_PATH, "faiss.index")
    faiss.write_index(index, faiss_path)
    print(f"Saved FAISS index to {faiss_path}")
    
    print("Building BM25 index...")
    tokenized_corpus = [text.lower().split() for text in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    
    bm25_path = os.path.join(DATA_PATH, "bm25.pkl")
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25, f)
    print(f"Saved BM25 index to {bm25_path}")
    
    chunks_path = os.path.join(DATA_PATH, "processed_chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved chunks to {chunks_path}")

def main():
    parser = argparse.ArgumentParser(description="Ingest a PDF dataset for BIS RAG")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"Error: PDF file not found at {args.pdf}")
        return
        
    text = extract_text_from_pdf(args.pdf)
    chunks = create_chunks(text)
    build_indices(chunks)
    print("Ingestion complete!")

if __name__ == "__main__":
    main()
