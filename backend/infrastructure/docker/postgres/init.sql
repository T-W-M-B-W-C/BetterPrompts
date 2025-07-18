-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS prompts;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set search path
SET search_path TO public, auth, prompts, analytics;

-- Users table
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    role VARCHAR(50) DEFAULT 'user',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS auth.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT sessions_user_fk FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Prompt templates table
CREATE TABLE IF NOT EXISTS prompts.templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    technique VARCHAR(100) NOT NULL,
    template_text TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    examples JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Prompt history table
CREATE TABLE IF NOT EXISTS prompts.history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    original_input TEXT NOT NULL,
    enhanced_output TEXT NOT NULL,
    intent VARCHAR(100),
    complexity VARCHAR(50),
    techniques_used TEXT[],
    confidence FLOAT,
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Intent patterns table (for training data)
CREATE TABLE IF NOT EXISTS prompts.intent_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern TEXT NOT NULL,
    intent VARCHAR(100) NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Technique effectiveness table
CREATE TABLE IF NOT EXISTS analytics.technique_effectiveness (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    technique VARCHAR(100) NOT NULL,
    intent VARCHAR(100) NOT NULL,
    success_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    average_feedback FLOAT,
    metadata JSONB DEFAULT '{}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(technique, intent)
);

-- User preferences table
CREATE TABLE IF NOT EXISTS auth.user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    preferred_techniques TEXT[],
    excluded_techniques TEXT[],
    complexity_preference VARCHAR(50),
    ui_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Vector embeddings for semantic search (using pgvector)
CREATE TABLE IF NOT EXISTS prompts.embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID REFERENCES prompts.history(id) ON DELETE CASCADE,
    embedding vector(768), -- DeBERTa embedding size
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON auth.sessions(expires_at);
CREATE INDEX idx_history_user_id ON prompts.history(user_id);
CREATE INDEX idx_history_created_at ON prompts.history(created_at);
CREATE INDEX idx_history_intent ON prompts.history(intent);
CREATE INDEX idx_patterns_intent ON prompts.intent_patterns(intent);
CREATE INDEX idx_effectiveness_technique_intent ON analytics.technique_effectiveness(technique, intent);

-- Create vector index for similarity search
CREATE INDEX idx_embeddings_vector ON prompts.embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON prompts.templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON auth.user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_effectiveness_updated_at BEFORE UPDATE ON analytics.technique_effectiveness
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default prompt templates
INSERT INTO prompts.templates (name, technique, description, template_text, variables) VALUES
    ('Chain of Thought', 'chain_of_thought', 'Step-by-step reasoning approach', 
     'Let''s approach this step-by-step:\n\n{input}\n\nFirst, I''ll identify the key components...',
     '["input"]'),
    
    ('Few-Shot Learning', 'few_shot', 'Learning from examples',
     'Here are some examples:\n\n{examples}\n\nNow, for your request:\n{input}',
     '["examples", "input"]'),
    
    ('Tree of Thoughts', 'tree_of_thoughts', 'Exploring multiple reasoning paths',
     'I''ll explore different approaches to this problem:\n\n{input}\n\nApproach 1:...\nApproach 2:...',
     '["input"]'),
    
    ('Self-Consistency', 'self_consistency', 'Multiple attempts with consistency check',
     'I''ll solve this multiple ways and verify consistency:\n\n{input}\n\nAttempt 1:...',
     '["input"]');

-- Grant permissions
GRANT ALL ON SCHEMA auth TO betterprompts;
GRANT ALL ON SCHEMA prompts TO betterprompts;
GRANT ALL ON SCHEMA analytics TO betterprompts;
GRANT ALL ON ALL TABLES IN SCHEMA auth TO betterprompts;
GRANT ALL ON ALL TABLES IN SCHEMA prompts TO betterprompts;
GRANT ALL ON ALL TABLES IN SCHEMA analytics TO betterprompts;
GRANT ALL ON ALL SEQUENCES IN SCHEMA auth TO betterprompts;
GRANT ALL ON ALL SEQUENCES IN SCHEMA prompts TO betterprompts;
GRANT ALL ON ALL SEQUENCES IN SCHEMA analytics TO betterprompts;