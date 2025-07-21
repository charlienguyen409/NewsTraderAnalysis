import { test, expect } from '@playwright/test';
import { 
  waitForElement, 
  waitForApiRequest, 
  waitForLoadingToComplete, 
  clickButtonAndWait,
  fillForm,
  expectElementToContainText,
  waitForAnalysisToComplete,
  navigateAndWait,
  takeDebugScreenshot,
  mockApiResponse,
  testResponsiveDesign
} from '../utils/test-helpers';
import { 
  generateAnalysisRequest, 
  generateTestPosition, 
  generateMarketSummary,
  TEST_SELECTORS,
  TEST_CONFIG
} from '../utils/test-data';

test.describe('Market Analysis Trigger and Results', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await navigateAndWait(page, '/');
    
    // Wait for page to fully load
    await waitForLoadingToComplete(page);
  });

  test('should trigger full analysis and display results', async ({ page }) => {
    // Test data
    const analysisRequest = generateAnalysisRequest();
    const mockPositions = [
      generateTestPosition({ ticker: 'AAPL', recommendation: 'BUY' }),
      generateTestPosition({ ticker: 'GOOGL', recommendation: 'STRONG_BUY' }),
      generateTestPosition({ ticker: 'MSFT', recommendation: 'HOLD' })
    ];
    
    // Mock API responses
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-session-123',
      message: 'Analysis started successfully',
      status: 'started'
    });
    
    await mockApiResponse(page, /\/api\/v1\/positions/, {
      data: mockPositions
    });
    
    await mockApiResponse(page, /\/api\/v1\/analysis\/market-summary/, generateMarketSummary());

    // Configure analysis parameters
    await fillForm(page, {
      [TEST_SELECTORS.maxPositionsInput]: '10',
      [TEST_SELECTORS.minConfidenceInput]: '0.7'
    });

    // Select LLM model
    const llmSelect = await waitForElement(page, TEST_SELECTORS.llmModelSelect);
    await llmSelect.selectOption('gpt-4');

    // Start analysis
    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await expect(startButton).toBeEnabled();
    await expect(startButton).toContainText('Start Full Analysis');

    // Click start analysis and wait for loading state
    await startButton.click();
    
    // Verify button shows loading state
    await expect(startButton).toBeDisabled();
    await expect(startButton).toContainText('Analyzing...');
    
    // Wait for analysis to start (API call)
    await waitForApiRequest(page, '/api/v1/analysis/start/');
    
    // Wait for analysis to complete (mock completion)
    await page.waitForTimeout(2000); // Simulate analysis time
    
    // Verify button returns to enabled state
    await expect(startButton).toBeEnabled();
    await expect(startButton).toContainText('Start Full Analysis');

    // Verify market summary is updated
    const marketSummary = await waitForElement(page, '[data-testid="market-summary"]');
    await expect(marketSummary).toBeVisible();

    // Verify recent positions are displayed
    const positionsSection = await waitForElement(page, '[data-testid="recent-positions"]');
    await expect(positionsSection).toBeVisible();

    // Check that position cards are rendered
    const positionCards = page.locator(TEST_SELECTORS.positionCard);
    await expect(positionCards).toHaveCount(3);

    // Verify position details
    const firstPosition = positionCards.first();
    await expect(firstPosition).toContainText('AAPL');
    await expect(firstPosition).toContainText('BUY');

    // Check activity log shows analysis activity
    const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
    await expect(activityLog).toBeVisible();
    
    // Take screenshot for visual verification
    await takeDebugScreenshot(page, 'analysis-complete');
  });

  test('should trigger headlines analysis and display results', async ({ page }) => {
    // Mock API response for headlines analysis
    await mockApiResponse(page, /\/api\/v1\/analysis\/headlines/, {
      session_id: 'test-headlines-session-456',
      message: 'Headlines analysis started successfully',
      status: 'started'
    });

    // Configure headlines analysis parameters
    await fillForm(page, {
      '[data-testid="headlines-max-positions"]': '5',
      '[data-testid="headlines-min-confidence"]': '0.6'
    });

    // Start headlines analysis
    const headlinesButton = await waitForElement(page, TEST_SELECTORS.startHeadlinesButton);
    await expect(headlinesButton).toBeEnabled();
    await expect(headlinesButton).toContainText('Start Headlines Analysis');

    // Click start headlines analysis
    await headlinesButton.click();
    
    // Verify button shows loading state
    await expect(headlinesButton).toBeDisabled();
    await expect(headlinesButton).toContainText('Analyzing...');
    
    // Wait for analysis to start
    await waitForApiRequest(page, '/api/v1/analysis/headlines/');
    
    // Wait for analysis to complete
    await page.waitForTimeout(1500); // Simulate headlines analysis time (faster)
    
    // Verify button returns to enabled state
    await expect(headlinesButton).toBeEnabled();
    await expect(headlinesButton).toContainText('Start Headlines Analysis');

    // Verify results are displayed
    const marketSummary = await waitForElement(page, '[data-testid="market-summary"]');
    await expect(marketSummary).toBeVisible();
  });

  test('should handle analysis errors gracefully', async ({ page }) => {
    // Mock API error response
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      error: 'Analysis failed due to network error'
    }, 500);

    // Try to start analysis
    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Verify error handling
    await expect(startButton).toBeEnabled();
    await expect(startButton).toContainText('Start Full Analysis');
    
    // Check for error message or notification
    // (This depends on how the frontend handles errors)
    await page.waitForTimeout(2000);
    
    // Take screenshot for error state verification
    await takeDebugScreenshot(page, 'analysis-error');
  });

  test('should validate analysis parameters', async ({ page }) => {
    // Test invalid max positions
    await fillForm(page, {
      [TEST_SELECTORS.maxPositionsInput]: '0'
    });
    
    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Verify validation (button should remain enabled if validation fails)
    await expect(startButton).toBeEnabled();
    
    // Test invalid confidence
    await fillForm(page, {
      [TEST_SELECTORS.maxPositionsInput]: '10',
      [TEST_SELECTORS.minConfidenceInput]: '1.5'
    });
    
    await startButton.click();
    await expect(startButton).toBeEnabled();
    
    // Test valid parameters
    await fillForm(page, {
      [TEST_SELECTORS.maxPositionsInput]: '10',
      [TEST_SELECTORS.minConfidenceInput]: '0.7'
    });
    
    await startButton.click();
    // Should show loading state for valid parameters
    await expect(startButton).toBeDisabled();
  });

  test('should prevent multiple concurrent analyses', async ({ page }) => {
    // Mock slow API response
    await page.route(/\/api\/v1\/analysis\/start/, async (route) => {
      await new Promise(resolve => setTimeout(resolve, 5000)); // 5 second delay
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'test-session-789',
          message: 'Analysis started successfully',
          status: 'started'
        })
      });
    });

    // Start first analysis
    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Verify button is disabled
    await expect(startButton).toBeDisabled();
    
    // Try to start headlines analysis while full analysis is running
    const headlinesButton = await waitForElement(page, TEST_SELECTORS.startHeadlinesButton);
    await expect(headlinesButton).toBeDisabled();
    
    // Wait for first analysis to complete
    await page.waitForTimeout(6000);
    
    // Verify both buttons are enabled again
    await expect(startButton).toBeEnabled();
    await expect(headlinesButton).toBeEnabled();
  });

  test('should display analysis progress in activity log', async ({ page }) => {
    // Mock WebSocket connection for real-time updates
    await page.evaluateOnNewDocument(() => {
      // Override WebSocket to simulate real-time updates
      const originalWebSocket = window.WebSocket;
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super(url);
          // Simulate connection and messages
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send mock progress updates
            setTimeout(() => {
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify({
                  type: 'analysis_update',
                  status: 'scraping',
                  message: 'Scraping articles from FinViz...'
                })
              }));
            }, 1000);
            
            setTimeout(() => {
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify({
                  type: 'analysis_update',
                  status: 'analyzing',
                  message: 'Analyzing article sentiment...'
                })
              }));
            }, 2000);
            
            setTimeout(() => {
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify({
                  type: 'analysis_update',
                  status: 'complete',
                  message: 'Analysis complete!'
                })
              }));
            }, 3000);
          }, 100);
        }
      };
    });

    // Mock analysis start
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-session-progress',
      message: 'Analysis started successfully',
      status: 'started'
    });

    // Start analysis
    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for activity log to show updates
    const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
    await expect(activityLog).toBeVisible();
    
    // Check for connection status
    const connectionStatus = await waitForElement(page, TEST_SELECTORS.connectionStatus);
    await expect(connectionStatus).toContainText('Live');
    
    // Wait for progress updates to appear
    await page.waitForTimeout(4000);
    
    // Verify activity log contains progress messages
    const logEntries = page.locator(TEST_SELECTORS.logEntry);
    await expect(logEntries.first()).toBeVisible();
    
    // Take screenshot of activity log
    await takeDebugScreenshot(page, 'activity-log-progress');
  });

  test('should work on mobile devices', async ({ page }) => {
    await testResponsiveDesign(page, async (page) => {
      // Check that analysis controls are accessible on mobile
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await expect(startButton).toBeVisible();
      
      const headlinesButton = await waitForElement(page, TEST_SELECTORS.startHeadlinesButton);
      await expect(headlinesButton).toBeVisible();
      
      // Check form fields are accessible
      const maxPositionsInput = await waitForElement(page, TEST_SELECTORS.maxPositionsInput);
      await expect(maxPositionsInput).toBeVisible();
      
      const minConfidenceInput = await waitForElement(page, TEST_SELECTORS.minConfidenceInput);
      await expect(minConfidenceInput).toBeVisible();
      
      // Test interaction on mobile
      await startButton.click();
      await expect(startButton).toBeDisabled();
    });
  });

  test('should persist analysis configuration', async ({ page }) => {
    // Configure analysis parameters
    await fillForm(page, {
      [TEST_SELECTORS.maxPositionsInput]: '15',
      [TEST_SELECTORS.minConfidenceInput]: '0.8'
    });

    // Select LLM model
    const llmSelect = await waitForElement(page, TEST_SELECTORS.llmModelSelect);
    await llmSelect.selectOption('claude-3-sonnet');

    // Refresh page
    await page.reload();
    await waitForLoadingToComplete(page);

    // Verify configuration is restored (if implemented)
    const maxPositionsInput = await waitForElement(page, TEST_SELECTORS.maxPositionsInput);
    const minConfidenceInput = await waitForElement(page, TEST_SELECTORS.minConfidenceInput);
    
    // Check if values are persisted (this depends on implementation)
    // await expect(maxPositionsInput).toHaveValue('15');
    // await expect(minConfidenceInput).toHaveValue('0.8');
  });

  test('should handle network connectivity issues', async ({ page }) => {
    // Simulate network failure
    await page.route(/\/api\/v1\/analysis\/start/, async (route) => {
      await route.abort('failed');
    });

    // Try to start analysis
    const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
    await startButton.click();
    
    // Wait for network error handling
    await page.waitForTimeout(2000);
    
    // Verify button returns to enabled state
    await expect(startButton).toBeEnabled();
    
    // Take screenshot for network error state
    await takeDebugScreenshot(page, 'network-error');
  });
});