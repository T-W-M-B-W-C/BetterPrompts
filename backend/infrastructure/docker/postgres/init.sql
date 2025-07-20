-- BetterPrompts Database Initialization
-- This script runs the initial migration to set up the database schema

-- Create a migrations tracking table
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Check if migration has been applied
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.schema_migrations WHERE version = 1) THEN
        -- Run the initial migration
        \i /docker-entrypoint-initdb.d/migrations/001_initial_schema.sql
        
        -- Record the migration
        INSERT INTO public.schema_migrations (version) VALUES (1);
        
        RAISE NOTICE 'Migration 001_initial_schema.sql applied successfully';
    ELSE
        RAISE NOTICE 'Migration 001_initial_schema.sql already applied, skipping';
    END IF;
END $$;