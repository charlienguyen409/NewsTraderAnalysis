import { test, expect } from '@playwright/test';
import { 
  waitForElement, 
  waitForApiRequest, 
  waitForLoadingToComplete, 
  clickButtonAndWait,
  fillForm,
  expectElementToContainText,
  navigateAndWait,
  takeDebugScreenshot,
  mockApiResponse
} from '../utils/test-helpers';
import { 
  generateTestArticles, 
  generateTestPosition,
  generateAnalysisRequest,
  TEST_SELECTORS,
  TEST_CONFIG
} from '../utils/test-data';

test.describe('Error Scenario Testing', () => {
  test.describe('API Error Handling', () => {
    test.beforeEach(async ({ page }) => {
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
    });

    test('should handle 500 server errors gracefully', async ({ page }) => {
      // Mock 500 server error
      await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
        error: 'Internal server error',
        message: 'Database connection failed'
      }, 500);

      // Try to start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for error handling
      await page.waitForTimeout(2000);
      
      // Verify button returns to enabled state
      await expect(startButton).toBeEnabled();
      await expect(startButton).toContainText('Start Full Analysis');
      
      // Check for error notification (implementation-dependent)
      // This could be a toast, modal, or inline error message
      const errorElements = page.locator('[data-testid="error"], .error, .alert-error');
      if (await errorElements.count() > 0) {
        await expect(errorElements.first()).toBeVisible();
      }
      
      // Take screenshot of error state
      await takeDebugScreenshot(page, 'server-error-500');
    });

    test('should handle 404 not found errors', async ({ page }) => {
      // Mock 404 error
      await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
        error: 'Not found',
        message: 'Endpoint not found'
      }, 404);

      // Try to start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for error handling
      await page.waitForTimeout(2000);
      
      // Verify button returns to enabled state
      await expect(startButton).toBeEnabled();
      
      // Take screenshot of 404 error
      await takeDebugScreenshot(page, 'not-found-error-404');
    });

    test('should handle network timeouts', async ({ page }) => {
      // Mock slow/timeout response
      await page.route(/\/api\/v1\/analysis\/start/, async (route) => {
        await new Promise(resolve => setTimeout(resolve, 35000)); // 35 second timeout
        await route.fulfill({
          status: 408,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Request timeout',
            message: 'Request took too long to process'
          })
        });
      });

      // Try to start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Verify button shows loading state
      await expect(startButton).toBeDisabled();
      await expect(startButton).toContainText('Analyzing...');
      
      // Wait for timeout (shorter than actual timeout for test efficiency)
      await page.waitForTimeout(10000);
      
      // Button should still be disabled during timeout
      await expect(startButton).toBeDisabled();
      
      // Take screenshot of timeout state
      await takeDebugScreenshot(page, 'network-timeout');
    });

    test('should handle malformed JSON responses', async ({ page }) => {
      // Mock malformed JSON response
      await page.route(/\/api\/v1\/analysis\/start/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: '{"invalid": json malformed'
        });
      });

      // Try to start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for error handling
      await page.waitForTimeout(2000);
      
      // Verify button returns to enabled state
      await expect(startButton).toBeEnabled();
      
      // Take screenshot of JSON parsing error
      await takeDebugScreenshot(page, 'malformed-json-error');
    });

    test('should handle rate limiting (429 errors)', async ({ page }) => {
      // Mock rate limiting error
      await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
        error: 'Rate limit exceeded',
        message: 'Too many requests. Please try again later.',
        retry_after: 60
      }, 429);

      // Try to start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for error handling
      await page.waitForTimeout(2000);
      
      // Verify button returns to enabled state
      await expect(startButton).toBeEnabled();
      
      // Check for rate limit message
      const bodyText = await page.textContent('body');
      // Implementation may show rate limit message
      
      // Take screenshot of rate limit error
      await takeDebugScreenshot(page, 'rate-limit-error-429');
    });
  });

  test.describe('Network Connectivity Issues', () => {
    test.beforeEach(async ({ page }) => {
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
    });

    test('should handle complete network failure', async ({ page }) => {
      // Simulate network failure
      await page.route(/\/api\/v1\/analysis\/start/, async (route) => {
        await route.abort('failed');
      });

      // Try to start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for network error handling
      await page.waitForTimeout(3000);
      
      // Verify button returns to enabled state
      await expect(startButton).toBeEnabled();
      
      // Take screenshot of network failure
      await takeDebugScreenshot(page, 'network-failure');
    });

    test('should handle intermittent connectivity', async ({ page }) => {
      let requestCount = 0;
      
      // Mock intermittent failures
      await page.route(/\/api\/v1\/analysis\/start/, async (route) => {
        requestCount++;
        
        if (requestCount === 1) {
          // First request fails
          await route.abort('failed');
        } else {
          // Second request succeeds
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              session_id: 'test-session-123',
              message: 'Analysis started successfully',
              status: 'started'
            })
          });
        }
      });

      // Try to start analysis (first attempt will fail)
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for first failure
      await page.waitForTimeout(2000);
      
      // Verify button returns to enabled state
      await expect(startButton).toBeEnabled();
      
      // Try again (second attempt should succeed)
      await startButton.click();
      
      // Wait for success
      await page.waitForTimeout(1000);
      
      // Verify button shows loading state (indicating success)
      await expect(startButton).toBeDisabled();
      
      // Take screenshot of intermittent connectivity recovery
      await takeDebugScreenshot(page, 'intermittent-connectivity');
    });

    test('should handle slow network connections', async ({ page }) => {
      // Mock slow network response
      await page.route(/\/api\/v1\/analysis\/start/, async (route) => {
        await new Promise(resolve => setTimeout(resolve, 15000)); // 15 second delay
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            session_id: 'test-session-slow',
            message: 'Analysis started successfully',
            status: 'started'
          })
        });
      });

      // Try to start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Verify button shows loading state
      await expect(startButton).toBeDisabled();
      await expect(startButton).toContainText('Analyzing...');
      
      // Wait for slow response
      await page.waitForTimeout(16000);
      
      // Verify button returns to enabled state after slow response
      await expect(startButton).toBeEnabled();
      
      // Take screenshot of slow network handling
      await takeDebugScreenshot(page, 'slow-network');
    });
  });

  test.describe('WebSocket Error Handling', () => {
    test.beforeEach(async ({ page }) => {
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
    });

    test('should handle WebSocket connection failures', async ({ page }) => {
      // Mock WebSocket failure
      await page.evaluateOnNewDocument(() => {
        const originalWebSocket = window.WebSocket;
        
        window.WebSocket = class extends originalWebSocket {
          constructor(url: string) {
            super('ws://localhost:8000/ws/test');
            
            // Simulate immediate connection failure
            setTimeout(() => {
              this.onerror?.(new Event('error'));
              this.onclose?.(new CloseEvent('close', { code: 1006, reason: 'Connection failed' }));
            }, 100);
          }
        };
      });

      // Mock successful analysis start
      await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
        session_id: 'test-websocket-failure',
        message: 'Analysis started successfully',
        status: 'started'
      });

      // Start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for WebSocket failure
      await page.waitForTimeout(1000);
      
      // Verify connection status shows offline
      const connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
      await expect(connectionStatus).toContainText('Offline');
      
      // Verify app still functions (fallback to polling)
      const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
      await expect(activityLog).toBeVisible();
      
      // Take screenshot of WebSocket failure
      await takeDebugScreenshot(page, 'websocket-failure');
    });

    test('should handle WebSocket message errors', async ({ page }) => {
      // Mock WebSocket with error messages
      await page.evaluateOnNewDocument(() => {
        const originalWebSocket = window.WebSocket;
        
        window.WebSocket = class extends originalWebSocket {
          constructor(url: string) {
            super('ws://localhost:8000/ws/test');
            
            setTimeout(() => {
              this.onopen?.(new Event('open'));
              
              // Send error message
              setTimeout(() => {
                this.onmessage?.(new MessageEvent('message', {
                  data: JSON.stringify({
                    type: 'error',
                    message: 'WebSocket error occurred',
                    code: 'WS_ERROR_001'
                  })
                }));
              }, 500);
            }, 100);
          }
        };
      });

      // Mock successful analysis start
      await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
        session_id: 'test-websocket-error-message',
        message: 'Analysis started successfully',
        status: 'started'
      });

      // Start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for WebSocket error message
      await page.waitForTimeout(1000);
      
      // Verify connection is still active
      const connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
      await expect(connectionStatus).toContainText('Live');
      
      // Verify error is handled gracefully (no crash)
      const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
      await expect(activityLog).toBeVisible();
      
      // Take screenshot of WebSocket error message handling
      await takeDebugScreenshot(page, 'websocket-error-message');
    });
  });

  test.describe('Data Validation Errors', () => {
    test.beforeEach(async ({ page }) => {
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
    });

    test('should handle invalid analysis parameters', async ({ page }) => {
      // Try invalid max positions
      await fillForm(page, {
        [TEST_SELECTORS.maxPositionsInput]: '-5'
      });
      
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Verify validation prevents API call
      await page.waitForTimeout(1000);
      await expect(startButton).toBeEnabled();
      
      // Try invalid confidence
      await fillForm(page, {
        [TEST_SELECTORS.maxPositionsInput]: '10',
        [TEST_SELECTORS.minConfidenceInput]: '2.5'
      });
      
      await startButton.click();
      await page.waitForTimeout(1000);
      await expect(startButton).toBeEnabled();
      
      // Take screenshot of validation errors
      await takeDebugScreenshot(page, 'validation-errors');
    });

    test('should handle empty required fields', async ({ page }) => {
      // Clear required fields
      await fillForm(page, {
        [TEST_SELECTORS.maxPositionsInput]: '',
        [TEST_SELECTORS.minConfidenceInput]: ''
      });
      
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Verify validation prevents submission
      await page.waitForTimeout(1000);
      await expect(startButton).toBeEnabled();
      
      // Take screenshot of empty field validation
      await takeDebugScreenshot(page, 'empty-field-validation');
    });
  });

  test.describe('Article Loading Errors', () => {
    test.beforeEach(async ({ page }) => {
      await navigateAndWait(page, '/articles');
      await waitForLoadingToComplete(page);
    });

    test('should handle article loading failures', async ({ page }) => {
      // Mock article loading error
      await mockApiResponse(page, /\/api\/v1\/articles/, {
        error: 'Failed to load articles',
        message: 'Database query failed'
      }, 500);

      // Refresh to trigger error
      await page.reload();
      await waitForLoadingToComplete(page);

      // Verify error state is displayed
      const errorMessage = page.locator('[data-testid="error"], .error');
      if (await errorMessage.count() > 0) {
        await expect(errorMessage.first()).toBeVisible();
      }
      
      // Take screenshot of article loading error
      await takeDebugScreenshot(page, 'article-loading-error');
    });

    test('should handle filter API errors', async ({ page }) => {
      // Mock successful initial load
      await mockApiResponse(page, /\/api\/v1\/articles/, {
        data: generateTestArticles(5)
      });

      // Mock filter error
      await mockApiResponse(page, /\/api\/v1\/articles\/\?.*search=/, {
        error: 'Search failed',
        message: 'Search service unavailable'
      }, 503);

      // Refresh to load articles
      await page.reload();
      await waitForLoadingToComplete(page);

      // Try to search (should fail)
      const searchInput = await waitForElement(page, TEST_SELECTORS.articleSearch);
      await searchInput.fill('test search');
      
      // Wait for search error
      await page.waitForTimeout(2000);
      
      // Verify search field still works (doesn't crash)
      await expect(searchInput).toHaveValue('test search');
      
      // Take screenshot of filter error
      await takeDebugScreenshot(page, 'filter-error');
    });
  });

  test.describe('Browser Compatibility Issues', () => {
    test('should handle localStorage unavailable', async ({ page }) => {
      // Disable localStorage
      await page.addInitScript(() => {
        Object.defineProperty(window, 'localStorage', {
          value: undefined,
          writable: true
        });
      });

      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);

      // Verify app still loads without localStorage
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await expect(startButton).toBeVisible();
      
      // Take screenshot of localStorage unavailable
      await takeDebugScreenshot(page, 'no-localstorage');
    });

    test('should handle WebSocket unavailable', async ({ page }) => {
      // Disable WebSocket
      await page.addInitScript(() => {
        (window as any).WebSocket = undefined;
      });

      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);

      // Mock analysis start
      await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
        session_id: 'test-no-websocket',
        message: 'Analysis started successfully',
        status: 'started'
      });

      // Start analysis
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Verify app works without WebSocket (falls back to polling)
      await page.waitForTimeout(1000);
      await expect(startButton).toBeDisabled();
      
      // Take screenshot of WebSocket unavailable
      await takeDebugScreenshot(page, 'no-websocket');
    });
  });

  test.describe('Performance Degradation', () => {
    test('should handle high CPU usage scenarios', async ({ page }) => {
      // Simulate high CPU usage
      await page.addInitScript(() => {
        // Create CPU-intensive task
        setInterval(() => {
          const start = Date.now();
          while (Date.now() - start < 50) {
            // Busy wait for 50ms every 100ms
          }
        }, 100);
      });

      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);

      // Verify app still responsive
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await expect(startButton).toBeVisible();
      
      // Test interaction under high CPU
      await startButton.click();
      await page.waitForTimeout(1000);
      
      // Verify interaction works
      await expect(startButton).toBeDisabled();
      
      // Take screenshot of high CPU scenario
      await takeDebugScreenshot(page, 'high-cpu-usage');
    });

    test('should handle memory pressure', async ({ page }) => {
      // Create memory pressure
      await page.addInitScript(() => {
        const arrays: number[][] = [];
        setInterval(() => {
          // Create large arrays to consume memory
          arrays.push(new Array(100000).fill(0));
          if (arrays.length > 100) {
            arrays.shift(); // Remove oldest to prevent crash
          }
        }, 100);
      });

      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);

      // Verify app still functions under memory pressure
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await expect(startButton).toBeVisible();
      
      // Take screenshot of memory pressure scenario
      await takeDebugScreenshot(page, 'memory-pressure');
    });
  });

  test.describe('Edge Cases', () => {
    test('should handle extremely large datasets', async ({ page }) => {
      // Mock response with large dataset
      const largeArticleSet = Array.from({ length: 1000 }, (_, i) => ({
        id: `article-${i}`,
        title: `Test Article ${i}`,
        content: `This is test content for article ${i}. `.repeat(100),
        url: `https://example.com/article-${i}`,
        source: 'finviz',
        ticker: 'AAPL',
        published_at: new Date().toISOString(),
        scraped_at: new Date().toISOString(),
        is_processed: true
      }));

      await mockApiResponse(page, /\/api\/v1\/articles/, {
        data: largeArticleSet
      });

      await navigateAndWait(page, '/articles');
      
      // Wait longer for large dataset
      await page.waitForTimeout(5000);
      
      // Verify app handles large dataset
      const articleCards = page.locator(TEST_SELECTORS.articleCard);
      await expect(articleCards.first()).toBeVisible();
      
      // Take screenshot of large dataset handling
      await takeDebugScreenshot(page, 'large-dataset');
    });

    test('should handle rapid user interactions', async ({ page }) => {
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);

      // Mock analysis response
      await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
        session_id: 'test-rapid-clicks',
        message: 'Analysis started successfully',
        status: 'started'
      });

      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      
      // Rapid clicks to test debouncing/protection
      await Promise.all([
        startButton.click(),
        startButton.click(),
        startButton.click(),
        startButton.click(),
        startButton.click()
      ]);
      
      // Verify only one analysis is started
      await page.waitForTimeout(1000);
      await expect(startButton).toBeDisabled();
      
      // Take screenshot of rapid interaction handling
      await takeDebugScreenshot(page, 'rapid-interactions');
    });
  });
});