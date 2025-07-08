"""API endpoints for LLM model information"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config.models import (
    get_supported_models, 
    get_models_by_provider, 
    get_model_config,
    LLMModelConfig
)
from ...services.llm_service import LLMService

router = APIRouter()


class ModelInfoResponse(BaseModel):
    """Response model for model information"""
    id: str
    name: str
    provider: str
    context_window: int
    input_pricing: float
    output_pricing: float
    description: str


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics"""
    cache_enabled: bool
    total_keys: Optional[int] = None
    headline_cache_count: Optional[int] = None
    sentiment_cache_count: Optional[int] = None
    position_cache_count: Optional[int] = None
    memory_used: Optional[str] = None
    hits: Optional[int] = None
    misses: Optional[int] = None
    hit_rate: Optional[float] = None
    error: Optional[str] = None


class CacheClearResponse(BaseModel):
    """Response model for cache clearing"""
    deleted: int
    error: Optional[str] = None


@router.get("/models", response_model=List[ModelInfoResponse])
async def get_available_models():
    """Get list of all supported LLM models"""
    models = get_supported_models()
    return [
        ModelInfoResponse(
            id=model.id,
            name=model.name,
            provider=model.provider,
            context_window=model.context_window,
            input_pricing=model.input_pricing,
            output_pricing=model.output_pricing,
            description=model.description
        )
        for model in models
    ]


@router.get("/models/{provider}", response_model=List[ModelInfoResponse])
async def get_models_by_provider_endpoint(provider: str):
    """Get models by provider (openai or anthropic)"""
    if provider not in ["openai", "anthropic"]:
        raise HTTPException(status_code=400, detail="Provider must be 'openai' or 'anthropic'")
    
    models = get_models_by_provider(provider)
    return [
        ModelInfoResponse(
            id=model.id,
            name=model.name,
            provider=model.provider,
            context_window=model.context_window,
            input_pricing=model.input_pricing,
            output_pricing=model.output_pricing,
            description=model.description
        )
        for model in models
    ]


@router.get("/models/info/{model_id}", response_model=ModelInfoResponse)
async def get_model_info(model_id: str):
    """Get detailed information about a specific model"""
    try:
        model = get_model_config(model_id)
        return ModelInfoResponse(
            id=model.id,
            name=model.name,
            provider=model.provider,
            context_window=model.context_window,
            input_pricing=model.input_pricing,
            output_pricing=model.output_pricing,
            description=model.description
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get LLM cache statistics"""
    llm_service = LLMService()
    stats = llm_service.get_cache_stats()
    return CacheStatsResponse(**stats)


@router.delete("/cache", response_model=CacheClearResponse)
async def clear_all_cache():
    """Clear all LLM cache"""
    llm_service = LLMService()
    result = llm_service.clear_cache()
    return CacheClearResponse(**result)


@router.delete("/cache/{cache_type}", response_model=CacheClearResponse)
async def clear_cache_by_type(cache_type: str):
    """Clear specific type of LLM cache (headlines, sentiment, positions)"""
    if cache_type not in ["headlines", "sentiment", "positions"]:
        raise HTTPException(
            status_code=400, 
            detail="Cache type must be 'headlines', 'sentiment', or 'positions'"
        )
    
    llm_service = LLMService()
    result = llm_service.clear_cache(cache_type)
    return CacheClearResponse(**result)