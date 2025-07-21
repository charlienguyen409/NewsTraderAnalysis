-- Create the market_summaries table
-- This script can be run manually if the table creation via SQLAlchemy fails

CREATE TYPE analysis_type_enum AS ENUM ('full', 'headlines');

CREATE TABLE IF NOT EXISTS market_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    summary_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_type analysis_type_enum NOT NULL,
    model_used VARCHAR NOT NULL,
    data_sources JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_market_summaries_session_generated 
    ON market_summaries (session_id, generated_at);

CREATE INDEX IF NOT EXISTS ix_market_summaries_analysis_type_generated 
    ON market_summaries (analysis_type, generated_at);

CREATE INDEX IF NOT EXISTS ix_market_summaries_model_generated 
    ON market_summaries (model_used, generated_at);

-- Grant permissions to the market_user
GRANT ALL PRIVILEGES ON TABLE market_summaries TO market_user;
GRANT USAGE ON TYPE analysis_type_enum TO market_user;