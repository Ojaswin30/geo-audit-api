import json
import traceback
from model import generate


def _extract_json_from_text(raw: str) -> dict:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)


def detect_schema_type(scraped: dict) -> str:
    text = " ".join([
        scraped.get("title") or "",
        scraped.get("meta_description") or "",
        " ".join(scraped.get("headings") or [])
    ]).lower()

    if any(w in text for w in ["product", "buy", "price", "shop"]):
        return "Product"
    if any(w in text for w in ["blog", "article", "author"]):
        return "Article"
    if any(w in text for w in ["company", "about", "team"]):
        return "Organization"

    return "Organization"


def generate_json_ld_local(url, scraped, schema_type):
    prompt = f"""
Generate a valid JSON-LD object of type "{schema_type}".
Return ONLY JSON.

URL: {url}

Title: {scraped.get('title')}
Meta Description: {scraped.get('meta_description')}

Headings:
{chr(10).join(scraped.get('headings', [])[:5])}

Content:
{scraped.get('raw_text', '')[:1200]}
"""

    raw = generate(prompt)
    return _extract_json_from_text(raw)


def get_schema_recommendation(url: str, scraped: dict):
    schema_type = detect_schema_type(scraped)

    try:
        json_ld = generate_json_ld_local(url, scraped, schema_type)
        return json_ld, schema_type, True

    except Exception as e:
        print("LLM FAILED:", e)
        print(traceback.format_exc())

        fallback = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "name": scraped.get("title") or "Unknown",
            "description": scraped.get("meta_description") or "",
            "url": url
        }

        return fallback, schema_type, False