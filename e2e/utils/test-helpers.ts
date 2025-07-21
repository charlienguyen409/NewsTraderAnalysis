import { Page, expect, Locator } from '@playwright/test';

/**
 * Test helper utilities for Market News Analysis Agent E2E tests
 */

/**
 * Wait for an element to be visible and ready for interaction
 */
export async function waitForElement(page: Page, selector: string, timeout = 10000): Promise<Locator> {
  const element = page.locator(selector);
  await expect(element).toBeVisible({ timeout });
  return element;
}

/**
 * Wait for API request to complete
 */
export async function waitForApiRequest(page: Page, urlPattern: string | RegExp, timeout = 30000): Promise<void> {
  await page.waitForResponse(
    response => {
      const url = response.url();
      const matches = typeof urlPattern === 'string' 
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matches && response.status() < 400;
    },
    { timeout }
  );
}

/**
 * Wait for WebSocket connection to be established
 */
export async function waitForWebSocketConnection(page: Page, timeout = 10000): Promise<void> {
  await page.waitForFunction(() => {
    return new Promise((resolve) => {
      // Check if WebSocket connection status indicator is present
      const connectionIndicator = document.querySelector('[data-testid="connection-status"]');
      if (connectionIndicator?.textContent?.includes('Live')) {
        resolve(true);
      } else {
        // Keep checking
        setTimeout(() => resolve(false), 100);
      }
    });
  }, { timeout });
}

/**
 * Fill form fields with validation
 */
export async function fillForm(page: Page, fields: Record<string, string>): Promise<void> {
  for (const [selector, value] of Object.entries(fields)) {
    const field = await waitForElement(page, selector);
    await field.fill(value);
    
    // Verify the field was filled correctly
    await expect(field).toHaveValue(value);
  }
}

/**
 * Click button and wait for action to complete
 */
export async function clickButtonAndWait(
  page: Page, 
  buttonSelector: string, 
  waitForSelector?: string,
  timeout = 10000
): Promise<void> {
  const button = await waitForElement(page, buttonSelector);
  await button.click();
  
  if (waitForSelector) {
    await waitForElement(page, waitForSelector, timeout);
  }
}

/**
 * Wait for loading state to complete
 */
export async function waitForLoadingToComplete(page: Page, timeout = 30000): Promise<void> {
  // Wait for any loading spinners to disappear
  await page.waitForFunction(() => {
    const spinners = document.querySelectorAll('.animate-spin, [data-testid="loading"]');
    return spinners.length === 0;
  }, { timeout });
  
  // Wait for network to be idle
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Check if element contains specific text
 */
export async function expectElementToContainText(
  page: Page, 
  selector: string, 
  text: string
): Promise<void> {
  const element = await waitForElement(page, selector);
  await expect(element).toContainText(text);
}

/**
 * Take screenshot for debugging
 */
export async function takeDebugScreenshot(page: Page, name: string): Promise<void> {
  await page.screenshot({ 
    path: `test-results/debug-${name}-${Date.now()}.png`,
    fullPage: true 
  });
}

/**
 * Mock API responses for testing
 */
export async function mockApiResponse(
  page: Page, 
  url: string | RegExp, 
  responseData: any,
  status = 200
): Promise<void> {
  await page.route(url, async (route) => {
    await route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(responseData)
    });
  });
}

/**
 * Check responsive design at different viewport sizes
 */
export async function testResponsiveDesign(
  page: Page,
  testCallback: (page: Page) => Promise<void>
): Promise<void> {
  const viewports = [
    { width: 1920, height: 1080, name: 'desktop' },
    { width: 768, height: 1024, name: 'tablet' },
    { width: 375, height: 667, name: 'mobile' }
  ];

  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.waitForTimeout(1000); // Allow time for responsive changes
    
    try {
      await testCallback(page);
    } catch (error) {
      throw new Error(`Test failed at ${viewport.name} viewport (${viewport.width}x${viewport.height}): ${error}`);
    }
  }
}

/**
 * Wait for analysis to complete
 */
export async function waitForAnalysisToComplete(page: Page, timeout = 120000): Promise<void> {
  // Wait for the analysis button to be enabled again (indicating completion)
  await page.waitForFunction(() => {
    const startButton = document.querySelector('[data-testid="start-analysis"]') as HTMLButtonElement;
    return startButton && !startButton.disabled;
  }, { timeout });
  
  // Also wait for any loading indicators to disappear
  await waitForLoadingToComplete(page);
}

/**
 * Navigate to page and wait for it to load
 */
export async function navigateAndWait(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await page.waitForLoadState('networkidle');
  await waitForLoadingToComplete(page);
}

/**
 * Check accessibility basics
 */
export async function checkBasicAccessibility(page: Page): Promise<void> {
  // Check for essential accessibility features
  const mainContent = page.locator('main, [role="main"]');
  await expect(mainContent).toBeVisible();
  
  // Check for heading structure
  const h1 = page.locator('h1');
  await expect(h1).toBeVisible();
  
  // Check for proper focus management
  await page.keyboard.press('Tab');
  const focusedElement = page.locator(':focus');
  await expect(focusedElement).toBeVisible();
}

/**
 * Verify WebSocket real-time updates
 */
export async function verifyWebSocketUpdates(
  page: Page, 
  triggerAction: () => Promise<void>,
  expectedUpdateSelector: string,
  timeout = 30000
): Promise<void> {
  // Set up listener for the expected update
  const updatePromise = page.waitForSelector(expectedUpdateSelector, { timeout });
  
  // Trigger the action that should cause WebSocket updates
  await triggerAction();
  
  // Wait for the update to appear
  await updatePromise;
}