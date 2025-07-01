"""API endpoints for LLM model information"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config.models import (
    get_supported_models, 
    get_models_by_provider, 
    get_model_config,
    LLMModelConfig
)

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