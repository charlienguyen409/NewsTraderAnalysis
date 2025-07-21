import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { setupIntegrationTestEnvironment } from '../setup'
import { MockWebSocket, mockWebSocketServer, mockHandlers } from '../mocks'
import Dashboard from '../../pages/Dashboard'
import ActivityLog from '../../components/ActivityLog'

describe('Real-time Updates Integration Tests', () => {
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
    MockWebSocket.reset()
    mockWebSocketServer.reset()
  })

  afterEach(() => {
    cleanupTimers()
  })

  describe('WebSocket Connection Management', () => {
    it('should establish WebSocket connection on analysis start', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Verify WebSocket connection is established
      await waitFor(() => {
        const instances = MockWebSocket.getAllInstances()
        expect(instances.length).toBe(1)
        expect(instances[0].url).toMatch(/\/ws\/analysis\//)
      })

      // Verify connection status indicator
      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })
    })

    it('should handle connection failures gracefully', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Simulate connection failure
      const ws = MockWebSocket.getLastInstance()
      ws?.simulateError()

      // Should show offline status
      await waitFor(() => {
        expect(screen.getByText('Offline')).toBeInTheDocument()
      })

      // Should fall back to polling
      jest.advanceTimersByTime(5000)
      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })
    })

    it('should reconnect after connection loss', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Verify initial connection
      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Simulate connection loss
      const ws = MockWebSocket.getLastInstance()
      ws?.simulateClose(1006, 'Connection lost')

      // Should show offline status
      await waitFor(() => {
        expect(screen.getByText('Offline')).toBeInTheDocument()
      })

      // Should continue to work with polling fallback
      jest.advanceTimersByTime(5000)
      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })
    })
  })

  describe('Real-time Analysis Updates', () => {
    it('should receive and display real-time analysis progress', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Simulate analysis progress messages
      const sessionId = 'test-session-123'
      mockWebSocketServer.simulateAnalysisProgress(sessionId)

      // Should see starting message
      await waitFor(() => {
        expect(screen.getByText(/starting analysis/i)).toBeInTheDocument()
      })

      // Advance time to see next progress message
      jest.advanceTimersByTime(1000)
      await waitFor(() => {
        expect(screen.getByText(/scraping articles/i)).toBeInTheDocument()
      })

      // Advance time to see processing message
      jest.advanceTimersByTime(1000)
      await waitFor(() => {
        expect(screen.getByText(/processing.*articles/i)).toBeInTheDocument()
      })

      // Advance time to see completion
      jest.advanceTimersByTime(3000)
      await waitFor(() => {
        expect(screen.getByText(/analysis completed/i)).toBeInTheDocument()
      })
    })

    it('should update activity log in real-time', async () => {
      render(
        <TestProvider>
          <ActivityLog sessionId="test-session-123" />
        </TestProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Session Activity')).toBeInTheDocument()
      })

      // Simulate activity log updates
      const logEntry = {
        id: 'log-realtime-1',
        timestamp: new Date().toISOString(),
        level: 'INFO',
        category: 'scraping',
        action: 'page_scraped',
        message: 'Successfully scraped page 1 of 5',
        details: { page: 1, total: 5, articles_found: 25 },
        session_id: 'test-session-123'
      }

      mockWebSocketServer.simulateActivityLogUpdate('test-session-123', logEntry)

      // Should see the new log entry
      await waitFor(() => {
        expect(screen.getByText('Successfully scraped page 1 of 5')).toBeInTheDocument()
      })
    })

    it('should handle different message types correctly', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      const sessionId = 'test-session-123'
      const ws = MockWebSocket.getLastInstance()

      // Test analysis_status message
      ws?.simulateMessage({
        type: 'analysis_status',
        status: 'processing',
        message: 'Analysis is processing...',
        session_id: sessionId
      })

      await waitFor(() => {
        expect(screen.getByText(/analysis is processing/i)).toBeInTheDocument()
      })

      // Test analysis_update message
      ws?.simulateMessage({
        type: 'analysis_update',
        status: 'scraping',
        message: 'Scraping finviz...',
        session_id: sessionId
      })

      await waitFor(() => {
        expect(screen.getByText(/scraping finviz/i)).toBeInTheDocument()
      })

      // Test completion message
      ws?.simulateMessage({
        type: 'analysis_status',
        status: 'completed',
        message: 'Analysis completed successfully',
        session_id: sessionId,
        positions_count: 5
      })

      await waitFor(() => {
        expect(screen.getByText(/analysis completed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Data Synchronization', () => {
    it('should refresh data when analysis completes', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Wait for initial data load
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })

      // Start analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Simulate analysis completion
      const sessionId = 'test-session-123'
      const ws = MockWebSocket.getLastInstance()
      
      ws?.simulateMessage({
        type: 'analysis_status',
        status: 'completed',
        message: 'Analysis completed successfully',
        session_id: sessionId,
        positions_count: 3
      })

      // Should trigger data refresh
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })

      // Should see updated positions
      jest.advanceTimersByTime(1000)
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
      })
    })

    it('should handle multiple concurrent sessions', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      // Start first analysis
      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      const session1 = 'session-1'
      const ws1 = MockWebSocket.getLastInstance()

      // Start second analysis (headlines)
      const headlineButton = screen.getByRole('button', { name: /start headlines analysis/i })
      
      // Wait for first analysis to finish
      ws1?.simulateMessage({
        type: 'analysis_status',
        status: 'completed',
        message: 'Analysis completed',
        session_id: session1
      })

      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })

      // Now start second analysis
      await user.click(headlineButton)

      const session2 = 'session-2'
      const ws2 = MockWebSocket.getLastInstance()

      // Both sessions should be handled correctly
      ws1?.simulateMessage({
        type: 'analysis_update',
        status: 'completed',
        message: 'Full analysis done',
        session_id: session1
      })

      ws2?.simulateMessage({
        type: 'analysis_update',
        status: 'processing',
        message: 'Headlines analysis in progress',
        session_id: session2
      })

      await waitFor(() => {
        expect(screen.getByText(/headlines analysis in progress/i)).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling in Real-time', () => {
    it('should handle WebSocket errors gracefully', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      // Simulate WebSocket error
      const ws = MockWebSocket.getLastInstance()
      ws?.simulateError()

      // Should handle error gracefully
      await waitFor(() => {
        expect(screen.getByText('Offline')).toBeInTheDocument()
      })

      // Should continue to work with polling
      jest.advanceTimersByTime(5000)
      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })
    })

    it('should handle malformed WebSocket messages', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Simulate malformed message
      const ws = MockWebSocket.getLastInstance()
      if (ws && ws.onmessage) {
        const malformedEvent = new MessageEvent('message', {
          data: 'invalid json{'
        })
        ws.onmessage(malformedEvent)
      }

      // Should continue to work normally
      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })
    })

    it('should handle analysis errors via WebSocket', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Simulate analysis error
      const sessionId = 'test-session-123'
      mockWebSocketServer.simulateError(sessionId, 'LLM service unavailable')

      // Should display error message
      await waitFor(() => {
        expect(screen.getByText(/llm service unavailable/i)).toBeInTheDocument()
      })

      // Should stop showing analyzing state
      await waitFor(() => {
        expect(screen.queryByText('Analyzing...')).not.toBeInTheDocument()
      })
    })
  })

  describe('Performance Under Load', () => {
    it('should handle high frequency WebSocket messages', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      const ws = MockWebSocket.getLastInstance()
      const sessionId = 'test-session-123'

      // Simulate high frequency updates
      for (let i = 0; i < 100; i++) {
        ws?.simulateMessage({
          type: 'analysis_update',
          status: 'processing',
          message: `Processing article ${i}`,
          session_id: sessionId
        })
      }

      // Should handle all messages without crashing
      await waitFor(() => {
        expect(screen.getByText(/processing article 99/i)).toBeInTheDocument()
      })
    })

    it('should throttle UI updates appropriately', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      const ws = MockWebSocket.getLastInstance()
      const sessionId = 'test-session-123'

      // Simulate rapid updates
      const startTime = performance.now()
      for (let i = 0; i < 50; i++) {
        ws?.simulateMessage({
          type: 'analysis_update',
          status: 'processing',
          message: `Rapid update ${i}`,
          session_id: sessionId
        })
      }

      // Should complete updates within reasonable time
      await waitFor(() => {
        expect(screen.getByText(/rapid update 49/i)).toBeInTheDocument()
      })

      const endTime = performance.now()
      expect(endTime - startTime).toBeLessThan(1000) // Should complete within 1 second
    })
  })

  describe('Connection Recovery', () => {
    it('should recover from temporary network issues', async () => {
      render(
        <TestProvider>
          <Dashboard />
        </TestProvider>
      )

      const startButton = screen.getByRole('button', { name: /start full analysis/i })
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })

      // Simulate temporary disconnection
      const ws = MockWebSocket.getLastInstance()
      ws?.simulateClose(1006, 'Network error')

      await waitFor(() => {
        expect(screen.getByText('Offline')).toBeInTheDocument()
      })

      // Should continue with polling fallback
      jest.advanceTimersByTime(5000)
      await waitFor(() => {
        expect(screen.getByText('Activity Log')).toBeInTheDocument()
      })

      // Data should still be updated via polling
      jest.advanceTimersByTime(5000)
      await waitFor(() => {
        expect(screen.getByText('Recent Positions')).toBeInTheDocument()
      })
    })
  })
})