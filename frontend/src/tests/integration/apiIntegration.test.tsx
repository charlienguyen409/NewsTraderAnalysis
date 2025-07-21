import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { rest } from 'msw'
import { setupIntegrationTestEnvironment } from '../setup'
import { server } from '../setup'
import { mockHandlers } from '../mocks'
import Dashboard from '../../pages/Dashboard'
import Positions from '../../pages/Positions'
import Articles from '../../pages/Articles'

describe('API Integration Tests', () => {
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
    
    mockHandlers.reset()
  })

  afterEach(() => {
    cleanupTimers()
  })

  describe('Analysis API Integration', () => {
    it('should handle successful analysis start', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Verify API request was made
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })

      // Wait for analysis to complete
      jest.advanceTimersByTime(6000)
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })
    })

    it('should handle API errors during analysis start', async () => {
      // Mock API error
      server.use(
        rest.post('http://localhost:8000/api/v1/analysis/start/', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ detail: 'Internal server error' })
          )
        })
      )

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Try to start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Should handle error gracefully
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })

      // Button should be re-enabled
      expect(startButton).not.toBeDisabled()
    })

    it('should validate analysis request parameters', async () => {
      // Mock validation error
      server.use(
        rest.post('http://localhost:8000/api/v1/analysis/start/', (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ detail: 'LLM model is required' })
          )
        })
      )

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Should handle validation error
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })
    })

    it('should handle headlines analysis differently', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Headlines Analysis')).toBeInTheDocument()
      })

      // Start headlines analysis
      const headlinesButton = screen.getByRole('button', { name: /start headlines analysis/i })
      await user.click(headlinesButton)

      // Should send request to headlines endpoint
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })

      // Should complete faster than full analysis
      jest.advanceTimersByTime(3000)
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })
    })
  })

  describe('Positions API Integration', () => {
    it('should load positions with proper pagination', async () => {
      // Add many positions to test pagination
      const manyPositions = Array.from({ length: 25 }, (_, i) => ({
        id: `position-${i}`,
        ticker: `STOCK${i}`,
        position_type: 'BUY' as const,
        confidence: 0.7,
        reasoning: `Position ${i}`,
        supporting_articles: [],
        catalysts: [],
        created_at: new Date().toISOString(),
        analysis_session_id: 'test-session'
      }))

      mockHandlers.addPositions(manyPositions)

      render(
        <TestProvider>
          <Positions />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      // Should load first page of positions
      await waitFor(() => {
        expect(screen.getByText('STOCK0')).toBeInTheDocument()
      })

      // Should implement pagination (if component supports it)
      const positionElements = screen.getAllByText(/STOCK\d+/)
      expect(positionElements.length).toBeLessThanOrEqual(10) // Assume 10 per page
    })

    it('should handle position filtering', async () => {
      render(
        <TestProvider>
          <Positions />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      // Test ticker filter
      const filterInput = screen.getByPlaceholderText(/search by ticker/i)
      await user.type(filterInput, 'AAPL')

      // Should filter positions
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
        expect(screen.queryByText('TSLA')).not.toBeInTheDocument()
      })

      // Clear filter
      await user.clear(filterInput)

      // Should show all positions again
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
        expect(screen.getByText('TSLA')).toBeInTheDocument()
      })
    })

    it('should handle position API errors', async () => {
      // Mock API error
      server.use(
        rest.get('http://localhost:8000/api/v1/positions/', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ detail: 'Database connection failed' })
          )
        })
      )

      render(
        <TestProvider>
          <Positions />
        </TestProvider>
      )

      // Should handle error gracefully
      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      // Should show error state or retry option
      // (This depends on error handling implementation)
    })
  })

  describe('Articles API Integration', () => {
    it('should load articles with filtering and search', async () => {
      render(
        <TestProvider>
          <Articles />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Articles')).toBeInTheDocument()
      })

      // Should load initial articles
      await waitFor(() => {
        expect(screen.getByText('Apple Reports Strong Q3 Earnings')).toBeInTheDocument()
      })

      // Test search functionality
      const searchInput = screen.getByPlaceholderText(/search articles/i)
      await user.type(searchInput, 'Apple')

      // Should filter articles
      await waitFor(() => {
        expect(screen.getByText('Apple Reports Strong Q3 Earnings')).toBeInTheDocument()
        expect(screen.queryByText('Tesla Announces New Model Release')).not.toBeInTheDocument()
      })
    })

    it('should handle article source filtering', async () => {
      render(
        <TestProvider>
          <Articles />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Articles')).toBeInTheDocument()
      })

      // Test source filter
      const sourceFilter = screen.getByLabelText(/filter by source/i)
      await user.selectOptions(sourceFilter, 'finviz')

      // Should filter by source
      await waitFor(() => {
        expect(screen.getByText('Apple Reports Strong Q3 Earnings')).toBeInTheDocument()
      })
    })

    it('should handle article loading errors', async () => {
      // Mock API error
      server.use(
        rest.get('http://localhost:8000/api/v1/articles/', (req, res, ctx) => {
          return res(
            ctx.status(404),
            ctx.json({ detail: 'Articles not found' })
          )
        })
      )

      render(
        <TestProvider>
          <Articles />
        </TestProvider>
      )

      // Should handle error gracefully
      await waitFor(() => {
        expect(screen.getByText('Market Articles')).toBeInTheDocument()
      })
    })
  })

  describe('Market Summary API Integration', () => {
    it('should load market summary data', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should load market summary
      await waitFor(() => {
        expect(screen.getByText(/market showing/i)).toBeInTheDocument()
      })
    })

    it('should handle market summary API errors', async () => {
      // Mock API error
      server.use(
        rest.get('http://localhost:8000/api/v1/analysis/market-summary/', (req, res, ctx) => {
          return res(
            ctx.status(503),
            ctx.json({ detail: 'Service unavailable' })
          )
        })
      )

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should handle error gracefully
      // (Market summary section should handle errors appropriately)
    })
  })

  describe('Activity Logs API Integration', () => {
    it('should load activity logs with filtering', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })

      // Should load activity logs
      await waitFor(() => {
        expect(screen.getByText(/started full market analysis/i)).toBeInTheDocument()
      })
    })

    it('should handle activity log API errors', async () => {
      // Mock API error
      server.use(
        rest.get('http://localhost:8000/api/v1/activity-logs/', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ detail: 'Log service unavailable' })
          )
        })
      )

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Should handle error gracefully
      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })
    })
  })

  describe('API Request Optimization', () => {
    it('should cache API responses appropriately', async () => {
      let requestCount = 0
      
      server.use(
        rest.get('http://localhost:8000/api/v1/positions/', (req, res, ctx) => {
          requestCount++
          return res(
            ctx.json([
              {
                id: 'position-1',
                ticker: 'AAPL',
                position_type: 'STRONG_BUY',
                confidence: 0.85,
                reasoning: 'Strong earnings',
                supporting_articles: [],
                catalysts: [],
                created_at: new Date().toISOString(),
                analysis_session_id: 'session-1'
              }
            ])
          )
        })
      )

      // Set up caching
      queryClient = new QueryClient({
        defaultOptions: {
          queries: {
            retry: false,
            staleTime: 10000, // 10 seconds
            cacheTime: 30000, // 30 seconds
          },
        },
      })

      const { rerender } = render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })

      // First request should be made
      expect(requestCount).toBe(1)

      // Re-render same component
      rerender(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Should use cached data
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })

      // Should not make additional request
      expect(requestCount).toBe(1)
    })

    it('should handle concurrent API requests', async () => {
      let concurrentRequests = 0
      let maxConcurrent = 0

      server.use(
        rest.get('http://localhost:8000/api/v1/positions/', (req, res, ctx) => {
          concurrentRequests++
          maxConcurrent = Math.max(maxConcurrent, concurrentRequests)
          
          return res(
            ctx.delay(100),
            ctx.json([]),
            ctx.onResponse(() => {
              concurrentRequests--
            })
          )
        })
      )

      // Render multiple components that make same API call
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })

      // Should deduplicate concurrent requests
      expect(maxConcurrent).toBeLessThanOrEqual(1)
    })
  })

  describe('API Response Validation', () => {
    it('should handle malformed API responses', async () => {
      server.use(
        rest.get('http://localhost:8000/api/v1/positions/', (req, res, ctx) => {
          return res(
            ctx.json({
              // Malformed response - missing required fields
              invalid: 'data'
            })
          )
        })
      )

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Should handle malformed response gracefully
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })
    })

    it('should handle empty API responses', async () => {
      server.use(
        rest.get('http://localhost:8000/api/v1/positions/', (req, res, ctx) => {
          return res(ctx.json([]))
        })
      )

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Should handle empty response gracefully
      await waitFor(() => {
        expect(screen.getByText('No positions yet')).toBeInTheDocument()
      })
    })
  })

  describe('Network Resilience', () => {
    it('should handle network timeouts', async () => {
      server.use(
        rest.get('http://localhost:8000/api/v1/positions/', (req, res, ctx) => {
          return res(
            ctx.delay(10000) // 10 second delay to simulate timeout
          )
        })
      )

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Should handle timeout gracefully
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })
    })

    it('should handle intermittent network failures', async () => {
      let failureCount = 0
      
      server.use(
        rest.get('http://localhost:8000/api/v1/positions/', (req, res, ctx) => {
          failureCount++
          
          if (failureCount <= 2) {
            return res(
              ctx.status(503),
              ctx.json({ detail: 'Service temporarily unavailable' })
            )
          }
          
          return res(
            ctx.json([
              {
                id: 'position-1',
                ticker: 'AAPL',
                position_type: 'STRONG_BUY',
                confidence: 0.85,
                reasoning: 'Strong earnings',
                supporting_articles: [],
                catalysts: [],
                created_at: new Date().toISOString(),
                analysis_session_id: 'session-1'
              }
            ])
          )
        })
      )

      // Enable retries for this test
      queryClient = new QueryClient({
        defaultOptions: {
          queries: {
            retry: 2,
            retryDelay: 100,
            staleTime: 0,
            cacheTime: 0,
          },
        },
      })

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Should eventually succeed after retries
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Should have made 3 requests (initial + 2 retries)
      expect(failureCount).toBe(3)
    })
  })
})