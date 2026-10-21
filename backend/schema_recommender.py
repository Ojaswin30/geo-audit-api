import json
import re
import traceback
from model import generate


def _extract_json_from_text(raw: str) -> dict:
    if not raw or not raw.strip():
        raise ValueError("Empty output received from model")

    cleaned = raw.strip()

    # 1. Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    # 2. Try direct json.loads
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
            return parsed[0]
    except Exception:
        pass

    # 3. Extract substring between first '{' and last '}'
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1].strip()
        # Clean trailing commas
        candidate = re.sub(r",\s*([\}\]])", r"\1", candidate)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                return parsed[0]
        except Exception:
            pass

    raise ValueError(f"Could not parse valid JSON from LLM output: {cleaned[:150]}...")


def detect_schema_type(scraped: dict) -> str:
    headings_raw = scraped.get("headings") or []
    headings_str = " ".join(h["text"] if isinstance(h, dict) else str(h) for h in headings_raw)
    text = " ".join([
        scraped.get("title") or "",
        scraped.get("meta_description") or "",
        headings_str
    ]).lower()

    if any(w in text for w in [
        "software engineer", "data engineer", "ai engineer", "developer", "programmer",
        "engineer", "scientist", "researcher", "consultant", "freelancer", "creator",
        "profile", "portfolio", "bio", "resume", "cv", "personal website", "github.io"
    ]):
        return "Person"
    if any(w in text for w in ["product", "buy", "price", "shop", "cart", "pricing"]):
        return "Product"
    if any(w in text for w in ["blog", "article", "author", "published", "post", "news"]):
        return "Article"
    if any(w in text for w in ["company", "about", "team", "organization", "platform", "solutions"]):
        return "Organization"

    return "Organization"


def _extract_clean_name(title: str) -> str:
    if not title:
        return "Unknown"
    # Split on bullet, em-dash, en-dash, hyphen, and pipe
    for sep in ["·", "—", "–", "|", "-"]:
        if sep in title:
            title = title.split(sep)[0]
    return title.strip() or "Unknown"


def generate_json_ld_local(url: str, scraped: dict, schema_type: str) -> dict:
    social_links = scraped.get("social_links") or [url]
    clean_name = _extract_clean_name(scraped.get("title") or "")

    prompt = f"""Generate a valid schema.org JSON-LD object of type "{schema_type}".
Page URL: {url}
Entity Name: {clean_name}
Description: {scraped.get('meta_description') or ''}
Social Profiles: {', '.join(social_links)}

Return ONLY a valid JSON object matching:
{{
  "@context": "https://schema.org",
  "@type": "{schema_type}",
  "name": "{clean_name}",
  "jobTitle": "...",
  "description": "...",
  "url": "{url}",
  "sameAs": [{', '.join(f'"{s}"' for s in social_links)}],
  "knowsAbout": [...]
}}"""

    raw = generate(prompt)
    return _extract_json_from_text(raw)


def wrap_in_schema_graph(url: str, entity_data: dict, schema_type: str, scraped: dict) -> dict:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain_root = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else url
    website_id = f"{domain_root}/#website"
    webpage_id = f"{url}/#webpage"
    entity_id = f"{url}/#{schema_type.lower()}"

    # Clean main entity
    main_entity = dict(entity_data)
    main_entity.pop("@context", None)
    main_entity["@type"] = schema_type
    main_entity["@id"] = entity_id
    if not main_entity.get("url"):
        main_entity["url"] = url

    # Deduplicate sameAs links
    if "sameAs" in main_entity and isinstance(main_entity["sameAs"], list):
        cleaned_same_as = []
        seen_norm = set()
        for item in main_entity["sameAs"]:
            norm = str(item).replace("www.", "").rstrip("/")
            if norm not in seen_norm:
                seen_norm.add(norm)
                cleaned_same_as.append(str(item))
        main_entity["sameAs"] = cleaned_same_as

    # Clean site name
    site_name = scraped.get("title") or parsed.netloc or "Website"
    for sep in ["·", "—", "–", "|", "-"]:
        if sep in site_name:
            site_name = site_name.split(sep)[-1].strip()
            break

    website_node = {
        "@type": "WebSite",
        "@id": website_id,
        "url": domain_root,
        "name": site_name
    }

    page_type = "ProfilePage" if schema_type == "Person" else ("ItemPage" if schema_type == "Product" else "WebPage")
    webpage_node = {
        "@type": page_type,
        "@id": webpage_id,
        "url": url,
        "name": scraped.get("title") or "WebPage",
        "isPartOf": {
            "@id": website_id
        },
        "mainEntity": {
            "@id": entity_id
        }
    }
    if scraped.get("meta_description"):
        webpage_node["description"] = scraped["meta_description"]

    if schema_type == "Organization":
        website_node["publisher"] = {"@id": entity_id}
    elif schema_type == "Person":
        webpage_node["about"] = {"@id": entity_id}

    return {
        "@context": "https://schema.org",
        "@graph": [
            website_node,
            webpage_node,
            main_entity
        ]
    }


def get_schema_recommendation(url: str, scraped: dict):
    schema_type = detect_schema_type(scraped)

    try:
        json_ld = generate_json_ld_local(url, scraped, schema_type)

        # Enrich schema with verified page metadata
        if schema_type == "Person":
            try:
                # 1. Enrich sameAs with discovered social profile links
                existing_same_as = json_ld.get("sameAs")
                same_as_list = []
                if isinstance(existing_same_as, list):
                    same_as_list.extend([str(x) for x in existing_same_as if x])
                elif isinstance(existing_same_as, str) and existing_same_as:
                    same_as_list.append(existing_same_as)

                for s in (scraped.get("social_links") or []):
                    if s not in same_as_list:
                        same_as_list.append(s)

                if same_as_list:
                    json_ld["sameAs"] = same_as_list

                # 2. Clean jobTitle dynamically
                if json_ld.get("jobTitle") and isinstance(json_ld["jobTitle"], str):
                    for sep in ["|", "-", "—", "–"]:
                        if sep in json_ld["jobTitle"]:
                            json_ld["jobTitle"] = json_ld["jobTitle"].split(sep)[0]
                    json_ld["jobTitle"] = json_ld["jobTitle"].strip()

                # 3. Clean knowsAbout: retain only non-URL topics extracted by LLM
                knows = json_ld.get("knowsAbout")
                if isinstance(knows, list):
                    valid_topics = [str(x).strip() for x in knows if x and not str(x).startswith("http")]
                    if valid_topics:
                        json_ld["knowsAbout"] = valid_topics
                    else:
                        json_ld.pop("knowsAbout", None)
            except Exception as enrich_err:
                print(f"Notice: Enrichment warning: {enrich_err}")

        graph_ld = wrap_in_schema_graph(url, json_ld, schema_type, scraped)
        return graph_ld, schema_type, True, None

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print("LLM generation/parsing failed:", error_msg)
        print(traceback.format_exc())

        social_links = scraped.get("social_links") or [url]
        clean_name = _extract_clean_name(scraped.get("title") or "Unknown")

        fallback_entity = {
            "@type": schema_type,
            "name": clean_name,
            "description": scraped.get("meta_description") or "",
            "url": url,
            "sameAs": social_links
        }

        if scraped.get("image_url"):
            fallback_entity["image"] = scraped["image_url"]

        graph_fallback = wrap_in_schema_graph(url, fallback_entity, schema_type, scraped)
        return graph_fallback, schema_type, False, error_msg
