-- Initialize pgvector extension for warp memory database
\c warp_memory;

-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a table for storing conversation memory with vector embeddings
CREATE TABLE IF NOT EXISTS conversation_memory (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'message',
    embedding vector(1536), -- OpenAI ada-002 embedding dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversation_memory_session_id ON conversation_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_memory_timestamp ON conversation_memory(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversation_memory_content_type ON conversation_memory(content_type);
CREATE INDEX IF NOT EXISTS idx_conversation_memory_embedding ON conversation_memory USING ivfflat (embedding vector_cosine_ops);

-- Create a table for storing project context
CREATE TABLE IF NOT EXISTS project_context (
    id SERIAL PRIMARY KEY,
    project_path VARCHAR(500) NOT NULL,
    context_type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for project context
CREATE INDEX IF NOT EXISTS idx_project_context_path ON project_context(project_path);
CREATE INDEX IF NOT EXISTS idx_project_context_type ON project_context(context_type);
CREATE INDEX IF NOT EXISTS idx_project_context_embedding ON project_context USING ivfflat (embedding vector_cosine_ops);

-- Create a table for storing user preferences and settings
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    preference_key VARCHAR(255) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

-- Create index for user preferences
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Grant permissions to the saas_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO saas_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO saas_user;

