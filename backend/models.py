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
    schema_type: str
    json_ld: dict
    llm_used: bool
    error: Optional[str] = None