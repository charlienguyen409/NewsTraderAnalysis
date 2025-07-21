// Mock WebSocket class for testing
export class MockWebSocket {
  public static instances: MockWebSocket[] = []
  
  public url: string
  public readyState: number = WebSocket.CONNECTING
  public onopen: ((event: Event) => void) | null = null
  public onclose: ((event: CloseEvent) => void) | null = null
  public onmessage: ((event: MessageEvent) => void) | null = null
  public onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
    
    // Simulate connection delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      this.onopen?.(new Event('open'))
    }, 100)
  }

  send(data: string | ArrayBuffer | Blob) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open')
    }
    // In tests, we don't actually send data anywhere
    console.log('WebSocket send:', data)
  }

  close(code?: number, reason?: string) {
    this.readyState = WebSocket.CLOSED
    const event = new CloseEvent('close', { code, reason })
    this.onclose?.(event)
  }

  // Test helper methods
  public simulateMessage(data: any) {
    if (this.readyState === WebSocket.OPEN) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data)
      })
      this.onmessage?.(event)
    }
  }

  public simulateError() {
    const event = new Event('error')
    this.onerror?.(event)
  }

  public simulateClose(code = 1000, reason = 'Normal closure') {
    this.readyState = WebSocket.CLOSED
    const event = new CloseEvent('close', { code, reason })
    this.onclose?.(event)
  }

  // Static methods for test control
  public static reset() {
    MockWebSocket.instances = []
  }

  public static getLastInstance(): MockWebSocket | undefined {
    return MockWebSocket.instances[MockWebSocket.instances.length - 1]
  }

  public static getAllInstances(): MockWebSocket[] {
    return MockWebSocket.instances
  }
}

// Mock WebSocket server for testing real-time updates
export class MockWebSocketServer {
  private clients: MockWebSocket[] = []
  
  public addClient(ws: MockWebSocket) {
    this.clients.push(ws)
  }

  public removeClient(ws: MockWebSocket) {
    this.clients = this.clients.filter(client => client !== ws)
  }

  public broadcast(data: any) {
    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.simulateMessage(data)
      }
    })
  }

  public sendToSession(sessionId: string, data: any) {
    // Filter clients by session ID (assuming URL contains session ID)
    const sessionClients = this.clients.filter(client => 
      client.url.includes(sessionId)
    )
    
    sessionClients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.simulateMessage(data)
      }
    })
  }

  public simulateAnalysisProgress(sessionId: string) {
    const progressMessages = [
      { type: 'analysis_status', status: 'starting', message: 'Starting analysis...' },
      { type: 'analysis_update', status: 'scraping', message: 'Scraping articles from finviz...' },
      { type: 'analysis_update', status: 'processing', message: 'Processing 25 articles...' },
      { type: 'analysis_update', status: 'analyzing', message: 'Analyzing sentiment and catalysts...' },
      { type: 'analysis_update', status: 'generating', message: 'Generating position recommendations...' },
      { type: 'analysis_status', status: 'completed', message: 'Analysis completed successfully' }
    ]

    progressMessages.forEach((message, index) => {
      setTimeout(() => {
        this.sendToSession(sessionId, {
          ...message,
          session_id: sessionId,
          timestamp: new Date().toISOString()
        })
      }, index * 1000)
    })
  }

  public simulateActivityLogUpdate(sessionId: string, logEntry: any) {
    this.sendToSession(sessionId, {
      type: 'activity_log_update',
      session_id: sessionId,
      log: logEntry,
      timestamp: new Date().toISOString()
    })
  }

  public simulateError(sessionId: string, error: string) {
    this.sendToSession(sessionId, {
      type: 'analysis_status',
      status: 'error',
      message: error,
      session_id: sessionId,
      timestamp: new Date().toISOString()
    })
  }

  public reset() {
    this.clients = []
  }
}

// Global mock server instance for tests
export const mockWebSocketServer = new MockWebSocketServer()

// Setup function for tests
export const setupWebSocketMocks = () => {
  // Replace global WebSocket with mock
  global.WebSocket = MockWebSocket as any
  
  // Reset all instances
  MockWebSocket.reset()
  mockWebSocketServer.reset()
  
  // Auto-add instances to server
  const originalConstructor = MockWebSocket
  global.WebSocket = class extends originalConstructor {
    constructor(url: string) {
      super(url)
      mockWebSocketServer.addClient(this)
    }
  } as any
}

// Cleanup function for tests
export const cleanupWebSocketMocks = () => {
  MockWebSocket.reset()
  mockWebSocketServer.reset()
}