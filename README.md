#  BIS Standards Recommendation Engine

AI-powered Retrieval-Augmented Generation (RAG) system that converts product descriptions into accurate **Bureau of Indian Standards (BIS)** recommendations in seconds.

---

##  Problem Statement

Micro and Small Enterprises (MSEs) often spend **days or weeks** identifying applicable BIS standards for their products. This slows compliance and increases operational overhead.

---

##  Solution

We built an **AI-based Recommendation Engine** that:

* Accepts a **product description**
* Retrieves relevant BIS standards using **hybrid search (FAISS + BM25)**
* Uses an LLM to generate **grounded rationale**
* Returns **top 3–5 standards with explanation and evidence**

---

##  System Architecture

```
User Input (Product Description)
        ↓
Retriever Layer
   ├── Dense Search (FAISS + BGE embeddings)
   ├── Sparse Search (BM25)
   └── RRF Re-ranking
        ↓
Top-K Relevant Chunks
        ↓
LLM (Gemini Flash)
        ↓
Final Output (Standards + Rationale)
        ↓
Frontend UI (React + Tailwind)
```

---

##  Key Features

*  **Hybrid Retrieval**: Combines semantic + keyword search
*  **Fast Response**: Optimized for <5s latency
*  **Grounded LLM Output**: No hallucinated standards
*  **Confidence Scoring**: Visual match percentage
*  **Clause Highlighting**: Shows exact matched text
*  **Explainable AI**: Rationale derived from retrieved context

---

##  Project Structure

```
.
├── src/
│   ├── backend/
│   │   ├── retriever.py
│   │   ├── main.py
│   │   └── utils/
│   ├── frontend/
│   │   └── (React app)
│
├── data/
│   ├── processed_chunks.json
│   ├── faiss_index/
│   └── results.json
│
├── inference.py
├── eval_script.py
├── requirements.txt
├── presentation.pdf
└── README.md
```

---

##  Installation & Setup

### 1. Clone the Repository

```bash
git clone <https://github.com/Deon2005/BIS_RAG>
cd <BIS_RAG>
```

---

### 2. Backend Setup

```bash
pip install -r requirements.txt
```

Run server:

```bash
python main.py
```

Server will run on:

```
http://localhost:8000
```

---

### 3. Frontend Setup

```bash
cd src/frontend
npm install
npm run dev
```

Open:

```
http://localhost:5173
```

---

##  API Endpoint

### POST `/recommend`

**Request:**

```json
{
  "query": "High strength Portland cement for construction"
}
```

**Response:**

```json
{
  "results": [
    {
      "id": "IS 1234",
      "title": "Portland Cement Specification",
      "score": 0.85,
      "rationale": "Suitable for structural applications...",
      "snippet": "Portland cement shall conform to..."
    }
  ]
}
```

---

##  Evaluation

We use the provided `eval_script.py` to measure:

*  Hit Rate @3 (>80%)
*  MRR @5 (>0.7)
*  Latency (<5 seconds)

Run:

```bash
python inference.py --input test.json --output output.json
python eval_script.py
```

---

##  Anti-Hallucination Strategy

* Only retrieved standards are passed to LLM
* Output IDs are validated against retrieved context
* No external or fabricated standards allowed

---

##  Technologies Used

* Python, FastAPI
* FAISS (vector search)
* Sentence Transformers (BGE embeddings)
* BM25 (rank-bm25)
* Gemini Flash (LLM)
* React + Tailwind CSS

---

##  Impact

*  Reduces compliance discovery time from weeks → seconds
*  Helps MSEs adopt standards faster
*  Improves regulatory alignment and product quality

---

##  Submission Notes

* Fully runnable on standard hardware
* All dependencies listed in `requirements.txt`
* `inference.py` follows required evaluation format

---

##  License

This project is for hackathon purposes.
