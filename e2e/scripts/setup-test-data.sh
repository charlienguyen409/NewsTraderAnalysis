#!/bin/bash

# Test Data Setup Script
# This script seeds the test database with consistent test data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DATABASE_URL="${DATABASE_URL:-postgresql://testuser:testpass@localhost:5433/market_analysis_test}"
API_URL="${API_URL:-http://localhost:8001}"

# Function to print colored output
print_status() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for database
wait_for_database() {
  print_status "Waiting for database to be ready..."
  
  local max_attempts=30
  local attempt=1
  
  while [ $attempt -le $max_attempts ]; do
    if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
      print_success "Database is ready!"
      return 0
    fi
    
    echo -n "."
    sleep 2
    ((attempt++))
  done
  
  print_error "Database failed to become ready"
  return 1
}

# Function to create test articles
create_test_articles() {
  print_status "Creating test articles..."
  
  psql "$DATABASE_URL" << EOF
-- Clear existing test data
DELETE FROM analyses WHERE article_id IN (SELECT id FROM articles WHERE url LIKE '%test-article%');
DELETE FROM articles WHERE url LIKE '%test-article%';

-- Insert test articles
INSERT INTO articles (id, title, content, summary, url, source, ticker, published_at, scraped_at, is_processed) VALUES
  ('test-article-1', 'Apple Reports Strong Q4 Earnings with Record iPhone Sales', 
   'Apple Inc. reported its strongest fourth-quarter earnings in company history, driven by record iPhone sales and growing services revenue. The company beat analyst expectations across all product categories.', 
   'Apple Q4 earnings beat expectations with record iPhone sales',
   'https://example.com/test-article-1', 'finviz', 'AAPL', 
   NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', true),
   
  ('test-article-2', 'Google Announces Major AI Breakthrough in Natural Language Processing',
   'Alphabet Inc.''s Google division unveiled a groundbreaking advancement in AI technology that significantly improves natural language understanding and generation capabilities.',
   'Google unveils major AI breakthrough in NLP',
   'https://example.com/test-article-2', 'biztoc', 'GOOGL',
   NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours', true),
   
  ('test-article-3', 'Microsoft Cloud Revenue Grows 35% as Enterprise Adoption Accelerates',
   'Microsoft Corporation reported exceptional growth in its cloud computing division, with Azure revenue increasing 35% year-over-year as more enterprises migrate to cloud services.',
   'Microsoft cloud revenue grows 35% with strong enterprise adoption',
   'https://example.com/test-article-3', 'finviz', 'MSFT',
   NOW() - INTERVAL '6 hours', NOW() - INTERVAL '5 hours', true),
   
  ('test-article-4', 'Tesla Delivers Record Number of Vehicles in Q4',
   'Tesla Inc. announced record vehicle deliveries for the fourth quarter, exceeding analyst expectations and demonstrating strong demand for electric vehicles globally.',
   'Tesla achieves record Q4 vehicle deliveries',
   'https://example.com/test-article-4', 'biztoc', 'TSLA',
   NOW() - INTERVAL '8 hours', NOW() - INTERVAL '7 hours', true),
   
  ('test-article-5', 'NVIDIA Stock Surges on AI Chip Demand',
   'NVIDIA Corporation shares reached new highs following reports of unprecedented demand for its AI computing chips from major technology companies.',
   'NVIDIA stock surges on strong AI chip demand',
   'https://example.com/test-article-5', 'finviz', 'NVDA',
   NOW() - INTERVAL '10 hours', NOW() - INTERVAL '9 hours', true);
EOF

  print_success "Test articles created!"
}

# Function to create test analyses
create_test_analyses() {
  print_status "Creating test analyses..."
  
  psql "$DATABASE_URL" << EOF
-- Insert test analyses
INSERT INTO analyses (id, article_id, sentiment_score, confidence, ticker, reasoning, catalysts, llm_model, created_at) VALUES
  ('test-analysis-1', 'test-article-1', 0.75, 0.85, 'AAPL',
   'Strong earnings beat with positive guidance indicates continued growth momentum',
   '[{"type": "earnings_beat", "description": "Q4 earnings exceeded expectations by 15%", "impact": "positive", "significance": "high"}, {"type": "guidance_upgrade", "description": "Management raised Q1 guidance", "impact": "positive", "significance": "medium"}]'::jsonb,
   'gpt-4', NOW() - INTERVAL '30 minutes'),
   
  ('test-analysis-2', 'test-article-2', 0.65, 0.78, 'GOOGL',
   'AI breakthrough positions Google competitively but commercial impact unclear',
   '[{"type": "product_innovation", "description": "Major AI advancement in NLP", "impact": "positive", "significance": "high"}, {"type": "competitive_advantage", "description": "Strengthens position in AI race", "impact": "positive", "significance": "medium"}]'::jsonb,
   'claude-3-sonnet', NOW() - INTERVAL '2 hours'),
   
  ('test-analysis-3', 'test-article-3', 0.68, 0.82, 'MSFT',
   'Strong cloud growth demonstrates successful digital transformation strategy',
   '[{"type": "revenue_growth", "description": "35% cloud revenue growth", "impact": "positive", "significance": "high"}, {"type": "market_expansion", "description": "Growing enterprise adoption", "impact": "positive", "significance": "medium"}]'::jsonb,
   'gpt-4', NOW() - INTERVAL '4 hours'),
   
  ('test-analysis-4', 'test-article-4', 0.72, 0.80, 'TSLA',
   'Record deliveries validate production capabilities and market demand',
   '[{"type": "delivery_beat", "description": "Record Q4 vehicle deliveries", "impact": "positive", "significance": "high"}, {"type": "demand_validation", "description": "Strong global EV demand", "impact": "positive", "significance": "medium"}]'::jsonb,
   'claude-3-sonnet', NOW() - INTERVAL '6 hours'),
   
  ('test-analysis-5', 'test-article-5', 0.80, 0.88, 'NVDA',
   'AI chip demand surge creates significant revenue opportunity',
   '[{"type": "demand_surge", "description": "Unprecedented AI chip demand", "impact": "positive", "significance": "high"}, {"type": "market_leadership", "description": "Dominant position in AI hardware", "impact": "positive", "significance": "high"}]'::jsonb,
   'gpt-4', NOW() - INTERVAL '8 hours');
EOF

  print_success "Test analyses created!"
}

# Function to create test positions
create_test_positions() {
  print_status "Creating test positions..."
  
  psql "$DATABASE_URL" << EOF
-- Clear existing test positions
DELETE FROM positions WHERE session_id LIKE 'test-session%';

-- Insert test positions
INSERT INTO positions (id, ticker, recommendation, confidence, sentiment_score, reasoning, catalysts, session_id, created_at) VALUES
  ('test-position-1', 'AAPL', 'BUY', 0.85, 0.75,
   'Strong fundamentals with positive earnings momentum and innovation pipeline',
   '[{"type": "earnings_beat", "description": "Consistent earnings outperformance", "impact": "positive", "significance": "high"}]'::jsonb,
   'test-session-1', NOW() - INTERVAL '1 hour'),
   
  ('test-position-2', 'GOOGL', 'BUY', 0.78, 0.65,
   'AI leadership and strong advertising business provide growth foundation',
   '[{"type": "ai_innovation", "description": "Leading AI technology development", "impact": "positive", "significance": "high"}]'::jsonb,
   'test-session-1', NOW() - INTERVAL '1 hour'),
   
  ('test-position-3', 'MSFT', 'STRONG_BUY', 0.90, 0.68,
   'Cloud dominance and enterprise focus drive consistent growth',
   '[{"type": "cloud_growth", "description": "Dominant cloud market position", "impact": "positive", "significance": "high"}]'::jsonb,
   'test-session-1', NOW() - INTERVAL '1 hour'),
   
  ('test-position-4', 'TSLA', 'HOLD', 0.65, 0.72,
   'Strong delivery numbers but valuation concerns limit upside',
   '[{"type": "delivery_growth", "description": "Record vehicle deliveries", "impact": "positive", "significance": "medium"}]'::jsonb,
   'test-session-1', NOW() - INTERVAL '1 hour'),
   
  ('test-position-5', 'NVDA', 'STRONG_BUY', 0.92, 0.80,
   'AI revolution creates unprecedented demand for GPU technology',
   '[{"type": "ai_demand", "description": "Explosive AI chip demand", "impact": "positive", "significance": "high"}]'::jsonb,
   'test-session-1', NOW() - INTERVAL '1 hour');
EOF

  print_success "Test positions created!"
}

# Function to create test activity logs
create_test_activity_logs() {
  print_status "Creating test activity logs..."
  
  psql "$DATABASE_URL" << EOF
-- Clear existing test activity logs
DELETE FROM activity_logs WHERE session_id LIKE 'test-session%';

-- Insert test activity logs
INSERT INTO activity_logs (id, timestamp, level, category, action, message, details, session_id) VALUES
  ('test-log-1', NOW() - INTERVAL '2 hours', 'INFO', 'analysis', 'start',
   'Analysis session started with full content analysis',
   '{"analysis_type": "full", "max_positions": 10, "min_confidence": 0.7, "llm_model": "gpt-4"}'::jsonb,
   'test-session-1'),
   
  ('test-log-2', NOW() - INTERVAL '2 hours', 'INFO', 'scraping', 'start',
   'Starting article scraping from FinViz',
   '{"source": "finviz", "target_articles": 50}'::jsonb,
   'test-session-1'),
   
  ('test-log-3', NOW() - INTERVAL '2 hours', 'INFO', 'scraping', 'complete',
   'Successfully scraped 45 articles from FinViz',
   '{"source": "finviz", "articles_scraped": 45, "duration_seconds": 30}'::jsonb,
   'test-session-1'),
   
  ('test-log-4', NOW() - INTERVAL '1 hour 45 minutes', 'INFO', 'scraping', 'start',
   'Starting article scraping from BizToc',
   '{"source": "biztoc", "target_articles": 30}'::jsonb,
   'test-session-1'),
   
  ('test-log-5', NOW() - INTERVAL '1 hour 30 minutes', 'INFO', 'scraping', 'complete',
   'Successfully scraped 28 articles from BizToc',
   '{"source": "biztoc", "articles_scraped": 28, "duration_seconds": 25}'::jsonb,
   'test-session-1'),
   
  ('test-log-6', NOW() - INTERVAL '1 hour 25 minutes', 'INFO', 'llm', 'analyze',
   'Starting sentiment analysis with GPT-4',
   '{"model": "gpt-4", "articles_to_analyze": 73}'::jsonb,
   'test-session-1'),
   
  ('test-log-7', NOW() - INTERVAL '1 hour 10 minutes', 'INFO', 'llm', 'complete',
   'Completed sentiment analysis for all articles',
   '{"model": "gpt-4", "articles_analyzed": 73, "avg_confidence": 0.82}'::jsonb,
   'test-session-1'),
   
  ('test-log-8', NOW() - INTERVAL '1 hour 5 minutes', 'INFO', 'analysis', 'generate_positions',
   'Generating position recommendations',
   '{"total_articles": 73, "min_confidence": 0.7}'::jsonb,
   'test-session-1'),
   
  ('test-log-9', NOW() - INTERVAL '1 hour', 'INFO', 'analysis', 'complete',
   'Analysis session completed successfully',
   '{"positions_generated": 5, "total_duration_minutes": 62}'::jsonb,
   'test-session-1');
EOF

  print_success "Test activity logs created!"
}

# Function to verify test data
verify_test_data() {
  print_status "Verifying test data..."
  
  local article_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM articles WHERE url LIKE '%test-article%';" | xargs)
  local analysis_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM analyses WHERE article_id LIKE 'test-article%';" | xargs)
  local position_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM positions WHERE session_id LIKE 'test-session%';" | xargs)
  local log_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM activity_logs WHERE session_id LIKE 'test-session%';" | xargs)
  
  print_status "Test data summary:"
  echo "  Articles: $article_count"
  echo "  Analyses: $analysis_count"
  echo "  Positions: $position_count"
  echo "  Activity Logs: $log_count"
  
  if [ "$article_count" -eq 5 ] && [ "$analysis_count" -eq 5 ] && [ "$position_count" -eq 5 ] && [ "$log_count" -eq 9 ]; then
    print_success "Test data verification passed!"
    return 0
  else
    print_error "Test data verification failed!"
    return 1
  fi
}

# Function to clean test data
clean_test_data() {
  print_status "Cleaning existing test data..."
  
  psql "$DATABASE_URL" << EOF
-- Clean all test data
DELETE FROM analyses WHERE article_id IN (SELECT id FROM articles WHERE url LIKE '%test-article%');
DELETE FROM articles WHERE url LIKE '%test-article%';
DELETE FROM positions WHERE session_id LIKE 'test-session%';
DELETE FROM activity_logs WHERE session_id LIKE 'test-session%';
EOF

  print_success "Test data cleaned!"
}

# Main function
main() {
  local command="${1:-setup}"
  
  case $command in
    setup)
      print_status "Setting up test data..."
      wait_for_database
      clean_test_data
      create_test_articles
      create_test_analyses
      create_test_positions
      create_test_activity_logs
      verify_test_data
      print_success "Test data setup completed!"
      ;;
    clean)
      print_status "Cleaning test data..."
      wait_for_database
      clean_test_data
      print_success "Test data cleaned!"
      ;;
    verify)
      print_status "Verifying test data..."
      wait_for_database
      verify_test_data
      ;;
    *)
      print_error "Unknown command: $command"
      echo "Usage: $0 [setup|clean|verify]"
      exit 1
      ;;
  esac
}

# Check if running directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi