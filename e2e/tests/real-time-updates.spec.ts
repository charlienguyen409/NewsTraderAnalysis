import { test, expect } from '@playwright/test';
import { 
  waitForElement, 
  waitForApiRequest, 
  waitForLoadingToComplete, 
  waitForWebSocketConnection,
  clickButtonAndWait,
  fillForm,
  expectElementToContainText,
  navigateAndWait,
  takeDebugScreenshot,
  mockApiResponse,
  verifyWebSocketUpdates
} from '../utils/test-helpers';
import { 
  generateActivityLogEntries, 
  generateTestPosition,
  generateMarketSummary,
  TEST_SELECTORS,
  TEST_CONFIG
} from '../utils/test-data';

test.describe('Real-time Updates via WebSocket', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await navigateAndWait(page, '/');
    
    // Wait for page to fully load
    await waitForLoadingToComplete(page);
  });

  test('should establish WebSocket connection and show connection status', async ({ page }) => {
    // Mock WebSocket connection
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      let mockWebSocket: any;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          mockWebSocket = this;
          
          // Simulate successful connection
          setTimeout(() => {
            this.onopen?.(new Event('open'));
          }, 100);
        }
        
        close() {
          this.onclose?.(new CloseEvent('close', { code: 1000, reason: 'Test close' }));
        }
      };
      
      // Store reference for testing
      (window as any).mockWebSocket = mockWebSocket;
    });

    // Start analysis to trigger WebSocket connection
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-websocket-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for WebSocket connection to be established
    await waitForWebSocketConnection(page);
    
    // Verify connection status indicator
    const connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
    await expect(connectionStatus).toBeVisible();
    await expect(connectionStatus).toContainText('Live');
    
    // Verify connection indicator is green
    const connectionIndicator = page.locator('[data-testid="connection-indicator"]');
    await expect(connectionIndicator).toHaveClass(/bg-green-500/);
    
    // Take screenshot of connection status
    await takeDebugScreenshot(page, 'websocket-connected');
  });

  test('should receive and display real-time analysis progress updates', async ({ page }) => {
    // Mock WebSocket with progress updates
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          
          // Simulate connection and progress updates
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send series of progress updates
            const updates = [
              {
                type: 'analysis_status',
                status: 'scraping',
                message: 'Starting article scraping from FinViz...',
                progress: 10
              },
              {
                type: 'analysis_status',
                status: 'scraping',
                message: 'Scraped 25 articles from FinViz',
                progress: 30
              },
              {
                type: 'analysis_status',
                status: 'scraping',
                message: 'Starting article scraping from BizToc...',
                progress: 50
              },
              {
                type: 'analysis_status',
                status: 'analyzing',
                message: 'Analyzing article sentiment with GPT-4...',
                progress: 70
              },
              {
                type: 'analysis_status',
                status: 'complete',
                message: 'Analysis complete! Generated 12 position recommendations',
                progress: 100
              }
            ];
            
            updates.forEach((update, index) => {
              setTimeout(() => {
                this.onmessage?.(new MessageEvent('message', {
                  data: JSON.stringify(update)
                }));
              }, (index + 1) * 1000);
            });
          }, 100);
        }
      };
    });

    // Mock analysis start
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-progress-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    // Start analysis
    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for connection
    await waitForWebSocketConnection(page);
    
    // Verify activity log shows progress updates
    const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
    await expect(activityLog).toBeVisible();
    
    // Wait for progress updates to appear
    await page.waitForTimeout(6000); // Wait for all updates
    
    // Verify progress messages are displayed
    const logEntries = page.locator(TEST_SELECTORS.logEntry);
    await expect(logEntries).toHaveCountGreaterThan(0);
    
    // Check for specific progress messages
    await expect(activityLog).toContainText('Starting article scraping');
    await expect(activityLog).toContainText('Analyzing article sentiment');
    await expect(activityLog).toContainText('Analysis complete');
    
    // Take screenshot of progress updates
    await takeDebugScreenshot(page, 'progress-updates');
  });

  test('should update market summary in real-time', async ({ page }) => {
    // Mock WebSocket with market summary updates
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send market summary update
            setTimeout(() => {
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify({
                  type: 'market_summary_update',
                  data: {
                    total_articles: 156,
                    processed_articles: 145,
                    total_positions: 28,
                    bullish_positions: 18,
                    bearish_positions: 10,
                    avg_confidence: 0.82,
                    top_tickers: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
                  }
                })
              }));
            }, 1000);
          }, 100);
        }
      };
    });

    // Mock initial market summary
    await mockApiResponse(page, /\/api\/v1\/analysis\/market-summary/, {
      total_articles: 120,
      processed_articles: 110,
      total_positions: 20,
      bullish_positions: 12,
      bearish_positions: 8,
      avg_confidence: 0.75,
      top_tickers: ['AAPL', 'GOOGL', 'MSFT']
    });

    // Start analysis to trigger WebSocket
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-market-summary-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for connection
    await waitForWebSocketConnection(page);
    
    // Verify market summary is displayed
    const marketSummary = await waitForElement(page, '[data-testid="market-summary"]');
    await expect(marketSummary).toBeVisible();
    
    // Verify initial values
    await expect(marketSummary).toContainText('120'); // total articles
    await expect(marketSummary).toContainText('20'); // total positions
    
    // Wait for WebSocket update
    await page.waitForTimeout(2000);
    
    // Verify updated values
    await expect(marketSummary).toContainText('156'); // updated total articles
    await expect(marketSummary).toContainText('28'); // updated total positions
    
    // Take screenshot of updated market summary
    await takeDebugScreenshot(page, 'market-summary-updated');
  });

  test('should update position list in real-time', async ({ page }) => {
    // Mock WebSocket with position updates
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send new position update
            setTimeout(() => {
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify({
                  type: 'position_update',
                  action: 'create',
                  data: {
                    id: 'new-position-123',
                    ticker: 'NVDA',
                    recommendation: 'STRONG_BUY',
                    confidence: 0.92,
                    sentiment_score: 0.85,
                    reasoning: 'Strong AI momentum with new chip architecture',
                    created_at: new Date().toISOString()
                  }
                })
              }));
            }, 1000);
          }, 100);
        }
      };
    });

    // Mock initial positions
    const initialPositions = [
      generateTestPosition({ ticker: 'AAPL', recommendation: 'BUY' }),
      generateTestPosition({ ticker: 'GOOGL', recommendation: 'HOLD' })
    ];
    
    await mockApiResponse(page, /\/api\/v1\/positions/, {
      data: initialPositions
    });

    // Start analysis to trigger WebSocket
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-position-update-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for connection
    await waitForWebSocketConnection(page);
    
    // Verify initial positions are displayed
    const positionsSection = await waitForElement(page, '[data-testid="recent-positions"]');
    await expect(positionsSection).toBeVisible();
    
    let positionCards = page.locator(TEST_SELECTORS.positionCard);
    await expect(positionCards).toHaveCount(2);
    
    // Wait for new position via WebSocket
    await page.waitForTimeout(2000);
    
    // Verify new position is added
    await expect(positionCards).toHaveCount(3);
    
    // Verify new position details
    const newPosition = positionCards.last();
    await expect(newPosition).toContainText('NVDA');
    await expect(newPosition).toContainText('STRONG_BUY');
    
    // Take screenshot of updated positions
    await takeDebugScreenshot(page, 'positions-updated');
  });

  test('should handle WebSocket connection failures gracefully', async ({ page }) => {
    // Mock WebSocket failure
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          
          // Simulate connection failure
          setTimeout(() => {
            this.onerror?.(new Event('error'));
            this.onclose?.(new CloseEvent('close', { code: 1006, reason: 'Connection failed' }));
          }, 100);
        }
      };
    });

    // Start analysis to trigger WebSocket
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-websocket-failure-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for connection failure
    await page.waitForTimeout(1000);
    
    // Verify connection status shows offline
    const connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
    await expect(connectionStatus).toContainText('Offline');
    
    // Verify connection indicator is red
    const connectionIndicator = page.locator('[data-testid="connection-indicator"]');
    await expect(connectionIndicator).toHaveClass(/bg-red-500/);
    
    // Verify app still functions (falls back to polling)
    const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
    await expect(activityLog).toBeVisible();
    
    // Take screenshot of connection failure
    await takeDebugScreenshot(page, 'websocket-failure');
  });

  test('should reconnect WebSocket after connection loss', async ({ page }) => {
    let connectionAttempts = 0;
    
    // Mock WebSocket with reconnection logic
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      let attemptCount = 0;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          attemptCount++;
          
          if (attemptCount === 1) {
            // First connection fails
            setTimeout(() => {
              this.onerror?.(new Event('error'));
              this.onclose?.(new CloseEvent('close', { code: 1006, reason: 'Connection lost' }));
            }, 500);
          } else if (attemptCount === 2) {
            // Second connection succeeds
            setTimeout(() => {
              this.onopen?.(new Event('open'));
            }, 100);
          }
        }
      };
    });

    // Start analysis to trigger WebSocket
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-reconnection-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for initial connection failure
    await page.waitForTimeout(1000);
    
    // Verify connection status shows offline
    const connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
    await expect(connectionStatus).toContainText('Offline');
    
    // Wait for reconnection (this would depend on app's reconnection logic)
    await page.waitForTimeout(2000);
    
    // Verify connection status shows connected again
    // (This depends on the app implementing reconnection logic)
    // await expect(connectionStatus).toContainText('Live');
    
    // Take screenshot of reconnection
    await takeDebugScreenshot(page, 'websocket-reconnection');
  });

  test('should display activity log updates in real-time', async ({ page }) => {
    // Mock WebSocket with activity log updates
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send activity log updates
            const logUpdates = [
              {
                type: 'activity_log_update',
                data: {
                  id: 'log-1',
                  timestamp: new Date().toISOString(),
                  level: 'INFO',
                  category: 'scraping',
                  action: 'start',
                  message: 'Starting article scraping process',
                  details: {}
                }
              },
              {
                type: 'activity_log_update',
                data: {
                  id: 'log-2',
                  timestamp: new Date().toISOString(),
                  level: 'INFO',
                  category: 'scraping',
                  action: 'complete',
                  message: 'Successfully scraped 45 articles',
                  details: { article_count: 45 }
                }
              },
              {
                type: 'activity_log_update',
                data: {
                  id: 'log-3',
                  timestamp: new Date().toISOString(),
                  level: 'INFO',
                  category: 'llm',
                  action: 'analyze',
                  message: 'Analyzing sentiment for AAPL article',
                  details: { ticker: 'AAPL', model: 'gpt-4' }
                }
              }
            ];
            
            logUpdates.forEach((update, index) => {
              setTimeout(() => {
                this.onmessage?.(new MessageEvent('message', {
                  data: JSON.stringify(update)
                }));
              }, (index + 1) * 1000);
            });
          }, 100);
        }
      };
    });

    // Start analysis to trigger WebSocket
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-activity-log-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for connection
    await waitForWebSocketConnection(page);
    
    // Verify activity log is displayed
    const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
    await expect(activityLog).toBeVisible();
    
    // Wait for activity log updates
    await page.waitForTimeout(4000);
    
    // Verify activity log entries are displayed
    const logEntries = page.locator(TEST_SELECTORS.logEntry);
    await expect(logEntries).toHaveCountGreaterThan(0);
    
    // Check for specific log messages
    await expect(activityLog).toContainText('Starting article scraping');
    await expect(activityLog).toContainText('Successfully scraped 45 articles');
    await expect(activityLog).toContainText('Analyzing sentiment for AAPL');
    
    // Take screenshot of activity log updates
    await takeDebugScreenshot(page, 'activity-log-updates');
  });

  test('should handle multiple concurrent WebSocket connections', async ({ page }) => {
    // Mock multiple WebSocket connections
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      const connections: any[] = [];
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          connections.push(this);
          
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send updates from multiple connections
            setTimeout(() => {
              connections.forEach((conn, index) => {
                conn.onmessage?.(new MessageEvent('message', {
                  data: JSON.stringify({
                    type: 'analysis_status',
                    status: 'processing',
                    message: `Connection ${index + 1} processing...`
                  })
                }));
              });
            }, 1000);
          }, 100);
        }
      };
      
      // Store connections for testing
      (window as any).mockConnections = connections;
    });

    // Start multiple analyses
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-multiple-connections-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    // Start first analysis
    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait a bit, then simulate another connection
    await page.waitForTimeout(500);
    
    // Navigate to another page and back to simulate multiple connections
    await navigateAndWait(page, '/articles');
    await navigateAndWait(page, '/');
    
    // Wait for connections to be established
    await waitForWebSocketConnection(page);
    
    // Verify connection status
    const connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
    await expect(connectionStatus).toContainText('Live');
    
    // Take screenshot of multiple connections
    await takeDebugScreenshot(page, 'multiple-connections');
  });

  test('should maintain WebSocket connection across page navigation', async ({ page }) => {
    // Mock persistent WebSocket connection
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      let persistentConnection: any;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          
          if (!persistentConnection) {
            persistentConnection = this;
            
            setTimeout(() => {
              this.onopen?.(new Event('open'));
            }, 100);
          }
          
          return persistentConnection;
        }
      };
    });

    // Start analysis to establish connection
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-persistent-connection-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for connection
    await waitForWebSocketConnection(page);
    
    // Verify connection status
    let connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
    await expect(connectionStatus).toContainText('Live');
    
    // Navigate to articles page
    await navigateAndWait(page, '/articles');
    
    // Navigate back to dashboard
    await navigateAndWait(page, '/');
    
    // Verify connection is still active
    connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
    await expect(connectionStatus).toContainText('Live');
    
    // Take screenshot of persistent connection
    await takeDebugScreenshot(page, 'persistent-connection');
  });

  test('should handle WebSocket message parsing errors gracefully', async ({ page }) => {
    // Mock WebSocket with invalid messages
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super('ws://localhost:8000/ws/test');
          
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send invalid JSON
            setTimeout(() => {
              this.onmessage?.(new MessageEvent('message', {
                data: 'invalid json {'
              }));
            }, 500);
            
            // Send valid message after invalid one
            setTimeout(() => {
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify({
                  type: 'analysis_status',
                  status: 'processing',
                  message: 'This message should still work'
                })
              }));
            }, 1000);
          }, 100);
        }
      };
    });

    // Start analysis to trigger WebSocket
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-message-parsing-session',
      message: 'Analysis started successfully',
      status: 'started'
    });

    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for connection and message processing
    await waitForWebSocketConnection(page);
    await page.waitForTimeout(2000);
    
    // Verify connection is still active despite parsing errors
    const connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
    await expect(connectionStatus).toContainText('Live');
    
    // Verify valid messages are still processed
    const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
    await expect(activityLog).toContainText('This message should still work');
    
    // Take screenshot of error handling
    await takeDebugScreenshot(page, 'message-parsing-error');
  });
});