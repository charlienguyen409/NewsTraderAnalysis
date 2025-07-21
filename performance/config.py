"""
Performance testing configuration and settings
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any
from pydantic import BaseSettings


class PerformanceConfig(BaseSettings):
    """Configuration for performance tests"""
    
    # Target system URLs
    API_BASE_URL: str = "http://localhost:8000"
    WS_BASE_URL: str = "ws://localhost:8000"
    
    # Database configuration
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/market_analysis_test"
    TEST_REDIS_URL: str = "redis://localhost:6379/1"
    
    # Test configuration
    MIN_WAIT_TIME: int = 100  # milliseconds
    MAX_WAIT_TIME: int = 2000  # milliseconds
    
    # Load test parameters
    USERS_PER_SECOND: float = 1.0
    MAX_USERS: int = 100
    TEST_DURATION: int = 300  # seconds
    
    # Performance targets
    API_RESPONSE_TARGET: float = 500.0  # milliseconds
    WS_MESSAGE_TARGET: float = 100.0  # milliseconds
    DB_QUERY_TARGET: float = 200.0  # milliseconds
    ANALYSIS_COMPLETION_TARGET: float = 30.0  # seconds
    
    # Test data configuration
    SAMPLE_TICKERS: List[str] = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "AMD", "INTC", "CRM"]
    SAMPLE_ARTICLES_COUNT: int = 1000
    SAMPLE_ANALYSES_COUNT: int = 500
    
    class Config:
        env_file = ".env"


@dataclass
class PerformanceTargets:
    """Performance targets for different test scenarios"""
    
    # API Response Time Targets (95th percentile)
    api_response_time_95th: float = 500.0  # ms
    api_response_time_99th: float = 1000.0  # ms
    
    # Throughput Targets
    api_requests_per_second: float = 100.0
    websocket_messages_per_second: float = 1000.0
    
    # Concurrent User Targets
    max_concurrent_users: int = 50
    max_websocket_connections: int = 100
    
    # Database Performance Targets
    db_query_time_95th: float = 200.0  # ms
    db_connection_pool_max: int = 20
    
    # Memory and Resource Targets
    max_memory_usage_mb: float = 2048.0
    max_cpu_usage_percent: float = 80.0
    
    # Analysis Performance Targets
    analysis_time_10_articles: float = 30.0  # seconds
    analysis_time_50_articles: float = 120.0  # seconds


@dataclass
class TestScenarios:
    """Different test scenarios and their configurations"""
    
    # Light load scenario
    light_load = {
        "users": 10,
        "spawn_rate": 1,
        "duration": 60,
        "description": "Light load testing with 10 concurrent users"
    }
    
    # Medium load scenario
    medium_load = {
        "users": 25,
        "spawn_rate": 2,
        "duration": 180,
        "description": "Medium load testing with 25 concurrent users"
    }
    
    # Heavy load scenario
    heavy_load = {
        "users": 50,
        "spawn_rate": 5,
        "duration": 300,
        "description": "Heavy load testing with 50 concurrent users"
    }
    
    # Stress test scenario
    stress_test = {
        "users": 100,
        "spawn_rate": 10,
        "duration": 600,
        "description": "Stress testing with 100 concurrent users"
    }
    
    # WebSocket stress test
    websocket_stress = {
        "connections": 100,
        "messages_per_second": 10,
        "duration": 300,
        "description": "WebSocket stress testing with 100 connections"
    }


# Global configuration instance
config = PerformanceConfig()
targets = PerformanceTargets()
scenarios = TestScenarios()