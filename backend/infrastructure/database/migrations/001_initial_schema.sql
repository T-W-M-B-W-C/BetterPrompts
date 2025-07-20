-- BetterPrompts Initial Schema Migration
-- This is the canonical schema definition for the BetterPrompts database

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

-- =====================================================
-- AUTH SCHEMA - User authentication and authorization
-- =====================================================

-- Users table with comprehensive fields
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verify_token VARCHAR(255),
    email_verify_expires TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    role VARCHAR(50) DEFAULT 'user',
    tier VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table for JWT refresh tokens
CREATE TABLE IF NOT EXISTS auth.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_agent TEXT,
    ip_address VARCHAR(45),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API Keys for developer access
CREATE TABLE IF NOT EXISTS auth.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    scopes TEXT[],
    rate_limit INTEGER DEFAULT 1000,
    rate_limit_window VARCHAR(50) DEFAULT '1h',
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences table
CREATE TABLE IF NOT EXISTS auth.user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    preferred_techniques TEXT[],
    excluded_techniques TEXT[],
    complexity_preference VARCHAR(50), -- simple, moderate, advanced
    ui_theme VARCHAR(50) DEFAULT 'light',
    ui_language VARCHAR(10) DEFAULT 'en',
    email_notifications BOOLEAN DEFAULT true,
    analytics_opt_in BOOLEAN DEFAULT true,
    custom_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- =====================================================
-- PROMPTS SCHEMA - Core business logic
-- =====================================================

-- Prompt templates table
CREATE TABLE IF NOT EXISTS prompts.templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    technique VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    template_text TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    examples JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    effectiveness_score FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT true,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Prompt history table
CREATE TABLE IF NOT EXISTS prompts.history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    request_id VARCHAR(255) UNIQUE,
    original_input TEXT NOT NULL,
    enhanced_output TEXT NOT NULL,
    intent VARCHAR(100),
    intent_confidence FLOAT,
    complexity VARCHAR(50),
    techniques_used TEXT[],
    technique_scores JSONB DEFAULT '{}',
    processing_time_ms INTEGER,
    token_count INTEGER,
    model_used VARCHAR(100),
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
    feedback_text TEXT,
    is_favorite BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Intent patterns table (for training data)
CREATE TABLE IF NOT EXISTS prompts.intent_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern TEXT NOT NULL,
    normalized_pattern TEXT NOT NULL,
    intent VARCHAR(100) NOT NULL,
    sub_intent VARCHAR(100),
    confidence FLOAT DEFAULT 1.0,
    is_verified BOOLEAN DEFAULT false,
    verified_by UUID REFERENCES auth.users(id),
    source VARCHAR(50), -- user_generated, ml_predicted, manual
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Saved prompts (user's library)
CREATE TABLE IF NOT EXISTS prompts.saved_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    history_id UUID REFERENCES prompts.history(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags TEXT[],
    is_public BOOLEAN DEFAULT false,
    share_token VARCHAR(255) UNIQUE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Prompt collections (folders)
CREATE TABLE IF NOT EXISTS prompts.collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7),
    icon VARCHAR(50),
    is_public BOOLEAN DEFAULT false,
    share_token VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many relationship for prompts in collections
CREATE TABLE IF NOT EXISTS prompts.collection_prompts (
    collection_id UUID NOT NULL REFERENCES prompts.collections(id) ON DELETE CASCADE,
    saved_prompt_id UUID NOT NULL REFERENCES prompts.saved_prompts(id) ON DELETE CASCADE,
    position INTEGER DEFAULT 0,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, saved_prompt_id)
);

-- Vector embeddings for semantic search (using pgvector)
CREATE TABLE IF NOT EXISTS prompts.embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL, -- prompt_history, saved_prompt, template
    source_id UUID NOT NULL,
    embedding vector(768), -- DeBERTa embedding size
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT embeddings_source_unique UNIQUE (source_type, source_id)
);

-- =====================================================
-- ANALYTICS SCHEMA - Metrics and insights
-- =====================================================

-- Technique effectiveness table
CREATE TABLE IF NOT EXISTS analytics.technique_effectiveness (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    technique VARCHAR(100) NOT NULL,
    intent VARCHAR(100) NOT NULL,
    success_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    average_feedback FLOAT,
    average_processing_time_ms FLOAT,
    p95_processing_time_ms FLOAT,
    metadata JSONB DEFAULT '{}',
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(technique, intent, date)
);

-- User activity metrics
CREATE TABLE IF NOT EXISTS analytics.user_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    activity_data JSONB DEFAULT '{}',
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Daily usage statistics
CREATE TABLE IF NOT EXISTS analytics.daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    total_enhancements INTEGER DEFAULT 0,
    average_response_time_ms FLOAT,
    error_count INTEGER DEFAULT 0,
    by_technique JSONB DEFAULT '{}',
    by_intent JSONB DEFAULT '{}',
    by_hour JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

-- API usage metrics
CREATE TABLE IF NOT EXISTS analytics.api_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES auth.api_keys(id) ON DELETE SET NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES - Performance optimization
-- =====================================================

-- Auth indexes
CREATE INDEX idx_users_email ON auth.users(LOWER(email));
CREATE INDEX idx_users_username ON auth.users(LOWER(username));
CREATE INDEX idx_users_role ON auth.users(role);
CREATE INDEX idx_users_tier ON auth.users(tier);
CREATE INDEX idx_users_created_at ON auth.users(created_at);
CREATE INDEX idx_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON auth.sessions(expires_at);
CREATE INDEX idx_api_keys_user_id ON auth.api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON auth.api_keys(key_hash);

-- Prompts indexes
CREATE INDEX idx_history_user_id ON prompts.history(user_id);
CREATE INDEX idx_history_session_id ON prompts.history(session_id);
CREATE INDEX idx_history_created_at ON prompts.history(created_at DESC);
CREATE INDEX idx_history_intent ON prompts.history(intent);
CREATE INDEX idx_history_techniques ON prompts.history USING GIN(techniques_used);
CREATE INDEX idx_patterns_intent ON prompts.intent_patterns(intent);
CREATE INDEX idx_patterns_normalized ON prompts.intent_patterns(normalized_pattern);
CREATE INDEX idx_saved_prompts_user_id ON prompts.saved_prompts(user_id);
CREATE INDEX idx_collections_user_id ON prompts.collections(user_id);

-- Analytics indexes
CREATE INDEX idx_effectiveness_technique_intent ON analytics.technique_effectiveness(technique, intent);
CREATE INDEX idx_effectiveness_date ON analytics.technique_effectiveness(date DESC);
CREATE INDEX idx_activity_user_id ON analytics.user_activity(user_id);
CREATE INDEX idx_activity_type ON analytics.user_activity(activity_type);
CREATE INDEX idx_activity_created_at ON analytics.user_activity(created_at DESC);
CREATE INDEX idx_daily_stats_date ON analytics.daily_stats(date DESC);
CREATE INDEX idx_api_metrics_created_at ON analytics.api_metrics(created_at DESC);

-- Vector index for similarity search
CREATE INDEX idx_embeddings_vector ON prompts.embeddings 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- =====================================================
-- TRIGGERS - Automated behaviors
-- =====================================================

-- Update timestamp trigger
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

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON auth.api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON auth.user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON prompts.templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patterns_updated_at BEFORE UPDATE ON prompts.intent_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_prompts_updated_at BEFORE UPDATE ON prompts.saved_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON prompts.collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_effectiveness_updated_at BEFORE UPDATE ON analytics.technique_effectiveness
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Normalize pattern trigger
CREATE OR REPLACE FUNCTION normalize_pattern()
RETURNS TRIGGER AS $$
BEGIN
    NEW.normalized_pattern = LOWER(TRIM(NEW.pattern));
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER normalize_intent_pattern BEFORE INSERT OR UPDATE ON prompts.intent_patterns
    FOR EACH ROW EXECUTE FUNCTION normalize_pattern();

-- Generate slug trigger
CREATE OR REPLACE FUNCTION generate_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug = LOWER(REGEXP_REPLACE(NEW.name, '[^a-zA-Z0-9]+', '-', 'g'));
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER generate_template_slug BEFORE INSERT OR UPDATE ON prompts.templates
    FOR EACH ROW EXECUTE FUNCTION generate_slug();

-- =====================================================
-- DEFAULT DATA - Initial setup
-- =====================================================

-- Insert default prompt templates
INSERT INTO prompts.templates (name, slug, technique, description, template_text, variables, category) VALUES
    ('Chain of Thought', 'chain-of-thought', 'chain_of_thought', 
     'Step-by-step reasoning approach for complex problems', 
     'Let''s approach this step-by-step:\n\n{input}\n\nFirst, I''ll identify the key components...',
     '["input"]'::jsonb, 'reasoning'),
    
    ('Few-Shot Learning', 'few-shot-learning', 'few_shot', 
     'Learning from examples to solve similar problems',
     'Here are some examples:\n\n{examples}\n\nNow, for your request:\n{input}',
     '["examples", "input"]'::jsonb, 'learning'),
    
    ('Tree of Thoughts', 'tree-of-thoughts', 'tree_of_thoughts', 
     'Exploring multiple reasoning paths simultaneously',
     'I''ll explore different approaches to this problem:\n\n{input}\n\nApproach 1:...\nApproach 2:...',
     '["input"]'::jsonb, 'reasoning'),
    
    ('Self-Consistency', 'self-consistency', 'self_consistency', 
     'Multiple attempts with consistency verification',
     'I''ll solve this multiple ways and verify consistency:\n\n{input}\n\nAttempt 1:...',
     '["input"]'::jsonb, 'verification'),
     
    ('Role Playing', 'role-playing', 'role_play', 
     'Adopting specific personas or expertise',
     'As a {role}, I''ll address your request:\n\n{input}\n\nFrom my perspective...',
     '["role", "input"]'::jsonb, 'creative'),
     
    ('Structured Output', 'structured-output', 'structured_output', 
     'Generating responses in specific formats',
     'I''ll provide a structured response in {format} format:\n\n{input}\n\nOutput:',
     '["format", "input"]'::jsonb, 'formatting')
ON CONFLICT (slug) DO NOTHING;

-- =====================================================
-- PERMISSIONS - Grant access
-- =====================================================

-- Grant permissions to the application user
GRANT ALL ON SCHEMA auth TO betterprompts;
GRANT ALL ON SCHEMA prompts TO betterprompts;
GRANT ALL ON SCHEMA analytics TO betterprompts;
GRANT ALL ON ALL TABLES IN SCHEMA auth TO betterprompts;
GRANT ALL ON ALL TABLES IN SCHEMA prompts TO betterprompts;
GRANT ALL ON ALL TABLES IN SCHEMA analytics TO betterprompts;
GRANT ALL ON ALL SEQUENCES IN SCHEMA auth TO betterprompts;
GRANT ALL ON ALL SEQUENCES IN SCHEMA prompts TO betterprompts;
GRANT ALL ON ALL SEQUENCES IN SCHEMA analytics TO betterprompts;