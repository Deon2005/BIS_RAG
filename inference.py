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
                "retrieved_standards": result["retrieved_standards"],
                "latency_seconds": result["latency_seconds"],
            })
        except Exception as e:
            print(f"  ERROR on {query_id}: {e}", flush=True)
            results.append({
                "id": query_id,
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