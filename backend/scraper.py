import requests
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GEOAuditBot/1.0)"
}

def scrape_page(url: str) -> dict:
    """
    Scrape a public webpage and extract:
    - title
    - meta description
    - all h1 and h2 headings
    - first image URL found
    Returns a dict. Raises ValueError on failure.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ValueError("Request timed out. The page took too long to respond.")
    except requests.exceptions.ConnectionError:
        raise ValueError("Could not connect to the URL. Check if it's a valid public page.")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error: {e.response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string.strip() if soup.title else None

    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_tag["content"].strip() if meta_tag else None

    headings = []
    for tag in soup.find_all(["h1", "h2"]):
        text = tag.get_text(strip=True)
        if text:
            headings.append(text)

    image_url = None
    img_tag = soup.find("img", src=True)
    if img_tag:
        src = img_tag["src"]
        # handle relative URLs
        if src.startswith("http"):
            image_url = src
        else:
            from urllib.parse import urljoin
            image_url = urljoin(url, src)

    return {
        "title": title,
        "meta_description": meta_description,
        "headings": headings[:10],   # cap at 10 so response stays clean
        "image_url": image_url,
        "raw_text": soup.get_text(separator=" ", strip=True)[:3000]  # for LLM context
    }