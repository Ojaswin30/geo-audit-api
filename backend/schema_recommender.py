import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def detect_schema_type(scraped: dict) -> str:
    """
    Rule-based schema type detection.
    Fast, deterministic, zero LLM cost.
    """
    text = " ".join([
        scraped.get("title") or "",
        scraped.get("meta_description") or "",
        " ".join(scraped.get("headings") or [])
    ]).lower()

    if any(word in text for word in ["product", "buy", "price", "shop", "cart", "order"]):
        return "Product"
    if any(word in text for word in ["blog", "article", "author", "published", "posted on"]):
        return "Article"
    if any(word in text for word in ["about us", "our team", "company", "founded", "mission"]):
        return "Organization"
    
    return "Organization"   # safe default


def generate_json_ld_with_llm(url: str, scraped: dict, schema_type: str) -> dict:
    """
    Uses LLM to generate a populated JSON-LD block.
    LLM is used here because filling field values requires
    understanding page meaning, not just pattern matching.
    """
    prompt = f"""
You are a structured data expert for SEO and GEO (Generative Engine Optimization).

Given the following webpage content, generate a valid JSON-LD block of type "{schema_type}".
Fill in as many relevant fields as you can based on the content.
Return ONLY the raw JSON object. No explanation, no markdown, no backticks.

URL: {url}
Title: {scraped.get('title')}
Meta Description: {scraped.get('meta_description')}
Headings: {', '.join(scraped.get('headings', [])[:5])}
Page Text Snippet: {scraped.get('raw_text', '')[:1500]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",     # cheap and fast, sufficient for this
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # LLM sometimes adds backticks despite instructions — strip them
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)


def get_schema_recommendation(url: str, scraped: dict) -> tuple[dict, str, bool]:
    """
    Returns (json_ld dict, schema_type string, llm_used bool)
    """
    schema_type = detect_schema_type(scraped)

    try:
        json_ld = generate_json_ld_with_llm(url, scraped, schema_type)
        return json_ld, schema_type, True
    except Exception:
        # LLM failed — fall back to a minimal hardcoded template
        fallback = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "name": scraped.get("title") or "Unknown",
            "description": scraped.get("meta_description") or "",
            "url": url
        }
        return fallback, schema_type, False