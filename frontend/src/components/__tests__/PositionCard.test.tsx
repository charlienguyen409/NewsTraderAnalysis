import { render, screen } from '@testing-library/react'
import PositionCard from '../PositionCard'
import { Position } from '../../types'

const mockPosition: Position = {
  id: '1',
  ticker: 'AAPL',
  position_type: 'STRONG_BUY',
  confidence: 0.85,
  reasoning: 'Strong earnings beat expectations with positive guidance',
  supporting_articles: ['article1', 'article2'],
  catalysts: [
    {
      type: 'earnings_beat',
      description: 'Q3 earnings exceeded expectations',
      impact: 'positive',
      significance: 'high'
    }
  ],
  created_at: '2023-12-01T10:00:00Z',
  analysis_session_id: 'session1'
}

describe('PositionCard', () => {
  it('renders position information correctly', () => {
    render(<PositionCard position={mockPosition} />)
    
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('STRONG BUY')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText(/Strong earnings beat expectations/)).toBeInTheDocument()
  })

  it('displays catalysts when present', () => {
    render(<PositionCard position={mockPosition} />)
    
    expect(screen.getByText('Key Catalysts:')).toBeInTheDocument()
    expect(screen.getByText('earnings beat')).toBeInTheDocument()
  })

  it('handles position without catalysts', () => {
    const positionWithoutCatalysts = {
      ...mockPosition,
      catalysts: []
    }
    
    render(<PositionCard position={positionWithoutCatalysts} />)
    
    expect(screen.queryByText('Key Catalysts:')).not.toBeInTheDocument()
  })
})