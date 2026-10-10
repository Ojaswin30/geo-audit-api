import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GEOAuditBot/1.0)"
}

def scrape_page(url: str) -> dict:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ValueError("Request timed out.")
    except requests.exceptions.ConnectionError:
        raise ValueError("Connection failed.")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error: {e.response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string.strip() if soup.title else None

    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_tag["content"].strip() if meta_tag else None

    headings = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        h_text = tag.get_text(strip=True)
        if not h_text:
            continue

        sibling_text = []
        for sibling in tag.find_next_siblings():
            if sibling.name in ["h1", "h2", "h3"]:
                break
            text = sibling.get_text(separator=" ", strip=True)
            if text:
                sibling_text.append(text)
            if len(" ".join(sibling_text)) > 300:
                break

        if not sibling_text and tag.parent and tag.parent.name in ["div", "header", "section"]:
            for parent_sib in tag.parent.find_next_siblings():
                if parent_sib.name in ["h1", "h2", "h3"] or "markdown-heading" in (parent_sib.get("class") or []):
                    break
                text = parent_sib.get_text(separator=" ", strip=True)
                if text:
                    sibling_text.append(text)
                if len(" ".join(sibling_text)) > 300:
                    break

        if not sibling_text and tag.parent:
            p_text = tag.parent.get_text(separator=" ", strip=True)
            if len(p_text) > len(h_text):
                cleaned_p = p_text.replace(h_text, "", 1).strip()
                if cleaned_p:
                    sibling_text.append(cleaned_p[:300])

        content = " ".join(sibling_text).strip()
        headings.append({
            "tag": tag.name.upper(),
            "text": h_text,
            "content": content if content else "No direct text block detected under this heading."
        })
        if len(headings) >= 15:
            break

    image_url = None
    img = soup.find("img", src=True)
    if img:
        image_url = urljoin(url, img["src"])

    valid_social_patterns = ["linkedin.com/in/", "twitter.com/", "x.com/", "youtube.com/@", "kaggle.com/"]
    social_links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if any(pat in href.lower() for pat in valid_social_patterns) and href.startswith("http"):
            cleaned = href.rstrip("/")
            if cleaned not in seen:
                seen.add(cleaned)
                social_links.append(cleaned)

    return {
        "title": title,
        "meta_description": meta_description,
        "headings": headings,
        "image_url": image_url,
        "social_links": social_links,
        "raw_text": soup.get_text(separator=" ", strip=True)[:3000]
    }