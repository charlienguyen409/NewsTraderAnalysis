import { chromium, FullConfig } from '@playwright/test';

/**
 * Global setup for E2E tests
 * This runs once before all tests
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Setting up E2E test environment...');
  
  // Launch browser for setup
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Wait for frontend to be ready
    console.log('⏳ Waiting for frontend server...');
    await page.goto(config.use?.baseURL || 'http://localhost:5173', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    // Wait for API to be ready
    console.log('⏳ Waiting for API server...');
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    await page.goto(`${apiUrl}/docs`, { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    // Check if we can reach the health endpoint
    try {
      const response = await page.request.get(`${apiUrl}/health`);
      if (response.ok()) {
        console.log('✅ API health check passed');
      } else {
        console.log('⚠️  API health check failed, but continuing...');
      }
    } catch (error) {
      console.log('⚠️  API health endpoint not found, but continuing...');
    }
    
    // Set up test data if needed
    await setupTestData(page);
    
    console.log('✅ E2E test environment setup complete');
    
  } catch (error) {
    console.error('❌ E2E test environment setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

/**
 * Set up test data for E2E tests
 */
async function setupTestData(page: any) {
  // This would typically seed the database with test data
  // For now, we'll just ensure the application is in a known state
  
  // Clear any existing data that might interfere with tests
  try {
    await page.evaluate(() => {
      // Clear localStorage
      localStorage.clear();
      
      // Clear sessionStorage
      sessionStorage.clear();
      
      // Clear any application-specific state
      if (window.location.pathname !== '/') {
        window.location.href = '/';
      }
    });
  } catch (error) {
    console.log('Note: Could not clear browser state, continuing...');
  }
}

export default globalSetup;