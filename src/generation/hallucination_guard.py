import re

def extract_is_numbers(text: str) -> set:
    pattern = r'IS\s*[\d]+(?:[\:\-]\d+)?'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return set(m.strip() for m in matches)

def guard(standards: list, retrieved_chunks: list) -> list:
    valid_codes = set()
    for chunk in retrieved_chunks:
        code = chunk.get('standard_code', '')
        if code:
            valid_codes.add(code.strip())
        valid_codes.update(extract_is_numbers(chunk.get('text', '')))

    clean = []
    for standard in standards:
        code = standard.get('standard_code', '')
        found = any(
            code.replace(' ', '').lower() in v.replace(' ', '').lower()
            or v.replace(' ', '').lower() in code.replace(' ', '').lower()
            for v in valid_codes
        )
        if found:
            clean.append(standard)

    return clean
