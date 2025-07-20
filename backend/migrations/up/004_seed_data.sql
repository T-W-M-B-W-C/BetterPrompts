-- Migration: 004_seed_data.sql
-- Description: Initial seed data for development and testing
-- Author: Backend Team
-- Date: 2024-01-20

-- =====================================================
-- PROMPT TEMPLATES - Core Techniques
-- =====================================================

-- Clear existing templates to ensure consistency
TRUNCATE prompts.templates CASCADE;

-- Insert comprehensive prompt templates
INSERT INTO prompts.templates (name, slug, technique, description, template_text, variables, category, effectiveness_score) VALUES
    -- Reasoning Techniques
    ('Chain of Thought', 'chain-of-thought', 'chain_of_thought', 
     'Step-by-step reasoning approach that breaks down complex problems into manageable parts', 
     E'Let\'s approach this step-by-step:\n\n{input}\n\nStep 1: First, I\'ll identify the key components of the problem...\nStep 2: Next, I\'ll analyze each component separately...\nStep 3: Then, I\'ll examine how these components relate to each other...\nStep 4: Finally, I\'ll synthesize the findings into a comprehensive solution...\n\nLet me work through each step:',
     '["input"]'::jsonb, 'reasoning', 0.85),
    
    ('Tree of Thoughts', 'tree-of-thoughts', 'tree_of_thoughts', 
     'Explores multiple reasoning paths simultaneously to find the best solution',
     E'I\'ll explore different approaches to solve this problem:\n\n{input}\n\nApproach 1: [Direct Method]\n- Pros: ...\n- Cons: ...\n- Implementation: ...\n\nApproach 2: [Alternative Method]\n- Pros: ...\n- Cons: ...\n- Implementation: ...\n\nApproach 3: [Creative Method]\n- Pros: ...\n- Cons: ...\n- Implementation: ...\n\nEvaluating all approaches, the best solution appears to be...',
     '["input"]'::jsonb, 'reasoning', 0.82),
    
    -- Learning Techniques
    ('Few-Shot Learning', 'few-shot-learning', 'few_shot', 
     'Learning from examples to solve similar problems effectively',
     E'Here are some examples of how to approach this type of problem:\n\n{examples}\n\nNow, applying the same pattern to your request:\n\n{input}\n\nFollowing the examples above, the solution would be:',
     '["examples", "input"]'::jsonb, 'learning', 0.88),
    
    ('Zero-Shot Learning', 'zero-shot-learning', 'zero_shot', 
     'Solving new problems without specific examples by applying general knowledge',
     E'Although I haven\'t seen this exact problem before, I can apply general principles:\n\n{input}\n\nBased on my understanding of {domain}, the key principles that apply here are:\n1. ...\n2. ...\n3. ...\n\nApplying these principles to your specific case:',
     '["input", "domain"]'::jsonb, 'learning', 0.75),
    
    -- Verification Techniques
    ('Self-Consistency', 'self-consistency', 'self_consistency', 
     'Multiple attempts with consistency verification for reliable results',
     E'I\'ll solve this problem multiple ways to ensure consistency:\n\n{input}\n\nAttempt 1: [First approach]\nResult: ...\n\nAttempt 2: [Second approach]\nResult: ...\n\nAttempt 3: [Third approach]\nResult: ...\n\nVerifying consistency across attempts...\nFinal verified answer:',
     '["input"]'::jsonb, 'verification', 0.90),
    
    ('Reflection', 'reflection', 'reflection', 
     'Critical self-evaluation to improve response quality',
     E'Initial response to your request:\n\n{input}\n\n[Initial answer...]\n\nUpon reflection:\n- What I did well: ...\n- What could be improved: ...\n- Potential blind spots: ...\n\nRevised and improved response:',
     '["input"]'::jsonb, 'verification', 0.78),
    
    -- Creative Techniques
    ('Role Playing', 'role-playing', 'role_play', 
     'Adopting specific personas or expertise for specialized insights',
     E'As a {role}, I\'ll address your request:\n\n{input}\n\nFrom my perspective as a {role}, the key considerations are:\n1. [Domain-specific insight]\n2. [Professional recommendation]\n3. [Expert best practice]\n\nMy professional recommendation would be:',
     '["role", "input"]'::jsonb, 'creative', 0.80),
    
    ('Analogical Reasoning', 'analogical-reasoning', 'analogical', 
     'Using analogies to explain complex concepts clearly',
     E'To understand this concept, let me use an analogy:\n\n{input}\n\nThis is similar to {analogy}:\n- Just as [analogy component 1] relates to [analogy component 2]...\n- Your [concept component 1] relates to [concept component 2]...\n\nApplying this analogy to your specific situation:',
     '["input", "analogy"]'::jsonb, 'creative', 0.77),
    
    -- Structured Techniques
    ('Structured Output', 'structured-output', 'structured_output', 
     'Generating responses in specific formats for clarity',
     E'I\'ll provide a structured response in {format} format:\n\n{input}\n\n{format_template}\n\nDetailed response following the above structure:',
     '["format", "input", "format_template"]'::jsonb, 'formatting', 0.83),
    
    ('Meta Prompting', 'meta-prompting', 'meta_prompt', 
     'Creating prompts that generate other prompts',
     E'I\'ll help you create an effective prompt for this task:\n\n{input}\n\nOptimal prompt structure:\n- Context: [Provide background]\n- Specific request: [Clear ask]\n- Constraints: [Any limitations]\n- Desired format: [Output structure]\n\nHere\'s your optimized prompt:',
     '["input"]'::jsonb, 'meta', 0.81);

-- =====================================================
-- INTENT PATTERNS - Training Data
-- =====================================================

-- Insert common intent patterns
INSERT INTO prompts.intent_patterns (pattern, normalized_pattern, intent, sub_intent, confidence, is_verified, source) VALUES
    -- Code generation patterns
    ('write code', 'write code', 'code_generation', NULL, 0.95, true, 'manual'),
    ('create function', 'create function', 'code_generation', 'function', 0.95, true, 'manual'),
    ('implement algorithm', 'implement algorithm', 'code_generation', 'algorithm', 0.90, true, 'manual'),
    ('build component', 'build component', 'code_generation', 'component', 0.90, true, 'manual'),
    
    -- Explanation patterns
    ('explain', 'explain', 'explanation', NULL, 0.95, true, 'manual'),
    ('how does', 'how does', 'explanation', 'mechanism', 0.90, true, 'manual'),
    ('what is', 'what is', 'explanation', 'definition', 0.90, true, 'manual'),
    ('why does', 'why does', 'explanation', 'reasoning', 0.90, true, 'manual'),
    
    -- Problem solving patterns
    ('solve', 'solve', 'problem_solving', NULL, 0.95, true, 'manual'),
    ('fix bug', 'fix bug', 'problem_solving', 'debugging', 0.95, true, 'manual'),
    ('optimize', 'optimize', 'problem_solving', 'optimization', 0.90, true, 'manual'),
    ('improve performance', 'improve performance', 'problem_solving', 'performance', 0.90, true, 'manual'),
    
    -- Analysis patterns
    ('analyze', 'analyze', 'analysis', NULL, 0.95, true, 'manual'),
    ('compare', 'compare', 'analysis', 'comparison', 0.90, true, 'manual'),
    ('evaluate', 'evaluate', 'analysis', 'evaluation', 0.90, true, 'manual'),
    ('review code', 'review code', 'analysis', 'code_review', 0.95, true, 'manual'),
    
    -- Creative patterns
    ('brainstorm', 'brainstorm', 'creative', 'ideation', 0.90, true, 'manual'),
    ('suggest ideas', 'suggest ideas', 'creative', 'ideation', 0.90, true, 'manual'),
    ('design', 'design', 'creative', 'design', 0.85, true, 'manual'),
    ('create story', 'create story', 'creative', 'storytelling', 0.85, true, 'manual');

-- =====================================================
-- TECHNIQUE EFFECTIVENESS - Initial Metrics
-- =====================================================

-- Insert baseline effectiveness data
INSERT INTO analytics.technique_effectiveness (technique, intent, success_count, total_count, average_feedback, average_processing_time_ms) VALUES
    ('chain_of_thought', 'problem_solving', 850, 1000, 4.2, 1200),
    ('chain_of_thought', 'explanation', 750, 900, 4.3, 1100),
    ('chain_of_thought', 'analysis', 800, 950, 4.1, 1300),
    
    ('few_shot', 'code_generation', 920, 1000, 4.5, 800),
    ('few_shot', 'problem_solving', 880, 1000, 4.4, 900),
    ('few_shot', 'creative', 700, 850, 4.0, 1000),
    
    ('tree_of_thoughts', 'problem_solving', 820, 1000, 4.3, 1500),
    ('tree_of_thoughts', 'analysis', 780, 950, 4.2, 1600),
    
    ('self_consistency', 'problem_solving', 900, 1000, 4.6, 2000),
    ('self_consistency', 'code_generation', 870, 1000, 4.5, 1800),
    
    ('role_play', 'creative', 850, 1000, 4.3, 1000),
    ('role_play', 'explanation', 800, 950, 4.2, 1100),
    
    ('structured_output', 'code_generation', 900, 1000, 4.4, 700),
    ('structured_output', 'analysis', 850, 1000, 4.3, 800);

-- =====================================================
-- TEST USERS - For Development
-- =====================================================

-- Only insert test users in non-production environments
DO $$
BEGIN
    -- Check if we're in a development environment (customize this check as needed)
    IF current_database() LIKE '%dev%' OR current_database() LIKE '%test%' THEN
        -- Insert test users with hashed passwords (password: 'testpass123')
        INSERT INTO auth.users (email, username, password_hash, first_name, last_name, roles, tier, is_verified) VALUES
            ('admin@betterprompts.test', 'admin', '$2a$10$YourHashedPasswordHere', 'Admin', 'User', ARRAY['admin'], 'enterprise', true),
            ('developer@betterprompts.test', 'developer', '$2a$10$YourHashedPasswordHere', 'Dev', 'User', ARRAY['developer'], 'pro', true),
            ('user@betterprompts.test', 'testuser', '$2a$10$YourHashedPasswordHere', 'Test', 'User', ARRAY['user'], 'free', true)
        ON CONFLICT (email) DO NOTHING;
        
        -- Create preferences for test users
        INSERT INTO auth.user_preferences (user_id, preferred_techniques, ui_theme)
        SELECT id, ARRAY['chain_of_thought', 'few_shot'], 'dark'
        FROM auth.users
        WHERE email IN ('admin@betterprompts.test', 'developer@betterprompts.test', 'user@betterprompts.test')
        ON CONFLICT (user_id) DO NOTHING;
    END IF;
END $$;

-- =====================================================
-- DAILY STATS - Sample Data
-- =====================================================

-- Insert some sample daily stats for the last 7 days
INSERT INTO analytics.daily_stats (date, total_requests, unique_users, new_users, total_enhancements, average_response_time_ms, error_count, by_technique, by_intent)
SELECT 
    CURRENT_DATE - interval '1 day' * generate_series(0, 6) as date,
    1000 + random() * 500 as total_requests,
    100 + random() * 50 as unique_users,
    5 + random() * 10 as new_users,
    800 + random() * 400 as total_enhancements,
    500 + random() * 300 as average_response_time_ms,
    random() * 20 as error_count,
    '{"chain_of_thought": 300, "few_shot": 250, "tree_of_thoughts": 150, "self_consistency": 100}'::jsonb,
    '{"problem_solving": 400, "code_generation": 300, "explanation": 200, "analysis": 100}'::jsonb
ON CONFLICT (date) DO NOTHING;

-- Record migration
INSERT INTO public.schema_migrations (version, description, checksum)
VALUES (4, 'Seed data', md5('004_seed_data'))
ON CONFLICT (version) DO NOTHING;