import { rest } from 'msw'
import { Article, Position, AnalysisRequest, AnalysisStatus, AnalysisSession } from '../../types'

const API_BASE_URL = 'http://localhost:8000/api/v1'

// Mock data generators
const createMockArticle = (overrides?: Partial<Article>): Article => ({
  id: `article-${Math.random().toString(36).substr(2, 9)}`,
  url: 'https://example.com/article',
  title: 'Mock Article Title',
  content: 'Mock article content describing market events...',
  summary: 'Brief summary of the article',
  source: 'finviz',
  ticker: 'AAPL',
  scraped_at: new Date().toISOString(),
  published_at: new Date().toISOString(),
  is_processed: true,
  metadata: { section: 'news' },
  analyses: [],
  ...overrides
})

const createMockPosition = (overrides?: Partial<Position>): Position => ({
  id: `position-${Math.random().toString(36).substr(2, 9)}`,
  ticker: 'AAPL',
  position_type: 'STRONG_BUY',
  confidence: 0.85,
  reasoning: 'Strong earnings beat expectations with positive guidance',
  supporting_articles: ['article-1', 'article-2'],
  catalysts: [
    {
      type: 'earnings_beat',
      description: 'Q3 earnings exceeded expectations',
      impact: 'positive',
      significance: 'high'
    }
  ],
  created_at: new Date().toISOString(),
  analysis_session_id: 'session-123',
  ...overrides
})

const createMockAnalysisStatus = (overrides?: Partial<AnalysisStatus>): AnalysisStatus => ({
  session_id: 'session-123',
  status: 'processing',
  message: 'Analysis in progress...',
  positions_count: 0,
  created_at: new Date().toISOString(),
  ...overrides
})

// Mock data stores
let mockArticles: Article[] = [
  createMockArticle({ 
    id: 'article-1',
    title: 'Apple Reports Strong Q3 Earnings',
    ticker: 'AAPL',
    source: 'finviz'
  }),
  createMockArticle({ 
    id: 'article-2',
    title: 'Tesla Announces New Model Release',
    ticker: 'TSLA',
    source: 'biztoc'
  }),
  createMockArticle({ 
    id: 'article-3',
    title: 'Microsoft Cloud Revenue Surges',
    ticker: 'MSFT',
    source: 'finviz'
  })
]

let mockPositions: Position[] = [
  createMockPosition({ 
    id: 'position-1',
    ticker: 'AAPL',
    position_type: 'STRONG_BUY',
    confidence: 0.85
  }),
  createMockPosition({ 
    id: 'position-2',
    ticker: 'TSLA',
    position_type: 'BUY',
    confidence: 0.72
  }),
  createMockPosition({ 
    id: 'position-3',
    ticker: 'MSFT',
    position_type: 'HOLD',
    confidence: 0.65
  })
]

let analysisInProgress = false
let currentSessionId = 'session-123'

export const handlers = [
  // Articles endpoints
  rest.get(`${API_BASE_URL}/articles/`, (req, res, ctx) => {
    const url = new URL(req.url)
    const skip = parseInt(url.searchParams.get('skip') || '0')
    const limit = parseInt(url.searchParams.get('limit') || '10')
    const source = url.searchParams.get('source')
    const ticker = url.searchParams.get('ticker')
    const search = url.searchParams.get('search')

    let filteredArticles = mockArticles

    if (source) {
      filteredArticles = filteredArticles.filter(article => article.source === source)
    }

    if (ticker) {
      filteredArticles = filteredArticles.filter(article => article.ticker === ticker)
    }

    if (search) {
      filteredArticles = filteredArticles.filter(article => 
        article.title.toLowerCase().includes(search.toLowerCase()) ||
        article.content?.toLowerCase().includes(search.toLowerCase())
      )
    }

    const paginatedArticles = filteredArticles.slice(skip, skip + limit)

    return res(
      ctx.delay(Math.random() * 500 + 200), // Realistic delay
      ctx.json(paginatedArticles)
    )
  }),

  rest.get(`${API_BASE_URL}/articles/:id/`, (req, res, ctx) => {
    const { id } = req.params
    const article = mockArticles.find(a => a.id === id)

    if (!article) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Article not found' })
      )
    }

    return res(
      ctx.delay(200),
      ctx.json(article)
    )
  }),

  // Positions endpoints
  rest.get(`${API_BASE_URL}/positions/`, (req, res, ctx) => {
    const url = new URL(req.url)
    const skip = parseInt(url.searchParams.get('skip') || '0')
    const limit = parseInt(url.searchParams.get('limit') || '10')
    const session_id = url.searchParams.get('session_id')
    const ticker = url.searchParams.get('ticker')

    let filteredPositions = mockPositions

    if (session_id) {
      filteredPositions = filteredPositions.filter(position => position.analysis_session_id === session_id)
    }

    if (ticker) {
      filteredPositions = filteredPositions.filter(position => position.ticker === ticker)
    }

    const paginatedPositions = filteredPositions.slice(skip, skip + limit)

    return res(
      ctx.delay(Math.random() * 500 + 200),
      ctx.json(paginatedPositions)
    )
  }),

  rest.get(`${API_BASE_URL}/positions/:id/`, (req, res, ctx) => {
    const { id } = req.params
    const position = mockPositions.find(p => p.id === id)

    if (!position) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Position not found' })
      )
    }

    return res(
      ctx.delay(200),
      ctx.json(position)
    )
  }),

  rest.get(`${API_BASE_URL}/positions/session/:sessionId/`, (req, res, ctx) => {
    const { sessionId } = req.params
    const sessionPositions = mockPositions.filter(p => p.analysis_session_id === sessionId)

    return res(
      ctx.delay(300),
      ctx.json(sessionPositions)
    )
  }),

  // Analysis endpoints
  rest.post(`${API_BASE_URL}/analysis/start/`, (req, res, ctx) => {
    const request = req.body as AnalysisRequest
    
    if (!request.llm_model) {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'LLM model is required' })
      )
    }

    analysisInProgress = true
    const sessionId = `session-${Date.now()}`
    currentSessionId = sessionId

    // Simulate analysis completion after delay
    setTimeout(() => {
      analysisInProgress = false
      // Add new positions to mock data
      mockPositions.push(
        createMockPosition({ 
          analysis_session_id: sessionId,
          ticker: 'NVDA',
          position_type: 'BUY',
          confidence: 0.78
        })
      )
    }, 5000)

    return res(
      ctx.delay(1000),
      ctx.json({
        session_id: sessionId,
        message: 'Analysis started successfully',
        status: 'processing'
      })
    )
  }),

  rest.post(`${API_BASE_URL}/analysis/headlines/`, (req, res, ctx) => {
    const request = req.body as AnalysisRequest
    
    if (!request.llm_model) {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'LLM model is required' })
      )
    }

    analysisInProgress = true
    const sessionId = `headlines-session-${Date.now()}`
    currentSessionId = sessionId

    // Simulate faster headline analysis
    setTimeout(() => {
      analysisInProgress = false
      mockPositions.push(
        createMockPosition({ 
          analysis_session_id: sessionId,
          ticker: 'AMZN',
          position_type: 'STRONG_BUY',
          confidence: 0.82
        })
      )
    }, 2000)

    return res(
      ctx.delay(500),
      ctx.json({
        session_id: sessionId,
        message: 'Headlines analysis started successfully',
        status: 'processing'
      })
    )
  }),

  rest.get(`${API_BASE_URL}/analysis/status/:sessionId/`, (req, res, ctx) => {
    const { sessionId } = req.params
    const sessionPositions = mockPositions.filter(p => p.analysis_session_id === sessionId)
    
    let status: AnalysisStatus['status'] = 'completed'
    let message = 'Analysis completed successfully'
    
    if (sessionId === currentSessionId && analysisInProgress) {
      status = 'processing'
      message = 'Analysis in progress...'
    }

    return res(
      ctx.delay(100),
      ctx.json(createMockAnalysisStatus({
        session_id: sessionId as string,
        status,
        message,
        positions_count: sessionPositions.length
      }))
    )
  }),

  rest.get(`${API_BASE_URL}/analysis/market-summary/`, (req, res, ctx) => {
    const mockMarketSummary = {
      overview: 'Market showing strong bullish sentiment with tech stocks leading gains.',
      sentiment: 'bullish',
      key_trends: [
        'AI and machine learning stocks continue to outperform',
        'Energy sector showing signs of recovery',
        'Healthcare stocks remain stable'
      ],
      risk_factors: [
        'Inflation concerns persist',
        'Geopolitical tensions may impact markets'
      ],
      total_positions: mockPositions.length,
      last_updated: new Date().toISOString()
    }

    return res(
      ctx.delay(800),
      ctx.json(mockMarketSummary)
    )
  }),

  // Activity logs endpoints
  rest.get(`${API_BASE_URL}/activity-logs/`, (req, res, ctx) => {
    const url = new URL(req.url)
    const limit = parseInt(url.searchParams.get('limit') || '100')
    const level = url.searchParams.get('level')
    const category = url.searchParams.get('category')
    const session_id = url.searchParams.get('session_id')

    const mockLogs = [
      {
        id: 'log-1',
        timestamp: new Date().toISOString(),
        level: 'INFO',
        category: 'analysis',
        action: 'analysis_started',
        message: 'Started full market analysis',
        details: { max_positions: 10, min_confidence: 0.7 },
        session_id: session_id || currentSessionId
      },
      {
        id: 'log-2',
        timestamp: new Date(Date.now() - 30000).toISOString(),
        level: 'INFO',
        category: 'scraping',
        action: 'scraping_started',
        message: 'Started scraping from finviz',
        details: { source: 'finviz', expected_articles: 50 },
        session_id: session_id || currentSessionId
      },
      {
        id: 'log-3',
        timestamp: new Date(Date.now() - 45000).toISOString(),
        level: 'WARNING',
        category: 'llm',
        action: 'rate_limit_hit',
        message: 'LLM rate limit reached, retrying in 5 seconds',
        details: { retry_count: 1, model: 'gpt-4' },
        session_id: session_id || currentSessionId
      }
    ]

    let filteredLogs = mockLogs

    if (level) {
      filteredLogs = filteredLogs.filter(log => log.level === level)
    }

    if (category) {
      filteredLogs = filteredLogs.filter(log => log.category === category)
    }

    if (session_id) {
      filteredLogs = filteredLogs.filter(log => log.session_id === session_id)
    }

    const paginatedLogs = filteredLogs.slice(0, limit)

    return res(
      ctx.delay(300),
      ctx.json(paginatedLogs)
    )
  }),

  rest.get(`${API_BASE_URL}/activity-logs/summary/`, (req, res, ctx) => {
    const mockSummary = {
      total_errors: 2,
      errors_by_category: {
        'scraping': 1,
        'llm': 1
      },
      time_window_hours: 24
    }

    return res(
      ctx.delay(400),
      ctx.json(mockSummary)
    )
  })
]

// Helper functions for tests
export const mockHandlers = {
  // Reset mock data
  reset: () => {
    mockArticles = [
      createMockArticle({ 
        id: 'article-1',
        title: 'Apple Reports Strong Q3 Earnings',
        ticker: 'AAPL',
        source: 'finviz'
      }),
      createMockArticle({ 
        id: 'article-2',
        title: 'Tesla Announces New Model Release',
        ticker: 'TSLA',
        source: 'biztoc'
      }),
      createMockArticle({ 
        id: 'article-3',
        title: 'Microsoft Cloud Revenue Surges',
        ticker: 'MSFT',
        source: 'finviz'
      })
    ]

    mockPositions = [
      createMockPosition({ 
        id: 'position-1',
        ticker: 'AAPL',
        position_type: 'STRONG_BUY',
        confidence: 0.85
      }),
      createMockPosition({ 
        id: 'position-2',
        ticker: 'TSLA',
        position_type: 'BUY',
        confidence: 0.72
      }),
      createMockPosition({ 
        id: 'position-3',
        ticker: 'MSFT',
        position_type: 'HOLD',
        confidence: 0.65
      })
    ]

    analysisInProgress = false
    currentSessionId = 'session-123'
  },

  // Add custom articles
  addArticles: (articles: Article[]) => {
    mockArticles.push(...articles)
  },

  // Add custom positions
  addPositions: (positions: Position[]) => {
    mockPositions.push(...positions)
  },

  // Set analysis state
  setAnalysisState: (inProgress: boolean, sessionId?: string) => {
    analysisInProgress = inProgress
    if (sessionId) {
      currentSessionId = sessionId
    }
  },

  // Get current mock data
  getCurrentData: () => ({
    articles: mockArticles,
    positions: mockPositions,
    analysisInProgress,
    currentSessionId
  })
}