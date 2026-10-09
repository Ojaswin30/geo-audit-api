from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import AuditRequest, AuditResponse
from scraper import scrape_page
from schema_recommender import get_schema_recommendation

app = FastAPI(
    title="GEO Audit API",
    description="Audits a webpage and generates JSON-LD schema.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "GEO Audit API running"}

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