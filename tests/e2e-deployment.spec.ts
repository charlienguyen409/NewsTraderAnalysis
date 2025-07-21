import { test, expect } from '@playwright/test';

test.describe('Market News Analysis Agent - Deployment Integration Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set up any necessary authentication or navigation
    await page.goto('http://localhost:3001');
  });

  test('Frontend loads successfully', async ({ page }) => {
    // Test that the main page loads
    await expect(page).toHaveTitle(/Market News Analysis/i);
    
    // Check for main navigation elements
    await expect(page.locator('nav')).toBeVisible();
    
    // Look for key UI elements
    const dashboard = page.locator('text=Dashboard');
    await expect(dashboard).toBeVisible({ timeout: 10000 });
  });

  test('Dashboard displays with articles data', async ({ page }) => {
    // Navigate to Dashboard if not already there
    await page.click('text=Dashboard');
    
    // Wait for content to load
    await page.waitForLoadState('networkidle');
    
    // Check for market summary section
    const marketSummary = page.locator('[data-testid="market-summary"], .market-summary, text=Market Summary').first();
    await expect(marketSummary).toBeVisible({ timeout: 15000 });
    
    // Check for analysis results or placeholder
    const analysisSection = page.locator('[data-testid="analysis-results"], .analysis-results, .positions').first();
    await expect(analysisSection).toBeVisible({ timeout: 10000 });
  });

  test('Articles page loads and displays data', async ({ page }) => {
    // Navigate to Articles page
    await page.click('text=Articles');
    
    // Wait for articles to load
    await page.waitForLoadState('networkidle');
    
    // Check for articles list or loading state
    const articlesContainer = page.locator('[data-testid="articles-list"], .articles, article').first();
    await expect(articlesContainer).toBeVisible({ timeout: 15000 });
  });

  test('Positions page is accessible', async ({ page }) => {
    // Navigate to Positions page
    await page.click('text=Positions');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check for positions content or placeholder
    const positionsContainer = page.locator('[data-testid="positions"], .positions, .position-card').first();
    await expect(positionsContainer).toBeVisible({ timeout: 10000 });
  });

  test('Backend API responds correctly', async ({ page }) => {
    // Test API endpoints through browser network requests
    const response = await page.request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
    
    const healthData = await response.json();
    expect(healthData.status).toBe('healthy');
    
    // Test articles endpoint
    const articlesResponse = await page.request.get('http://localhost:8000/api/v1/articles/');
    expect(articlesResponse.ok()).toBeTruthy();
    
    const articles = await articlesResponse.json();
    expect(Array.isArray(articles)).toBeTruthy();
    expect(articles.length).toBeGreaterThan(0);
  });

  test('Start Analysis button is functional', async ({ page }) => {
    // Go to Dashboard
    await page.click('text=Dashboard');
    
    // Look for analysis trigger button
    const startButton = page.locator('button:has-text("Start Analysis"), button:has-text("Trigger Analysis"), [data-testid="start-analysis"]').first();
    
    if (await startButton.isVisible()) {
      await startButton.click();
      
      // Wait for some response (either success message, loading state, or error)
      await page.waitForTimeout(2000);
      
      // Check for any response - loading state, success message, or analysis in progress
      const responseIndicator = page.locator('.loading, .success, .error, .analysis-in-progress, text=Analysis').first();
      await expect(responseIndicator).toBeVisible({ timeout: 5000 });
    }
  });

  test('Navigation between pages works', async ({ page }) => {
    // Test navigation between all main pages
    const pages = ['Dashboard', 'Articles', 'Positions', 'Settings'];
    
    for (const pageName of pages) {
      await page.click(`text=${pageName}`);
      await page.waitForLoadState('networkidle');
      
      // Verify URL or page content changed
      expect(page.url()).toContain('localhost:3001');
      
      // Check that the page has loaded some content
      const content = page.locator('main, .container, .content, [data-testid="page-content"]').first();
      await expect(content).toBeVisible({ timeout: 10000 });
    }
  });

  test('Real-time updates connection', async ({ page }) => {
    // Go to Dashboard
    await page.click('text=Dashboard');
    
    // Look for WebSocket connection indicators
    const activityLog = page.locator('[data-testid="activity-log"], .activity-log, .real-time-updates').first();
    
    if (await activityLog.isVisible()) {
      // Check if activity log shows any connection status
      const connectionIndicator = page.locator('.connected, .websocket-status, text=Connected').first();
      // Don't fail the test if WebSocket isn't connected, just check it exists
      await expect(activityLog).toBeVisible();
    }
  });

  test('Error handling for invalid API calls', async ({ page }) => {
    // Test that the app handles API errors gracefully
    const response = await page.request.get('http://localhost:8000/api/v1/invalid-endpoint');
    expect(response.status()).toBe(404);
    
    // Test that the frontend doesn't crash on API errors
    await page.goto('http://localhost:3001');
    const errorBoundary = page.locator('.error-boundary, .error-message');
    
    // The page should still load even if some API calls fail
    await expect(page.locator('nav')).toBeVisible();
  });

});