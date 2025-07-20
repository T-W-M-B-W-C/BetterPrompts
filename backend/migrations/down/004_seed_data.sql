-- Rollback Migration: 004_seed_data.sql
-- Description: Remove seed data
-- Author: Backend Team
-- Date: 2024-01-20

-- Remove test users and their related data
DELETE FROM auth.users 
WHERE email IN ('admin@betterprompts.test', 'developer@betterprompts.test', 'user@betterprompts.test');

-- Remove sample daily stats
DELETE FROM analytics.daily_stats 
WHERE date >= CURRENT_DATE - interval '7 days';

-- Remove baseline effectiveness data
DELETE FROM analytics.technique_effectiveness
WHERE metadata = '{}'; -- Only remove seed data with empty metadata

-- Remove intent patterns marked as manual source
DELETE FROM prompts.intent_patterns
WHERE source = 'manual' AND is_verified = true;

-- Remove seeded templates
DELETE FROM prompts.templates
WHERE created_by IS NULL; -- Seed data has no creator

-- Remove migration record
DELETE FROM public.schema_migrations WHERE version = 4;