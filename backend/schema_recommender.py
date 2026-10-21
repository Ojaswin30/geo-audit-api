import json
import re
import traceback
from model import generate


def _extract_json_from_text(raw: str) -> dict:
    if not raw or not raw.strip():
        raise ValueError("Empty output received from model")

    cleaned = raw.strip()

    def _unwrap(obj):
        if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
            return obj[0]
        if isinstance(obj, dict):
            return obj
        return None

    # 1. Try parsing directly
    try:
        res = _unwrap(json.loads(cleaned))
        if res:
            return res
    except json.JSONDecodeError:
        pass

    # 2. Try extracting from markdown code block ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\[\{][\s\S]*?[\]\}])\s*```", cleaned, re.IGNORECASE)
    if match:
        try:
            res = _unwrap(json.loads(match.group(1).strip()))
            if res:
                return res
        except json.JSONDecodeError:
            pass

    # 3. Try finding outermost brackets or braces { ... } or [ ... ]
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        first_idx = cleaned.find(start_char)
        last_idx = cleaned.rfind(end_char)
        if first_idx != -1 and last_idx != -1 and last_idx > first_idx:
            candidate = cleaned[first_idx:last_idx + 1].strip()
            try:
                res = _unwrap(json.loads(candidate))
                if res:
                    return res
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not parse valid JSON from text: {cleaned[:120]}...")


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
                cleaned_same_as.append(item)
        main_entity["sameAs"] = cleaned_same_as

    # Clean site name
    site_name = scraped.get("title") or parsed.netloc or "Website"
    if "·" in site_name:
        site_name = site_name.split("·")[-1].strip()
    elif "|" in site_name:
        site_name = site_name.split("|")[-1].strip()

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
            # 1. Enrich sameAs with discovered social profile links
            existing_same_as = json_ld.get("sameAs")
            same_as_list = []
            if isinstance(existing_same_as, list):
                same_as_list.extend(existing_same_as)
            elif isinstance(existing_same_as, str) and existing_same_as:
                same_as_list.append(existing_same_as)

            for s in (scraped.get("social_links") or []):
                if s not in same_as_list:
                    same_as_list.append(s)

            if same_as_list:
                json_ld["sameAs"] = same_as_list

            # 2. Clean jobTitle dynamically (remove trailing pipe/dash if present)
            if json_ld.get("jobTitle"):
                json_ld["jobTitle"] = str(json_ld["jobTitle"]).split("|")[0].split("-")[0].strip()

            # 3. Clean knowsAbout: retain only non-URL topics extracted by LLM
            knows = json_ld.get("knowsAbout")
            if isinstance(knows, list):
                valid_topics = [str(x).strip() for x in knows if x and not str(x).startswith("http")]
                if valid_topics:
                    json_ld["knowsAbout"] = valid_topics
                else:
                    json_ld.pop("knowsAbout", None)

        graph_ld = wrap_in_schema_graph(url, json_ld, schema_type, scraped)
        return graph_ld, schema_type, True

    except Exception as e:
        print("LLM generation/parsing failed:", e)
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
        return graph_fallback, schema_type, False
