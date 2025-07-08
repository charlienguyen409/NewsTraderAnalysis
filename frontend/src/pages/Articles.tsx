import { useState } from 'react'
import { useQuery } from 'react-query'
import { Search, Filter, ExternalLink, TrendingUp, TrendingDown, Clock, Brain, BarChart3, Eye, EyeOff, Calendar, Tag } from 'lucide-react'
import { articlesApi } from '../lib/api'
import { formatDate } from '../lib/utils'
import { Article, Analysis } from '../types'

// Helper functions
const getSentimentLabel = (score: number) => {
  if (score >= 0.7) return { label: 'Very Bullish', color: 'bg-green-600 text-white' }
  if (score >= 0.3) return { label: 'Bullish', color: 'bg-green-100 text-green-800' }
  if (score >= -0.3) return { label: 'Neutral', color: 'bg-gray-100 text-gray-800' }
  if (score >= -0.7) return { label: 'Bearish', color: 'bg-red-100 text-red-800' }
  return { label: 'Very Bearish', color: 'bg-red-600 text-white' }
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'text-green-600'
  if (confidence >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

const formatSentimentScore = (score: number) => {
  const percentage = Math.round(score * 100)
  return score >= 0 ? `+${percentage}%` : `${percentage}%`
}

export default function Articles() {
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [tickerFilter, setTickerFilter] = useState('')
  const [expandedArticles, setExpandedArticles] = useState<Set<string>>(new Set())

  const { data: articles, isLoading, error } = useQuery(
    ['articles', search, sourceFilter, tickerFilter],
    () => articlesApi.getAll({
      search: search || undefined,
      source: sourceFilter || undefined,
      ticker: tickerFilter || undefined,
      limit: 50
    }),
    { select: data => data.data }
  )

  const toggleExpanded = (articleId: string) => {
    const newExpanded = new Set(expandedArticles)
    if (newExpanded.has(articleId)) {
      newExpanded.delete(articleId)
    } else {
      newExpanded.add(articleId)
    }
    setExpandedArticles(newExpanded)
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Articles</h1>
        <p className="mt-2 text-gray-600">
          Browse and search scraped financial news articles
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search articles..."
              className="input pl-10"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="select"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
          >
            <option value="">All Sources</option>
            <option value="finviz">FinViz</option>
            <option value="biztoc">BizToc</option>
          </select>

          <input
            type="text"
            placeholder="Filter by ticker..."
            className="input"
            value={tickerFilter}
            onChange={(e) => setTickerFilter(e.target.value)}
          />

          <button
            onClick={() => {
              setSearch('')
              setSourceFilter('')
              setTickerFilter('')
            }}
            className="btn btn-secondary flex items-center justify-center"
          >
            <Filter className="h-4 w-4 mr-2" />
            Clear Filters
          </button>
        </div>
      </div>

      {/* Articles List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading articles...</p>
          </div>
        ) : error ? (
          <div className="card text-center py-8">
            <p className="text-red-600">Error loading articles</p>
          </div>
        ) : articles?.length === 0 ? (
          <div className="card text-center py-8">
            <p className="text-gray-500">No articles found</p>
          </div>
        ) : (
          articles?.map((article: Article) => {
            const isExpanded = expandedArticles.has(article.id)
            const latestAnalysis = article.analyses?.[0] // Most recent analysis
            
            return (
              <div key={article.id} className="card hover:shadow-lg transition-all duration-200 border-l-4 border-l-gray-200">
                {/* Main Article Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center mb-2">
                      <h3 className="text-xl font-bold text-gray-900 mr-3 line-clamp-2 leading-tight">
                        {article.title}
                      </h3>
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 flex-shrink-0"
                        title="Open article"
                      >
                        <ExternalLink className="h-5 w-5" />
                      </a>
                    </div>

                    {/* Article Metadata */}
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                        <Tag className="h-3 w-3 mr-1" />
                        {article.source.toUpperCase()}
                      </span>
                      
                      {article.ticker && (
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                          <BarChart3 className="h-3 w-3 mr-1" />
                          {article.ticker}
                        </span>
                      )}

                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        article.is_processed 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {article.is_processed ? (
                          <>
                            <Brain className="h-3 w-3 mr-1" />
                            Analyzed
                          </>
                        ) : (
                          <>
                            <Clock className="h-3 w-3 mr-1" />
                            Pending
                          </>
                        )}
                      </span>

                      {latestAnalysis && (
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getSentimentLabel(latestAnalysis.sentiment_score).color}`}>
                          {latestAnalysis.sentiment_score >= 0 ? (
                            <TrendingUp className="h-3 w-3 mr-1" />
                          ) : (
                            <TrendingDown className="h-3 w-3 mr-1" />
                          )}
                          {getSentimentLabel(latestAnalysis.sentiment_score).label}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Expand/Collapse Button */}
                  <button
                    onClick={() => toggleExpanded(article.id)}
                    className="ml-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    title={isExpanded ? "Show less" : "Show more"}
                  >
                    {isExpanded ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>

                {/* Quick Sentiment Summary (Always Visible) */}
                {latestAnalysis && (
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-gray-900">
                            {formatSentimentScore(latestAnalysis.sentiment_score)}
                          </div>
                          <div className="text-xs text-gray-600">Sentiment</div>
                        </div>
                        <div className="text-center">
                          <div className={`text-2xl font-bold ${getConfidenceColor(latestAnalysis.confidence)}`}>
                            {Math.round(latestAnalysis.confidence * 100)}%
                          </div>
                          <div className="text-xs text-gray-600">Confidence</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-gray-900">
                            {latestAnalysis.catalysts?.length || 0}
                          </div>
                          <div className="text-xs text-gray-600">Catalysts</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">{latestAnalysis.llm_model}</div>
                        <div className="text-xs text-gray-600">Model Used</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="space-y-6 border-t pt-4">
                    {/* Article Content */}
                    {(article.content || article.summary) && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                          <Eye className="h-4 w-4 mr-2" />
                          Article Content
                        </h4>
                        <div className="prose prose-sm max-w-none">
                          <p className="text-gray-700 leading-relaxed">
                            {article.content || article.summary}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Detailed Analysis Results */}
                    {article.analyses && article.analyses.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                          <Brain className="h-4 w-4 mr-2" />
                          AI Analysis Results
                        </h4>
                        
                        <div className="space-y-4">
                          {article.analyses.map((analysis: Analysis, index: number) => (
                            <div key={analysis.id} className="bg-white border border-gray-200 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center space-x-3">
                                  <span className="text-sm font-medium text-gray-900">
                                    Analysis #{index + 1}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {formatDate(analysis.created_at)}
                                  </span>
                                </div>
                                <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                                  {analysis.llm_model}
                                </span>
                              </div>

                              {/* Analysis Metrics */}
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                <div className="text-center p-2 bg-gray-50 rounded">
                                  <div className="text-lg font-bold text-gray-900">
                                    {formatSentimentScore(analysis.sentiment_score)}
                                  </div>
                                  <div className="text-xs text-gray-600">Sentiment</div>
                                </div>
                                <div className="text-center p-2 bg-gray-50 rounded">
                                  <div className={`text-lg font-bold ${getConfidenceColor(analysis.confidence)}`}>
                                    {Math.round(analysis.confidence * 100)}%
                                  </div>
                                  <div className="text-xs text-gray-600">Confidence</div>
                                </div>
                                <div className="text-center p-2 bg-gray-50 rounded">
                                  <div className="text-lg font-bold text-blue-600">
                                    {analysis.ticker}
                                  </div>
                                  <div className="text-xs text-gray-600">Primary Ticker</div>
                                </div>
                                <div className="text-center p-2 bg-gray-50 rounded">
                                  <div className="text-lg font-bold text-purple-600">
                                    {analysis.catalysts?.length || 0}
                                  </div>
                                  <div className="text-xs text-gray-600">Catalysts</div>
                                </div>
                              </div>

                              {/* AI Reasoning */}
                              <div className="mb-4">
                                <h5 className="text-sm font-medium text-gray-900 mb-2">AI Reasoning:</h5>
                                <p className="text-sm text-gray-700 bg-blue-50 p-3 rounded border-l-4 border-blue-200">
                                  {analysis.reasoning}
                                </p>
                              </div>

                              {/* Catalysts */}
                              {analysis.catalysts && analysis.catalysts.length > 0 && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-900 mb-2">Key Catalysts:</h5>
                                  <div className="space-y-2">
                                    {analysis.catalysts.map((catalyst, catIndex) => (
                                      <div key={catIndex} className="flex items-start space-x-3 p-2 bg-gray-50 rounded">
                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                          catalyst.impact === 'positive' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                        }`}>
                                          {catalyst.impact === 'positive' ? '↗' : '↘'} {catalyst.impact}
                                        </span>
                                        <div className="flex-1">
                                          <div className="text-sm font-medium text-gray-900">{catalyst.type}</div>
                                          <div className="text-sm text-gray-600">{catalyst.description}</div>
                                          <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs ${
                                            catalyst.significance === 'high' ? 'bg-red-100 text-red-700' :
                                            catalyst.significance === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                            'bg-gray-100 text-gray-700'
                                          }`}>
                                            {catalyst.significance} impact
                                          </span>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Article Metadata */}
                    <div className="border-t pt-4">
                      <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                        <Calendar className="h-4 w-4 mr-2" />
                        Article Information
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-700">Scraped:</span>
                          <span className="ml-2 text-gray-600">{formatDate(article.scraped_at)}</span>
                        </div>
                        {article.published_at && (
                          <div>
                            <span className="font-medium text-gray-700">Published:</span>
                            <span className="ml-2 text-gray-600">{formatDate(article.published_at)}</span>
                          </div>
                        )}
                        <div>
                          <span className="font-medium text-gray-700">Source:</span>
                          <span className="ml-2 text-gray-600">{article.source}</span>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">Analyses:</span>
                          <span className="ml-2 text-gray-600">{article.analyses?.length || 0} performed</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Load More */}
      {articles && articles.length === 50 && (
        <div className="text-center">
          <button className="btn btn-secondary">
            Load More Articles
          </button>
        </div>
      )}
    </div>
  )
}