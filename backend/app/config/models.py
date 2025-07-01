"""LLM model configuration and validation"""

from typing import Dict, List, Set
from pydantic import BaseModel


class LLMModelConfig(BaseModel):
    """Configuration for an LLM model"""
    id: str
    name: str
    provider: str  # 'openai' or 'anthropic'
    context_window: int
    input_pricing: float  # per 1M tokens
    output_pricing: float  # per 1M tokens
    description: str
    supported: bool = True


# Supported LLM models with their configurations
SUPPORTED_MODELS: Dict[str, LLMModelConfig] = {
    # OpenAI GPT-4.1 Series (Latest 2025)
    "gpt-4.1": LLMModelConfig(
        id="gpt-4.1",
        name="GPT-4.1",
        provider="openai",
        context_window=1000000,
        input_pricing=2.0,
        output_pricing=8.0,
        description="Latest GPT-4.1 with enhanced coding and instruction following"
    ),
    "gpt-4.1-mini": LLMModelConfig(
        id="gpt-4.1-mini",
        name="GPT-4.1 Mini",
        provider="openai",
        context_window=128000,
        input_pricing=0.40,
        output_pricing=1.60,
        description="Efficient version of GPT-4.1 for most tasks"
    ),
    "gpt-4.1-nano": LLMModelConfig(
        id="gpt-4.1-nano",
        name="GPT-4.1 Nano",
        provider="openai",
        context_window=32000,
        input_pricing=0.10,
        output_pricing=0.40,
        description="Fastest and most affordable GPT-4.1 model"
    ),
    
    # OpenAI GPT-4o Series
    "gpt-4o": LLMModelConfig(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        context_window=128000,
        input_pricing=2.50,
        output_pricing=10.0,
        description="Multimodal flagship model for complex reasoning"
    ),
    "gpt-4o-mini": LLMModelConfig(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        context_window=128000,
        input_pricing=0.15,
        output_pricing=0.60,
        description="Affordable and intelligent small model"
    ),
    
    # OpenAI GPT-4 Series (Legacy)
    "gpt-4-turbo": LLMModelConfig(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider="openai",
        context_window=128000,
        input_pricing=10.0,
        output_pricing=30.0,
        description="Previous generation high-performance model"
    ),
    "gpt-4": LLMModelConfig(
        id="gpt-4",
        name="GPT-4",
        provider="openai",
        context_window=32000,
        input_pricing=30.0,
        output_pricing=60.0,
        description="Original GPT-4 model"
    ),
    
    # Legacy support for existing model names
    "gpt-4-turbo-preview": LLMModelConfig(
        id="gpt-4-turbo-preview",
        name="GPT-4 Turbo Preview",
        provider="openai",
        context_window=128000,
        input_pricing=10.0,
        output_pricing=30.0,
        description="Legacy name for GPT-4 Turbo",
        supported=False  # Deprecated but maintained for backwards compatibility
    ),
    
    # OpenAI GPT-3.5 Series
    "gpt-3.5-turbo": LLMModelConfig(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        context_window=16000,
        input_pricing=0.5,
        output_pricing=1.5,
        description="Fast and affordable for simple tasks"
    ),
    
    # Anthropic Claude Series
    "claude-3-5-sonnet-20241022": LLMModelConfig(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        context_window=200000,
        input_pricing=3.0,
        output_pricing=15.0,
        description="Anthropic's most intelligent model"
    ),
    "claude-3-5-haiku-20241022": LLMModelConfig(
        id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        provider="anthropic",
        context_window=200000,
        input_pricing=1.0,
        output_pricing=5.0,
        description="Fast and affordable Claude model"
    ),
    "claude-3-opus-20240229": LLMModelConfig(
        id="claude-3-opus-20240229",
        name="Claude 3 Opus",
        provider="anthropic",
        context_window=200000,
        input_pricing=15.0,
        output_pricing=75.0,
        description="Most powerful Claude model for complex tasks"
    ),
    
    # Legacy Claude models for backwards compatibility
    "claude-3-sonnet-20240229": LLMModelConfig(
        id="claude-3-sonnet-20240229",
        name="Claude 3 Sonnet (Legacy)",
        provider="anthropic",
        context_window=200000,
        input_pricing=3.0,
        output_pricing=15.0,
        description="Legacy Claude 3 Sonnet model",
        supported=False
    ),
    "claude-3-haiku-20240307": LLMModelConfig(
        id="claude-3-haiku-20240307",
        name="Claude 3 Haiku (Legacy)",
        provider="anthropic",
        context_window=200000,
        input_pricing=1.0,
        output_pricing=5.0,
        description="Legacy Claude 3 Haiku model",
        supported=False
    ),
}

# Default model
DEFAULT_MODEL = "gpt-4o-mini"

# Helper functions
def get_model_config(model_id: str) -> LLMModelConfig:
    """Get configuration for a model by ID"""
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}")
    return SUPPORTED_MODELS[model_id]


def is_model_supported(model_id: str) -> bool:
    """Check if a model is supported"""
    return model_id in SUPPORTED_MODELS and SUPPORTED_MODELS[model_id].supported


def get_supported_models() -> List[LLMModelConfig]:
    """Get list of all supported models"""
    return [config for config in SUPPORTED_MODELS.values() if config.supported]


def get_models_by_provider(provider: str) -> List[LLMModelConfig]:
    """Get models by provider (openai or anthropic)"""
    return [
        config for config in SUPPORTED_MODELS.values() 
        if config.provider == provider and config.supported
    ]


def validate_model_id(model_id: str) -> str:
    """Validate and normalize model ID"""
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}. Supported models: {list(SUPPORTED_MODELS.keys())}")
    
    config = SUPPORTED_MODELS[model_id]
    if not config.supported:
        # For deprecated models, suggest modern alternatives
        if model_id == "gpt-4-turbo-preview":
            return "gpt-4-turbo"
        elif model_id == "claude-3-sonnet-20240229":
            return "claude-3-5-sonnet-20241022"
        elif model_id == "claude-3-haiku-20240307":
            return "claude-3-5-haiku-20241022"
    
    return model_id