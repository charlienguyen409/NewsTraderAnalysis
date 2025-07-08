import { Position } from '../types'
import { getPositionColor, getConfidenceColor, formatConfidence, formatDate } from '../lib/utils'
import { TrendingUp, TrendingDown, Minus, Zap, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface PositionCardProps {
  position: Position
}

export default function PositionCard({ position }: PositionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showAllCatalysts, setShowAllCatalysts] = useState(false)

  const getIcon = () => {
    switch (position.position_type) {
      case 'STRONG_BUY':
      case 'BUY':
        return <TrendingUp className="h-5 w-5" />
      case 'STRONG_SHORT':
      case 'SHORT':
        return <TrendingDown className="h-5 w-5" />
      default:
        return <Minus className="h-5 w-5" />
    }
  }

  const isHeadlineBased = position.reasoning.includes('[HEADLINE-BASED RECOMMENDATION]')
  const cleanReasoning = position.reasoning.replace('[HEADLINE-BASED RECOMMENDATION] ', '')
  
  // Check if reasoning is long enough to need expansion
  const needsExpansion = cleanReasoning.length > 150

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="space-y-4">
        {/* Header section */}
        <div className="flex items-start justify-between">
          <div className="flex items-center flex-wrap gap-2">
            <span className="text-xl font-bold text-gray-900">
              {position.ticker}
            </span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getPositionColor(position.position_type)}`}>
              {getIcon()}
              <span className="ml-1">{position.position_type.replace('_', ' ')}</span>
            </span>
            {isHeadlineBased && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
                <Zap className="h-3 w-3 mr-1" />
                Headline-Based
              </span>
            )}
          </div>
          
          <div className="text-right">
            <div className={`text-xl font-bold ${getConfidenceColor(position.confidence)}`}>
              {formatConfidence(position.confidence)}
            </div>
            <div className="text-xs text-gray-500">
              {formatDate(position.created_at)}
            </div>
          </div>
        </div>

        {/* Reasoning section with expansion */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-700">Analysis & Recommendation</h4>
            {needsExpansion && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center text-xs text-blue-600 hover:text-blue-800 transition-colors"
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className="h-3 w-3 mr-1" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3 mr-1" />
                    Read More
                  </>
                )}
              </button>
            )}
          </div>
          
          <div className={`text-sm text-gray-600 leading-relaxed ${
            !isExpanded && needsExpansion ? 'line-clamp-3' : ''
          }`}>
            {cleanReasoning}
          </div>
        </div>

        {/* Catalysts section */}
        {position.catalysts.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-700">Key Catalysts</h4>
              {position.catalysts.length > 3 && (
                <button
                  onClick={() => setShowAllCatalysts(!showAllCatalysts)}
                  className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
                >
                  {showAllCatalysts ? 'Show Less' : `Show All (${position.catalysts.length})`}
                </button>
              )}
            </div>
            
            <div className="space-y-2">
              {(showAllCatalysts ? position.catalysts : position.catalysts.slice(0, 3)).map((catalyst, index) => (
                <div key={index} className="p-2 bg-gray-50 rounded-md border">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-700 capitalize">
                      {catalyst.type.replace('_', ' ')}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      catalyst.impact === 'positive' ? 'bg-green-100 text-green-700' :
                      catalyst.impact === 'negative' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {catalyst.impact}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 break-words">
                    {catalyst.description}
                  </p>
                  {catalyst.significance && (
                    <div className="mt-1">
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        catalyst.significance === 'high' ? 'bg-red-50 text-red-600' :
                        catalyst.significance === 'medium' ? 'bg-yellow-50 text-yellow-600' :
                        'bg-blue-50 text-blue-600'
                      }`}>
                        {catalyst.significance} significance
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}