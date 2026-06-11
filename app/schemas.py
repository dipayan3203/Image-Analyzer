from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    image: Optional[str] = Field(
        None,
        description="Base64 image data URI or local file path. If omitted use multipart file upload.",
    )
    analysis_type: str = Field("general", description="general|classification|extraction")
    metadata: Optional[Dict[str, Any]] = None


class Label(BaseModel):
    name: str
    confidence: float


class Analysis(BaseModel):
    description: str
    labels: List[Label]
    confidence: float
    data: Optional[Dict[str, Any]] = Field(None, description="Structured data extracted from the analysis.")


class AnalyzeResponse(BaseModel):
    status: str
    analysis: Optional[Analysis] = None
    errors: List[str] = []
