-- Create test users for Phase 4 E2E tests
-- Password for all test users: Test123!@#

-- Power user with existing history
INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified, tier)
VALUES (
  'power',
  'power@example.com',
  '$2a$10$ZxW6Tlvn6H9J6Kx.BmxCIOJ8N5EO0h6i6PWBMhGFaCLBQR6wm5Ojm',
  'Power',
  'User',
  true,
  true,
  'pro'
) ON CONFLICT (email) DO NOTHING;

-- New user with no history
INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified, tier)
VALUES (
  'newuser',
  'new@example.com',
  '$2a$10$ZxW6Tlvn6H9J6Kx.BmxCIOJ8N5EO0h6i6PWBMhGFaCLBQR6wm5Ojm',
  'New',
  'User',
  true,
  true,
  'free'
) ON CONFLICT (email) DO NOTHING;

-- Add some sample history for the power user
DO $$
DECLARE
  power_user_id UUID;
BEGIN
  -- Get the power user's ID
  SELECT id INTO power_user_id FROM users WHERE email = 'power@example.com';
  
  -- Only insert if user exists and has no history
  IF power_user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM prompts WHERE user_id = power_user_id) THEN
    -- Insert 25 sample prompts for the power user
    INSERT INTO prompts (user_id, original_prompt, enhanced_prompt, intent, complexity, techniques, metadata, created_at)
    VALUES
      (power_user_id, 'Write a function to sort an array', 'Let''s approach writing a sorting function step by step...', 'code_generation', 'moderate', '{"techniques": ["step_by_step", "structured_output"]}'::jsonb, '{"confidence": 0.85}'::jsonb, NOW() - INTERVAL '25 days'),
      (power_user_id, 'Explain machine learning concepts', 'I''ll explain machine learning using analogical reasoning...', 'explanation', 'complex', ARRAY['analogical_reasoning', 'few_shot'], 0.92, NOW() - INTERVAL '24 days'),
      (power_user_id, 'Create a REST API for user management', 'I''ll help you create a REST API step by step...', 'code_generation', 'complex', ARRAY['step_by_step', 'structured_output', 'few_shot'], 0.88, NOW() - INTERVAL '23 days'),
      (power_user_id, 'Analyze market trends for EVs', 'Let''s analyze electric vehicle market trends systematically...', 'analysis', 'complex', ARRAY['perspective_taking', 'structured_output'], 0.91, NOW() - INTERVAL '22 days'),
      (power_user_id, 'Debug this Python code', 'I''ll debug this Python code using chain of thought...', 'problem_solving', 'moderate', ARRAY['chain_of_thought', 'socratic_questioning'], 0.83, NOW() - INTERVAL '21 days'),
      (power_user_id, 'Write a blog post introduction', 'Let me craft a compelling introduction using role playing...', 'creative_writing', 'moderate', ARRAY['role_playing', 'structured_output'], 0.79, NOW() - INTERVAL '20 days'),
      (power_user_id, 'Optimize SQL query performance', 'I''ll optimize this SQL query systematically...', 'problem_solving', 'complex', ARRAY['step_by_step', 'constraint_setting'], 0.87, NOW() - INTERVAL '19 days'),
      (power_user_id, 'Generate app ideas for fitness', 'Let''s explore fitness app ideas using tree of thoughts...', 'ideation', 'moderate', ARRAY['tree_of_thoughts', 'creative_exploration'], 0.90, NOW() - INTERVAL '18 days'),
      (power_user_id, 'Explain recursion simply', 'I''ll explain recursion using simple analogies...', 'explanation', 'simple', ARRAY['analogical_reasoning', 'simplification'], 0.86, NOW() - INTERVAL '17 days'),
      (power_user_id, 'Review code architecture', 'I''ll review your architecture from multiple perspectives...', 'analysis', 'complex', ARRAY['perspective_taking', 'structured_output'], 0.84, NOW() - INTERVAL '16 days'),
      (power_user_id, 'Create unit tests', 'Let me create comprehensive unit tests step by step...', 'code_generation', 'moderate', ARRAY['step_by_step', 'few_shot'], 0.88, NOW() - INTERVAL '15 days'),
      (power_user_id, 'Design database schema', 'I''ll design your database schema with constraints...', 'problem_solving', 'complex', ARRAY['constraint_setting', 'structured_output'], 0.91, NOW() - INTERVAL '14 days'),
      (power_user_id, 'Write technical documentation', 'Let me structure technical documentation professionally...', 'creative_writing', 'moderate', ARRAY['structured_output', 'role_playing'], 0.82, NOW() - INTERVAL '13 days'),
      (power_user_id, 'Implement authentication', 'I''ll help implement authentication step by step...', 'code_generation', 'complex', ARRAY['step_by_step', 'chain_of_thought', 'few_shot'], 0.89, NOW() - INTERVAL '12 days'),
      (power_user_id, 'Analyze performance metrics', 'Let''s analyze performance metrics systematically...', 'analysis', 'moderate', ARRAY['step_by_step', 'perspective_taking'], 0.85, NOW() - INTERVAL '11 days'),
      (power_user_id, 'Fix memory leak issue', 'I''ll help fix this memory leak using debugging techniques...', 'problem_solving', 'complex', ARRAY['chain_of_thought', 'socratic_questioning'], 0.87, NOW() - INTERVAL '10 days'),
      (power_user_id, 'Create marketing copy', 'Let me create compelling marketing copy...', 'creative_writing', 'simple', ARRAY['role_playing', 'creative_exploration'], 0.90, NOW() - INTERVAL '9 days'),
      (power_user_id, 'Design microservices', 'I''ll design microservices architecture systematically...', 'problem_solving', 'complex', ARRAY['constraint_setting', 'perspective_taking'], 0.93, NOW() - INTERVAL '8 days'),
      (power_user_id, 'Explain blockchain', 'Let me explain blockchain using analogies...', 'explanation', 'moderate', ARRAY['analogical_reasoning', 'step_by_step'], 0.84, NOW() - INTERVAL '7 days'),
      (power_user_id, 'Optimize React performance', 'I''ll optimize React performance step by step...', 'problem_solving', 'moderate', ARRAY['step_by_step', 'few_shot'], 0.86, NOW() - INTERVAL '6 days'),
      (power_user_id, 'Write user stories', 'Let me write user stories from user perspective...', 'creative_writing', 'moderate', ARRAY['perspective_taking', 'structured_output'], 0.81, NOW() - INTERVAL '5 days'),
      (power_user_id, 'Debug network issue', 'I''ll debug this network issue systematically...', 'problem_solving', 'complex', ARRAY['chain_of_thought', 'step_by_step'], 0.88, NOW() - INTERVAL '4 days'),
      (power_user_id, 'Create data pipeline', 'Let me design a data pipeline with constraints...', 'code_generation', 'complex', ARRAY['constraint_setting', 'structured_output'], 0.91, NOW() - INTERVAL '3 days'),
      (power_user_id, 'Analyze user feedback', 'I''ll analyze user feedback from multiple angles...', 'analysis', 'moderate', ARRAY['perspective_taking', 'structured_output'], 0.83, NOW() - INTERVAL '2 days'),
      (power_user_id, 'Implement search feature', 'Let''s implement search functionality step by step...', 'code_generation', 'moderate', ARRAY['step_by_step', 'few_shot'], 0.87, NOW() - INTERVAL '1 day');
  END IF;
END $$;