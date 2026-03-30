from fastapi import FastAPI, HTTPException
from models import AuditRequest, AuditResponse
from scraper import scrape_page
from schema_recommender import get_schema_recommendation

app = FastAPI(
    title="GEO Audit API",
    description="Audits a webpage for AI search visibility and recommends structured JSON-LD schema.",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "GEO Audit API is running. Use POST /audit to analyze a page."}

@app.post("/audit", response_model=AuditResponse)
def audit_page(request: AuditRequest):
    url = str(request.url)

    try:
        scraped = scrape_page(url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    json_ld, schema_type, llm_used = get_schema_recommendation(url, scraped)

    return AuditResponse(
        url=url,
        title=scraped["title"],
        meta_description=scraped["meta_description"],
        headings=scraped["headings"],
        image_url=scraped["image_url"],
        schema_type=schema_type,
        json_ld=json_ld,
        llm_used=llm_used
    )