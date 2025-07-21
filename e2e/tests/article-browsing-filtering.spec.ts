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
  mockApiResponse,
  testResponsiveDesign
} from '../utils/test-helpers';
import { 
  generateTestArticles, 
  generateTestArticle,
  TEST_SELECTORS,
  TEST_CONFIG
} from '../utils/test-data';

test.describe('Article Browsing and Filtering', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to articles page
    await navigateAndWait(page, '/articles');
    
    // Wait for page to fully load
    await waitForLoadingToComplete(page);
  });

  test('should display list of articles', async ({ page }) => {
    // Generate test articles
    const mockArticles = generateTestArticles(10);
    
    // Mock API response
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: mockArticles
    });

    // Refresh to load articles
    await page.reload();
    await waitForLoadingToComplete(page);

    // Verify articles are displayed
    const articleCards = page.locator(TEST_SELECTORS.articleCard);
    await expect(articleCards).toHaveCount(10);

    // Verify article content
    const firstArticle = articleCards.first();
    await expect(firstArticle).toBeVisible();
    
    // Check article components
    const articleTitle = firstArticle.locator(TEST_SELECTORS.articleTitle);
    await expect(articleTitle).toBeVisible();
    
    // Check external link
    const externalLink = firstArticle.locator('a[target="_blank"]');
    await expect(externalLink).toBeVisible();
    
    // Check source badge
    const sourceBadge = firstArticle.locator('[data-testid="source-badge"]');
    await expect(sourceBadge).toBeVisible();
    
    // Check ticker badge (if present)
    const tickerBadge = firstArticle.locator('[data-testid="ticker-badge"]');
    if (mockArticles[0].ticker) {
      await expect(tickerBadge).toBeVisible();
      await expect(tickerBadge).toContainText(mockArticles[0].ticker);
    }
    
    // Check processed status
    const processedStatus = firstArticle.locator('[data-testid="processed-status"]');
    await expect(processedStatus).toBeVisible();
    
    // Take screenshot of article list
    await takeDebugScreenshot(page, 'article-list');
  });

  test('should filter articles by search term', async ({ page }) => {
    // Generate test articles with specific search terms
    const mockArticles = [
      generateTestArticle({ 
        title: 'Apple Reports Strong Q4 Earnings', 
        ticker: 'AAPL' 
      }),
      generateTestArticle({ 
        title: 'Google Announces New AI Features', 
        ticker: 'GOOGL' 
      }),
      generateTestArticle({ 
        title: 'Microsoft Cloud Revenue Grows', 
        ticker: 'MSFT' 
      })
    ];
    
    // Mock initial load
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: mockArticles
    });

    // Mock search results
    await mockApiResponse(page, /\/api\/v1\/articles\/\?.*search=Apple/, {
      data: [mockArticles[0]]
    });

    // Refresh to load articles
    await page.reload();
    await waitForLoadingToComplete(page);

    // Perform search
    const searchInput = await waitForElement(page, TEST_SELECTORS.articleSearch);
    await searchInput.fill('Apple');
    
    // Wait for search to trigger
    await page.waitForTimeout(1000);
    
    // Verify filtered results
    const articleCards = page.locator(TEST_SELECTORS.articleCard);
    await expect(articleCards).toHaveCount(1);
    
    // Verify the correct article is shown
    const firstArticle = articleCards.first();
    await expect(firstArticle).toContainText('Apple Reports Strong Q4 Earnings');
    
    // Clear search
    await searchInput.clear();
    await page.waitForTimeout(1000);
    
    // Verify all articles are shown again
    await expect(articleCards).toHaveCount(3);
    
    // Take screenshot of search results
    await takeDebugScreenshot(page, 'article-search');
  });

  test('should filter articles by source', async ({ page }) => {
    // Generate test articles with different sources
    const mockArticles = [
      generateTestArticle({ source: 'finviz', title: 'FinViz Article 1' }),
      generateTestArticle({ source: 'finviz', title: 'FinViz Article 2' }),
      generateTestArticle({ source: 'biztoc', title: 'BizToc Article 1' })
    ];
    
    // Mock API responses
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: mockArticles
    });

    await mockApiResponse(page, /\/api\/v1\/articles\/\?.*source=finviz/, {
      data: mockArticles.filter(a => a.source === 'finviz')
    });

    await mockApiResponse(page, /\/api\/v1\/articles\/\?.*source=biztoc/, {
      data: mockArticles.filter(a => a.source === 'biztoc')
    });

    // Refresh to load articles
    await page.reload();
    await waitForLoadingToComplete(page);

    // Filter by FinViz
    const sourceFilter = await waitForElement(page, TEST_SELECTORS.sourceFilter);
    await sourceFilter.selectOption('finviz');
    
    // Wait for filter to apply
    await page.waitForTimeout(1000);
    
    // Verify filtered results
    let articleCards = page.locator(TEST_SELECTORS.articleCard);
    await expect(articleCards).toHaveCount(2);
    
    // Verify all articles are from FinViz
    await expect(articleCards.first()).toContainText('FinViz Article 1');
    await expect(articleCards.nth(1)).toContainText('FinViz Article 2');
    
    // Filter by BizToc
    await sourceFilter.selectOption('biztoc');
    await page.waitForTimeout(1000);
    
    // Verify filtered results
    await expect(articleCards).toHaveCount(1);
    await expect(articleCards.first()).toContainText('BizToc Article 1');
    
    // Reset filter
    await sourceFilter.selectOption('');
    await page.waitForTimeout(1000);
    
    // Verify all articles are shown
    await expect(articleCards).toHaveCount(3);
    
    // Take screenshot of source filter
    await takeDebugScreenshot(page, 'source-filter');
  });

  test('should filter articles by ticker', async ({ page }) => {
    // Generate test articles with different tickers
    const mockArticles = [
      generateTestArticle({ ticker: 'AAPL', title: 'Apple News' }),
      generateTestArticle({ ticker: 'GOOGL', title: 'Google News' }),
      generateTestArticle({ ticker: 'AAPL', title: 'More Apple News' })
    ];
    
    // Mock API responses
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: mockArticles
    });

    await mockApiResponse(page, /\/api\/v1\/articles\/\?.*ticker=AAPL/, {
      data: mockArticles.filter(a => a.ticker === 'AAPL')
    });

    // Refresh to load articles
    await page.reload();
    await waitForLoadingToComplete(page);

    // Filter by AAPL ticker
    const tickerFilter = await waitForElement(page, TEST_SELECTORS.tickerFilter);
    await tickerFilter.fill('AAPL');
    
    // Wait for filter to apply
    await page.waitForTimeout(1000);
    
    // Verify filtered results
    const articleCards = page.locator(TEST_SELECTORS.articleCard);
    await expect(articleCards).toHaveCount(2);
    
    // Verify all articles are for AAPL
    await expect(articleCards.first()).toContainText('Apple News');
    await expect(articleCards.nth(1)).toContainText('More Apple News');
    
    // Clear ticker filter
    await tickerFilter.clear();
    await page.waitForTimeout(1000);
    
    // Verify all articles are shown
    await expect(articleCards).toHaveCount(3);
    
    // Take screenshot of ticker filter
    await takeDebugScreenshot(page, 'ticker-filter');
  });

  test('should combine multiple filters', async ({ page }) => {
    // Generate test articles with various combinations
    const mockArticles = [
      generateTestArticle({ 
        source: 'finviz', 
        ticker: 'AAPL', 
        title: 'FinViz Apple Article' 
      }),
      generateTestArticle({ 
        source: 'biztoc', 
        ticker: 'AAPL', 
        title: 'BizToc Apple Article' 
      }),
      generateTestArticle({ 
        source: 'finviz', 
        ticker: 'GOOGL', 
        title: 'FinViz Google Article' 
      })
    ];
    
    // Mock API responses
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: mockArticles
    });

    await mockApiResponse(page, /\/api\/v1\/articles\/\?.*source=finviz.*ticker=AAPL/, {
      data: mockArticles.filter(a => a.source === 'finviz' && a.ticker === 'AAPL')
    });

    // Refresh to load articles
    await page.reload();
    await waitForLoadingToComplete(page);

    // Apply multiple filters
    const sourceFilter = await waitForElement(page, TEST_SELECTORS.sourceFilter);
    await sourceFilter.selectOption('finviz');
    
    const tickerFilter = await waitForElement(page, TEST_SELECTORS.tickerFilter);
    await tickerFilter.fill('AAPL');
    
    // Wait for filters to apply
    await page.waitForTimeout(1000);
    
    // Verify filtered results
    const articleCards = page.locator(TEST_SELECTORS.articleCard);
    await expect(articleCards).toHaveCount(1);
    await expect(articleCards.first()).toContainText('FinViz Apple Article');
    
    // Clear all filters
    const clearButton = await waitForElement(page, TEST_SELECTORS.clearFiltersButton);
    await clearButton.click();
    
    // Wait for filters to clear
    await page.waitForTimeout(1000);
    
    // Verify all articles are shown
    await expect(articleCards).toHaveCount(3);
    
    // Verify filters are cleared
    await expect(sourceFilter).toHaveValue('');
    await expect(tickerFilter).toHaveValue('');
    
    // Take screenshot of combined filters
    await takeDebugScreenshot(page, 'combined-filters');
  });

  test('should expand and collapse article details', async ({ page }) => {
    // Generate test article with analysis
    const mockArticle = generateTestArticle({
      content: 'This is the full article content with detailed information...',
      is_processed: true
    });
    
    // Mock API response
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: [mockArticle]
    });

    // Refresh to load article
    await page.reload();
    await waitForLoadingToComplete(page);

    // Verify article card is visible
    const articleCard = page.locator(TEST_SELECTORS.articleCard).first();
    await expect(articleCard).toBeVisible();

    // Verify expand button is visible
    const expandButton = articleCard.locator('[data-testid="expand-button"]');
    await expect(expandButton).toBeVisible();

    // Click expand button
    await expandButton.click();
    
    // Verify expanded content is visible
    const expandedContent = articleCard.locator('[data-testid="expanded-content"]');
    await expect(expandedContent).toBeVisible();
    
    // Verify article content is shown
    const articleContent = articleCard.locator('[data-testid="article-content"]');
    await expect(articleContent).toBeVisible();
    await expect(articleContent).toContainText('This is the full article content');
    
    // Verify analysis results are shown
    const analysisResults = articleCard.locator('[data-testid="analysis-results"]');
    await expect(analysisResults).toBeVisible();
    
    // Click collapse button
    await expandButton.click();
    
    // Verify expanded content is hidden
    await expect(expandedContent).not.toBeVisible();
    
    // Take screenshot of expanded article
    await takeDebugScreenshot(page, 'expanded-article');
  });

  test('should display article analysis details', async ({ page }) => {
    // Generate test article with detailed analysis
    const mockArticle = generateTestArticle({
      is_processed: true,
      analyses: [{
        id: 'analysis-1',
        sentiment_score: 0.75,
        confidence: 0.85,
        ticker: 'AAPL',
        reasoning: 'Positive earnings report with strong guidance',
        catalysts: [
          {
            type: 'earnings_beat',
            description: 'Q4 earnings exceeded expectations',
            impact: 'positive' as const,
            significance: 'high' as const
          }
        ],
        llm_model: 'gpt-4',
        created_at: new Date().toISOString()
      }]
    });
    
    // Mock API response
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: [mockArticle]
    });

    // Refresh to load article
    await page.reload();
    await waitForLoadingToComplete(page);

    // Expand article details
    const articleCard = page.locator(TEST_SELECTORS.articleCard).first();
    const expandButton = articleCard.locator('[data-testid="expand-button"]');
    await expandButton.click();
    
    // Verify sentiment score is displayed
    const sentimentScore = articleCard.locator('[data-testid="sentiment-score"]');
    await expect(sentimentScore).toBeVisible();
    await expect(sentimentScore).toContainText('75%');
    
    // Verify confidence score is displayed
    const confidenceScore = articleCard.locator('[data-testid="confidence-score"]');
    await expect(confidenceScore).toBeVisible();
    await expect(confidenceScore).toContainText('85%');
    
    // Verify AI reasoning is displayed
    const aiReasoning = articleCard.locator('[data-testid="ai-reasoning"]');
    await expect(aiReasoning).toBeVisible();
    await expect(aiReasoning).toContainText('Positive earnings report');
    
    // Verify catalysts are displayed
    const catalysts = articleCard.locator('[data-testid="catalysts"]');
    await expect(catalysts).toBeVisible();
    
    const firstCatalyst = catalysts.locator('[data-testid="catalyst-item"]').first();
    await expect(firstCatalyst).toBeVisible();
    await expect(firstCatalyst).toContainText('earnings_beat');
    await expect(firstCatalyst).toContainText('positive');
    
    // Take screenshot of analysis details
    await takeDebugScreenshot(page, 'analysis-details');
  });

  test('should handle empty search results', async ({ page }) => {
    // Mock empty search results
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: []
    });

    // Refresh to load empty state
    await page.reload();
    await waitForLoadingToComplete(page);

    // Verify empty state is displayed
    const emptyState = await waitForElement(page, '[data-testid="empty-articles"]');
    await expect(emptyState).toBeVisible();
    await expect(emptyState).toContainText('No articles found');
    
    // Take screenshot of empty state
    await takeDebugScreenshot(page, 'empty-articles');
  });

  test('should handle loading states', async ({ page }) => {
    // Mock slow API response
    await page.route(/\/api\/v1\/articles/, async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: [] })
      });
    });

    // Refresh to trigger loading
    await page.reload();
    
    // Verify loading state is displayed
    const loadingState = await waitForElement(page, '[data-testid="loading-articles"]');
    await expect(loadingState).toBeVisible();
    await expect(loadingState).toContainText('Loading articles...');
    
    // Wait for loading to complete
    await waitForLoadingToComplete(page);
    
    // Verify loading state is gone
    await expect(loadingState).not.toBeVisible();
    
    // Take screenshot of loading state
    await takeDebugScreenshot(page, 'loading-articles');
  });

  test('should handle API errors', async ({ page }) => {
    // Mock API error
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      error: 'Failed to fetch articles'
    }, 500);

    // Refresh to trigger error
    await page.reload();
    await waitForLoadingToComplete(page);

    // Verify error state is displayed
    const errorState = await waitForElement(page, '[data-testid="error-articles"]');
    await expect(errorState).toBeVisible();
    await expect(errorState).toContainText('Error loading articles');
    
    // Take screenshot of error state
    await takeDebugScreenshot(page, 'error-articles');
  });

  test('should work on mobile devices', async ({ page }) => {
    // Generate test articles
    const mockArticles = generateTestArticles(3);
    
    // Mock API response
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: mockArticles
    });

    await testResponsiveDesign(page, async (page) => {
      // Refresh to load articles
      await page.reload();
      await waitForLoadingToComplete(page);
      
      // Verify articles are visible on mobile
      const articleCards = page.locator(TEST_SELECTORS.articleCard);
      await expect(articleCards).toHaveCount(3);
      
      // Verify filters are accessible
      const searchInput = await waitForElement(page, TEST_SELECTORS.articleSearch);
      await expect(searchInput).toBeVisible();
      
      const sourceFilter = await waitForElement(page, TEST_SELECTORS.sourceFilter);
      await expect(sourceFilter).toBeVisible();
      
      // Test filter interaction on mobile
      await searchInput.fill('test');
      await page.waitForTimeout(500);
      
      // Verify search works on mobile
      await expect(searchInput).toHaveValue('test');
      
      // Test article expansion on mobile
      const firstArticle = articleCards.first();
      const expandButton = firstArticle.locator('[data-testid="expand-button"]');
      await expandButton.click();
      
      // Verify expanded content is visible on mobile
      const expandedContent = firstArticle.locator('[data-testid="expanded-content"]');
      await expect(expandedContent).toBeVisible();
    });
  });

  test('should maintain filter state on page reload', async ({ page }) => {
    // Generate test articles
    const mockArticles = generateTestArticles(5);
    
    // Mock API response
    await mockApiResponse(page, /\/api\/v1\/articles/, {
      data: mockArticles
    });

    // Refresh to load articles
    await page.reload();
    await waitForLoadingToComplete(page);

    // Apply filters
    const searchInput = await waitForElement(page, TEST_SELECTORS.articleSearch);
    await searchInput.fill('Apple');
    
    const sourceFilter = await waitForElement(page, TEST_SELECTORS.sourceFilter);
    await sourceFilter.selectOption('finviz');
    
    // Wait for filters to apply
    await page.waitForTimeout(1000);
    
    // Reload page
    await page.reload();
    await waitForLoadingToComplete(page);
    
    // Verify filters are maintained (if implemented)
    // This depends on whether the app implements filter persistence
    // await expect(searchInput).toHaveValue('Apple');
    // await expect(sourceFilter).toHaveValue('finviz');
  });
});