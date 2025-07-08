import axios from 'axios'
import { Article, Position, AnalysisRequest, AnalysisStatus } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Articles API
export const articlesApi = {
  getAll: (params?: {
    skip?: number
    limit?: number
    source?: string
    ticker?: string
    search?: string
  }) => api.get<Article[]>('/articles/', { params }),
  
  getById: (id: string) => api.get<Article>(`/articles/${id}/`),
}

// Positions API
export const positionsApi = {
  getAll: (params?: {
    skip?: number
    limit?: number
    session_id?: string
    ticker?: string
  }) => api.get<Position[]>('/positions/', { params }),
  
  getById: (id: string) => api.get<Position>(`/positions/${id}/`),
  
  getBySession: (sessionId: string) => 
    api.get<Position[]>(`/positions/session/${sessionId}/`),
}

// Analysis API
export const analysisApi = {
  start: (request: AnalysisRequest) => 
    api.post<{ session_id: string; message: string; status: string }>('/analysis/start/', request),
  
  startHeadlines: (request: AnalysisRequest) => 
    api.post<{ session_id: string; message: string; status: string }>('/analysis/headlines/', request),
  
  getStatus: (sessionId: string) => 
    api.get<AnalysisStatus>(`/analysis/status/${sessionId}/`),
  
  getMarketSummary: () => 
    api.get('/analysis/market-summary/').then(response => response.data),
}

export default api