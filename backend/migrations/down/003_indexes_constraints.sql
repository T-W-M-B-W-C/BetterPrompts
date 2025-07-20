-- Rollback Migration: 003_indexes_constraints.sql
-- Description: Remove additional indexes and constraints
-- Author: Backend Team
-- Date: 2024-01-20

-- Drop function and statistics table
DROP FUNCTION IF EXISTS public.update_index_statistics();
DROP TABLE IF EXISTS public.index_statistics;

-- Drop check constraints
ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_email_format;
ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_username_format;
ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_roles_not_empty;
ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_dates_valid;

ALTER TABLE auth.api_keys DROP CONSTRAINT IF EXISTS api_keys_name_length;
ALTER TABLE auth.api_keys DROP CONSTRAINT IF EXISTS api_keys_dates_valid;

ALTER TABLE auth.sessions DROP CONSTRAINT IF EXISTS sessions_unique_tokens;
ALTER TABLE auth.sessions DROP CONSTRAINT IF EXISTS sessions_dates_valid;

ALTER TABLE auth.user_preferences DROP CONSTRAINT IF EXISTS user_preferences_one_per_user;

ALTER TABLE prompts.templates DROP CONSTRAINT IF EXISTS templates_slug_format;
ALTER TABLE prompts.history DROP CONSTRAINT IF EXISTS history_processing_time_max;
ALTER TABLE prompts.history DROP CONSTRAINT IF EXISTS history_feedback_consistency;

ALTER TABLE analytics.technique_effectiveness DROP CONSTRAINT IF EXISTS effectiveness_metrics_valid;

-- Drop composite indexes
DROP INDEX IF EXISTS idx_users_email_username_lookup;
DROP INDEX IF EXISTS idx_sessions_cleanup;
DROP INDEX IF EXISTS idx_api_keys_rate_limit;
DROP INDEX IF EXISTS idx_history_user_date_range;
DROP INDEX IF EXISTS idx_templates_technique_effectiveness;
DROP INDEX IF EXISTS idx_effectiveness_dashboard;
DROP INDEX IF EXISTS idx_activity_dashboard;

-- Drop partial indexes
DROP INDEX IF EXISTS idx_users_admin_active;
DROP INDEX IF EXISTS idx_users_developer_active;
DROP INDEX IF EXISTS idx_users_verified_email;
DROP INDEX IF EXISTS idx_history_high_value;
DROP INDEX IF EXISTS idx_templates_by_category;

-- Drop foreign key indexes (only if created by this migration)
DROP INDEX IF EXISTS idx_history_user_fk;
DROP INDEX IF EXISTS idx_api_keys_user_fk;
DROP INDEX IF EXISTS idx_preferences_user_fk;
DROP INDEX IF EXISTS idx_templates_created_by_fk;
DROP INDEX IF EXISTS idx_patterns_verified_by_fk;

-- Remove migration record
DELETE FROM public.schema_migrations WHERE version = 3;