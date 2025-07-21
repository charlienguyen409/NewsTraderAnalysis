# E2E Testing Guide for Market News Analysis Agent

This guide provides detailed instructions for writing, running, and maintaining end-to-end tests for the Market News Analysis Agent.

## 🎯 Testing Philosophy

### What to Test

1. **Critical User Journeys**: Test complete workflows from user perspective
2. **Cross-browser Compatibility**: Ensure functionality across different browsers
3. **Mobile Experience**: Verify responsive design and touch interactions
4. **Error Scenarios**: Test how the application handles failures
5. **Performance**: Verify acceptable load times and responsiveness

### What NOT to Test

1. **Unit-level Logic**: Leave to unit tests
2. **Internal API Details**: Focus on user-visible behavior
3. **Styling Details**: Unless they affect functionality
4. **Third-party Services**: Mock external dependencies

## 📝 Writing Tests

### Test Structure

```typescript
import { test, expect } from '@playwright/test';
import { 
  waitForElement, 
  navigateAndWait,
  mockApiResponse 
} from '../utils/test-helpers';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await navigateAndWait(page, '/target-page');
  });

  test('should perform expected behavior', async ({ page }) => {
    // Arrange
    await mockApiResponse(page, /api-endpoint/, mockData);
    
    // Act
    const button = await waitForElement(page, '[data-testid="action-button"]');
    await button.click();
    
    // Assert
    await expect(page.locator('[data-testid="result"]')).toBeVisible();
  });
});
```

### Best Practices

#### 1. Use Data Test IDs

```html
<!-- Good: Reliable selector -->
<button data-testid="start-analysis">Start Analysis</button>

<!-- Bad: Fragile selector -->
<button class="btn btn-primary bg-blue-500">Start Analysis</button>
```

```typescript
// Good: Using data-testid
await page.locator('[data-testid="start-analysis"]').click();

// Bad: Using CSS classes
await page.locator('.btn.btn-primary.bg-blue-500').click();
```

#### 2. Mock External Services

```typescript
// Mock API responses for consistent testing
await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
  session_id: 'test-session-123',
  message: 'Analysis started successfully',
  status: 'started'
});
```

#### 3. Wait for Elements and States

```typescript
// Wait for element to be visible
const element = await waitForElement(page, '[data-testid="result"]');

// Wait for loading to complete
await waitForLoadingToComplete(page);

// Wait for API call
await waitForApiRequest(page, '/api/v1/articles');
```

#### 4. Use Helper Functions

```typescript
// Use custom helpers for common actions
await navigateAndWait(page, '/articles');
await fillForm(page, {
  '[data-testid="search-input"]': 'Apple',
  '[data-testid="source-filter"]': 'finviz'
});
```

### Test Data Management

#### Generate Realistic Test Data

```typescript
import { generateTestArticle, generateTestPosition } from '../utils/test-data';

// Generate article with specific properties
const testArticle = generateTestArticle({
  ticker: 'AAPL',
  sentiment_score: 0.75,
  source: 'finviz'
});

// Generate multiple articles
const testArticles = generateTestArticles(10);
```

#### Use Consistent Test Data

```typescript
// Define reusable test data
const MOCK_ARTICLES = [
  generateTestArticle({ ticker: 'AAPL', title: 'Apple Earnings Beat' }),
  generateTestArticle({ ticker: 'GOOGL', title: 'Google AI Breakthrough' }),
  generateTestArticle({ ticker: 'MSFT', title: 'Microsoft Cloud Growth' })
];
```

### Error Testing

#### Test Network Failures

```typescript
test('should handle network failures gracefully', async ({ page }) => {
  // Simulate network failure
  await page.route(/\/api\/v1\/analysis\/start/, async (route) => {
    await route.abort('failed');
  });

  // Try to start analysis
  const startButton = await waitForElement(page, '[data-testid="start-analysis"]');
  await startButton.click();
  
  // Verify graceful handling
  await expect(startButton).toBeEnabled();
});
```

#### Test API Errors

```typescript
test('should display error message for API failures', async ({ page }) => {
  // Mock API error
  await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
    error: 'Internal server error'
  }, 500);

  // Trigger action
  await page.locator('[data-testid="start-analysis"]').click();
  
  // Verify error handling
  await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
});
```

### Mobile Testing

#### Test Multiple Viewports

```typescript
test('should work on mobile devices', async ({ page }) => {
  await testResponsiveDesign(page, async (page) => {
    // Test functionality at current viewport
    const startButton = await waitForElement(page, '[data-testid="start-analysis"]');
    await expect(startButton).toBeVisible();
    
    // Test touch interaction
    await startButton.tap();
    await expect(startButton).toBeDisabled();
  });
});
```

#### Test Touch Interactions

```typescript
test('should support touch gestures', async ({ page }) => {
  // Set mobile viewport
  await page.setViewportSize({ width: 375, height: 667 });
  
  // Test tap interaction
  const articleCard = await waitForElement(page, '[data-testid="article-card"]');
  await articleCard.tap();
  
  // Test swipe gesture (if implemented)
  await page.touchscreen.tap(200, 300);
});
```

## 🚀 Running Tests

### Local Development

```bash
# Run all tests
npm test

# Run specific test file
npx playwright test market-analysis-trigger.spec.ts

# Run specific test
npx playwright test -g "should start analysis"

# Run with specific browser
npx playwright test --project=firefox

# Run in headed mode (visible browser)
npx playwright test --headed

# Run in debug mode
npx playwright test --debug

# Run tests matching pattern
npx playwright test --grep="mobile"
```

### Using Test Runner Script

```bash
# Run with default settings
./scripts/run-tests.sh

# Run with specific browser
./scripts/run-tests.sh --browser webkit

# Run in headed mode
./scripts/run-tests.sh --headed

# Run in debug mode
./scripts/run-tests.sh --debug

# Use Docker environment
./scripts/run-tests.sh --docker
```

### CI Environment

```bash
# Run in CI mode
CI=true npm test

# Run with Docker (production-like)
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🐛 Debugging

### Debug Single Test

```bash
# Run specific test in debug mode
npx playwright test market-analysis-trigger.spec.ts --debug

# Open Playwright inspector
npx playwright test --ui
```

### Common Issues and Solutions

#### Element Not Found

```typescript
// Problem: Element not found
await page.locator('[data-testid="button"]').click();

// Solution: Wait for element
const button = await waitForElement(page, '[data-testid="button"]');
await button.click();

// Or use Playwright's built-in waiting
await expect(page.locator('[data-testid="button"]')).toBeVisible();
await page.locator('[data-testid="button"]').click();
```

#### Flaky Tests Due to Timing

```typescript
// Problem: Race condition
await page.click('[data-testid="submit"]');
await expect(page.locator('[data-testid="result"]')).toBeVisible();

// Solution: Wait for API call or loading state
await page.click('[data-testid="submit"]');
await waitForApiRequest(page, '/api/submit');
await expect(page.locator('[data-testid="result"]')).toBeVisible();
```

#### WebSocket Testing Issues

```typescript
// Problem: WebSocket not connecting in test
test('should receive real-time updates', async ({ page }) => {
  // Solution: Mock WebSocket behavior
  await page.evaluateOnNewDocument(() => {
    const originalWebSocket = window.WebSocket;
    window.WebSocket = class extends originalWebSocket {
      constructor(url: string) {
        super(url);
        setTimeout(() => {
          this.onopen?.(new Event('open'));
        }, 100);
      }
    };
  });
});
```

### Screenshots and Videos

```typescript
// Take screenshot for debugging
await takeDebugScreenshot(page, 'test-step-name');

// Configure video recording in playwright.config.ts
use: {
  video: 'retain-on-failure',
  screenshot: 'only-on-failure'
}
```

## 📊 Test Reports

### Viewing Reports

```bash
# Generate and view HTML report
npm run show-report

# View specific test results
npx playwright show-report
```

### CI Reports

Reports are automatically generated in CI and uploaded as artifacts:
- HTML report with screenshots
- JUnit XML for integration
- JSON results for processing

## 🔄 Maintenance

### Updating Tests for UI Changes

1. **Identify breaking changes** in selectors or behavior
2. **Update test selectors** to use stable data-testid attributes
3. **Modify test expectations** if behavior changed intentionally
4. **Update mock data** to match new API contracts

### Adding New Tests

1. **Choose appropriate test file** or create new one
2. **Follow naming conventions**: `feature-description.spec.ts`
3. **Use existing helpers** and patterns
4. **Add test to CI** if needed
5. **Update documentation**

### Performance Monitoring

```typescript
// Monitor page load performance
test('should load within acceptable time', async ({ page }) => {
  const startTime = Date.now();
  await page.goto('/');
  await waitForLoadingToComplete(page);
  const loadTime = Date.now() - startTime;
  
  expect(loadTime).toBeLessThan(3000); // 3 seconds
});
```

## 🛡️ Security Testing

### Input Validation

```typescript
test('should prevent XSS attacks', async ({ page }) => {
  const maliciousInput = '<script>alert("XSS")</script>';
  
  await page.fill('[data-testid="search-input"]', maliciousInput);
  await page.click('[data-testid="search-button"]');
  
  // Verify script is not executed
  const alertHandler = page.on('dialog', () => {
    throw new Error('XSS vulnerability detected');
  });
  
  await page.waitForTimeout(1000);
  page.off('dialog', alertHandler);
});
```

### Authentication

```typescript
test('should require authentication for protected routes', async ({ page }) => {
  // Try to access protected route without auth
  await page.goto('/admin');
  
  // Should redirect to login
  await expect(page).toHaveURL(/.*login/);
});
```

## 📱 Accessibility Testing

### Basic Accessibility Checks

```typescript
import { checkBasicAccessibility } from '../utils/test-helpers';

test('should be accessible', async ({ page }) => {
  await navigateAndWait(page, '/');
  await checkBasicAccessibility(page);
});
```

### Keyboard Navigation

```typescript
test('should support keyboard navigation', async ({ page }) => {
  await page.goto('/');
  
  // Tab through interactive elements
  await page.keyboard.press('Tab');
  const focusedElement = page.locator(':focus');
  await expect(focusedElement).toBeVisible();
  
  // Enter should activate focused element
  await page.keyboard.press('Enter');
});
```

### Screen Reader Support

```typescript
test('should have proper ARIA labels', async ({ page }) => {
  await page.goto('/');
  
  // Check for proper heading structure
  const h1 = page.locator('h1');
  await expect(h1).toBeVisible();
  
  // Check for form labels
  const inputs = page.locator('input');
  const inputCount = await inputs.count();
  
  for (let i = 0; i < inputCount; i++) {
    const input = inputs.nth(i);
    const inputId = await input.getAttribute('id');
    
    if (inputId) {
      const label = page.locator(`label[for="${inputId}"]`);
      await expect(label).toBeVisible();
    }
  }
});
```

## 🔧 Troubleshooting

### Common Error Messages

#### "locator.click: Target closed"

**Cause**: Page navigation or reload happened during test
**Solution**: Wait for navigation to complete or use proper navigation methods

```typescript
// Instead of
await page.click('a[href="/new-page"]');

// Use
await Promise.all([
  page.waitForNavigation(),
  page.click('a[href="/new-page"]')
]);
```

#### "TimeoutError: Timeout exceeded"

**Cause**: Element not appearing or API call taking too long
**Solution**: Increase timeout or fix underlying issue

```typescript
// Increase timeout
await expect(page.locator('[data-testid="result"]')).toBeVisible({ timeout: 10000 });

// Or fix the root cause
await waitForApiRequest(page, '/api/endpoint');
```

#### "Error: expect(received).toBe(expected)"

**Cause**: Assertion failure due to incorrect expectation
**Solution**: Debug the actual value and fix expectation

```typescript
// Debug the actual value
const actualText = await page.textContent('[data-testid="element"]');
console.log('Actual text:', actualText);

// Fix expectation
await expect(page.locator('[data-testid="element"]')).toContainText('expected text');
```

### Getting Help

1. **Check test logs** and error messages
2. **Review screenshots** and videos of failed tests
3. **Run tests in headed mode** to see what's happening
4. **Use debug mode** to step through tests
5. **Check recent application changes** that might affect tests

## 📚 Resources

- [Playwright Documentation](https://playwright.dev/)
- [Testing Library Best Practices](https://testing-library.com/docs/guiding-principles)
- [Web Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Mobile Testing Guide](https://web.dev/mobile-web-development/)

---

**Remember**: Good E2E tests are reliable, maintainable, and test real user scenarios. Focus on critical user journeys and edge cases that could break the user experience.