/**
 * Test data generators and fixtures for E2E tests
 */

export interface TestArticle {
  id: string;
  title: string;
  content: string;
  url: string;
  source: string;
  ticker?: string;
  published_at: string;
  scraped_at: string;
  is_processed: boolean;
  analyses?: TestAnalysis[];
}

export interface TestAnalysis {
  id: string;
  sentiment_score: number;
  confidence: number;
  ticker: string;
  reasoning: string;
  catalysts: TestCatalyst[];
  llm_model: string;
  created_at: string;
}

export interface TestCatalyst {
  type: string;
  description: string;
  impact: 'positive' | 'negative';
  significance: 'high' | 'medium' | 'low';
}

export interface TestPosition {
  id: string;
  ticker: string;
  recommendation: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';
  confidence: number;
  sentiment_score: number;
  reasoning: string;
  catalysts: TestCatalyst[];
  session_id: string;
  created_at: string;
}

/**
 * Generate mock article data for testing
 */
export function generateTestArticle(overrides: Partial<TestArticle> = {}): TestArticle {
  const baseArticle: TestArticle = {
    id: `test-article-${Date.now()}`,
    title: 'Apple Reports Strong Q4 Earnings with iPhone Revenue Growth',
    content: 'Apple Inc. reported strong fourth-quarter earnings with significant growth in iPhone revenue, beating analyst expectations...',
    url: 'https://example.com/apple-earnings',
    source: 'finviz',
    ticker: 'AAPL',
    published_at: new Date().toISOString(),
    scraped_at: new Date().toISOString(),
    is_processed: true,
    analyses: [generateTestAnalysis()]
  };

  return { ...baseArticle, ...overrides };
}

/**
 * Generate mock analysis data for testing
 */
export function generateTestAnalysis(overrides: Partial<TestAnalysis> = {}): TestAnalysis {
  const baseAnalysis: TestAnalysis = {
    id: `test-analysis-${Date.now()}`,
    sentiment_score: 0.75,
    confidence: 0.85,
    ticker: 'AAPL',
    reasoning: 'Strong earnings beat with positive guidance for next quarter. iPhone sales exceeded expectations despite market headwinds.',
    catalysts: [
      {
        type: 'earnings_beat',
        description: 'Q4 earnings exceeded analyst expectations by 12%',
        impact: 'positive',
        significance: 'high'
      },
      {
        type: 'guidance_upgrade',
        description: 'Management raised guidance for next quarter',
        impact: 'positive',
        significance: 'medium'
      }
    ],
    llm_model: 'gpt-4',
    created_at: new Date().toISOString()
  };

  return { ...baseAnalysis, ...overrides };
}

/**
 * Generate mock position data for testing
 */
export function generateTestPosition(overrides: Partial<TestPosition> = {}): TestPosition {
  const basePosition: TestPosition = {
    id: `test-position-${Date.now()}`,
    ticker: 'AAPL',
    recommendation: 'BUY',
    confidence: 0.85,
    sentiment_score: 0.75,
    reasoning: 'Strong fundamentals with positive catalysts outweighing market concerns',
    catalysts: [
      {
        type: 'earnings_beat',
        description: 'Q4 earnings exceeded expectations',
        impact: 'positive',
        significance: 'high'
      }
    ],
    session_id: `test-session-${Date.now()}`,
    created_at: new Date().toISOString()
  };

  return { ...basePosition, ...overrides };
}

/**
 * Generate multiple test articles for list testing
 */
export function generateTestArticles(count: number = 5): TestArticle[] {
  const tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'];
  const sources = ['finviz', 'biztoc'];
  const titles = [
    'Strong Q4 Earnings Beat Expectations',
    'New Product Launch Drives Growth',
    'Market Volatility Impacts Stock Price',
    'CEO Comments on Future Strategy',
    'Regulatory Concerns Affect Outlook'
  ];

  return Array.from({ length: count }, (_, index) => {
    const ticker = tickers[index % tickers.length];
    const source = sources[index % sources.length];
    const title = `${ticker} ${titles[index % titles.length]}`;
    
    return generateTestArticle({
      id: `test-article-${index}`,
      title,
      ticker,
      source,
      url: `https://example.com/${ticker.toLowerCase()}-news-${index}`,
      published_at: new Date(Date.now() - index * 3600000).toISOString() // Stagger by hours
    });
  });
}

/**
 * Generate test analysis request data
 */
export function generateAnalysisRequest(overrides: any = {}) {
  return {
    max_positions: 10,
    min_confidence: 0.7,
    llm_model: 'gpt-4',
    sources: ['finviz', 'biztoc'],
    ...overrides
  };
}

/**
 * Generate test market summary data
 */
export function generateMarketSummary() {
  return {
    total_articles: 145,
    processed_articles: 132,
    total_positions: 23,
    bullish_positions: 14,
    bearish_positions: 9,
    avg_confidence: 0.78,
    top_tickers: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'],
    last_analysis: new Date().toISOString()
  };
}

/**
 * Generate test activity log entries
 */
export function generateActivityLogEntries(count: number = 10) {
  const categories = ['scraping', 'llm', 'analysis', 'database', 'processing'];
  const actions = ['start', 'complete', 'error', 'update', 'cache_hit'];
  const levels = ['INFO', 'WARNING', 'ERROR'];

  return Array.from({ length: count }, (_, index) => {
    const category = categories[index % categories.length];
    const action = actions[index % actions.length];
    const level = levels[index % levels.length];
    
    return {
      id: `test-log-${index}`,
      timestamp: new Date(Date.now() - index * 60000).toISOString(),
      level,
      category,
      action,
      message: `Test ${action} message for ${category}`,
      details: {
        test_data: true,
        index,
        category,
        action
      },
      session_id: `test-session-${Math.floor(index / 3)}`
    };
  });
}

/**
 * Common test selectors
 */
export const TEST_SELECTORS = {
  // Dashboard
  startAnalysisButton: '[data-testid="start-analysis"]',
  startHeadlinesButton: '[data-testid="start-headlines"]',
  maxPositionsInput: '[data-testid="max-positions"]',
  minConfidenceInput: '[data-testid="min-confidence"]',
  llmModelSelect: '[data-testid="llm-model"]',
  
  // Articles
  articleCard: '[data-testid="article-card"]',
  articleTitle: '[data-testid="article-title"]',
  articleSearch: '[data-testid="article-search"]',
  sourceFilter: '[data-testid="source-filter"]',
  tickerFilter: '[data-testid="ticker-filter"]',
  clearFiltersButton: '[data-testid="clear-filters"]',
  
  // Positions
  positionCard: '[data-testid="position-card"]',
  positionTicker: '[data-testid="position-ticker"]',
  positionRecommendation: '[data-testid="position-recommendation"]',
  
  // Activity Log
  activityLog: '[data-testid="activity-log"]',
  connectionStatus: '[data-testid="connection-status"]',
  logEntry: '[data-testid="log-entry"]',
  
  // Navigation
  navDashboard: '[data-testid="nav-dashboard"]',
  navArticles: '[data-testid="nav-articles"]',
  navPositions: '[data-testid="nav-positions"]',
  navSettings: '[data-testid="nav-settings"]',
  
  // Common
  loading: '[data-testid="loading"]',
  error: '[data-testid="error"]',
  success: '[data-testid="success"]'
};

/**
 * Test environment configuration
 */
export const TEST_CONFIG = {
  API_URL: process.env.API_URL || 'http://localhost:8000',
  FRONTEND_URL: process.env.FRONTEND_URL || 'http://localhost:5173',
  WEBSOCKET_URL: process.env.WEBSOCKET_URL || 'ws://localhost:8000/ws',
  DEFAULT_TIMEOUT: 30000,
  ANALYSIS_TIMEOUT: 120000,
  WEBSOCKET_TIMEOUT: 10000
};