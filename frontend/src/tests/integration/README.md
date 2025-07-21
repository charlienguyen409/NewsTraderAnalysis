# Frontend Integration Tests

This directory contains comprehensive integration tests for the Market News Analysis frontend application. These tests verify complete user journeys, real-time functionality, and cross-component data flow.

## Test Categories

### 1. Analysis Workflow Tests (`analysisWorkflow.test.tsx`)
Tests the complete user journey from dashboard to analysis results:
- **Full Analysis Journey**: Tests configuration, execution, and results display
- **Headlines Analysis Journey**: Tests faster analysis workflow  
- **Cross-Page Data Flow**: Verifies data consistency across navigation
- **Error Handling**: Tests graceful error recovery
- **Settings Integration**: Tests settings persistence and application
- **Performance**: Tests with large datasets and accessibility

### 2. Real-time Updates Tests (`realTimeUpdates.test.tsx`)
Tests WebSocket integration and real-time functionality:
- **WebSocket Connection Management**: Connection establishment and cleanup
- **Analysis Progress Updates**: Real-time progress notifications
- **Activity Log Updates**: Live activity stream
- **Connection Recovery**: Graceful fallback to polling
- **Error Handling**: WebSocket error scenarios
- **Performance**: High-frequency update handling

### 3. Cross-Component Data Flow Tests (`crossComponentDataFlow.test.tsx`)  
Tests data synchronization across application components:
- **Dashboard ↔ Positions**: Position data sharing
- **Dashboard ↔ Articles**: Article data filtering
- **Settings Integration**: Configuration persistence
- **State Management**: Consistent state across navigation
- **Concurrent Updates**: Multiple data source handling
- **Memory Management**: Resource cleanup

### 4. API Integration Tests (`apiIntegration.test.tsx`)
Tests frontend-backend API communication:
- **Analysis API**: Start, status, and completion handling
- **Positions API**: Loading, filtering, and pagination
- **Articles API**: Search, filtering, and source selection
- **Error Handling**: API error scenarios and recovery
- **Request Optimization**: Caching and deduplication
- **Network Resilience**: Timeout and retry handling

### 5. Performance & Accessibility Tests (`performanceAccessibility.test.tsx`)
Tests application performance and accessibility compliance:
- **Performance Metrics**: Render time budgets and optimization
- **Large Dataset Handling**: Virtualization and pagination
- **Accessibility Compliance**: WCAG 2.1 AA standard compliance
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: ARIA labels and announcements
- **Mobile Responsiveness**: Touch and viewport adaptation

## Test Architecture

### MSW (Mock Service Worker) Setup
- **Realistic API Mocking**: Simulates actual backend responses with delays
- **WebSocket Mocking**: Custom WebSocket implementation for real-time testing
- **Data Management**: Configurable mock data with helper functions
- **Error Scenarios**: Simulated API failures and edge cases

### Test Environment Setup
- **jsdom Environment**: DOM simulation for component testing
- **Fake Timers**: Controlled time progression for async testing
- **Browser API Mocks**: localStorage, sessionStorage, matchMedia
- **Performance Monitoring**: Memory and render time tracking

### Test Utilities
- **Query Client**: React Query setup with appropriate cache settings
- **Router Provider**: Browser router for navigation testing
- **User Events**: Realistic user interaction simulation
- **Accessibility Testing**: jest-axe integration for a11y validation

## Running Tests

### All Integration Tests
```bash
npm run test:integration
```

### Specific Test Files
```bash
# Analysis workflow tests
npm test -- analysisWorkflow.test.tsx

# Real-time updates tests  
npm test -- realTimeUpdates.test.tsx

# Cross-component data flow tests
npm test -- crossComponentDataFlow.test.tsx

# API integration tests
npm test -- apiIntegration.test.tsx

# Performance and accessibility tests
npm test -- performanceAccessibility.test.tsx
```

### Watch Mode
```bash
npm run test:watch -- --testPathPattern=integration
```

### Coverage Report
```bash
npm run test:coverage -- --testPathPattern=integration
```

## Test Data Management

### Mock Data Reset
Each test automatically resets mock data to ensure isolation:
```typescript
beforeEach(() => {
  mockHandlers.reset()
  MockWebSocket.reset()
  mockWebSocketServer.reset()
})
```

### Custom Test Data
Tests can add custom data as needed:
```typescript
mockHandlers.addPositions([
  createMockPosition({ ticker: 'CUSTOM', confidence: 0.9 })
])
```

### WebSocket Simulation
Real-time updates can be simulated:
```typescript
mockWebSocketServer.simulateAnalysisProgress(sessionId)
mockWebSocketServer.simulateError(sessionId, 'Connection lost')
```

## Performance Benchmarks

### Render Performance
- **Dashboard**: < 1 second initial render
- **Large Datasets**: < 2 seconds with 1000+ items
- **Real-time Updates**: < 3 seconds for 100 rapid updates

### Memory Usage
- **Long Sessions**: No memory leaks after 5 analysis cycles
- **Component Cleanup**: Proper WebSocket and timer cleanup

### Accessibility Standards
- **WCAG 2.1 AA**: Zero violations in axe-core testing
- **Keyboard Navigation**: Full functionality without mouse
- **Screen Reader**: Proper ARIA labels and announcements

## Test Scenarios Coverage

### User Journeys
- ✅ Complete analysis workflow (dashboard → configuration → execution → results)
- ✅ Multi-page navigation with data persistence
- ✅ Error scenarios and recovery paths
- ✅ Settings configuration and application

### Real-time Features
- ✅ WebSocket connection management
- ✅ Live progress updates during analysis
- ✅ Activity log real-time streaming
- ✅ Connection failure and recovery

### Data Management
- ✅ Cross-component data synchronization
- ✅ API request optimization and caching
- ✅ Large dataset handling and pagination
- ✅ Concurrent update scenarios

### Quality Assurance
- ✅ Performance benchmarks and optimization
- ✅ Accessibility compliance (WCAG 2.1 AA)
- ✅ Mobile responsiveness and touch support
- ✅ Error boundary and graceful failure handling

## Continuous Integration

These tests are designed to run in CI/CD environments:
- **Deterministic**: No flaky tests with proper mocking
- **Isolated**: Each test is independent and can run in parallel
- **Fast**: Optimized for quick feedback loops
- **Comprehensive**: Cover all critical user paths and edge cases

## Troubleshooting

### Common Issues

1. **Test Timeouts**: Increase timeout in jest.config.js if needed
2. **WebSocket Errors**: Ensure proper cleanup in afterEach
3. **Memory Leaks**: Check for unclosed timers and event listeners
4. **Race Conditions**: Use proper waitFor and async/await patterns

### Debug Mode
```bash
npm test -- --verbose --no-coverage analysisWorkflow.test.tsx
```

### Performance Profiling
```bash
npm test -- --detectOpenHandles performanceAccessibility.test.tsx
```