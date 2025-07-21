import { beforeAll, afterEach, afterAll } from '@jest/globals'
import { setupServer } from 'msw/node'
import { handlers } from './mocks/handlers'
import { setupWebSocketMocks, cleanupWebSocketMocks } from './mocks/websocket'
import '@testing-library/jest-dom'
import 'whatwg-fetch'

// Setup MSW server
export const server = setupServer(...handlers)

// Setup for all tests
beforeAll(() => {
  // Start MSW server
  server.listen({
    onUnhandledRequest: 'warn',
  })
  
  // Setup WebSocket mocks
  setupWebSocketMocks()
  
  // Mock localStorage
  const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  }
  global.localStorage = localStorageMock as any
  
  // Mock sessionStorage
  const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  }
  global.sessionStorage = sessionStorageMock as any
  
  // Mock window.location
  delete (window as any).location
  window.location = {
    ...window.location,
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000',
    pathname: '/',
    search: '',
    hash: '',
  } as any
  
  // Mock environment variables
  process.env.VITE_API_URL = 'http://localhost:8000'
  process.env.VITE_WS_URL = 'ws://localhost:8000/ws'
  
  // Mock console methods to reduce noise in tests
  global.console = {
    ...console,
    warn: jest.fn(),
    error: jest.fn(),
  }
})

// Reset handlers after each test
afterEach(() => {
  server.resetHandlers()
  cleanupWebSocketMocks()
  setupWebSocketMocks()
  
  // Clear localStorage mock
  ;(global.localStorage.getItem as jest.Mock).mockClear()
  ;(global.localStorage.setItem as jest.Mock).mockClear()
  ;(global.localStorage.removeItem as jest.Mock).mockClear()
  ;(global.localStorage.clear as jest.Mock).mockClear()
  
  // Clear sessionStorage mock
  ;(global.sessionStorage.getItem as jest.Mock).mockClear()
  ;(global.sessionStorage.setItem as jest.Mock).mockClear()
  ;(global.sessionStorage.removeItem as jest.Mock).mockClear()
  ;(global.sessionStorage.clear as jest.Mock).mockClear()
})

// Cleanup after all tests
afterAll(() => {
  server.close()
  cleanupWebSocketMocks()
})

// Helper function to wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0))

// Helper to advance timers and wait for async operations
export const advanceTimersAndWait = async (ms: number) => {
  jest.advanceTimersByTime(ms)
  await waitForAsync()
}

// Common test utilities
export const createMockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn()
  mockIntersectionObserver.mockReturnValue({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  })
  window.IntersectionObserver = mockIntersectionObserver
  window.IntersectionObserverEntry = {} as any
  window.IntersectionObserverInit = {} as any
}

// Mock ResizeObserver
export const createMockResizeObserver = () => {
  const mockResizeObserver = jest.fn()
  mockResizeObserver.mockReturnValue({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  })
  window.ResizeObserver = mockResizeObserver
}

// Mock matchMedia
export const createMockMatchMedia = () => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  })
}

// Common setup for integration tests
export const setupIntegrationTestEnvironment = () => {
  createMockIntersectionObserver()
  createMockResizeObserver()
  createMockMatchMedia()
  
  // Mock fetch for any non-MSW requests
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({}),
    text: async () => '',
  })
  
  // Mock setTimeout/setInterval for faster tests
  jest.useFakeTimers()
  
  return {
    cleanupTimers: () => {
      jest.useRealTimers()
    }
  }
}