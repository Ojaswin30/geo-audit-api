from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Union, Dict, Any

class AuditRequest(BaseModel):
    url: HttpUrl

class HeadingItem(BaseModel):
    tag: str
    text: str
    content: Optional[str] = None

class AuditResponse(BaseModel):
    url: str
    title: Optional[str]
    meta_description: Optional[str]
    headings: List[Union[str, HeadingItem, Dict[str, Any]]]
    image_url: Optional[str]
    schema_type: str
    json_ld: dict
    llm_used: bool
    error: Optional[str] = None