from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RetrievalFilter(BaseModel):
    # Car filters
    car_id: Optional[int] = None
    car_name: Optional[str] = None

    brand_id: Optional[int] = None
    brand_name: Optional[str] = None

    model_id: Optional[int] = None
    model_name: Optional[str] = None

    submodel_id: Optional[int] = None
    submodel_name: Optional[str] = None

    # Trim filters
    trim_id: Optional[int] = None
    trim_name: Optional[str] = None

    # Chunk filters
    chunk_type: Optional[str] = None
    chunk_types: Optional[List[str]] = None

    # Vehicle filters
    fuel_type: Optional[str] = None

    is_popular: Optional[bool] = None
    is_trending: Optional[bool] = None
    is_upcoming: Optional[bool] = None

    # Price filters
    min_price: Optional[float] = None
    max_price: Optional[float] = None

    # Mileage filters
    min_mileage: Optional[float] = None
    max_mileage: Optional[float] = None

    # Engine filters
    min_engine_displacement: Optional[float] = None
    max_engine_displacement: Optional[float] = None

    # Safety filters
    min_no_of_airbags: Optional[int] = None
    max_no_of_airbags: Optional[int] = None

    # Rating filters
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None


class RetrievedChunk(BaseModel):
    # Vector search info
    id: str
    score: float

    # Chunk info
    chunk_id: Optional[str] = None
    chunk_type: Optional[str] = None
    content: str = ""

    # Car info
    car_id: Optional[int] = None
    car_name: Optional[str] = None
    url: Optional[str] = None

    # Brand info
    brand_id: Optional[int] = None
    brand_name: Optional[str] = None
    brand_slug: Optional[str] = None
    brand_url: Optional[str] = None

    # Model info
    model_id: Optional[int] = None
    model_name: Optional[str] = None
    model_slug: Optional[str] = None

    # Submodel info
    submodel_id: Optional[int] = None
    submodel_name: Optional[str] = None
    submodel_slug: Optional[str] = None

    # Pricing
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price: Optional[float] = None
    absolute_price: Optional[float] = None

    # Vehicle specifications
    fuel_type: Optional[str] = None

    min_mileage: Optional[float] = None
    max_mileage: Optional[float] = None

    min_engine_displacement: Optional[float] = None
    max_engine_displacement: Optional[float] = None

    min_no_of_airbags: Optional[int] = None
    max_no_of_airbags: Optional[int] = None

    # Ratings
    overall_rating: Optional[float] = None

    # Status flags
    is_popular: Optional[bool] = None
    is_trending: Optional[bool] = None
    is_upcoming: Optional[bool] = None

    # Trim information
    trim_id: Optional[int] = None
    trim_name: Optional[str] = None

    is_base: Optional[bool] = None
    is_top: Optional[bool] = None
    is_new: Optional[bool] = None

    # Optional URLs
    image_page_url: Optional[str] = None
    news_url: Optional[str] = None
    comparison_url: Optional[str] = None

    compare_car_id: Optional[int] = None
    compare_car_name: Optional[str] = None
    compare_brand_name: Optional[str] = None

    compare_car_url: Optional[str] = None

    # FAQ metadata
    faq_index: Optional[int] = None
    question: Optional[str] = None

    # Raw metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[RetrievalFilter] = None


class RetrievalResponse(BaseModel):
    query: str
    top_k: int
    total_results: int
    results: List[RetrievedChunk]