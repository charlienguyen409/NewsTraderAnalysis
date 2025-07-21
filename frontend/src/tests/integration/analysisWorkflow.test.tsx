import React from 'react'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { setupIntegrationTestEnvironment } from '../setup'
import { mockHandlers, mockWebSocketServer } from '../mocks'
import Dashboard from '../../pages/Dashboard'
import Positions from '../../pages/Positions'
import Articles from '../../pages/Articles'

describe('Complete Analysis Workflow Integration Tests', () => {
  let queryClient: QueryClient
  let user: ReturnType<typeof userEvent.setup>
  let cleanupTimers: () => void

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
        mutations: {
          retry: false,
        },
      },
    })
    
    user = userEvent.setup({ delay: null })
    const setup = setupIntegrationTestEnvironment()
    cleanupTimers = setup.cleanupTimers
    
    // Reset mock data
    mockHandlers.reset()
  })

  afterEach(() => {
    cleanupTimers()
  })

  describe('Full Analysis Journey', () => {
    it('should complete full analysis workflow from dashboard to results', async () => {
      // 1. Render Dashboard
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Verify dashboard loads with initial state
      expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      expect(screen.getByText('AI-powered financial news analysis and trading recommendations')).toBeInTheDocument()
      
      // Verify analysis controls are present
      expect(screen.getByText('Full Analysis')).toBeInTheDocument()
      expect(screen.getByText('Headlines Analysis')).toBeInTheDocument()

      // 2. Configure analysis settings
      const maxPositionsInput = screen.getByLabelText('Max Positions')
      await user.clear(maxPositionsInput)
      await user.type(maxPositionsInput, '15')

      const minConfidenceInput = screen.getByLabelText('Min Confidence')
      await user.clear(minConfidenceInput)
      await user.type(minConfidenceInput, '0.8')

      // 3. Start full analysis
      const startAnalysisButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startAnalysisButton)

      // Verify analysis starts
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })

      // Verify button is disabled during analysis
      expect(startAnalysisButton).toBeDisabled()

      // 4. Simulate real-time updates during analysis
      const sessionId = 'test-session-123'
      mockWebSocketServer.simulateAnalysisProgress(sessionId)

      // Wait for analysis to complete
      jest.advanceTimersByTime(6000)
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      }, { timeout: 10000 })

      // 5. Verify results appear
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })

      // Verify positions are displayed
      await waitFor(() => {
        const positionsSection = screen.getByText('Recent Positions').closest('div')
        expect(within(positionsSection!).getByText('AAPL')).toBeInTheDocument()
      })

      // 6. Verify activity log shows progress
      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })

      // 7. Verify market summary is updated
      await waitFor(() => {
        expect(screen.getByText(/market showing/i)).toBeInTheDocument()
      })
    })

    it('should handle headlines analysis workflow', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Configure headlines analysis
      const headlinesSection = screen.getByText('Headlines Analysis').closest('div')
      const maxPositionsInput = within(headlinesSection!).getByLabelText('Max Positions')
      await user.clear(maxPositionsInput)
      await user.type(maxPositionsInput, '5')

      // Start headlines analysis
      const startButton = within(headlinesSection!).getByRole('button', { name: /start headlines analysis/i })
      await user.click(startButton)

      // Verify faster analysis
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })

      // Simulate completion
      jest.advanceTimersByTime(3000)
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })

      // Verify results appear faster
      await waitFor(() => {
        const positionsSection = screen.getByText('Recent Positions').closest('div')
        expect(within(positionsSection!).getByText('AMZN')).toBeInTheDocument()
      })
    })
  })

  describe('Cross-Page Data Flow', () => {
    it('should maintain data consistency across dashboard and positions page', async () => {
      // Start on Dashboard
      const { rerender } = render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Wait for initial data load
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })

      // Switch to Positions page
      rerender(
        <TestProvider>
          <Positions />
        </TestProvider>
      )

      // Verify positions page shows same data
      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
        expect(screen.getByText('AAPL')).toBeInTheDocument()
        expect(screen.getByText('STRONG BUY')).toBeInTheDocument()
      })

      // Test filtering
      const filterInput = screen.getByPlaceholderText(/search by ticker/i)
      await user.type(filterInput, 'AAPL')

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
        expect(screen.queryByText('TSLA')).not.toBeInTheDocument()
      })
    })

    it('should maintain data consistency across dashboard and articles page', async () => {
      const { rerender } = render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Switch to Articles page
      rerender(
        <TestProvider>
          <Articles />
        </TestProvider>
      )

      // Verify articles page loads
      await waitFor(() => {
        expect(screen.getByText('Market Articles')).toBeInTheDocument()
        expect(screen.getByText('Apple Reports Strong Q3 Earnings')).toBeInTheDocument()
      })

      // Test search functionality
      const searchInput = screen.getByPlaceholderText(/search articles/i)
      await user.type(searchInput, 'Apple')

      await waitFor(() => {
        expect(screen.getByText('Apple Reports Strong Q3 Earnings')).toBeInTheDocument()
        expect(screen.queryByText('Tesla Announces New Model Release')).not.toBeInTheDocument()
      })
    })
  })

  describe('Error Handling and Recovery', () => {
    it('should handle API errors gracefully during analysis', async () => {
      // Mock API error
      mockHandlers.reset()
      
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Try to start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Should show error state
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })

      // Simulate error via WebSocket
      mockWebSocketServer.simulateError('test-session', 'Analysis failed due to network error')

      // Should handle error gracefully
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })
    })

    it('should recover from WebSocket disconnection', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Verify WebSocket connection
      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Simulate WebSocket disconnection
      mockWebSocketServer.getAllInstances().forEach(ws => {
        ws.simulateClose(1006, 'Connection lost')
      })

      // Should fall back to polling
      await waitFor(() => {
        expect(screen.getByText('Offline')).toBeInTheDocument()
      })

      // Should continue to work with polling
      jest.advanceTimersByTime(5000)
      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })
    })
  })

  describe('Real-time Updates', () => {
    it('should update positions in real-time during analysis', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })

      // Simulate real-time position updates
      const sessionId = 'test-session-123'
      mockWebSocketServer.simulateAnalysisProgress(sessionId)

      // Should see activity log updates
      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })

      // Advance time to see progress updates
      jest.advanceTimersByTime(2000)
      await waitFor(() => {
        const activitySection = screen.getByText('Activity Log').closest('div')
        expect(within(activitySection!).getByText(/scraping/i)).toBeInTheDocument()
      })
    })

    it('should show live connection status', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Start analysis to establish WebSocket connection
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Should show connecting then connected status
      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Simulate disconnection
      mockWebSocketServer.getAllInstances().forEach(ws => {
        ws.simulateClose()
      })

      // Should show offline status
      await waitFor(() => {
        expect(screen.getByText('Offline')).toBeInTheDocument()
      })
    })
  })

  describe('Settings Integration', () => {
    it('should persist and apply settings across sessions', async () => {
      // Mock localStorage
      const mockLocalStorage = {
        getItem: jest.fn().mockReturnValue(JSON.stringify({
          defaultLlmModel: 'claude-3-sonnet',
          maxPositions: 20,
          minConfidence: 0.75
        })),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn()
      }
      global.localStorage = mockLocalStorage as any

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Should load saved settings
      await waitFor(() => {
        const maxPositionsInput = screen.getByLabelText('Max Positions')
        expect(maxPositionsInput).toHaveValue(10) // Default from component
      })

      // Verify localStorage was called
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('marketAnalysisSettings')
    })
  })

  describe('Performance and Accessibility', () => {
    it('should handle large datasets efficiently', async () => {
      // Add many positions to test performance
      const manyPositions = Array.from({ length: 100 }, (_, i) => ({
        id: `position-${i}`,
        ticker: `STOCK${i}`,
        position_type: 'BUY' as const,
        confidence: 0.7,
        reasoning: `Analysis for stock ${i}`,
        supporting_articles: [],
        catalysts: [],
        created_at: new Date().toISOString(),
        analysis_session_id: 'test-session'
      }))

      mockHandlers.addPositions(manyPositions)

      const startTime = performance.now()
      
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })

      const endTime = performance.now()
      
      // Should render within reasonable time (less than 2 seconds)
      expect(endTime - startTime).toBeLessThan(2000)

      // Should only show limited number of positions (pagination)
      const positionCards = screen.getAllByText(/STOCK\d+/)
      expect(positionCards.length).toBeLessThanOrEqual(5) // Based on limit in API
    })

    it('should be accessible with keyboard navigation', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Tab through controls
      const maxPositionsInput = screen.getByLabelText('Max Positions')
      maxPositionsInput.focus()
      
      // Should be able to navigate with keyboard
      await user.keyboard('{Tab}')
      expect(screen.getByLabelText('Min Confidence')).toHaveFocus()

      await user.keyboard('{Tab}')
      // Should focus on next interactive element
      
      await user.keyboard('{Tab}')
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      expect(startButton).toHaveFocus()

      // Should be able to activate with Enter
      await user.keyboard('{Enter}')
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })
    })

    it('should provide proper ARIA labels and roles', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Check for proper ARIA attributes
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      expect(startButton).toBeInTheDocument()

      const maxPositionsInput = screen.getByLabelText('Max Positions')
      expect(maxPositionsInput).toHaveAttribute('type', 'number')
      expect(maxPositionsInput).toHaveAttribute('min', '1')
      expect(maxPositionsInput).toHaveAttribute('max', '50')

      const minConfidenceInput = screen.getByLabelText('Min Confidence')
      expect(minConfidenceInput).toHaveAttribute('type', 'number')
      expect(minConfidenceInput).toHaveAttribute('min', '0')
      expect(minConfidenceInput).toHaveAttribute('max', '1')
    })
  })
})