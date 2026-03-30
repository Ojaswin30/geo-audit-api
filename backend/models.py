from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class AuditRequest(BaseModel):
    url: HttpUrl

class AuditResponse(BaseModel):
    url: str
    title: Optional[str]
    meta_description: Optional[str]
    headings: List[str]
    image_url: Optional[str]
    schema_type: str             # e.g. "Article", "Product", "Organization"
    json_ld: dict                # the actual recommended JSON-LD block
    llm_used: bool               # transparency flag
    error: Optional[str] = None