export interface Article {
  id: string
  url: string
  title: string
  content?: string
  summary?: string
  source: string
  ticker?: string
  scraped_at: string
  published_at?: string
  is_processed: boolean
  metadata: Record<string, any>
  analyses: Analysis[]
}

export interface Analysis {
  id: string
  article_id: string
  ticker: string
  sentiment_score: number
  confidence: number
  catalysts: Catalyst[]
  reasoning: string
  llm_model: string
  created_at: string
  raw_response?: Record<string, any>
}

export interface Catalyst {
  type: string
  description: string
  impact: 'positive' | 'negative'
  significance: 'low' | 'medium' | 'high'
}

export interface Position {
  id: string
  ticker: string
  position_type: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SHORT' | 'STRONG_SHORT'
  confidence: number
  reasoning: string
  supporting_articles: string[]
  catalysts: Catalyst[]
  created_at: string
  analysis_session_id: string
}

export interface AnalysisRequest {
  max_positions?: number
  min_confidence?: number
  llm_model: string
  sources: string[]
}

export interface AnalysisSession {
  session_id: string
  positions: Position[]
  total_articles_analyzed: number
  analysis_duration: number
  created_at: string
}

export interface AnalysisStatus {
  session_id: string
  status: 'processing' | 'completed' | 'error'
  message?: string
  positions_count: number
  created_at?: string
}