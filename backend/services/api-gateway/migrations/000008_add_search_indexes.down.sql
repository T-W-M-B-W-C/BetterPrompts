-- Drop search indexes
DROP INDEX IF EXISTS idx_prompts_user_search;
DROP INDEX IF EXISTS idx_prompts_techniques;
DROP INDEX IF EXISTS idx_prompts_complexity_created_at;
DROP INDEX IF EXISTS idx_prompts_task_type_created_at;
DROP INDEX IF EXISTS idx_prompts_user_id_created_at;
DROP INDEX IF EXISTS idx_prompts_enhanced_prompt_trgm;
DROP INDEX IF EXISTS idx_prompts_original_prompt_trgm;
DROP INDEX IF EXISTS idx_prompts_enhanced_prompt_gin;
DROP INDEX IF EXISTS idx_prompts_original_prompt_gin;