-- Create the regular test user for Phase 4 E2E tests
-- Password: Test123!@#

-- Regular test user
INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified, tier)
VALUES (
  'testuser',
  'test@example.com',
  '$2a$10$ZxW6Tlvn6H9J6Kx.BmxCIOJ8N5EO0h6i6PWBMhGFaCLBQR6wm5Ojm',
  'Test',
  'User',
  true,
  true,
  'free'
) ON CONFLICT (email) DO NOTHING;

-- Add some sample history for the regular test user
DO $$
DECLARE
  test_user_id UUID;
BEGIN
  -- Get the test user's ID
  SELECT id INTO test_user_id FROM users WHERE email = 'test@example.com';
  
  -- Only insert if user exists and has no history
  IF test_user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM prompts WHERE user_id = test_user_id) THEN
    -- Insert some sample prompts for the test user
    INSERT INTO prompts (user_id, original_prompt, enhanced_prompt, intent, complexity, techniques, metadata, created_at)
    VALUES
      (test_user_id, 'Calculate fibonacci sequence', 'Let''s calculate the fibonacci sequence step by step...', 'code_generation', 'simple', '{"techniques": ["step_by_step"]}'::jsonb, '{"confidence": 0.85}'::jsonb, NOW() - INTERVAL '5 days'),
      (test_user_id, 'Explain recursion', 'I''ll explain recursion using simple analogies...', 'explanation', 'moderate', '{"techniques": ["analogical_reasoning", "few_shot"]}'::jsonb, '{"confidence": 0.92}'::jsonb, NOW() - INTERVAL '3 days'),
      (test_user_id, 'Debug this code', 'Let me debug this code using chain of thought...', 'problem_solving', 'moderate', '{"techniques": ["chain_of_thought", "step_by_step"]}'::jsonb, '{"confidence": 0.88}'::jsonb, NOW() - INTERVAL '1 day');
  END IF;
END $$;