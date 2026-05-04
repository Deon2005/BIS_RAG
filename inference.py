import argparse, json, sys, os, time
sys.path.append(os.path.dirname(__file__))

from src.api.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    args = parser.parse_args()

    # ── Guard: input file must exist ──────────────────────────────────────────
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}", flush=True)
        sys.exit(1)

    # ── Guard: output directory must exist ────────────────────────────────────
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.exists(out_dir):
        print(f"ERROR: Output directory does not exist: {out_dir}", flush=True)
        sys.exit(1)

    print(f"Loading queries from {args.input} ...", flush=True)
    with open(args.input, "r", encoding="utf-8") as f:
        queries = json.load(f)

    print(f"Found {len(queries)} queries. Running pipeline...\n", flush=True)

    results = []
    for item in queries:
        query_id = item["id"]
        query_text = item["query"]

        print(f"  [{query_id}] {query_text[:70]}...", flush=True)
        time.sleep(1)
        try:
            result = run_pipeline(query_text)
            results.append({
                "id": query_id,
                "expected_standards": item.get("expected_standards", []),
                "retrieved_standards": result["retrieved_standards"],
                "latency_seconds": result["latency_seconds"],
            })
        except Exception as e:
            print(f"  ERROR on {query_id}: {e}", flush=True)
            results.append({
                "id": query_id,
                "expected_standards": item.get("expected_standards", []),
                "retrieved_standards": [],
                "latency_seconds": 0.0,
            })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(results)} results written to {args.output}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFATAL ERROR: {exc}", flush=True)
        raise
import json
import argparse
import time
import sys
import os

# 🔹 Fix import path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.backend.retriever import retrieve


def main(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    # Load input queries
    with open(input_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Input file is not valid JSON.")
            return

    results = []

    for item in data:
        query_id = item.get("id", "unknown")
        query = item.get("query", "")

        start_time = time.time()

        try:
            # 🔹 Call your retriever
            retrieved = retrieve(query, top_k=5)

            # Ensure it's a list of strings
            if not isinstance(retrieved, list):
                retrieved = ["UNKNOWN"]
            elif len(retrieved) == 0:
                retrieved = ["UNKNOWN"]

            # Filter duplicates and valid strings
            clean_retrieved = []
            for r in retrieved:
                if isinstance(r, str) and r not in clean_retrieved:
                    clean_retrieved.append(r)
            
            if not clean_retrieved:
                clean_retrieved = ["UNKNOWN"]

        except Exception as e:
            print(f"Error processing query {query_id}: {e}")
            clean_retrieved = ["UNKNOWN"]

        latency = time.time() - start_time

        results.append({
            "id": query_id,
            "retrieved_standards": clean_retrieved[:5],  # max 5
            "latency_seconds": round(latency, 4)
        })

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Save output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output JSON")

    args = parser.parse_args()

    main(args.input, args.output)
