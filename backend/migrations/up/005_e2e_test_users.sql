-- Migration: 005_e2e_test_users.sql
-- Description: E2E test users for automated testing
-- Author: E2E Team
-- Date: 2025-01-20

-- =====================================================
-- E2E TEST USERS - For E2E Testing
-- =====================================================

-- Only insert E2E test users in test environments
DO $$
BEGIN
    -- Check if we're in a test environment (e2e database name)
    IF current_database() LIKE '%e2e%' OR current_database() LIKE '%test%' THEN
        -- Insert E2E test users with properly hashed passwords
        -- Password: 'Test123!@#' hashed with bcrypt (cost factor 10)
        INSERT INTO auth.users (email, username, password_hash, first_name, last_name, roles, tier, is_verified, is_active) VALUES
            ('test@example.com', 'testuser', '$2a$10$g566yZvqXuqCoIaQR58ymO09./gAS27eQz12Q3zja7ZxiSPwtAk7C', 'Test', 'User', ARRAY['user'], 'free', true, true)
        ON CONFLICT (email) DO UPDATE SET 
            password_hash = '$2a$10$g566yZvqXuqCoIaQR58ymO09./gAS27eQz12Q3zja7ZxiSPwtAk7C',
            is_verified = true,
            is_active = true;
        
        -- Create preferences for E2E test user
        INSERT INTO auth.user_preferences (user_id, preferred_techniques, ui_theme)
        SELECT id, ARRAY['chain_of_thought', 'few_shot'], 'light'
        FROM auth.users
        WHERE email = 'test@example.com'
        ON CONFLICT (user_id) DO NOTHING;
        
        RAISE NOTICE 'E2E test user created: test@example.com with password Test123!@#';
    ELSE
        RAISE NOTICE 'Skipping E2E test user creation - not in test environment';
    END IF;
END $$;

-- Record migration
INSERT INTO public.schema_migrations (version, description, checksum)
VALUES (5, 'E2E test users', md5('005_e2e_test_users'))
ON CONFLICT (version) DO NOTHING;