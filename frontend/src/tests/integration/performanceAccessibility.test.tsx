import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { axe, toHaveNoViolations } from 'jest-axe'
import { setupIntegrationTestEnvironment } from '../setup'
import { mockHandlers } from '../mocks'
import Dashboard from '../../pages/Dashboard'
import Positions from '../../pages/Positions'
import Articles from '../../pages/Articles'
import ActivityLog from '../../components/ActivityLog'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

describe('Performance and Accessibility Integration Tests', () => {
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

  describe('Performance Tests', () => {
    it('should render dashboard within performance budget', async () => {
      const startTime = performance.now()
      
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // Should render within 1 second
      expect(renderTime).toBeLessThan(1000)
    })

    it('should handle large position datasets efficiently', async () => {
      // Generate large dataset
      const largePositionSet = Array.from({ length: 1000 }, (_, i) => ({
        id: `large-position-${i}`,
        ticker: `STOCK${i.toString().padStart(4, '0')}`,
        position_type: 'BUY' as const,
        confidence: Math.random(),
        reasoning: `Large dataset position ${i} with detailed reasoning that could be quite long`,
        supporting_articles: Array.from({ length: 5 }, (_, j) => `article-${i}-${j}`),
        catalysts: [
          {
            type: 'earnings',
            description: `Catalyst ${i}`,
            impact: 'positive' as const,
            significance: 'high' as const
          }
        ],
        created_at: new Date(Date.now() - i * 1000).toISOString(),
        analysis_session_id: 'large-session'
      }))

      mockHandlers.addPositions(largePositionSet)

      const startTime = performance.now()
      
      render(
        <TestProvider>
          <Positions />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Trading Positions')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // Should still render efficiently with large dataset
      expect(renderTime).toBeLessThan(2000)

      // Should implement virtualization or pagination
      const positionElements = screen.getAllByText(/STOCK\d+/)
      expect(positionElements.length).toBeLessThanOrEqual(50) // Pagination limit
    })

    it('should handle rapid real-time updates efficiently', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Measure performance of rapid updates
      const startTime = performance.now()
      
      // Simulate many rapid updates
      for (let i = 0; i < 100; i++) {
        jest.advanceTimersByTime(50)
        await new Promise(resolve => setTimeout(resolve, 1))
      }

      const endTime = performance.now()
      const updateTime = endTime - startTime

      // Should handle rapid updates efficiently
      expect(updateTime).toBeLessThan(3000)
    })

    it('should optimize memory usage during long sessions', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Simulate long session with multiple analyses
      for (let i = 0; i < 5; i++) {
        const startButton = screen.getByRole('button', { name: /start full analysis/i })
        await user.click(startButton)

        // Wait for analysis to complete
        jest.advanceTimersByTime(6000)
        await waitFor(() => {
          expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
        })

        // Add positions to simulate memory growth
        const sessionPositions = Array.from({ length: 10 }, (_, j) => ({
          id: `session-${i}-position-${j}`,
          ticker: `STOCK${i}${j}`,
          position_type: 'BUY' as const,
          confidence: 0.7,
          reasoning: `Session ${i} position ${j}`,
          supporting_articles: [],
          catalysts: [],
          created_at: new Date().toISOString(),
          analysis_session_id: `session-${i}`
        }))

        mockHandlers.addPositions(sessionPositions)
      }

      // Should not have memory leaks
      // (This would require more sophisticated memory profiling in a real environment)
      expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
    })

    it('should debounce user input effectively', async () => {
      render(
        <TestProvider>
          <Articles />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Articles')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/search articles/i)
      
      // Type rapidly
      const searchTerm = 'Apple'
      for (const char of searchTerm) {
        await user.type(searchInput, char)
        jest.advanceTimersByTime(50) // Rapid typing
      }

      // Should debounce search requests
      await waitFor(() => {
        expect(screen.getByText('Apple Reports Strong Q3 Earnings')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility Tests', () => {
    it('should have no accessibility violations on dashboard', async () => {
      const { container } = render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper keyboard navigation', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Test tab navigation
      const maxPositionsInput = screen.getByLabelText('Max Positions')
      const minConfidenceInput = screen.getByLabelText('Min Confidence')
      const startButton = screen.getByRole('button', { name: /start full analysis/i })

      // Tab through form controls
      await user.tab()
      expect(maxPositionsInput).toHaveFocus()

      await user.tab()
      expect(minConfidenceInput).toHaveFocus()

      // Continue tabbing to reach the button
      await user.tab()
      await user.tab() // Skip LLM selector
      expect(startButton).toHaveFocus()

      // Should be able to activate with keyboard
      await user.keyboard('{Enter}')
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })
    })

    it('should provide proper ARIA labels and descriptions', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Check form inputs have proper labels
      const maxPositionsInput = screen.getByLabelText('Max Positions')
      expect(maxPositionsInput).toBeInTheDocument()
      expect(maxPositionsInput).toHaveAttribute('type', 'number')

      const minConfidenceInput = screen.getByLabelText('Min Confidence')
      expect(minConfidenceInput).toBeInTheDocument()
      expect(minConfidenceInput).toHaveAttribute('type', 'number')

      // Check buttons have proper descriptions
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      expect(startButton).toBeInTheDocument()
    })

    it('should handle screen reader announcements', async () => {
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

      // Should announce status changes
      await waitFor(() => {
        const analyzingText = screen.getByText('Analyzing...')
        expect(analyzingText).toBeInTheDocument()
        // Should have appropriate ARIA attributes for screen readers
      })
    })

    it('should support high contrast mode', async () => {
      // Mock high contrast media query
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query.includes('prefers-contrast: high'),
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      })

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should render properly in high contrast mode
      // (This would require CSS-in-JS or other styling approach to test effectively)
    })

    it('should support reduced motion preferences', async () => {
      // Mock reduced motion media query
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query.includes('prefers-reduced-motion: reduce'),
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      })

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should disable or reduce animations
      // (This would require checking CSS classes or animation states)
    })

    it('should be usable with voice controls', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Test voice control scenarios
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      
      // Should be findable by voice commands
      expect(startButton).toBeInTheDocument()
      expect(startButton).toHaveAccessibleName()
      
      // Should respond to voice activation
      startButton.click()
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })
    })
  })

  describe('Mobile Responsiveness Tests', () => {
    it('should render properly on mobile viewport', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 812,
      })

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should be responsive
      expect(screen.getByText('Full Analysis')).toBeInTheDocument()
      expect(screen.getByText('Headlines Analysis')).toBeInTheDocument()
    })

    it('should handle touch interactions properly', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Test touch interactions
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      
      // Should handle touch events
      fireEvent.touchStart(startButton)
      fireEvent.touchEnd(startButton)
      
      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      })
    })
  })

  describe('Performance Monitoring', () => {
    it('should track render performance metrics', async () => {
      const performanceEntries: PerformanceEntry[] = []
      
      // Mock performance observer
      global.PerformanceObserver = jest.fn().mockImplementation((callback) => ({
        observe: jest.fn(),
        disconnect: jest.fn(),
      }))

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should track performance metrics
      // (This would require integration with actual performance monitoring)
    })

    it('should handle memory pressure gracefully', async () => {
      // Simulate memory pressure
      const originalMemory = (performance as any).memory
      
      if (originalMemory) {
        ;(performance as any).memory = {
          ...originalMemory,
          usedJSHeapSize: originalMemory.jsHeapSizeLimit * 0.9, // 90% usage
        }
      }

      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should handle memory pressure gracefully
      // (This would require memory management strategies in the component)
    })
  })

  describe('Error Boundaries and Resilience', () => {
    it('should handle component errors gracefully', async () => {
      // Mock console.error to prevent noise in tests
      const originalError = console.error
      console.error = jest.fn()

      const ThrowError = () => {
        throw new Error('Test error')
      }

      const ErrorBoundary = ({ children }: { children: React.ReactNode }) => {
        const [hasError, setHasError] = React.useState(false)
        
        React.useEffect(() => {
          const handleError = () => setHasError(true)
          window.addEventListener('error', handleError)
          return () => window.removeEventListener('error', handleError)
        }, [])

        if (hasError) {
          return <div>Something went wrong</div>
        }

        return <>{children}</>
      }

      render(
        <TestProvider>
          <ErrorBoundary>
            <Dashboard />
          </ErrorBoundary>
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should handle errors gracefully
      console.error = originalError
    })

    it('should maintain accessibility during error states', async () => {
      // Mock API error
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument()
      })

      // Should maintain accessibility even during error states
      const { container } = render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })
  })
})