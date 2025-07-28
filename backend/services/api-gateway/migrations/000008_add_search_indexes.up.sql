-- Add full-text search indexes for prompts table
-- Enable pg_trgm extension for fuzzy text searching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add GIN indexes for full-text search on prompt content
CREATE INDEX IF NOT EXISTS idx_prompts_original_prompt_gin ON prompts USING gin(to_tsvector('english', original_prompt));
CREATE INDEX IF NOT EXISTS idx_prompts_enhanced_prompt_gin ON prompts USING gin(to_tsvector('english', enhanced_prompt));

-- Add trigram indexes for fuzzy searching
CREATE INDEX IF NOT EXISTS idx_prompts_original_prompt_trgm ON prompts USING gin(original_prompt gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_prompts_enhanced_prompt_trgm ON prompts USING gin(enhanced_prompt gin_trgm_ops);

-- Add indexes for filtering and sorting
CREATE INDEX IF NOT EXISTS idx_prompts_user_id_created_at ON prompts(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_task_type_created_at ON prompts(task_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_complexity_created_at ON prompts(complexity, created_at DESC);

-- Create index on techniques JSONB column for filtering
CREATE INDEX IF NOT EXISTS idx_prompts_techniques ON prompts USING gin(techniques);

-- Create composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_prompts_user_search ON prompts(user_id, created_at DESC) 
WHERE original_prompt IS NOT NULL;