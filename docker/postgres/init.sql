-- Database and user already created by environment variables
-- Just set up additional configuration

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO market_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO market_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO market_user;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO market_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO market_user;