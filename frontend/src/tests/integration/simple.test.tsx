import React from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import PositionCard from '../../components/PositionCard'
import { Position } from '../../types'

describe('Simple Integration Test', () => {
  it('should render a position card', () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })

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
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <PositionCard position={mockPosition} />
        </BrowserRouter>
      </QueryClientProvider>
    )

    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('STRONG BUY')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
  })
})