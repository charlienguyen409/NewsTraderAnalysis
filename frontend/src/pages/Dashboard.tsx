import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from 'react-query'
import { Play, Loader2, Zap } from 'lucide-react'
import { analysisApi, positionsApi } from '../lib/api'
import { AnalysisRequest } from '../types'
import PositionCard from '../components/PositionCard'
import ActivityLog from '../components/ActivityLog'
import MarketSummary from '../components/MarketSummary'
import { LLMSelector } from '../components/LLMSelector'
import { DEFAULT_MODEL_ID } from '../config/models'

export default function Dashboard() {
  const queryClient = useQueryClient()
  
  const [analysisConfig, setAnalysisConfig] = useState<AnalysisRequest>({
    max_positions: 10,
    min_confidence: 0.7,
    llm_model: DEFAULT_MODEL_ID,
    sources: ['finviz', 'biztoc']
  })
  
  const [headlineConfig, setHeadlineConfig] = useState<AnalysisRequest>({
    max_positions: 5,
    min_confidence: 0.6,
    llm_model: DEFAULT_MODEL_ID,
    sources: ['finviz', 'biztoc']
  })
  
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)

  // Auto-refresh positions and market summary when analysis completes
  useEffect(() => {
    if (currentSessionId) {
      // Set up polling to refresh data when analysis completes
      const interval = setInterval(() => {
        queryClient.invalidateQueries('recent-positions');
        queryClient.invalidateQueries('market-summary');
      }, 10000); // Check every 10 seconds
      
      return () => clearInterval(interval);
    }
  }, [currentSessionId, queryClient]);

  // Load default LLM model from Settings on component mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('marketAnalysisSettings')
    if (savedSettings) {
      const settings = JSON.parse(savedSettings)
      if (settings.defaultLlmModel) {
        setAnalysisConfig(prev => ({
          ...prev,
          llm_model: settings.defaultLlmModel
        }))
        setHeadlineConfig(prev => ({
          ...prev,
          llm_model: settings.defaultLlmModel
        }))
      }
    }
  }, [])

  // Queries for recent data (used in Recent Results section)
  const { data: recentPositions } = useQuery(
    'recent-positions',
    () => positionsApi.getAll({ limit: 5 }),
    { select: data => data.data }
  )

  // Removed analysis status polling since we removed the status display

  // Mutations
  const startAnalysisMutation = useMutation(analysisApi.start, {
    onSuccess: (data) => {
      setCurrentSessionId(data.data.session_id)
      // Refresh market summary after analysis starts
      setTimeout(() => {
        queryClient.invalidateQueries('market-summary')
      }, 30000) // Refresh after 30 seconds
    },
    onError: (error) => {
      console.error('Analysis failed:', error)
    }
  })

  const startHeadlineAnalysisMutation = useMutation(analysisApi.startHeadlines, {
    onSuccess: (data) => {
      setCurrentSessionId(data.data.session_id)
      // Refresh market summary after analysis starts
      setTimeout(() => {
        queryClient.invalidateQueries('market-summary')
      }, 30000) // Refresh after 30 seconds
    },
    onError: (error) => {
      console.error('Headline analysis failed:', error)
    }
  })

  const handleStartAnalysis = () => {
    startAnalysisMutation.mutate(analysisConfig)
  }

  const handleStartHeadlineAnalysis = () => {
    startHeadlineAnalysisMutation.mutate(headlineConfig)
  }

  const isAnalyzing = startAnalysisMutation.isLoading || 
    startHeadlineAnalysisMutation.isLoading

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Market Analysis Dashboard</h1>
        <p className="mt-2 text-gray-600">
          AI-powered financial news analysis and trading recommendations
        </p>
      </div>


      {/* Analysis Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Full Analysis Section */}
        <div className="card">
          <div className="flex items-center mb-4">
            <Play className="h-6 w-6 text-blue-600 mr-3" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Full Analysis</h2>
              <p className="text-sm text-gray-600">
                Complete article content scraping and analysis
              </p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Positions
                </label>
                <input
                  type="number"
                  className="input"
                  value={analysisConfig.max_positions}
                  onChange={(e) => setAnalysisConfig(prev => ({
                    ...prev,
                    max_positions: parseInt(e.target.value)
                  }))}
                  min="1"
                  max="50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min Confidence
                </label>
                <input
                  type="number"
                  className="input"
                  value={analysisConfig.min_confidence}
                  onChange={(e) => setAnalysisConfig(prev => ({
                    ...prev,
                    min_confidence: parseFloat(e.target.value)
                  }))}
                  min="0"
                  max="1"
                  step="0.1"
                />
              </div>
            </div>

            <div>
              <LLMSelector
                value={analysisConfig.llm_model}
                onChange={(value) => setAnalysisConfig(prev => ({ ...prev, llm_model: value }))}
                label="LLM Model"
                description="AI model for content analysis"
                showPricing={false}
              />
            </div>

            <button
              onClick={handleStartAnalysis}
              disabled={isAnalyzing}
              className="btn btn-primary w-full flex items-center justify-center"
            >
              {isAnalyzing && startAnalysisMutation.isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start Full Analysis
                </>
              )}
            </button>
          </div>
        </div>

        {/* Headlines Analysis Section */}
        <div className="card">
          <div className="flex items-center mb-4">
            <Zap className="h-6 w-6 text-yellow-600 mr-3" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Headlines Analysis</h2>
              <p className="text-sm text-gray-600">
                Fast analysis using headlines and summaries only
              </p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Positions
                </label>
                <input
                  type="number"
                  className="input"
                  value={headlineConfig.max_positions}
                  onChange={(e) => setHeadlineConfig(prev => ({
                    ...prev,
                    max_positions: parseInt(e.target.value)
                  }))}
                  min="1"
                  max="50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min Confidence
                </label>
                <input
                  type="number"
                  className="input"
                  value={headlineConfig.min_confidence}
                  onChange={(e) => setHeadlineConfig(prev => ({
                    ...prev,
                    min_confidence: parseFloat(e.target.value)
                  }))}
                  min="0"
                  max="1"
                  step="0.1"
                />
              </div>
            </div>

            <div>
              <LLMSelector
                value={headlineConfig.llm_model}
                onChange={(value) => setHeadlineConfig(prev => ({ ...prev, llm_model: value }))}
                label="LLM Model"
                description="AI model for headline analysis"
                showPricing={false}
              />
            </div>

            <button
              onClick={handleStartHeadlineAnalysis}
              disabled={isAnalyzing}
              className="btn btn-secondary w-full flex items-center justify-center"
              title="Quick analysis based on headlines only"
            >
              {isAnalyzing && startHeadlineAnalysisMutation.isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Start Headlines Analysis
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Market Summary */}
      <MarketSummary />

      {/* Recent Results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Positions */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Positions</h2>
          <div className="space-y-4">
            {recentPositions?.map((position) => (
              <PositionCard key={position.id} position={position} />
            ))}
            {!recentPositions?.length && (
              <p className="text-gray-500 text-center py-8">
                No positions yet. Start an analysis to generate recommendations.
              </p>
            )}
          </div>
        </div>

        {/* Activity Log */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Activity Log</h2>
          <ActivityLog sessionId={currentSessionId} />
        </div>
      </div>
    </div>
  )
}