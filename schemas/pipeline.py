from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PipelineState(BaseModel):
    """State object tracked by LangGraph as a listing moves through the pipeline."""

    # Input
    url: str = ""
    source: str = "unknown"
    status: str = "queued"

    # After CRAWL (Crawl4AI)
    raw_html_key: str = ""          # MinIO object key (Bronze)
    markdown: str = ""               # LLM-friendly markdown from Crawl4AI

    # After EXTRACT (Qwen3 8B via LiteLLM)
    title: Optional[str] = None
    property_type: Optional[str] = None
    transaction_type: Optional[str] = None
    price: Optional[float] = None
    currency: str = "TND"
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_m2: Optional[float] = None
    floor: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    delegation: Optional[str] = None
    governorate: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    extraction_confidence: float = 0.0

    # After GEOCODE
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    codegeo_h3: Optional[str] = None

    # After DEDUP
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    similarity_score: float = 0.0

    # After FRAUD CHECK
    fraud_score: float = 0.0
    fraud_reasons: List[str] = Field(default_factory=list)

    # Meta
    retries: int = 0
    errors: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None