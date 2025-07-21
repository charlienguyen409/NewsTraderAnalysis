#!/usr/bin/env node
/**
 * Integration Test Runner
 * 
 * Provides utilities for running integration tests with proper setup and teardown.
 * Can be used for custom test execution scenarios and CI/CD integration.
 */

import { execSync } from 'child_process'
import { performance } from 'perf_hooks'

interface TestResult {
  name: string
  duration: number
  passed: boolean
  error?: string
}

interface TestSuite {
  name: string
  pattern: string
  description: string
  timeout?: number
}

const TEST_SUITES: TestSuite[] = [
  {
    name: 'Analysis Workflow',
    pattern: 'analysisWorkflow.test.tsx',
    description: 'Complete user journey from dashboard to analysis results',
    timeout: 60000
  },
  {
    name: 'Real-time Updates',
    pattern: 'realTimeUpdates.test.tsx',
    description: 'WebSocket integration and real-time functionality',
    timeout: 45000
  },
  {
    name: 'Cross-Component Data Flow',
    pattern: 'crossComponentDataFlow.test.tsx',
    description: 'Data synchronization across application components',
    timeout: 45000
  },
  {
    name: 'API Integration',
    pattern: 'apiIntegration.test.tsx',
    description: 'Frontend-backend API communication',
    timeout: 60000
  },
  {
    name: 'Performance & Accessibility',
    pattern: 'performanceAccessibility.test.tsx',
    description: 'Performance benchmarks and accessibility compliance',
    timeout: 90000
  }
]

export class IntegrationTestRunner {
  private results: TestResult[] = []
  private totalStartTime: number = 0

  constructor(private verbose: boolean = false) {}

  async runAllTests(): Promise<TestResult[]> {
    this.totalStartTime = performance.now()
    this.log('🚀 Starting Frontend Integration Tests...\n')

    for (const suite of TEST_SUITES) {
      await this.runTestSuite(suite)
    }

    this.printSummary()
    return this.results
  }

  async runTestSuite(suite: TestSuite): Promise<TestResult> {
    const startTime = performance.now()
    this.log(`📋 Running ${suite.name}...`)
    this.log(`   ${suite.description}`)

    try {
      const command = `npm test -- --testPathPattern=${suite.pattern} --testTimeout=${suite.timeout || 30000}`
      
      if (this.verbose) {
        this.log(`   Command: ${command}`)
      }

      execSync(command, { 
        stdio: this.verbose ? 'inherit' : 'pipe',
        timeout: suite.timeout || 30000
      })

      const duration = performance.now() - startTime
      const result: TestResult = {
        name: suite.name,
        duration,
        passed: true
      }

      this.results.push(result)
      this.log(`   ✅ Passed (${Math.round(duration)}ms)\n`)
      
      return result
    } catch (error) {
      const duration = performance.now() - startTime
      const result: TestResult = {
        name: suite.name,
        duration,
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }

      this.results.push(result)
      this.log(`   ❌ Failed (${Math.round(duration)}ms)`)
      
      if (this.verbose && error) {
        this.log(`   Error: ${error}`)
      }
      
      this.log('')
      return result
    }
  }

  async runSpecificTests(patterns: string[]): Promise<TestResult[]> {
    this.totalStartTime = performance.now()
    this.log('🚀 Starting Specific Integration Tests...\n')

    for (const pattern of patterns) {
      const suite = TEST_SUITES.find(s => s.pattern.includes(pattern))
      if (suite) {
        await this.runTestSuite(suite)
      } else {
        this.log(`⚠️  Test pattern '${pattern}' not found`)
      }
    }

    this.printSummary()
    return this.results
  }

  async runWithCoverage(): Promise<TestResult[]> {
    this.totalStartTime = performance.now()
    this.log('🚀 Starting Integration Tests with Coverage...\n')

    try {
      const command = 'npm run test:coverage -- --testPathPattern=integration'
      
      if (this.verbose) {
        this.log(`Command: ${command}`)
      }

      execSync(command, { 
        stdio: 'inherit',
        timeout: 120000 // 2 minutes for coverage
      })

      const result: TestResult = {
        name: 'All Integration Tests (with coverage)',
        duration: performance.now() - this.totalStartTime,
        passed: true
      }

      this.results.push(result)
      this.log('\n✅ All tests passed with coverage report generated')
      
      return this.results
    } catch (error) {
      const result: TestResult = {
        name: 'All Integration Tests (with coverage)',
        duration: performance.now() - this.totalStartTime,
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }

      this.results.push(result)
      this.log(`\n❌ Tests failed: ${error}`)
      
      return this.results
    }
  }

  private printSummary(): void {
    const totalDuration = performance.now() - this.totalStartTime
    const passed = this.results.filter(r => r.passed).length
    const failed = this.results.filter(r => !r.passed).length

    this.log('\n' + '='.repeat(60))
    this.log('📊 TEST SUMMARY')
    this.log('='.repeat(60))
    this.log(`Total Duration: ${Math.round(totalDuration)}ms`)
    this.log(`Tests Passed: ${passed}`)
    this.log(`Tests Failed: ${failed}`)
    this.log(`Success Rate: ${Math.round((passed / this.results.length) * 100)}%`)

    if (failed > 0) {
      this.log('\n❌ FAILED TESTS:')
      this.results
        .filter(r => !r.passed)
        .forEach(r => {
          this.log(`  - ${r.name}: ${r.error}`)
        })
    }

    this.log('\n📋 DETAILED RESULTS:')
    this.results.forEach(r => {
      const status = r.passed ? '✅' : '❌'
      this.log(`  ${status} ${r.name} (${Math.round(r.duration)}ms)`)
    })

    this.log('\n' + '='.repeat(60))
  }

  private log(message: string): void {
    console.log(message)
  }
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2)
  const runner = new IntegrationTestRunner(args.includes('--verbose'))

  if (args.includes('--coverage')) {
    runner.runWithCoverage()
  } else if (args.includes('--pattern')) {
    const patternIndex = args.indexOf('--pattern')
    const patterns = args.slice(patternIndex + 1).filter(arg => !arg.startsWith('--'))
    runner.runSpecificTests(patterns)
  } else {
    runner.runAllTests()
  }
}