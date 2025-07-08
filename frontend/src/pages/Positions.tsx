import { useState } from 'react'
import { useQuery } from 'react-query'
import { Filter, TrendingUp, TrendingDown } from 'lucide-react'
import { positionsApi } from '../lib/api'
import PositionCard from '../components/PositionCard'

export default function Positions() {
  const [tickerFilter, setTickerFilter] = useState('')
  const [sessionFilter, setSessionFilter] = useState('')

  const { data: positions, isLoading, error } = useQuery(
    ['positions', tickerFilter, sessionFilter],
    () => positionsApi.getAll({
      ticker: tickerFilter || undefined,
      session_id: sessionFilter || undefined,
      limit: 100
    }),
    { select: data => data.data }
  )

  const bullishPositions = positions?.filter(p => 
    p.position_type === 'BUY' || p.position_type === 'STRONG_BUY'
  ) || []

  const bearishPositions = positions?.filter(p => 
    p.position_type === 'SHORT' || p.position_type === 'STRONG_SHORT'
  ) || []

  const stats = {
    total: positions?.length || 0,
    bullish: bullishPositions.length,
    bearish: bearishPositions.length,
    avgConfidence: positions?.length 
      ? positions.reduce((sum, p) => sum + p.confidence, 0) / positions.length 
      : 0
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Trading Positions</h1>
        <p className="mt-2 text-gray-600">
          AI-generated trading recommendations with confidence scores
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
          <div className="text-sm text-gray-600">Total Positions</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-success-600">{stats.bullish}</div>
          <div className="text-sm text-gray-600 flex items-center justify-center">
            <TrendingUp className="h-4 w-4 mr-1" />
            Bullish
          </div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-danger-600">{stats.bearish}</div>
          <div className="text-sm text-gray-600 flex items-center justify-center">
            <TrendingDown className="h-4 w-4 mr-1" />
            Bearish
          </div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-gray-900">
            {Math.round(stats.avgConfidence * 100)}%
          </div>
          <div className="text-sm text-gray-600">Avg Confidence</div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Filter by ticker..."
            className="input"
            value={tickerFilter}
            onChange={(e) => setTickerFilter(e.target.value)}
          />

          <input
            type="text"
            placeholder="Filter by session ID..."
            className="input"
            value={sessionFilter}
            onChange={(e) => setSessionFilter(e.target.value)}
          />

          <button
            onClick={() => {
              setTickerFilter('')
              setSessionFilter('')
            }}
            className="btn btn-secondary flex items-center justify-center"
          >
            <Filter className="h-4 w-4 mr-2" />
            Clear Filters
          </button>
        </div>
      </div>

      {/* Positions List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading positions...</p>
          </div>
        ) : error ? (
          <div className="card text-center py-8">
            <p className="text-red-600">Error loading positions</p>
          </div>
        ) : positions?.length === 0 ? (
          <div className="card text-center py-8">
            <p className="text-gray-500">
              No positions found. Start an analysis to generate recommendations.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {positions?.map((position) => (
              <PositionCard key={position.id} position={position} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}