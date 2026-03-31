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

    headings = [
        tag.get_text(strip=True)
        for tag in soup.find_all(["h1", "h2"])
        if tag.get_text(strip=True)
    ][:10]

    image_url = None
    img = soup.find("img", src=True)
    if img:
        image_url = urljoin(url, img["src"])

    return {
        "title": title,
        "meta_description": meta_description,
        "headings": headings,
        "image_url": image_url,
        "raw_text": soup.get_text(separator=" ", strip=True)[:3000]
    }