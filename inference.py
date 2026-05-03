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