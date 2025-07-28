-- Rollback: Move prompts.history back to public.prompts

-- Drop the trigger first
DROP TRIGGER IF EXISTS update_prompts_history_updated_at ON prompts.history;

-- Drop the indexes we created
DROP INDEX IF EXISTS prompts.idx_history_updated_at;
DROP INDEX IF EXISTS prompts.idx_history_user_id_created_at;
DROP INDEX IF EXISTS prompts.idx_history_intent_complexity;

-- Move table back to public schema and rename
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'prompts' 
        AND table_name = 'history'
    ) THEN
        -- Rename back to prompts
        ALTER TABLE prompts.history RENAME TO prompts;
        -- Move to public schema
        ALTER TABLE prompts.prompts SET SCHEMA public;
    END IF;
END $$;

-- Note: We don't remove the updated_at column as it might contain data