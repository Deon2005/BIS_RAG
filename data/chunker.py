import re
import json
import os

DATA_DIR = os.path.abspath(os.path.dirname(__file__))

def chunk_text(text):
    chunks = []

    # Improved split by standard ID, supporting dash and year (e.g., IS 456 or IS 456:2000)
    parts = re.split(r"(IS\s\d+(?:-[A-Za-z0-9]+)?(?::\d{4})?)", text)

    current_category = "Unknown"

    for i in range(1, len(parts), 2):
        std_id = parts[i].strip()
        if i + 1 < len(parts):
            content = parts[i + 1]
        else:
            content = ""

        # Try to extract title (first line)
        lines = content.strip().split("\n")
        title = lines[0] if lines else ""

        paragraphs = content.split("\n\n")

        for j, para in enumerate(paragraphs):
            para = para.strip()

            if len(para) < 50:
                continue

            chunks.append({
                "id": f"{std_id}_chunk_{j}",
                "text": para,
                "standard_id": std_id,
                "title": title,
                "category": current_category
            })

    return chunks


if __name__ == "__main__":
    raw_path = os.path.join(DATA_DIR, "raw.txt")
    
    if os.path.exists(raw_path):
        with open(raw_path, encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)

        out_path = os.path.join(DATA_DIR, "processed_chunks.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)

        print("Chunks:", len(chunks))
    else:
        print("raw.txt not found. Run ingest.py first.")