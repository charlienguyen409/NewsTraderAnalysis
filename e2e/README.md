# End-to-End Testing for Market News Analysis Agent

This directory contains comprehensive end-to-end tests for the Market News Analysis Agent application using Playwright.

## 📁 Directory Structure

```
e2e/
├── config/                     # Test configuration
│   ├── global-setup.ts        # Global test setup
│   └── global-teardown.ts     # Global test cleanup
├── scripts/                   # Utility scripts
│   ├── run-tests.sh          # Main test runner script
│   └── setup-test-data.sh    # Test data setup script
├── tests/                     # Test files
│   ├── market-analysis-trigger.spec.ts  # Analysis workflow tests
│   ├── article-browsing-filtering.spec.ts  # Article page tests
│   ├── real-time-updates.spec.ts      # WebSocket tests
│   ├── error-scenarios.spec.ts        # Error handling tests
│   └── mobile-responsive.spec.ts      # Mobile/responsive tests
├── utils/                     # Test utilities
│   ├── test-helpers.ts       # Common test helpers
│   └── test-data.ts         # Test data generators
├── docker-compose.test.yml   # Docker test environment
├── Dockerfile.e2e           # E2E test container
├── playwright.config.ts     # Playwright configuration
├── package.json            # Dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18 or higher
- Docker and Docker Compose
- PostgreSQL client (for database setup)

### 1. Install Dependencies

```bash
cd e2e
npm install
npx playwright install --with-deps
```

### 2. Run Tests

#### Using the Test Runner Script (Recommended)

```bash
# Run all tests with Chromium
./scripts/run-tests.sh

# Run with specific browser
./scripts/run-tests.sh --browser firefox

# Run in headed mode (visible browser)
./scripts/run-tests.sh --headed

# Run in debug mode
./scripts/run-tests.sh --debug

# Run with UI mode
./scripts/run-tests.sh --ui

# Use Docker environment
./scripts/run-tests.sh --docker
```

#### Using npm Scripts

```bash
# Run all tests
npm test

# Run with specific browser
npm run test:chromium
npm run test:firefox
npm run test:webkit

# Run mobile tests
npm run test:mobile

# Run in headed mode
npm run test:headed

# Run in debug mode
npm run test:debug

# Open test UI
npm run test:ui
```

### 3. View Test Results

```bash
# Show test report
npm run show-report
```

## 🧪 Test Suites

### 1. Market Analysis Trigger and Results (`market-analysis-trigger.spec.ts`)

Tests the core analysis workflow:
- ✅ Full analysis trigger and completion
- ✅ Headlines-only analysis
- ✅ Parameter validation
- ✅ Error handling
- ✅ Progress tracking
- ✅ Multiple concurrent analysis prevention
- ✅ Mobile responsiveness

### 2. Article Browsing and Filtering (`article-browsing-filtering.spec.ts`)

Tests article management features:
- ✅ Article list display
- ✅ Search functionality
- ✅ Source filtering
- ✅ Ticker filtering
- ✅ Combined filters
- ✅ Article expansion/collapse
- ✅ Analysis details display
- ✅ Mobile article browsing

### 3. Real-time Updates (`real-time-updates.spec.ts`)

Tests WebSocket functionality:
- ✅ WebSocket connection establishment
- ✅ Real-time progress updates
- ✅ Market summary updates
- ✅ Position list updates
- ✅ Connection failure handling
- ✅ Reconnection logic
- ✅ Activity log updates
- ✅ Multiple connection handling

### 4. Error Scenarios (`error-scenarios.spec.ts`)

Tests error handling and edge cases:
- ✅ API errors (500, 404, 429)
- ✅ Network failures
- ✅ Malformed responses
- ✅ WebSocket errors
- ✅ Data validation errors
- ✅ Browser compatibility issues
- ✅ Performance under stress
- ✅ Memory pressure handling

### 5. Mobile and Responsive (`mobile-responsive.spec.ts`)

Tests mobile experience:
- ✅ Multiple viewport sizes
- ✅ Touch interactions
- ✅ Gesture support
- ✅ Accessibility compliance
- ✅ Performance on mobile
- ✅ Offline support
- ✅ Screen reader compatibility

## 🛠️ Configuration

### Environment Variables

```bash
# Test URLs
BASE_URL=http://localhost:5173        # Frontend URL
API_URL=http://localhost:8000         # Backend API URL
WEBSOCKET_URL=ws://localhost:8000/ws  # WebSocket URL

# Database
DATABASE_URL=postgresql://testuser:testpass@localhost:5433/market_analysis_test

# API Keys (for testing)
OPENAI_API_KEY=test-key
ANTHROPIC_API_KEY=test-key

# Test Configuration
CI=false                              # Set to true in CI environment
HEADED=false                         # Run tests in headed mode
DEBUG=false                          # Enable debug mode
```

### Playwright Configuration

The `playwright.config.ts` file contains:
- Browser configurations (Chromium, Firefox, WebKit)
- Mobile device emulation
- Test timeouts and retries
- Screenshot and video settings
- Report generation

### Docker Configuration

The `docker-compose.test.yml` provides:
- Isolated PostgreSQL test database
- Redis test instance
- Backend service with test configuration
- Frontend service with test environment
- E2E test runner container

## 📊 Test Data Management

### Setting Up Test Data

```bash
# Setup test data
./scripts/setup-test-data.sh setup

# Clean test data
./scripts/setup-test-data.sh clean

# Verify test data
./scripts/setup-test-data.sh verify
```

### Test Data Includes

- **Articles**: 5 sample articles with different tickers and sources
- **Analyses**: Corresponding sentiment analyses for each article
- **Positions**: Sample position recommendations
- **Activity Logs**: Complete analysis session logs

## 🔄 CI/CD Integration

### GitHub Actions

The `.github/workflows/e2e-tests.yml` workflow:
- Runs on push/PR to main branches
- Tests across multiple browsers
- Generates test reports
- Uploads artifacts
- Runs performance and security tests

### Local CI Simulation

```bash
# Run tests in CI mode
CI=true npm test

# Run with Docker (CI-like environment)
./scripts/run-tests.sh --docker
```

## 🐛 Debugging Tests

### Debug Mode

```bash
# Run single test in debug mode
npx playwright test market-analysis-trigger.spec.ts --debug

# Run with UI mode for interactive debugging
npx playwright test --ui
```

### Screenshots and Videos

Tests automatically capture:
- Screenshots on failure
- Videos for failed tests
- Full page screenshots for debugging

### Logs and Traces

- Test traces are collected on first retry
- Console logs are captured
- Network requests are recorded

## 📱 Mobile Testing

### Supported Devices

- iPhone SE (375x667)
- iPhone 11 Pro (414x896)
- iPad (768x1024)
- iPad Landscape (1024x768)
- Android Small (360x640)
- Android Large (412x915)

### Mobile Test Features

- Touch interactions
- Gesture support
- Responsive layouts
- Accessibility compliance
- Performance optimization

## 🛡️ Security Testing

Security tests include:
- XSS prevention
- CSRF protection
- Input validation
- Authentication flows
- Authorization checks

## ⚡ Performance Testing

Performance tests verify:
- Page load times
- Memory usage
- Network efficiency
- Responsiveness under load
- Mobile performance

## 🔧 Maintenance

### Updating Tests

1. **Add new test cases** to existing spec files
2. **Create new spec files** for new features
3. **Update test data** when models change
4. **Modify selectors** when UI changes

### Best Practices

1. **Use data-testid attributes** for reliable element selection
2. **Mock external services** for consistent testing
3. **Write descriptive test names** and comments
4. **Keep tests independent** and idempotent
5. **Use Page Object Model** for complex pages

### Common Issues

#### Port Conflicts

```bash
# Check for running services
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
lsof -i :5433  # Test database

# Kill processes if needed
kill -9 <PID>
```

#### Database Issues

```bash
# Reset test database
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d postgres-test
./scripts/setup-test-data.sh setup
```

#### Browser Issues

```bash
# Reinstall browsers
npx playwright install --force

# Clear browser cache
npx playwright install --force chromium firefox webkit
```

## 📈 Test Metrics

### Coverage Goals

- **Critical User Paths**: 100% coverage
- **Error Scenarios**: 90% coverage
- **Mobile Experience**: 85% coverage
- **Performance**: Baseline established

### Success Criteria

- All critical user journeys work end-to-end
- Error handling is graceful and informative
- Mobile experience is fully functional
- Performance meets acceptable thresholds
- Tests are reliable and maintainable

## 🤝 Contributing

### Adding New Tests

1. Create test file in appropriate directory
2. Follow naming convention: `feature-name.spec.ts`
3. Use existing test helpers and utilities
4. Add test to CI workflow if needed
5. Update documentation

### Test Guidelines

1. **Test user journeys**, not implementation details
2. **Use realistic test data** that represents actual usage
3. **Test error conditions** as thoroughly as happy paths
4. **Ensure tests are deterministic** and repeatable
5. **Write clear assertions** with descriptive error messages

## 📞 Support

For issues with E2E tests:

1. Check the test logs and screenshots
2. Verify test environment setup
3. Review recent changes to the application
4. Check browser compatibility
5. Consult the debugging guide above

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Testing Best Practices](https://playwright.dev/docs/best-practices)
- [CI/CD Integration](https://playwright.dev/docs/ci)
- [Mobile Testing Guide](https://playwright.dev/docs/emulation)

---

**Last Updated**: July 2024  
**Playwright Version**: 1.40.0  
**Node.js Version**: 18+