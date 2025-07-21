import { useQuery } from 'react-query'
import { TrendingUp, TrendingDown, AlertTriangle, Zap, Clock, Brain, BarChart3, Target, RefreshCw, Play, Eye } from 'lucide-react'
import { analysisApi } from '../lib/api'
import { formatDate } from '../lib/utils'

interface MarketSummaryData {
  overall_sentiment: string
  sentiment_score: number
  key_themes: string[]
  stocks_to_watch: {
    ticker: string
    reason: string
    sentiment: 'bullish' | 'bearish' | 'neutral'
    confidence: number
  }[]
  notable_catalysts: {
    type: string
    description: string
    impact: 'positive' | 'negative'
    affected_stocks: string[]
  }[]
  risk_factors: string[]
  summary: string
  generated_at: string
  model_used: string
  data_sources: {
    articles_analyzed: number
    sentiment_analyses: number
    positions_generated: number
    unique_tickers?: number
  }
  // Analysis session metadata
  analysis_session?: {
    session_id: string
    analysis_type: 'headlines' | 'full'
    started_at: string
    completed_at: string
    duration_seconds: number
    status: string
  }
  error?: string
}

const getSentimentIcon = (score: number) => {
  if (score >= 0.3) return <TrendingUp className="h-5 w-5 text-green-600" />
  if (score <= -0.3) return <TrendingDown className="h-5 w-5 text-red-600" />
  return <BarChart3 className="h-5 w-5 text-gray-600" />
}

const getSentimentLabel = (score: number) => {
  if (score >= 0.7) return { label: 'Very Bullish', color: 'text-green-700 bg-green-100' }
  if (score >= 0.3) return { label: 'Bullish', color: 'text-green-600 bg-green-50' }
  if (score >= -0.3) return { label: 'Neutral', color: 'text-gray-600 bg-gray-100' }
  if (score >= -0.7) return { label: 'Bearish', color: 'text-red-600 bg-red-50' }
  return { label: 'Very Bearish', color: 'text-red-700 bg-red-100' }
}

const getStockSentimentColor = (sentiment: string) => {
  switch (sentiment) {
    case 'bullish': return 'bg-green-100 text-green-800'
    case 'bearish': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

export default function MarketSummary() {
  const { data: summary, isLoading, error, refetch, isFetching } = useQuery<MarketSummaryData>(
    'market-summary',
    () => analysisApi.getMarketSummary(),
    {
      refetchOnWindowFocus: false,
      // Remove staleTime since summary is now analysis-triggered
      // Data stays fresh until new analysis is run
      staleTime: Infinity,
      cacheTime: 24 * 60 * 60 * 1000, // Cache for 24 hours
      retry: 2
    }
  )

  const handleRefresh = () => {
    refetch()
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="flex items-center mb-4">
            <div className="h-6 w-6 bg-gray-300 rounded mr-3"></div>
            <div className="h-6 bg-gray-300 rounded w-48"></div>
          </div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-300 rounded w-full"></div>
            <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !summary) {
    // Check if it's a "no analysis run yet" error vs actual error
    const isNoAnalysisError = error?.response?.status === 404 || 
                              error?.response?.data?.detail?.includes('No analysis') ||
                              error?.message?.includes('No analysis')

    if (isNoAnalysisError) {
      return (
        <div className="card border-blue-200 bg-blue-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Play className="h-6 w-6 text-blue-600 mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-blue-700">No Market Analysis Yet</h3>
                <p className="text-blue-600">Start an analysis to generate market summary</p>
              </div>
            </div>
            <button 
              onClick={handleRefresh}
              disabled={isFetching}
              className="btn btn-primary flex items-center"
            >
              {isFetching ? (
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Check Again
            </button>
          </div>
        </div>
      )
    }

    return (
      <div className="card border-red-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
            <div>
              <h3 className="text-lg font-semibold text-red-700">Market Summary Error</h3>
              <p className="text-red-600">Unable to load market summary</p>
            </div>
          </div>
          <button 
            onClick={handleRefresh}
            disabled={isFetching}
            className="btn btn-secondary flex items-center"
          >
            {isFetching ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (summary.error) {
    return (
      <div className="card border-yellow-200">
        <div className="flex items-center">
          <AlertTriangle className="h-6 w-6 text-yellow-600 mr-3" />
          <div>
            <h3 className="text-lg font-semibold text-yellow-700">Market Summary</h3>
            <p className="text-yellow-600">{summary.summary}</p>
            <div className="mt-2 text-sm text-gray-600">
              Analyzed {summary.data_sources?.articles_analyzed || 0} articles and {summary.data_sources?.sentiment_analyses || 0} sentiment analyses
            </div>
          </div>
        </div>
      </div>
    )
  }

  const sentimentInfo = getSentimentLabel(summary.sentiment_score)

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Brain className="h-6 w-6 text-blue-600 mr-3" />
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-xl font-bold text-gray-900">Market Summary</h3>
              {summary.analysis_session && (
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    summary.analysis_session.analysis_type === 'full' 
                      ? 'bg-purple-100 text-purple-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {summary.analysis_session.analysis_type === 'full' ? (
                      <Eye className="h-3 w-3 mr-1" />
                    ) : (
                      <Zap className="h-3 w-3 mr-1" />
                    )}
                    {summary.analysis_session.analysis_type === 'full' ? 'Full Analysis' : 'Headlines Only'}
                  </span>
                </div>
              )}
            </div>
            <p className="text-sm text-gray-600">
              {summary.analysis_session 
                ? `Generated from ${summary.analysis_session.analysis_type} analysis run on ${formatDate(summary.analysis_session.completed_at)}`
                : 'AI-generated analysis from recent market data'
              }
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${sentimentInfo.color}`}>
              {getSentimentIcon(summary.sentiment_score)}
              <span className="ml-2">{sentimentInfo.label}</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {summary.analysis_session 
                ? `Analysis: ${formatDate(summary.analysis_session.completed_at)}`
                : formatDate(summary.generated_at)
              }
            </div>
          </div>
          <button 
            onClick={handleRefresh}
            disabled={isFetching}
            className="btn btn-secondary btn-sm flex items-center"
            title="Refresh market summary"
          >
            {isFetching ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Overall Sentiment & Summary */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
        <h4 className="font-semibold text-blue-900 mb-2">{summary.overall_sentiment}</h4>
        <p className="text-blue-800 leading-relaxed">{summary.summary}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Themes */}
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <Zap className="h-5 w-5 mr-2 text-yellow-600" />
            Key Market Themes
          </h4>
          <div className="space-y-2">
            {(summary.key_themes || []).map((theme, index) => (
              <div key={index} className="flex items-start">
                <span className="flex-shrink-0 w-6 h-6 bg-yellow-100 text-yellow-800 rounded-full flex items-center justify-center text-sm font-medium mr-3 mt-0.5">
                  {index + 1}
                </span>
                <p className="text-gray-700">{theme}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Stocks to Watch */}
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <Target className="h-5 w-5 mr-2 text-green-600" />
            Stocks to Watch
          </h4>
          <div className="space-y-3">
            {(summary.stocks_to_watch || []).slice(0, 5).map((stock, index) => (
              <div key={index} className="p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-blue-600">{stock.ticker}</span>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStockSentimentColor(stock.sentiment)}`}>
                      {stock.sentiment}
                    </span>
                    <span className="text-sm text-gray-600">
                      {Math.round(stock.confidence * 100)}%
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-700">{stock.reason}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Notable Catalysts */}
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <Zap className="h-5 w-5 mr-2 text-purple-600" />
            Notable Catalysts
          </h4>
          <div className="space-y-3">
            {(summary.notable_catalysts || []).slice(0, 4).map((catalyst, index) => (
              <div key={index} className="p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    catalyst.impact === 'positive' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {catalyst.impact === 'positive' ? '↗' : '↘'} {catalyst.type}
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {(catalyst.affected_stocks || []).slice(0, 3).map((ticker, i) => (
                      <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                        {ticker}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="text-sm text-gray-700">{catalyst.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Factors */}
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-red-600" />
            Risk Factors
          </h4>
          <div className="space-y-2">
            {(summary.risk_factors || []).map((risk, index) => (
              <div key={index} className="flex items-start">
                <AlertTriangle className="flex-shrink-0 h-4 w-4 text-red-500 mr-2 mt-0.5" />
                <p className="text-gray-700 text-sm">{risk}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-3">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <Clock className="h-4 w-4 mr-1" />
              {summary.analysis_session 
                ? `Analysis completed ${formatDate(summary.analysis_session.completed_at)}`
                : `Updated ${formatDate(summary.generated_at)}`
              }
            </span>
            <span className="flex items-center">
              <Brain className="h-4 w-4 mr-1" />
              {summary.model_used || 'AI Model'}
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <span>{summary.data_sources?.articles_analyzed || 0} articles</span>
            <span>{summary.data_sources?.sentiment_analyses || 0} analyses</span>
            <span>{summary.data_sources?.positions_generated || 0} positions</span>
          </div>
        </div>
        
        {/* Analysis Session Details */}
        {summary.analysis_session && (
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <span className="font-medium text-gray-700">Session ID:</span>
                <div className="font-mono text-gray-600 mt-1 truncate" title={summary.analysis_session.session_id}>
                  {summary.analysis_session.session_id.split('_').pop()}
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700">Duration:</span>
                <div className="mt-1">
                  {summary.analysis_session.duration_seconds 
                    ? `${Math.round(summary.analysis_session.duration_seconds)}s`
                    : 'N/A'
                  }
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700">Status:</span>
                <div className="mt-1 capitalize">
                  {summary.analysis_session.status}
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700">Started:</span>
                <div className="mt-1">
                  {formatDate(summary.analysis_session.started_at)}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}