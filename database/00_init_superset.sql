-- Initialize Superset Database and User
-- This script creates the necessary database and user for Apache Superset

-- Create superset user
CREATE USER superset_user WITH PASSWORD 'superset_secure_password_2024';

-- Create superset database
CREATE DATABASE superset_db OWNER superset_user;

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE superset_db TO superset_user;

-- Connect to superset_db and set up permissions
\c superset_db;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO superset_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO superset_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO superset_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO superset_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO superset_user;

-- Switch back to main database and create read-only user for data access
\c saas_platform_dev;

-- Create read-only user for superset to access main database
CREATE USER superset_readonly WITH PASSWORD 'superset_readonly_password_2024';
GRANT CONNECT ON DATABASE saas_platform_dev TO superset_readonly;
GRANT USAGE ON SCHEMA public TO superset_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO superset_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO superset_readonly;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO superset_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO superset_readonly;
