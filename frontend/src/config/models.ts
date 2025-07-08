export interface LLMModel {
  id: string;
  name: string;
  provider: 'openai' | 'anthropic';
  inputPricing: number; // per 1M tokens
  outputPricing: number; // per 1M tokens
  contextWindow: number; // tokens
  description: string;
}

export const LLM_MODELS: LLMModel[] = [
  // OpenAI GPT-4.1 Series (Latest 2025)
  {
    id: 'gpt-4.1',
    name: 'GPT-4.1',
    provider: 'openai',
    inputPricing: 2.0,
    outputPricing: 8.0,
    contextWindow: 1000000,
    description: 'Latest GPT-4.1 with enhanced coding and instruction following'
  },
  {
    id: 'gpt-4.1-mini',
    name: 'GPT-4.1 Mini',
    provider: 'openai',
    inputPricing: 0.40,
    outputPricing: 1.60,
    contextWindow: 128000,
    description: 'Efficient version of GPT-4.1 for most tasks'
  },
  {
    id: 'gpt-4.1-nano',
    name: 'GPT-4.1 Nano',
    provider: 'openai',
    inputPricing: 0.10,
    outputPricing: 0.40,
    contextWindow: 32000,
    description: 'Fastest and most affordable GPT-4.1 model'
  },
  
  // OpenAI GPT-4o Series
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'openai',
    inputPricing: 2.50,
    outputPricing: 10.0,
    contextWindow: 128000,
    description: 'Multimodal flagship model for complex reasoning'
  },
  {
    id: 'gpt-4o-mini',
    name: 'GPT-4o Mini',
    provider: 'openai',
    inputPricing: 0.15,
    outputPricing: 0.60,
    contextWindow: 128000,
    description: 'Affordable and intelligent small model'
  },
  
  // OpenAI GPT-4 Series (Legacy)
  {
    id: 'gpt-4-turbo',
    name: 'GPT-4 Turbo',
    provider: 'openai',
    inputPricing: 10.0,
    outputPricing: 30.0,
    contextWindow: 128000,
    description: 'Previous generation high-performance model'
  },
  {
    id: 'gpt-4',
    name: 'GPT-4',
    provider: 'openai',
    inputPricing: 30.0,
    outputPricing: 60.0,
    contextWindow: 32000,
    description: 'Original GPT-4 model'
  },
  
  // OpenAI GPT-3.5 Series
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    provider: 'openai',
    inputPricing: 0.5,
    outputPricing: 1.5,
    contextWindow: 16000,
    description: 'Fast and affordable for simple tasks'
  },
  
  // Anthropic Claude Series
  {
    id: 'claude-3-5-sonnet-20241022',
    name: 'Claude 3.5 Sonnet',
    provider: 'anthropic',
    inputPricing: 3.0,
    outputPricing: 15.0,
    contextWindow: 200000,
    description: 'Anthropic\'s most intelligent model'
  },
  {
    id: 'claude-3-5-haiku-20241022',
    name: 'Claude 3.5 Haiku',
    provider: 'anthropic',
    inputPricing: 1.0,
    outputPricing: 5.0,
    contextWindow: 200000,
    description: 'Fast and affordable Claude model'
  },
  {
    id: 'claude-3-opus-20240229',
    name: 'Claude 3 Opus',
    provider: 'anthropic',
    inputPricing: 15.0,
    outputPricing: 75.0,
    contextWindow: 200000,
    description: 'Most powerful Claude model for complex tasks'
  }
];

export const DEFAULT_MODEL_ID = 'gpt-4.1-mini';

export const getModelById = (id: string): LLMModel | undefined => {
  return LLM_MODELS.find(model => model.id === id);
};

export const formatPricing = (inputPrice: number, outputPrice: number): string => {
  return `$${inputPrice}/$${outputPrice} per 1M tokens`;
};