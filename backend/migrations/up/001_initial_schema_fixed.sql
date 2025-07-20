-- Migration: 001_initial_schema.sql
-- Description: Initial database schema for BetterPrompts
-- Author: Backend Team
-- Date: 2024-01-20

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS prompts;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Create migration tracking table
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    version INTEGER PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64)
);

-- =====================================================
-- AUTH SCHEMA - User authentication and authorization
-- =====================================================

-- Users table with array support for multiple roles
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,
    email_verify_token VARCHAR(255),
    email_verify_expires TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    roles TEXT[] DEFAULT ARRAY['user']::TEXT[] NOT NULL, -- Array of roles
    tier VARCHAR(50) DEFAULT 'free' NOT NULL CHECK (tier IN ('free', 'pro', 'enterprise')),
    preferences JSONB DEFAULT '{}' NOT NULL,
    metadata JSONB DEFAULT '{}' NOT NULL,
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Sessions table for JWT refresh tokens
CREATE TABLE IF NOT EXISTS auth.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_agent TEXT,
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- API Keys for developer access
CREATE TABLE IF NOT EXISTS auth.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    scopes TEXT[] DEFAULT ARRAY[]::TEXT[],
    rate_limit INTEGER DEFAULT 1000 NOT NULL,
    rate_limit_window VARCHAR(50) DEFAULT '1h' NOT NULL,
    usage_count INTEGER DEFAULT 0 NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT api_keys_user_name_unique UNIQUE (user_id, name)
);

-- User preferences table
CREATE TABLE IF NOT EXISTS auth.user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    preferred_techniques TEXT[] DEFAULT ARRAY[]::TEXT[],
    excluded_techniques TEXT[] DEFAULT ARRAY[]::TEXT[],
    complexity_preference VARCHAR(50) CHECK (complexity_preference IN ('simple', 'moderate', 'advanced')),
    ui_theme VARCHAR(50) DEFAULT 'light' NOT NULL,
    ui_language VARCHAR(10) DEFAULT 'en' NOT NULL,
    email_notifications BOOLEAN DEFAULT true NOT NULL,
    analytics_opt_in BOOLEAN DEFAULT true NOT NULL,
    custom_settings JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT user_preferences_user_id_unique UNIQUE(user_id)
);

-- =====================================================
-- PROMPTS SCHEMA - Core business logic
-- =====================================================

-- Prompt history table
CREATE TABLE IF NOT EXISTS prompts.history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    request_id VARCHAR(255) UNIQUE,
    original_input TEXT NOT NULL,
    enhanced_output TEXT NOT NULL,
    intent VARCHAR(100),
    intent_confidence FLOAT CHECK (intent_confidence >= 0 AND intent_confidence <= 1),
    complexity VARCHAR(50) CHECK (complexity IN ('simple', 'moderate', 'advanced')),
    techniques_used TEXT[] DEFAULT ARRAY[]::TEXT[],
    technique_scores JSONB DEFAULT '{}' NOT NULL,
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    token_count INTEGER CHECK (token_count >= 0),
    model_used VARCHAR(100),
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
    feedback_text TEXT,
    is_favorite BOOLEAN DEFAULT false NOT NULL,
    metadata JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create index separately (PostgreSQL doesn't support inline INDEX in CREATE TABLE)
CREATE INDEX idx_history_user_created ON prompts.history(user_id, created_at DESC);

-- Prompt templates table
CREATE TABLE IF NOT EXISTS prompts.templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    technique VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    template_text TEXT NOT NULL,
    variables JSONB DEFAULT '[]' NOT NULL,
    examples JSONB DEFAULT '[]' NOT NULL,
    metadata JSONB DEFAULT '{}' NOT NULL,
    effectiveness_score FLOAT DEFAULT 0.0 CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
    usage_count INTEGER DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_public BOOLEAN DEFAULT true NOT NULL,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Intent patterns table (for training data)
CREATE TABLE IF NOT EXISTS prompts.intent_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern TEXT NOT NULL,
    normalized_pattern TEXT NOT NULL,
    intent VARCHAR(100) NOT NULL,
    sub_intent VARCHAR(100),
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    is_verified BOOLEAN DEFAULT false NOT NULL,
    verified_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    source VARCHAR(50) CHECK (source IN ('user_generated', 'ml_predicted', 'manual')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- =====================================================
-- ANALYTICS SCHEMA - Metrics and insights
-- =====================================================

-- Technique effectiveness table
CREATE TABLE IF NOT EXISTS analytics.technique_effectiveness (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    technique VARCHAR(100) NOT NULL,
    intent VARCHAR(100) NOT NULL,
    success_count INTEGER DEFAULT 0 NOT NULL CHECK (success_count >= 0),
    total_count INTEGER DEFAULT 0 NOT NULL CHECK (total_count >= 0),
    average_feedback FLOAT CHECK (average_feedback >= 1 AND average_feedback <= 5),
    average_processing_time_ms FLOAT CHECK (average_processing_time_ms >= 0),
    p95_processing_time_ms FLOAT CHECK (p95_processing_time_ms >= 0),
    metadata JSONB DEFAULT '{}' NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT technique_effectiveness_unique UNIQUE(technique, intent, date),
    CONSTRAINT technique_effectiveness_counts_valid CHECK (success_count <= total_count)
);

-- User activity metrics
CREATE TABLE IF NOT EXISTS analytics.user_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    activity_data JSONB DEFAULT '{}' NOT NULL,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Daily usage statistics
CREATE TABLE IF NOT EXISTS analytics.daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL UNIQUE,
    total_requests INTEGER DEFAULT 0 NOT NULL CHECK (total_requests >= 0),
    unique_users INTEGER DEFAULT 0 NOT NULL CHECK (unique_users >= 0),
    new_users INTEGER DEFAULT 0 NOT NULL CHECK (new_users >= 0),
    total_enhancements INTEGER DEFAULT 0 NOT NULL CHECK (total_enhancements >= 0),
    average_response_time_ms FLOAT CHECK (average_response_time_ms >= 0),
    error_count INTEGER DEFAULT 0 NOT NULL CHECK (error_count >= 0),
    by_technique JSONB DEFAULT '{}' NOT NULL,
    by_intent JSONB DEFAULT '{}' NOT NULL,
    by_hour JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- =====================================================
-- INDEXES - Performance optimization
-- =====================================================

-- Auth indexes
CREATE INDEX idx_users_email_lower ON auth.users(LOWER(email));
CREATE INDEX idx_users_username_lower ON auth.users(LOWER(username));
CREATE INDEX idx_users_roles ON auth.users USING GIN(roles);
CREATE INDEX idx_users_tier ON auth.users(tier) WHERE is_active = true;
CREATE INDEX idx_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON auth.sessions(expires_at) WHERE expires_at > NOW();
CREATE INDEX idx_api_keys_user_id ON auth.api_keys(user_id) WHERE is_active = true;
CREATE INDEX idx_api_keys_key_hash ON auth.api_keys(key_hash) WHERE is_active = true;

-- Prompts indexes
CREATE INDEX idx_history_session_id ON prompts.history(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX idx_history_intent ON prompts.history(intent) WHERE intent IS NOT NULL;
CREATE INDEX idx_history_techniques ON prompts.history USING GIN(techniques_used);
CREATE INDEX idx_templates_slug ON prompts.templates(slug) WHERE is_active = true;
CREATE INDEX idx_templates_technique ON prompts.templates(technique) WHERE is_active = true;
CREATE INDEX idx_patterns_intent ON prompts.intent_patterns(intent);
CREATE INDEX idx_patterns_normalized ON prompts.intent_patterns(normalized_pattern);

-- Analytics indexes
CREATE INDEX idx_effectiveness_technique_intent ON analytics.technique_effectiveness(technique, intent);
CREATE INDEX idx_effectiveness_date ON analytics.technique_effectiveness(date DESC);
CREATE INDEX idx_activity_user_id ON analytics.user_activity(user_id);
CREATE INDEX idx_activity_type_created ON analytics.user_activity(activity_type, created_at DESC);
CREATE INDEX idx_daily_stats_date ON analytics.daily_stats(date DESC);

-- =====================================================
-- TRIGGERS - Automated behaviors
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON auth.api_keys
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON auth.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON prompts.templates
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_patterns_updated_at BEFORE UPDATE ON prompts.intent_patterns
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_effectiveness_updated_at BEFORE UPDATE ON analytics.technique_effectiveness
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Normalize pattern trigger
CREATE OR REPLACE FUNCTION public.normalize_pattern()
RETURNS TRIGGER AS $$
BEGIN
    NEW.normalized_pattern = LOWER(TRIM(NEW.pattern));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER normalize_intent_pattern BEFORE INSERT OR UPDATE ON prompts.intent_patterns
    FOR EACH ROW EXECUTE FUNCTION public.normalize_pattern();

-- Generate slug trigger
CREATE OR REPLACE FUNCTION public.generate_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug = LOWER(REGEXP_REPLACE(NEW.name, '[^a-zA-Z0-9]+', '-', 'g'));
        -- Trim leading/trailing hyphens
        NEW.slug = TRIM(BOTH '-' FROM NEW.slug);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generate_template_slug BEFORE INSERT OR UPDATE ON prompts.templates
    FOR EACH ROW EXECUTE FUNCTION public.generate_slug();

-- Record migration (remove the file path reference)
INSERT INTO public.schema_migrations (version, description, checksum)
VALUES (1, 'Initial schema', 'manual_migration')
ON CONFLICT (version) DO NOTHING;