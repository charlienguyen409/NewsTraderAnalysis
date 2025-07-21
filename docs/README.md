# Documentation Index

## Overview

This directory contains comprehensive documentation for the Market News Analysis Agent. The documentation is organized into several key areas to help developers understand, test, and contribute to the project.

## Quick Start

For new developers, we recommend following this documentation path:

1. **[Architecture Documentation](architecture.md)** - Understand the system design
2. **[API Documentation](api-documentation.md)** - Learn the API endpoints
3. **[Testing Guide](testing-guide.md)** - Set up and run tests
4. **[Test Coverage](test-coverage.md)** - Understand coverage goals

## Core Documentation

### [Architecture Documentation](architecture.md)
**Complete system architecture overview**
- High-level system design
- Component interactions
- Database schema
- Service layer architecture
- Frontend architecture
- Security and deployment considerations

### [API Documentation](api-documentation.md)
**Comprehensive API reference with examples**
- Complete endpoint documentation
- Request/response examples
- WebSocket API specification
- Error handling reference
- Testing examples for all endpoints

### [Testing Guide](testing-guide.md)
**Complete testing instructions and best practices**
- Unit testing (backend and frontend)
- Integration testing workflows
- End-to-end testing with Playwright
- Performance testing strategies
- Test data management
- CI/CD testing configuration

### [Test Coverage](test-coverage.md)
**Coverage tracking and improvement plans**
- Current coverage metrics
- Coverage targets by component
- Critical path coverage analysis
- Coverage gap identification
- Improvement roadmap and milestones

## Quick Reference

### Testing Commands

```bash
# Backend unit tests
cd backend && pytest tests/unit/ -v

# Frontend unit tests
cd frontend && npm test

# Integration tests
cd backend && python tests/integration/run_integration_tests.py

# E2E tests
cd e2e && npm test

# Performance tests
cd performance && python run_all_tests.py
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analysis/start` | POST | Start market analysis |
| `/api/v1/analysis/status/{id}` | GET | Get analysis status |
| `/api/v1/articles` | GET | List articles with filtering |
| `/api/v1/positions` | GET | List trading positions |
| `/api/v1/positions/session/{id}` | GET | Get positions by session |
| `/ws` | WebSocket | Real-time updates |

### Environment Setup

| File | Purpose |
|------|---------|
| [`.env.example`](../.env.example) | Docker Compose configuration |
| [`backend/.env.example`](../backend/.env.example) | Backend environment setup |
| [`frontend/.env.example`](../frontend/.env.example) | Frontend environment setup |

## Additional Documentation

### Component-Specific Documentation

- **[Backend Integration Testing](../backend/tests/integration/README.md)** - Backend test setup and workflows
- **[Frontend Integration Testing](../frontend/src/tests/integration/README.md)** - Frontend test architecture
- **[E2E Testing Guide](../e2e/TESTING_GUIDE.md)** - End-to-end testing best practices
- **[Performance Testing](../performance/README.md)** - Load and performance testing
- **[Financial News Scraping Strategy](../backend/FINANCIAL_NEWS_SCRAPING_STRATEGY.md)** - Web scraping implementation

### Configuration Examples

- **[Backend Requirements](../backend/requirements.txt)** - Python dependencies
- **[Frontend Package](../frontend/package.json)** - Node.js dependencies
- **[Docker Configuration](../docker/)** - Container setup and orchestration
- **[Playwright Configuration](../e2e/playwright.config.ts)** - E2E test configuration

## Documentation Standards

### Writing Guidelines

1. **Clarity**: Use clear, concise language
2. **Examples**: Include code examples for all concepts
3. **Structure**: Follow consistent heading and formatting
4. **Completeness**: Cover both happy path and error scenarios
5. **Maintenance**: Keep documentation current with code changes

### Documentation Format

- Use Markdown for all documentation
- Include table of contents for long documents
- Use code fences with language specification
- Include diagrams where helpful (ASCII art or external links)
- Cross-reference related documentation

### Contributing to Documentation

1. **Keep It Current**: Update documentation when making code changes
2. **Test Examples**: Ensure all code examples work
3. **Review Process**: Include documentation review in pull requests
4. **User Focus**: Write from the user's perspective
5. **Accessibility**: Ensure documentation is accessible to all skill levels

## Support and Questions

### Getting Help

1. **Check Documentation**: Review relevant documentation first
2. **Search Issues**: Look for existing GitHub issues
3. **Testing**: Run tests to verify setup
4. **Community**: Ask questions in appropriate channels

### Reporting Documentation Issues

If you find issues with the documentation:

1. **Create Issue**: Open a GitHub issue with `documentation` label
2. **Be Specific**: Include the specific document and section
3. **Suggest Fix**: If possible, suggest improvements
4. **Examples**: Provide examples of what's unclear

### Documentation Roadmap

Planned documentation improvements:

- [ ] Video tutorials for setup and testing
- [ ] Interactive API documentation
- [ ] Troubleshooting guide with common issues
- [ ] Performance optimization guide
- [ ] Security best practices guide
- [ ] Deployment guide for various platforms

---

## Summary

This documentation provides comprehensive coverage of the Market News Analysis Agent system. Whether you're setting up the development environment, understanding the architecture, writing tests, or contributing new features, you'll find the information you need here.

For the most up-to-date information, always refer to the documentation in the main branch of the repository.