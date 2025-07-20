-- Migration: 003_indexes_constraints.sql
-- Description: Additional indexes and constraints for performance and data integrity
-- Author: Backend Team
-- Date: 2024-01-20

-- =====================================================
-- ADDITIONAL CONSTRAINTS
-- =====================================================

-- Ensure email format is valid
ALTER TABLE auth.users
ADD CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Ensure username format (alphanumeric, underscore, hyphen)
ALTER TABLE auth.users
ADD CONSTRAINT users_username_format CHECK (username ~* '^[a-zA-Z0-9_-]{3,50}$');

-- Ensure at least one role is assigned
ALTER TABLE auth.users
ADD CONSTRAINT users_roles_not_empty CHECK (array_length(roles, 1) > 0);

-- Ensure API key names are meaningful
ALTER TABLE auth.api_keys
ADD CONSTRAINT api_keys_name_length CHECK (length(name) >= 3);

-- Ensure template slugs are URL-safe
ALTER TABLE prompts.templates
ADD CONSTRAINT templates_slug_format CHECK (slug ~* '^[a-z0-9-]+$');

-- Ensure processing time is reasonable (max 30 seconds)
ALTER TABLE prompts.history
ADD CONSTRAINT history_processing_time_max CHECK (processing_time_ms <= 30000);

-- =====================================================
-- COMPOSITE INDEXES FOR COMMON QUERIES
-- =====================================================

-- User lookup by email or username (case-insensitive)
CREATE INDEX idx_users_email_username_lookup ON auth.users (LOWER(email), LOWER(username))
WHERE is_active = true;

-- Session cleanup queries
CREATE INDEX idx_sessions_cleanup ON auth.sessions (expires_at, created_at)
WHERE expires_at < CURRENT_TIMESTAMP;

-- API key lookup with rate limiting
CREATE INDEX idx_api_keys_rate_limit ON auth.api_keys (key_hash, usage_count, rate_limit)
WHERE is_active = true;

-- Prompt history search by user and date range
CREATE INDEX idx_history_user_date_range ON prompts.history (user_id, created_at DESC, intent)
WHERE user_id IS NOT NULL;

-- Template search by technique and effectiveness
CREATE INDEX idx_templates_technique_effectiveness ON prompts.templates (technique, effectiveness_score DESC)
WHERE is_active = true AND is_public = true;

-- Analytics queries for dashboard
CREATE INDEX idx_effectiveness_dashboard ON analytics.technique_effectiveness (date DESC, technique, average_feedback DESC);
CREATE INDEX idx_activity_dashboard ON analytics.user_activity (created_at DESC, activity_type, user_id);

-- =====================================================
-- PARTIAL INDEXES FOR SPECIFIC QUERIES
-- =====================================================

-- Active users with specific roles
CREATE INDEX idx_users_admin_active ON auth.users (id, email)
WHERE is_active = true AND 'admin' = ANY(roles);

CREATE INDEX idx_users_developer_active ON auth.users (id, email)
WHERE is_active = true AND 'developer' = ANY(roles);

-- Verified users for email campaigns
CREATE INDEX idx_users_verified_email ON auth.users (email, created_at)
WHERE is_verified = true AND email_notifications = true;

-- High-value prompts (favorited or high feedback)
CREATE INDEX idx_history_high_value ON prompts.history (user_id, created_at DESC)
WHERE is_favorite = true OR feedback_score >= 4;

-- Templates by category
CREATE INDEX idx_templates_by_category ON prompts.templates (category, effectiveness_score DESC)
WHERE category IS NOT NULL AND is_active = true;

-- =====================================================
-- FOREIGN KEY CONSTRAINTS WITH INDEXES
-- =====================================================

-- Ensure all foreign keys have supporting indexes (if not already created)
CREATE INDEX IF NOT EXISTS idx_history_user_fk ON prompts.history(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_fk ON auth.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_preferences_user_fk ON auth.user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_templates_created_by_fk ON prompts.templates(created_by);
CREATE INDEX IF NOT EXISTS idx_patterns_verified_by_fk ON prompts.intent_patterns(verified_by);

-- =====================================================
-- UNIQUE CONSTRAINTS
-- =====================================================

-- Ensure one preference record per user
ALTER TABLE auth.user_preferences
ADD CONSTRAINT user_preferences_one_per_user UNIQUE (user_id);

-- Ensure unique session tokens
ALTER TABLE auth.sessions
ADD CONSTRAINT sessions_unique_tokens UNIQUE (token_hash, refresh_token_hash);

-- =====================================================
-- CHECK CONSTRAINTS FOR DATA QUALITY
-- =====================================================

-- Ensure dates are logical
ALTER TABLE auth.users
ADD CONSTRAINT users_dates_valid CHECK (created_at <= updated_at);

ALTER TABLE auth.sessions
ADD CONSTRAINT sessions_dates_valid CHECK (created_at <= expires_at);

ALTER TABLE auth.api_keys
ADD CONSTRAINT api_keys_dates_valid CHECK (
    created_at <= updated_at 
    AND (expires_at IS NULL OR created_at <= expires_at)
    AND (last_used_at IS NULL OR created_at <= last_used_at)
);

-- Ensure feedback score is provided with feedback text
ALTER TABLE prompts.history
ADD CONSTRAINT history_feedback_consistency CHECK (
    (feedback_score IS NULL AND feedback_text IS NULL) OR
    (feedback_score IS NOT NULL)
);

-- Ensure effectiveness metrics are valid
ALTER TABLE analytics.technique_effectiveness
ADD CONSTRAINT effectiveness_metrics_valid CHECK (
    (average_feedback IS NULL OR (average_feedback >= 1 AND average_feedback <= 5))
    AND (p95_processing_time_ms IS NULL OR p95_processing_time_ms >= average_processing_time_ms)
);

-- =====================================================
-- PERFORMANCE STATISTICS TABLE
-- =====================================================

-- Create table to track index usage
CREATE TABLE IF NOT EXISTS public.index_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    index_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    idx_scan BIGINT DEFAULT 0,
    idx_tup_read BIGINT DEFAULT 0,
    idx_tup_fetch BIGINT DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Function to update index statistics
CREATE OR REPLACE FUNCTION public.update_index_statistics()
RETURNS void AS $$
BEGIN
    INSERT INTO public.index_statistics (index_name, table_name, idx_scan, idx_tup_read, idx_tup_fetch)
    SELECT 
        indexrelname AS index_name,
        tablename AS table_name,
        idx_scan,
        idx_tup_read,
        idx_tup_fetch
    FROM pg_stat_user_indexes
    WHERE schemaname IN ('auth', 'prompts', 'analytics')
    ON CONFLICT (index_name) DO UPDATE SET
        idx_scan = EXCLUDED.idx_scan,
        idx_tup_read = EXCLUDED.idx_tup_read,
        idx_tup_fetch = EXCLUDED.idx_tup_fetch,
        last_updated = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Record migration
INSERT INTO public.schema_migrations (version, description, checksum)
VALUES (3, 'Indexes and constraints', md5('003_indexes_constraints'))
ON CONFLICT (version) DO NOTHING;