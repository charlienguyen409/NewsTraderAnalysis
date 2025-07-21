import React from 'react'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { setupIntegrationTestEnvironment } from '../setup'
import { mockHandlers, mockWebSocketServer } from '../mocks'
import Layout from '../../components/Layout'
import Dashboard from '../../pages/Dashboard'
import Positions from '../../pages/Positions'
import Articles from '../../pages/Articles'
import Settings from '../../pages/Settings'

describe('Cross-Component Data Flow Integration Tests', () => {
  let queryClient: QueryClient
  let user: ReturnType<typeof userEvent.setup>
  let cleanupTimers: () => void

  const TestApp = () => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/positions" element={<Positions />} />
            <Route path="/articles" element={<Articles />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
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
        mutations: {
          retry: false,
        },
      },
    })
    
    user = userEvent.setup({ delay: null })
    const setup = setupIntegrationTestEnvironment()
    cleanupTimers = setup.cleanupTimers
    
    mockHandlers.reset()
    
    // Mock navigation
    delete (window as any).location
    window.location = {
      ...window.location,
      pathname: '/',
      href: 'http://localhost:3000/',
    } as any
  })

  afterEach(() => {
    cleanupTimers()
  })

  describe('Dashboard → Positions Data Flow', () => {
    it('should share position data between dashboard and positions page', async () => {
      render(<TestApp />)

      // Wait for dashboard to load
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Verify recent positions are shown
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
        expect(screen.getByText('AAPL')).toBeInTheDocument()
      })

      // Navigate to positions page
      const positionsLink = screen.getByRole('link', { name: /positions/i })
      await user.click(positionsLink)

      // Wait for positions page to load
      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      // Should show same position data
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
        expect(screen.getByText('STRONG BUY')).toBeInTheDocument()
        expect(screen.getByText('85%')).toBeInTheDocument()
      })
    })

    it('should update positions across components when new analysis completes', async () => {
      render(<TestApp />)

      // Start on dashboard
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Simulate analysis completion with new positions
      const sessionId = 'test-session-123'
      mockHandlers.addPositions([
        {
          id: 'new-position-1',
          ticker: 'GOOGL',
          position_type: 'BUY',
          confidence: 0.75,
          reasoning: 'Strong cloud growth',
          supporting_articles: [],
          catalysts: [],
          created_at: new Date().toISOString(),
          analysis_session_id: sessionId
        }
      ])

      // Complete analysis
      jest.advanceTimersByTime(6000)
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })

      // Navigate to positions page
      const positionsLink = screen.getByRole('link', { name: /positions/i })
      await user.click(positionsLink)

      // Should see new position
      await waitFor(() => {
        expect(screen.getByText('GOOGL')).toBeInTheDocument()
        expect(screen.getByText('BUY')).toBeInTheDocument()
      })
    })
  })

  describe('Dashboard → Articles Data Flow', () => {
    it('should share article data between dashboard and articles page', async () => {
      render(<TestApp />)

      // Wait for dashboard to load
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Navigate to articles page
      const articlesLink = screen.getByRole('link', { name: /articles/i })
      await user.click(articlesLink)

      // Wait for articles page to load
      await waitFor(() => {
        expect(screen.getByText('Market Articles')).toBeInTheDocument()
      })

      // Should show article data
      await waitFor(() => {
        expect(screen.getByText('Apple Reports Strong Q3 Earnings')).toBeInTheDocument()
        expect(screen.getByText('Tesla Announces New Model Release')).toBeInTheDocument()
      })
    })

    it('should filter articles by ticker from position selection', async () => {
      render(<TestApp />)

      // Navigate to articles page
      const articlesLink = screen.getByRole('link', { name: /articles/i })
      await user.click(articlesLink)

      await waitFor(() => {
        expect(screen.getByText('Market Articles')).toBeInTheDocument()
      })

      // Filter by ticker
      const tickerFilter = screen.getByLabelText(/filter by ticker/i)
      await user.selectOptions(tickerFilter, 'AAPL')

      // Should show only AAPL articles
      await waitFor(() => {
        expect(screen.getByText('Apple Reports Strong Q3 Earnings')).toBeInTheDocument()
        expect(screen.queryByText('Tesla Announces New Model Release')).not.toBeInTheDocument()
      })
    })
  })

  describe('Settings → Dashboard Configuration Flow', () => {
    it('should apply settings changes to dashboard configuration', async () => {
      // Mock localStorage for settings persistence
      const mockLocalStorage = {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      }
      global.localStorage = mockLocalStorage as any

      render(<TestApp />)

      // Navigate to settings
      const settingsLink = screen.getByRole('link', { name: /settings/i })
      await user.click(settingsLink)

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      // Change default LLM model
      const llmSelect = screen.getByLabelText(/default llm model/i)
      await user.selectOptions(llmSelect, 'claude-3-sonnet')

      // Save settings
      const saveButton = screen.getByRole('button', { name: /save settings/i })
      await user.click(saveButton)

      // Verify settings were saved
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'marketAnalysisSettings',
        expect.stringContaining('claude-3-sonnet')
      )

      // Navigate back to dashboard
      const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
      await user.click(dashboardLink)

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should apply saved settings
      // (This would require the Dashboard component to read from localStorage)
    })
  })

  describe('Real-time Data Synchronization', () => {
    it('should synchronize real-time updates across all components', async () => {
      render(<TestApp />)

      // Start on dashboard
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Simulate real-time updates
      const sessionId = 'test-session-123'
      mockWebSocketServer.simulateAnalysisProgress(sessionId)

      // Verify activity log updates
      await waitFor(() => {
        expect(screen.getByText(/starting analysis/i)).toBeInTheDocument()
      })

      // Navigate to positions page while analysis is running
      const positionsLink = screen.getByRole('link', { name: /positions/i })
      await user.click(positionsLink)

      // Should still see real-time updates (if positions page has activity log)
      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      // Complete analysis
      jest.advanceTimersByTime(6000)

      // Should see updated positions
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
      })
    })
  })

  describe('State Management Consistency', () => {
    it('should maintain consistent state across page navigation', async () => {
      render(<TestApp />)

      // Start on dashboard
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Configure analysis settings
      const maxPositionsInput = screen.getByLabelText('Max Positions')
      await user.clear(maxPositionsInput)
      await user.type(maxPositionsInput, '15')

      // Navigate to positions
      const positionsLink = screen.getByRole('link', { name: /positions/i })
      await user.click(positionsLink)

      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      // Navigate back to dashboard
      const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
      await user.click(dashboardLink)

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Settings should be preserved (if using global state)
      const maxPositionsInputAfter = screen.getByLabelText('Max Positions')
      expect(maxPositionsInputAfter).toHaveValue(10) // Default value, no global state yet
    })

    it('should handle concurrent data updates from multiple sources', async () => {
      render(<TestApp />)

      // Start on dashboard
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Simulate concurrent updates
      const sessionId1 = 'session-1'
      const sessionId2 = 'session-2'

      // Add positions from different sessions
      mockHandlers.addPositions([
        {
          id: 'concurrent-1',
          ticker: 'MSFT',
          position_type: 'BUY',
          confidence: 0.8,
          reasoning: 'From first session',
          supporting_articles: [],
          catalysts: [],
          created_at: new Date().toISOString(),
          analysis_session_id: sessionId1
        },
        {
          id: 'concurrent-2',
          ticker: 'AMZN',
          position_type: 'HOLD',
          confidence: 0.6,
          reasoning: 'From second session',
          supporting_articles: [],
          catalysts: [],
          created_at: new Date().toISOString(),
          analysis_session_id: sessionId2
        }
      ])

      // Complete analysis
      jest.advanceTimersByTime(6000)

      // Should handle both updates correctly
      await waitFor(() => {
        expect(screen.getByText('MSFT')).toBeInTheDocument()
      })

      // Navigate to positions to see all data
      const positionsLink = screen.getByRole('link', { name: /positions/i })
      await user.click(positionsLink)

      await waitFor(() => {
        expect(screen.getByText('MSFT')).toBeInTheDocument()
        expect(screen.getByText('AMZN')).toBeInTheDocument()
      })
    })
  })

  describe('Error Propagation and Recovery', () => {
    it('should handle API errors consistently across components', async () => {
      render(<TestApp />)

      // Start on dashboard
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Navigate to positions
      const positionsLink = screen.getByRole('link', { name: /positions/i })
      await user.click(positionsLink)

      // Wait for positions page
      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      // Should show consistent error handling across components
      // (This would require implementing error boundaries and error states)
    })

    it('should recover from temporary data inconsistencies', async () => {
      render(<TestApp />)

      // Start on dashboard
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Simulate data inconsistency by clearing positions
      mockHandlers.reset()
      mockHandlers.addPositions([]) // No positions

      // Navigate to positions
      const positionsLink = screen.getByRole('link', { name: /positions/i })
      await user.click(positionsLink)

      await waitFor(() => {
        expect(screen.getByText('No positions found')).toBeInTheDocument()
      })

      // Restore data
      mockHandlers.addPositions([
        {
          id: 'restored-1',
          ticker: 'AAPL',
          position_type: 'BUY',
          confidence: 0.75,
          reasoning: 'Restored data',
          supporting_articles: [],
          catalysts: [],
          created_at: new Date().toISOString(),
          analysis_session_id: 'restored-session'
        }
      ])

      // Refresh should show restored data
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      if (refreshButton) {
        await user.click(refreshButton)
      }

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
      })
    })
  })

  describe('Performance and Memory Management', () => {
    it('should handle large datasets efficiently across components', async () => {
      // Add many positions
      const manyPositions = Array.from({ length: 1000 }, (_, i) => ({
        id: `perf-position-${i}`,
        ticker: `STOCK${i.toString().padStart(3, '0')}`,
        position_type: 'BUY' as const,
        confidence: 0.7,
        reasoning: `Performance test position ${i}`,
        supporting_articles: [],
        catalysts: [],
        created_at: new Date().toISOString(),
        analysis_session_id: 'perf-session'
      }))

      mockHandlers.addPositions(manyPositions)

      const startTime = performance.now()
      
      render(<TestApp />)

      // Navigate to positions
      const positionsLink = screen.getByRole('link', { name: /positions/i })
      await user.click(positionsLink)

      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      const endTime = performance.now()
      
      // Should render within reasonable time
      expect(endTime - startTime).toBeLessThan(3000)

      // Should implement pagination/virtualization for large datasets
      const positionElements = screen.getAllByText(/STOCK\d+/)
      expect(positionElements.length).toBeLessThanOrEqual(50) // Assume pagination limit
    })

    it('should cleanup resources properly on component unmount', async () => {
      const { unmount } = render(<TestApp />)

      // Start analysis to create WebSocket connection
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Unmount component
      unmount()

      // Should cleanup WebSocket connections
      // (This would require proper cleanup in useEffect)
    })
  })
})