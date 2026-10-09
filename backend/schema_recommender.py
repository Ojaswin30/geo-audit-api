import json
import re
import traceback
from model import generate


def _extract_json_from_text(raw: str) -> dict:
    if not raw or not raw.strip():
        raise ValueError("Empty output received from model")

    cleaned = raw.strip()

    # 1. Try parsing directly
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. Try extracting from markdown code block ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Try finding outermost curly braces { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse valid JSON from text: {cleaned[:120]}...")


def detect_schema_type(scraped: dict) -> str:
    text = " ".join([
        scraped.get("title") or "",
        scraped.get("meta_description") or "",
        " ".join(scraped.get("headings") or [])
    ]).lower()

    if any(w in text for w in ["product", "buy", "price", "shop", "cart", "pricing"]):
        return "Product"
    if any(w in text for w in ["blog", "article", "author", "published", "post", "news"]):
        return "Article"
    if any(w in text for w in ["company", "about", "team", "organization", "platform", "solutions"]):
        return "Organization"

    return "Organization"


def generate_json_ld_local(url: str, scraped: dict, schema_type: str) -> dict:
    headings_sample = "\n".join(f"- {h}" for h in (scraped.get('headings') or [])[:6])
    raw_content = (scraped.get('raw_text') or '')[:1000]

    prompt = f"""Generate a valid schema.org JSON-LD object of type "{schema_type}" for this page.

Page URL: {url}
Title: {scraped.get('title') or ''}
Meta Description: {scraped.get('meta_description') or ''}
Headings:
{headings_sample}
Content Snippet:
{raw_content}

Instructions:
1. Output ONLY a valid JSON object matching Schema.org standards.
2. Must include "@context": "https://schema.org" and "@type": "{schema_type}".
3. Fill relevant properties (name, url, description, image, sameAs, etc.).
4. Do not include markdown fences, preambles, or explanations.
"""

    raw = generate(prompt)
    return _extract_json_from_text(raw)


def get_schema_recommendation(url: str, scraped: dict):
    schema_type = detect_schema_type(scraped)

    try:
        json_ld = generate_json_ld_local(url, scraped, schema_type)
        return json_ld, schema_type, True

    except Exception as e:
        print("LLM generation/parsing failed:", e)
        print(traceback.format_exc())

        fallback = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "name": scraped.get("title") or "Unknown",
            "description": scraped.get("meta_description") or "",
            "url": url
        }

        if scraped.get("image_url"):
            fallback["image"] = scraped["image_url"]

        return fallback, schema_type, False