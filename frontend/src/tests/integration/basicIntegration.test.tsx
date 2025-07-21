import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { mockHandlers } from '../mocks'
import PositionCard from '../../components/PositionCard'
import { Position } from '../../types'

describe('Basic Integration Test', () => {
  let queryClient: QueryClient

  const TestProvider = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          staleTime: 0,
          cacheTime: 0,
        },
      },
    })
    mockHandlers.reset()
  })

  it('should render a position card correctly', async () => {
    const mockPosition: Position = {
      id: 'test-1',
      ticker: 'AAPL',
      position_type: 'STRONG_BUY',
      confidence: 0.85,
      reasoning: 'Strong earnings beat expectations',
      supporting_articles: ['article-1'],
      catalysts: [
        {
          type: 'earnings_beat',
          description: 'Q3 earnings exceeded expectations',
          impact: 'positive',
          significance: 'high'
        }
      ],
      created_at: '2023-12-01T10:00:00Z',
      analysis_session_id: 'session-1'
    }

    render(
      <TestProvider>
        <PositionCard position={mockPosition} />
      </TestProvider>
    )

    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('STRONG BUY')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText(/Strong earnings beat expectations/)).toBeInTheDocument()
  })

  it('should handle basic mock data', () => {
    const mockData = mockHandlers.getCurrentData()
    
    expect(mockData.articles).toHaveLength(3)
    expect(mockData.positions).toHaveLength(3)
    expect(mockData.analysisInProgress).toBe(false)
  })
})