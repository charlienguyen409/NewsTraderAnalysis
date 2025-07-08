import React from 'react';
import { LLM_MODELS, formatPricing } from '../config/models';

interface LLMSelectorProps {
  value: string;
  onChange: (value: string) => void;
  label: string;
  description?: string;
  showPricing?: boolean;
  className?: string;
}

export const LLMSelector: React.FC<LLMSelectorProps> = ({
  value,
  onChange,
  label,
  description,
  showPricing = false,
  className = ''
}) => {
  const selectedModel = LLM_MODELS.find(model => model.id === value);

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {label}
      </label>
      {description && (
        <p className="text-sm text-gray-500">{description}</p>
      )}
      
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="select"
      >
        {LLM_MODELS.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name} {showPricing && `(${formatPricing(model.inputPricing, model.outputPricing)})`}
          </option>
        ))}
      </select>
      
      {selectedModel && showPricing && (
        <div className="text-sm text-gray-600 space-y-1">
          <div>
            <strong>Provider:</strong> {selectedModel.provider.toUpperCase()}
          </div>
          <div>
            <strong>Context Window:</strong> {selectedModel.contextWindow.toLocaleString()} tokens
          </div>
          <div>
            <strong>Pricing:</strong> {formatPricing(selectedModel.inputPricing, selectedModel.outputPricing)}
          </div>
          <div>
            <strong>Description:</strong> {selectedModel.description}
          </div>
        </div>
      )}
    </div>
  );
};