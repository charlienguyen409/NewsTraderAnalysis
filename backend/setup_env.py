#!/usr/bin/env python3
"""
Environment setup script for Market News Analysis backend.
This script helps users configure their .env file with proper API keys.
"""

import os
import sys


def main():
    print("🚀 Market News Analysis - Environment Setup")
    print("=" * 50)
    
    env_path = ".env"
    
    if os.path.exists(env_path):
        print(f"✅ Found existing {env_path} file")
        response = input("Do you want to update it? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping setup. Exiting...")
            return
    
    print("\nTo use this application, you need API keys from:")
    print("1. OpenAI (https://platform.openai.com/api-keys)")
    print("2. Anthropic (https://console.anthropic.com/)")
    print("\nNote: You only need ONE of these API keys to run the application.")
    print("The app will automatically use whichever key you provide.\n")
    
    # Get API keys
    openai_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
    anthropic_key = input("Enter your Anthropic API key (or press Enter to skip): ").strip()
    
    if not openai_key and not anthropic_key:
        print("⚠️  Warning: No API keys provided. The application will not be able to analyze news.")
        print("You can add API keys later by editing the .env file.")
    
    # Database configuration
    print("\n📊 Database Configuration")
    print("Default: PostgreSQL on localhost:5432")
    db_host = input("Database host (localhost): ").strip() or "localhost"
    db_port = input("Database port (5432): ").strip() or "5432"
    db_name = input("Database name (market_analysis): ").strip() or "market_analysis"
    db_user = input("Database user (postgres): ").strip() or "postgres"
    db_password = input("Database password (password): ").strip() or "password"
    
    # Redis configuration
    print("\n🔴 Redis Configuration")
    redis_host = input("Redis host (localhost): ").strip() or "localhost"
    redis_port = input("Redis port (6379): ").strip() or "6379"
    
    # Generate random secret key
    import secrets
    secret_key = secrets.token_urlsafe(32)
    
    # Create .env content
    env_content = f"""# Backend Configuration
DATABASE_URL=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}
REDIS_URL=redis://{redis_host}:{redis_port}
SECRET_KEY={secret_key}

# AI/LLM Configuration
OPENAI_API_KEY={openai_key or 'your-openai-api-key-here'}
ANTHROPIC_API_KEY={anthropic_key or 'your-anthropic-api-key-here'}

# Analysis Settings
MAX_POSITIONS=10
MIN_CONFIDENCE=0.7
SCRAPING_RATE_LIMIT=10
"""
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ Environment file created: {env_path}")
    
    # Validation
    print("\n🔍 Validating configuration...")
    try:
        # Test configuration loading
        sys.path.insert(0, 'app')
        from app.core.config import Settings
        settings = Settings()
        print("✅ Configuration loaded successfully")
        
        # Check API keys
        if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
            print("✅ OpenAI API key configured")
        else:
            print("⚠️  OpenAI API key not configured")
            
        if settings.anthropic_api_key and settings.anthropic_api_key != "your-anthropic-api-key-here":
            print("✅ Anthropic API key configured")
        else:
            print("⚠️  Anthropic API key not configured")
            
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Start PostgreSQL and Redis servers")
    print("2. Run: python -m alembic upgrade head  # Create database tables")
    print("3. Run: uvicorn app.main:app --host 0.0.0.0 --port 8000  # Start the backend")
    
    print("\n📝 Note: If you need to update API keys later, edit the .env file directly.")


if __name__ == "__main__":
    main()