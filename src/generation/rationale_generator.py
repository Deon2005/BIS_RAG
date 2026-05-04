import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost",
        "X-Title": "BIS_RAG_Testing"
    }
)

QUERY_EXPANSION_PROMPT = """You are a BIS domain expert in building materials.
Rewrite this product description using precise BIS-domain terminology.
Include material category names, synonyms, and structural applications.
Return only the expanded description as plain text. No bullet points, no preamble.
Product description: {query}"""

RATIONALE_GENERATION_PROMPT = """You are a BIS compliance assistant for Indian small enterprises.
STRICT RULES:
1. Only reference IS standard numbers that appear VERBATIM in the context chunks below.
2. Never invent or recall standard numbers from memory.
3. Write rationale in simple language.

Context chunks from BIS SP 21:
{chunks}

Product description: {query}

Respond in this exact JSON format only:
{{
  "standards": [
    {{
      "standard_code": "IS XXXX:YYYY",
      "title": "Standard title here",
      "rationale": "One sentence explanation here"
    }}
  ]
}}
Return only valid JSON. Nothing else."""

def _generate_with_retry(messages: list, max_tokens: int, temperature: float) -> str:
    import time
    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model="google/gemma-3-12b-it:free",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip() if response.choices else ""
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower() or "upstream" in str(e).lower():
                if attempt < 3:
                    print(f"    [WARN] OpenRouter rate limited. Retrying in {attempt * 5}s...", flush=True)
                    time.sleep(attempt * 5)
                else:
                    raise
            else:
                raise
    return ""

def expand_query(query: str) -> str:
    messages = [
        {"role": "user", "content": QUERY_EXPANSION_PROMPT.format(query=query)}
    ]
    try:
        return _generate_with_retry(messages, 200, 0.3) or query
    except Exception as e:
        print(f"    Expansion failed: {e}", flush=True)
        return query

def generate_rationale(query: str, chunks: list) -> list:
    chunk_text = ""
    for i, chunk in enumerate(chunks):
        chunk_text += f"\n--- Chunk {i+1} ---\n"
        chunk_text += f"Standard: {chunk.get('standard_code', 'Unknown')}\n"
        chunk_text += f"Content: {chunk['text']}\n"

    messages = [
        {"role": "user", "content": RATIONALE_GENERATION_PROMPT.format(
            chunks=chunk_text,
            query=query
        )}
    ]
    try:
        raw = _generate_with_retry(messages, 1000, 0.1)
    except Exception as e:
        print(f"    Generation failed after retries: {e}", flush=True)
        return []

    print(f"    Raw output: {raw[:150]}...")

    start_idx = raw.find("{")
    end_idx = raw.rfind("}") + 1
    if start_idx == -1 or end_idx == 0:
        print("    No JSON found")
        return []

    try:
        parsed = json.loads(raw[start_idx:end_idx])
        return parsed.get("standards", [])
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        return []
