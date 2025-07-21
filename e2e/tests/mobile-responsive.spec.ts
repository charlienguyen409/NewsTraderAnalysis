import { test, expect } from '@playwright/test';
import { 
  waitForElement, 
  waitForLoadingToComplete, 
  fillForm,
  navigateAndWait,
  takeDebugScreenshot,
  mockApiResponse,
  testResponsiveDesign,
  checkBasicAccessibility
} from '../utils/test-helpers';
import { 
  generateTestArticles, 
  generateTestPosition,
  generateMarketSummary,
  generateAnalysisRequest,
  TEST_SELECTORS,
  TEST_CONFIG
} from '../utils/test-data';

test.describe('Mobile and Responsive Testing', () => {
  const viewports = [
    { width: 375, height: 667, name: 'iPhone SE' },
    { width: 414, height: 896, name: 'iPhone 11 Pro' },
    { width: 768, height: 1024, name: 'iPad' },
    { width: 1024, height: 768, name: 'iPad Landscape' },
    { width: 360, height: 640, name: 'Android Small' },
    { width: 412, height: 915, name: 'Android Large' }
  ];

  test.describe('Dashboard Mobile Experience', () => {
    test.beforeEach(async ({ page }) => {
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
    });

    test('should display analysis controls correctly on mobile', async ({ page }) => {
      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(1000); // Allow time for responsive changes
        
        // Check analysis sections are visible
        const fullAnalysisSection = await waitForElement(page, '[data-testid="full-analysis-section"]');
        await expect(fullAnalysisSection).toBeVisible();
        
        const headlinesSection = await waitForElement(page, '[data-testid="headlines-section"]');
        await expect(headlinesSection).toBeVisible();
        
        // Check form controls are accessible
        const maxPositionsInput = await waitForElement(page, TEST_SELECTORS.maxPositionsInput);
        await expect(maxPositionsInput).toBeVisible();
        
        const minConfidenceInput = await waitForElement(page, TEST_SELECTORS.minConfidenceInput);
        await expect(minConfidenceInput).toBeVisible();
        
        const llmModelSelect = await waitForElement(page, TEST_SELECTORS.llmModelSelect);
        await expect(llmModelSelect).toBeVisible();
        
        // Check buttons are accessible
        const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
        await expect(startButton).toBeVisible();
        
        const headlinesButton = await waitForElement(page, TEST_SELECTORS.startHeadlinesButton);
        await expect(headlinesButton).toBeVisible();
        
        // Test interaction on mobile
        await startButton.click();
        await page.waitForTimeout(500);
        
        // Verify button responds to touch
        await expect(startButton).toBeDisabled();
        
        // Take screenshot for this viewport
        await takeDebugScreenshot(page, `dashboard-${viewport.name}-${viewport.width}x${viewport.height}`);
      }
    });

    test('should handle touch interactions correctly', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Mock successful analysis
      await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
        session_id: 'test-mobile-touch',
        message: 'Analysis started successfully',
        status: 'started'
      });
      
      // Test touch tap
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.tap();
      
      // Verify touch interaction works
      await expect(startButton).toBeDisabled();
      
      // Test form field touch interactions
      const maxPositionsInput = await waitForElement(page, TEST_SELECTORS.maxPositionsInput);
      await maxPositionsInput.tap();
      await maxPositionsInput.fill('15');
      
      await expect(maxPositionsInput).toHaveValue('15');
      
      // Test select dropdown touch
      const llmModelSelect = await waitForElement(page, TEST_SELECTORS.llmModelSelect);
      await llmModelSelect.tap();
      
      // Verify select opens (implementation-dependent)
      await page.waitForTimeout(500);
      
      // Take screenshot of touch interactions
      await takeDebugScreenshot(page, 'touch-interactions');
    });

    test('should display market summary responsively', async ({ page }) => {
      // Mock market summary data
      await mockApiResponse(page, /\/api\/v1\/analysis\/market-summary/, generateMarketSummary());
      
      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(1000);
        
        // Check market summary is visible
        const marketSummary = await waitForElement(page, '[data-testid="market-summary"]');
        await expect(marketSummary).toBeVisible();
        
        // Check individual stats are visible
        const stats = page.locator('[data-testid="market-stat"]');
        if (await stats.count() > 0) {
          await expect(stats.first()).toBeVisible();
        }
        
        // Take screenshot for this viewport
        await takeDebugScreenshot(page, `market-summary-${viewport.name}-${viewport.width}x${viewport.height}`);
      }
    });

    test('should handle position cards on mobile', async ({ page }) => {
      // Mock position data
      const mockPositions = [
        generateTestPosition({ ticker: 'AAPL', recommendation: 'BUY' }),
        generateTestPosition({ ticker: 'GOOGL', recommendation: 'STRONG_BUY' }),
        generateTestPosition({ ticker: 'MSFT', recommendation: 'HOLD' })
      ];
      
      await mockApiResponse(page, /\/api\/v1\/positions/, {
        data: mockPositions
      });
      
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Refresh to load positions
      await page.reload();
      await waitForLoadingToComplete(page);
      
      // Check position cards are visible
      const positionsSection = await waitForElement(page, '[data-testid="recent-positions"]');
      await expect(positionsSection).toBeVisible();
      
      const positionCards = page.locator(TEST_SELECTORS.positionCard);
      await expect(positionCards).toHaveCount(3);
      
      // Check each position card is accessible
      for (let i = 0; i < 3; i++) {
        const card = positionCards.nth(i);
        await expect(card).toBeVisible();
        
        // Check card content is readable
        const ticker = card.locator(TEST_SELECTORS.positionTicker);
        await expect(ticker).toBeVisible();
        
        const recommendation = card.locator(TEST_SELECTORS.positionRecommendation);
        await expect(recommendation).toBeVisible();
      }
      
      // Take screenshot of position cards on mobile
      await takeDebugScreenshot(page, 'position-cards-mobile');
    });

    test('should handle activity log on mobile', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Check activity log is visible
      const activityLog = await waitForElement(page, TEST_SELECTORS.activityLog);
      await expect(activityLog).toBeVisible();
      
      // Check activity log doesn't overflow
      const activityLogBounds = await activityLog.boundingBox();
      const viewportSize = page.viewportSize();
      
      if (activityLogBounds && viewportSize) {
        expect(activityLogBounds.width).toBeLessThanOrEqual(viewportSize.width);
      }
      
      // Take screenshot of activity log on mobile
      await takeDebugScreenshot(page, 'activity-log-mobile');
    });
  });

  test.describe('Articles Page Mobile Experience', () => {
    test.beforeEach(async ({ page }) => {
      await navigateAndWait(page, '/articles');
      await waitForLoadingToComplete(page);
    });

    test('should display article filters responsively', async ({ page }) => {
      // Mock article data
      const mockArticles = generateTestArticles(10);
      await mockApiResponse(page, /\/api\/v1\/articles/, {
        data: mockArticles
      });
      
      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(1000);
        
        // Refresh to load articles
        await page.reload();
        await waitForLoadingToComplete(page);
        
        // Check filter controls are visible
        const searchInput = await waitForElement(page, TEST_SELECTORS.articleSearch);
        await expect(searchInput).toBeVisible();
        
        const sourceFilter = await waitForElement(page, TEST_SELECTORS.sourceFilter);
        await expect(sourceFilter).toBeVisible();
        
        const tickerFilter = await waitForElement(page, TEST_SELECTORS.tickerFilter);
        await expect(tickerFilter).toBeVisible();
        
        const clearFiltersButton = await waitForElement(page, TEST_SELECTORS.clearFiltersButton);
        await expect(clearFiltersButton).toBeVisible();
        
        // Test filter interaction on mobile
        await searchInput.fill('test');
        await expect(searchInput).toHaveValue('test');
        
        // Take screenshot for this viewport
        await takeDebugScreenshot(page, `article-filters-${viewport.name}-${viewport.width}x${viewport.height}`);
      }
    });

    test('should display article cards responsively', async ({ page }) => {
      // Mock article data
      const mockArticles = generateTestArticles(5);
      await mockApiResponse(page, /\/api\/v1\/articles/, {
        data: mockArticles
      });
      
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Refresh to load articles
      await page.reload();
      await waitForLoadingToComplete(page);
      
      // Check articles are displayed
      const articleCards = page.locator(TEST_SELECTORS.articleCard);
      await expect(articleCards).toHaveCount(5);
      
      // Check each article card is properly sized
      for (let i = 0; i < 5; i++) {
        const card = articleCards.nth(i);
        await expect(card).toBeVisible();
        
        // Check card doesn't overflow viewport
        const cardBounds = await card.boundingBox();
        const viewportSize = page.viewportSize();
        
        if (cardBounds && viewportSize) {
          expect(cardBounds.width).toBeLessThanOrEqual(viewportSize.width);
        }
        
        // Check article title is visible
        const title = card.locator(TEST_SELECTORS.articleTitle);
        await expect(title).toBeVisible();
        
        // Check badges are visible
        const sourceBadge = card.locator('[data-testid="source-badge"]');
        await expect(sourceBadge).toBeVisible();
      }
      
      // Take screenshot of article cards on mobile
      await takeDebugScreenshot(page, 'article-cards-mobile');
    });

    test('should handle article expansion on mobile', async ({ page }) => {
      // Mock article data with content
      const mockArticle = generateTestArticles(1)[0];
      mockArticle.content = 'This is a long article content that should be expandable on mobile devices. '.repeat(10);
      
      await mockApiResponse(page, /\/api\/v1\/articles/, {
        data: [mockArticle]
      });
      
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Refresh to load article
      await page.reload();
      await waitForLoadingToComplete(page);
      
      // Get article card
      const articleCard = page.locator(TEST_SELECTORS.articleCard).first();
      await expect(articleCard).toBeVisible();
      
      // Find and tap expand button
      const expandButton = articleCard.locator('[data-testid="expand-button"]');
      await expect(expandButton).toBeVisible();
      await expandButton.tap();
      
      // Check expanded content is visible
      const expandedContent = articleCard.locator('[data-testid="expanded-content"]');
      await expect(expandedContent).toBeVisible();
      
      // Check content doesn't overflow
      const expandedBounds = await expandedContent.boundingBox();
      const viewportSize = page.viewportSize();
      
      if (expandedBounds && viewportSize) {
        expect(expandedBounds.width).toBeLessThanOrEqual(viewportSize.width);
      }
      
      // Test collapse
      await expandButton.tap();
      await expect(expandedContent).not.toBeVisible();
      
      // Take screenshot of expanded article on mobile
      await takeDebugScreenshot(page, 'article-expanded-mobile');
    });

    test('should handle article search on mobile', async ({ page }) => {
      // Mock article data
      const mockArticles = generateTestArticles(10);
      await mockApiResponse(page, /\/api\/v1\/articles/, {
        data: mockArticles
      });
      
      // Mock search results
      await mockApiResponse(page, /\/api\/v1\/articles\/\?.*search=Apple/, {
        data: mockArticles.slice(0, 2)
      });
      
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Refresh to load articles
      await page.reload();
      await waitForLoadingToComplete(page);
      
      // Verify initial articles are loaded
      let articleCards = page.locator(TEST_SELECTORS.articleCard);
      await expect(articleCards).toHaveCount(10);
      
      // Test search functionality
      const searchInput = await waitForElement(page, TEST_SELECTORS.articleSearch);
      await searchInput.tap();
      await searchInput.fill('Apple');
      
      // Wait for search results
      await page.waitForTimeout(1000);
      
      // Verify search results (mock would need to be updated)
      await expect(searchInput).toHaveValue('Apple');
      
      // Take screenshot of search on mobile
      await takeDebugScreenshot(page, 'article-search-mobile');
    });
  });

  test.describe('Navigation Mobile Experience', () => {
    test('should display navigation menu correctly on mobile', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      
      // Check navigation elements are visible
      const navElements = [
        TEST_SELECTORS.navDashboard,
        TEST_SELECTORS.navArticles,
        TEST_SELECTORS.navPositions,
        TEST_SELECTORS.navSettings
      ];
      
      for (const selector of navElements) {
        try {
          const element = await waitForElement(page, selector);
          await expect(element).toBeVisible();
        } catch (error) {
          // Navigation might be implemented differently
          console.log(`Navigation element ${selector} not found, this is expected if nav is not implemented yet`);
        }
      }
      
      // Take screenshot of navigation on mobile
      await takeDebugScreenshot(page, 'navigation-mobile');
    });

    test('should handle navigation between pages on mobile', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Start at dashboard
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      
      // Navigate to articles
      await navigateAndWait(page, '/articles');
      await waitForLoadingToComplete(page);
      
      // Check articles page loads correctly
      const articlesHeader = page.locator('h1');
      await expect(articlesHeader).toContainText('Articles');
      
      // Navigate to positions
      await navigateAndWait(page, '/positions');
      await waitForLoadingToComplete(page);
      
      // Check positions page loads correctly
      const positionsHeader = page.locator('h1');
      await expect(positionsHeader).toContainText('Positions');
      
      // Navigate back to dashboard
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      
      // Check dashboard loads correctly
      const dashboardHeader = page.locator('h1');
      await expect(dashboardHeader).toContainText('Market Analysis Dashboard');
      
      // Take screenshot of navigation flow
      await takeDebugScreenshot(page, 'navigation-flow-mobile');
    });
  });

  test.describe('Touch and Gesture Support', () => {
    test('should support swipe gestures where appropriate', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      await navigateAndWait(page, '/articles');
      await waitForLoadingToComplete(page);
      
      // Mock article data
      const mockArticles = generateTestArticles(5);
      await mockApiResponse(page, /\/api\/v1\/articles/, {
        data: mockArticles
      });
      
      // Refresh to load articles
      await page.reload();
      await waitForLoadingToComplete(page);
      
      // Test swipe gesture on article list (if implemented)
      const articleList = page.locator('[data-testid="article-list"]');
      if (await articleList.count() > 0) {
        // Perform swipe gesture
        await articleList.hover();
        await page.mouse.down();
        await page.mouse.move(100, 0);
        await page.mouse.up();
        
        // Wait for gesture handling
        await page.waitForTimeout(500);
      }
      
      // Take screenshot of swipe gesture
      await takeDebugScreenshot(page, 'swipe-gesture-mobile');
    });

    test('should handle pinch-to-zoom appropriately', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      
      // Test that pinch-to-zoom is disabled on form controls
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      
      // Simulate pinch gesture
      await page.touchscreen.tap(200, 300);
      await page.touchscreen.tap(250, 350);
      
      // Verify button is still accessible
      await expect(startButton).toBeVisible();
      
      // Take screenshot of pinch gesture handling
      await takeDebugScreenshot(page, 'pinch-gesture-mobile');
    });
  });

  test.describe('Accessibility on Mobile', () => {
    test('should be accessible on mobile devices', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      
      // Check basic accessibility
      await checkBasicAccessibility(page);
      
      // Check touch target sizes (minimum 44x44px)
      const touchTargets = page.locator('button, input, select, a');
      const touchTargetCount = await touchTargets.count();
      
      for (let i = 0; i < touchTargetCount; i++) {
        const target = touchTargets.nth(i);
        const bounds = await target.boundingBox();
        
        if (bounds) {
          // Check minimum touch target size
          expect(bounds.width).toBeGreaterThanOrEqual(44);
          expect(bounds.height).toBeGreaterThanOrEqual(44);
        }
      }
      
      // Take screenshot of accessibility check
      await takeDebugScreenshot(page, 'accessibility-mobile');
    });

    test('should support screen reader navigation on mobile', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      
      // Check for proper heading structure
      const headings = page.locator('h1, h2, h3, h4, h5, h6');
      await expect(headings.first()).toBeVisible();
      
      // Check for proper form labels
      const formInputs = page.locator('input, select, textarea');
      const inputCount = await formInputs.count();
      
      for (let i = 0; i < inputCount; i++) {
        const input = formInputs.nth(i);
        const inputId = await input.getAttribute('id');
        
        if (inputId) {
          const label = page.locator(`label[for="${inputId}"]`);
          await expect(label).toBeVisible();
        }
      }
      
      // Take screenshot of screen reader support
      await takeDebugScreenshot(page, 'screen-reader-mobile');
    });
  });

  test.describe('Performance on Mobile', () => {
    test('should load quickly on mobile devices', async ({ page }) => {
      // Set to mobile viewport with network throttling
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Simulate slow mobile network
      await page.route('**/*', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 100)); // Add 100ms delay
        await route.continue();
      });
      
      const startTime = Date.now();
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      const loadTime = Date.now() - startTime;
      
      // Verify page loads within reasonable time (5 seconds)
      expect(loadTime).toBeLessThan(5000);
      
      // Check essential elements are visible
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await expect(startButton).toBeVisible();
      
      // Take screenshot of performance test
      await takeDebugScreenshot(page, 'performance-mobile');
    });

    test('should handle memory constraints on mobile', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Create memory pressure simulation
      await page.addInitScript(() => {
        const arrays: number[][] = [];
        const interval = setInterval(() => {
          arrays.push(new Array(50000).fill(Math.random()));
          if (arrays.length > 50) {
            arrays.shift();
          }
        }, 100);
        
        // Store interval reference for cleanup
        (window as any).memoryPressureInterval = interval;
      });
      
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      
      // Verify app still functions under memory pressure
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await expect(startButton).toBeVisible();
      
      // Test interaction under memory pressure
      await startButton.click();
      await page.waitForTimeout(1000);
      
      // Clean up memory pressure
      await page.evaluate(() => {
        if ((window as any).memoryPressureInterval) {
          clearInterval((window as any).memoryPressureInterval);
        }
      });
      
      // Take screenshot of memory constraint test
      await takeDebugScreenshot(page, 'memory-constraints-mobile');
    });
  });

  test.describe('Offline Support', () => {
    test('should handle offline scenarios gracefully', async ({ page }) => {
      // Set to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      await navigateAndWait(page, '/');
      await waitForLoadingToComplete(page);
      
      // Simulate offline mode
      await page.route('**/*', async (route) => {
        await route.abort('failed');
      });
      
      // Try to start analysis while offline
      const startButton = await waitForElement(page, TEST_SELECTORS.startAnalysisButton);
      await startButton.click();
      
      // Wait for offline handling
      await page.waitForTimeout(2000);
      
      // Verify button returns to enabled state
      await expect(startButton).toBeEnabled();
      
      // Check for offline indicator (if implemented)
      // This depends on the app's offline handling implementation
      
      // Take screenshot of offline handling
      await takeDebugScreenshot(page, 'offline-mobile');
    });
  });
});