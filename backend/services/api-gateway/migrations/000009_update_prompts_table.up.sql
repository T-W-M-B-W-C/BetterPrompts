-- Migration: Update prompts table to use schema-qualified name
-- This migration ensures the prompts table is in the prompts schema

-- First check if we need to move the table to the correct schema
DO $$
BEGIN
    -- Check if prompts table exists in public schema
    IF EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'prompts'
    ) THEN
        -- Move table to prompts schema
        ALTER TABLE public.prompts SET SCHEMA prompts;
        -- Rename to history
        ALTER TABLE prompts.prompts RENAME TO history;
    END IF;
END $$;

-- Add missing updated_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'prompts' 
        AND table_name = 'history' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE prompts.history 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Update the updated_at trigger if needed
DROP TRIGGER IF EXISTS update_prompts_history_updated_at ON prompts.history;
CREATE TRIGGER update_prompts_history_updated_at 
    BEFORE UPDATE ON prompts.history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes on updated_at if they don't exist
CREATE INDEX IF NOT EXISTS idx_history_updated_at ON prompts.history(updated_at DESC);

-- Ensure all required indexes exist with correct names
CREATE INDEX IF NOT EXISTS idx_history_user_id_created_at ON prompts.history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_history_intent_complexity ON prompts.history(intent, complexity);