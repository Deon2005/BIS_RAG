import time, sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from src.generation.rationale_generator import expand_query, generate_rationale
from src.generation.hallucination_guard import guard

def mock_retrieve(query):
    return [
        {"standard_code": "IS 269:1989", "text": "IS 269:1989 specifies requirements for 33 Grade Ordinary Portland Cement including chemical composition, physical requirements, and manufacturing standards for use in general construction.", "category": "Cement & Lime", "confidence": 0.91},
        {"standard_code": "IS 8112:1989", "text": "IS 8112:1989 covers 43 Grade Ordinary Portland Cement used in construction where higher strength is required. Specifies chemical and physical requirements.", "category": "Cement & Lime", "confidence": 0.84},
        {"standard_code": "IS 456:2000", "text": "IS 456:2000 is the code of practice for plain and reinforced concrete covering materials, workmanship, and structural design requirements.", "category": "Cement & Concrete", "confidence": 0.76},
        {"standard_code": "IS 383:1970", "text": "IS 383:1970 specifies requirements for coarse and fine aggregates from natural sources for concrete including grading, physical and chemical properties.", "category": "Aggregates", "confidence": 0.71},
        {"standard_code": "IS 1786:2008", "text": "IS 1786:2008 covers high strength deformed steel bars and wires for concrete reinforcement including tensile strength, elongation, and bend test requirements.", "category": "Steel", "confidence": 0.68},
    ]

def run_pipeline(query, retriever=None, expand=False):
    start = time.time()

    if expand:
        try:
            expanded = expand_query(query)
            print(f"    Expanded: {expanded[:80]}...")
        except Exception as e:
            print(f"    Expansion failed ({e}), using raw query")
            expanded = query
    else:
        expanded = query

    chunks = (retriever or mock_retrieve)(expanded)
    print(f"    Retrieved {len(chunks)} chunks")

    generation_ok = False
    try:
        standards = generate_rationale(expanded, chunks)
        print(f"    Generated {len(standards)} standards", flush=True)
        generation_ok = True
    except Exception as e:
        print(f"    Generation failed after all retries: {e}", flush=True)
        standards = []

    if generation_ok:
        try:
            standards = guard(standards, chunks)
            print(f"    After guard: {len(standards)} standards", flush=True)
        except Exception as e:
            print(f"    Guard failed: {e}", flush=True)

    # Merge chunk details (category, text, confidence) into the standards
    for s in standards:
        match = next((c for c in chunks if c.get("standard_code") == s.get("standard_code")), None)
        if match:
            s["category"] = match.get("category", "")
            s["snippet"] = match.get("text", "")
            s["score"] = match.get("confidence", 0.0)

    latency = round(time.time() - start, 3)

    return {
        "query": query,
        "retrieved_standards": [s["standard_code"] for s in standards],
        "standards_detail": standards,
        "latency_seconds": latency
    }
