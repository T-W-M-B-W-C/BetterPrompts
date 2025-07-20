-- Rollback Migration: 001_initial_schema.sql
-- Description: Remove initial database schema
-- Author: Backend Team
-- Date: 2024-01-20

-- Drop triggers first
DROP TRIGGER IF EXISTS update_effectiveness_updated_at ON analytics.technique_effectiveness;
DROP TRIGGER IF EXISTS update_patterns_updated_at ON prompts.intent_patterns;
DROP TRIGGER IF EXISTS update_templates_updated_at ON prompts.templates;
DROP TRIGGER IF EXISTS update_preferences_updated_at ON auth.user_preferences;
DROP TRIGGER IF EXISTS update_api_keys_updated_at ON auth.api_keys;
DROP TRIGGER IF EXISTS update_users_updated_at ON auth.users;
DROP TRIGGER IF EXISTS normalize_intent_pattern ON prompts.intent_patterns;
DROP TRIGGER IF EXISTS generate_template_slug ON prompts.templates;

-- Drop functions
DROP FUNCTION IF EXISTS public.update_updated_at_column();
DROP FUNCTION IF EXISTS public.normalize_pattern();
DROP FUNCTION IF EXISTS public.generate_slug();

-- Drop analytics tables
DROP TABLE IF EXISTS analytics.daily_stats;
DROP TABLE IF EXISTS analytics.user_activity;
DROP TABLE IF EXISTS analytics.technique_effectiveness;

-- Drop prompts tables
DROP TABLE IF EXISTS prompts.intent_patterns;
DROP TABLE IF EXISTS prompts.templates;
DROP TABLE IF EXISTS prompts.history;

-- Drop auth tables
DROP TABLE IF EXISTS auth.user_preferences;
DROP TABLE IF EXISTS auth.api_keys;
DROP TABLE IF EXISTS auth.sessions;
DROP TABLE IF EXISTS auth.users;

-- Drop schemas
DROP SCHEMA IF EXISTS analytics;
DROP SCHEMA IF EXISTS prompts;
DROP SCHEMA IF EXISTS auth;

-- Remove migration record
DELETE FROM public.schema_migrations WHERE version = 1;

-- Drop migration tracking table if this is the last migration
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.schema_migrations LIMIT 1) THEN
        DROP TABLE IF EXISTS public.schema_migrations;
    END IF;
END $$;