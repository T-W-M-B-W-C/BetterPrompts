-- BetterPrompts Seed Data for Development and Testing
-- This script populates the database with sample data

-- =====================================================
-- Test Users
-- =====================================================

-- Password for all test users is: TestPassword123!
-- bcrypt hash: $2a$10$YourHashHere (you'll need to generate this)

INSERT INTO auth.users (id, email, username, password_hash, first_name, last_name, role, tier, is_active, is_verified) VALUES
-- Admin user
('550e8400-e29b-41d4-a716-446655440001', 'admin@betterprompts.com', 'admin', '$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', 'Admin', 'User', 'admin', 'enterprise', true, true),

-- Pro tier users
('550e8400-e29b-41d4-a716-446655440002', 'john.doe@example.com', 'johndoe', '$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', 'John', 'Doe', 'user', 'pro', true, true),
('550e8400-e29b-41d4-a716-446655440003', 'jane.smith@example.com', 'janesmith', '$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', 'Jane', 'Smith', 'user', 'pro', true, true),

-- Free tier users
('550e8400-e29b-41d4-a716-446655440004', 'bob.wilson@example.com', 'bobwilson', '$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', 'Bob', 'Wilson', 'user', 'free', true, true),
('550e8400-e29b-41d4-a716-446655440005', 'alice.brown@example.com', 'alicebrown', '$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', 'Alice', 'Brown', 'user', 'free', true, true),

-- Developer with API access
('550e8400-e29b-41d4-a716-446655440006', 'dev@techcorp.com', 'developer', '$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', 'Dev', 'User', 'developer', 'pro', true, true),

-- Unverified user
('550e8400-e29b-41d4-a716-446655440007', 'unverified@example.com', 'unverified', '$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', 'Unverified', 'User', 'user', 'free', true, false),

-- Inactive user
('550e8400-e29b-41d4-a716-446655440008', 'inactive@example.com', 'inactive', '$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', 'Inactive', 'User', 'user', 'free', false, true);

-- =====================================================
-- User Preferences
-- =====================================================

INSERT INTO auth.user_preferences (id, user_id, preferred_techniques, excluded_techniques, complexity_preference, ui_theme, ui_language) VALUES
('650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', ARRAY['chain_of_thought', 'few_shot'], ARRAY['emotional_appeal'], 'moderate', 'dark', 'en'),
('650e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440003', ARRAY['tree_of_thoughts', 'self_consistency'], ARRAY[], 'advanced', 'light', 'en'),
('650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440004', ARRAY['step_by_step'], ARRAY['role_play', 'emotional_appeal'], 'simple', 'light', 'en');

-- =====================================================
-- API Keys
-- =====================================================

INSERT INTO auth.api_keys (id, user_id, name, key_hash, scopes, rate_limit, is_active) VALUES
('750e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440006', 'Production API Key', '$2a$10$YourAPIKeyHashHere', ARRAY['prompt:read', 'prompt:write', 'analytics:read'], 5000, true),
('750e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440006', 'Development API Key', '$2a$10$YourAPIKeyHashHere2', ARRAY['prompt:read', 'prompt:write'], 1000, true);

-- =====================================================
-- Intent Patterns
-- =====================================================

INSERT INTO prompts.intent_patterns (id, pattern, intent, sub_intent, confidence, is_verified, source) VALUES
-- Creative Writing
('850e8400-e29b-41d4-a716-446655440001', 'help me write a story', 'creative_writing', 'fiction', 0.95, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440002', 'write a blog post about', 'creative_writing', 'blog', 0.90, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440003', 'create a poem', 'creative_writing', 'poetry', 0.95, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440004', 'draft an article on', 'creative_writing', 'article', 0.85, true, 'manual'),

-- Problem Solving
('850e8400-e29b-41d4-a716-446655440005', 'how do I solve', 'problem_solving', 'technical', 0.90, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440006', 'debug this code', 'problem_solving', 'debugging', 0.95, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440007', 'fix this error', 'problem_solving', 'debugging', 0.95, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440008', 'troubleshoot', 'problem_solving', 'technical', 0.85, true, 'manual'),

-- Analysis
('850e8400-e29b-41d4-a716-446655440009', 'analyze this data', 'analysis', 'data_analysis', 0.95, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440010', 'compare and contrast', 'analysis', 'comparison', 0.90, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440011', 'evaluate the pros and cons', 'analysis', 'evaluation', 0.90, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440012', 'what are the implications', 'analysis', 'impact_analysis', 0.85, true, 'manual'),

-- Learning
('850e8400-e29b-41d4-a716-446655440013', 'explain how', 'learning', 'explanation', 0.90, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440014', 'teach me about', 'learning', 'tutorial', 0.95, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440015', 'what is', 'learning', 'definition', 0.85, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440016', 'give me examples of', 'learning', 'examples', 0.90, true, 'manual'),

-- Planning
('850e8400-e29b-41d4-a716-446655440017', 'create a plan for', 'planning', 'project_planning', 0.90, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440018', 'outline the steps', 'planning', 'process_planning', 0.90, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440019', 'develop a strategy', 'planning', 'strategic_planning', 0.85, true, 'manual'),
('850e8400-e29b-41d4-a716-446655440020', 'roadmap for', 'planning', 'roadmap', 0.85, true, 'manual');

-- =====================================================
-- Prompt History (Sample interactions)
-- =====================================================

INSERT INTO prompts.history (
    id, user_id, session_id, request_id, original_input, enhanced_output,
    intent, intent_confidence, complexity, techniques_used, technique_scores,
    processing_time_ms, token_count, model_used, feedback_score
) VALUES
-- John's prompts
('950e8400-e29b-41d4-a716-446655440001', 
 '550e8400-e29b-41d4-a716-446655440002', 
 'session_001', 
 'req_001',
 'Help me write a blog post about sustainable living',
 'Let''s approach writing your blog post about sustainable living step-by-step:

1. First, I''ll help you identify your target audience and main message
2. Then, we''ll outline the key points you want to cover
3. Next, we''ll develop engaging examples and practical tips
4. Finally, we''ll craft a compelling introduction and conclusion

What specific aspect of sustainable living would you like to focus on? For example:
- Zero-waste lifestyle tips
- Sustainable food choices
- Eco-friendly home improvements
- Reducing carbon footprint in daily life',
 'creative_writing',
 0.92,
 'moderate',
 ARRAY['chain_of_thought', 'structured_output'],
 '{"chain_of_thought": 0.85, "structured_output": 0.80}'::jsonb,
 145,
 256,
 'gpt-4',
 5),

('950e8400-e29b-41d4-a716-446655440002',
 '550e8400-e29b-41d4-a716-446655440002',
 'session_001',
 'req_002',
 'How do I implement a binary search tree in Python?',
 'I''ll guide you through implementing a binary search tree in Python with clear explanations:

```python
class TreeNode:
    """Represents a single node in the binary search tree"""
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

class BinarySearchTree:
    """Implementation of a Binary Search Tree data structure"""
    def __init__(self):
        self.root = None
    
    def insert(self, value):
        """Insert a value into the BST"""
        if not self.root:
            self.root = TreeNode(value)
        else:
            self._insert_recursive(self.root, value)
    
    def _insert_recursive(self, node, value):
        """Helper method for recursive insertion"""
        if value < node.value:
            if node.left is None:
                node.left = TreeNode(value)
            else:
                self._insert_recursive(node.left, value)
        else:
            if node.right is None:
                node.right = TreeNode(value)
            else:
                self._insert_recursive(node.right, value)
```

Key concepts to understand:
1. Each node has at most two children
2. Left child values are always less than parent
3. Right child values are always greater than or equal to parent
4. This maintains O(log n) search time in balanced trees',
 'problem_solving',
 0.88,
 'moderate',
 ARRAY['step_by_step', 'few_shot'],
 '{"step_by_step": 0.90, "few_shot": 0.85}'::jsonb,
 132,
 412,
 'gpt-4',
 4),

-- Jane's prompts
('950e8400-e29b-41d4-a716-446655440003',
 '550e8400-e29b-41d4-a716-446655440003',
 'session_002',
 'req_003',
 'Analyze the pros and cons of remote work',
 'Let me explore multiple perspectives on remote work to provide a comprehensive analysis:

**Approach 1: Employee Perspective**
Pros:
- Flexibility in work location and often schedule
- No commute time (saves 2-3 hours daily)
- Better work-life balance potential
- Cost savings on transportation and work attire

Cons:
- Potential isolation and reduced social interaction
- Blurred work-life boundaries
- Home distractions
- Limited career visibility

**Approach 2: Employer Perspective**
Pros:
- Access to global talent pool
- Reduced overhead costs (office space, utilities)
- Often increased productivity (studies show 13% improvement)
- Higher employee retention

Cons:
- Challenges in team collaboration
- Difficulty monitoring performance
- Security risks with distributed data
- Company culture maintenance

**Approach 3: Societal Impact**
Pros:
- Reduced traffic congestion
- Lower carbon emissions
- Rural area economic opportunities
- Inclusion for disabled workers

Cons:
- Downtown business district decline
- Reduced spontaneous innovation
- Digital divide exacerbation

Which perspective would you like me to elaborate on further?',
 'analysis',
 0.94,
 'advanced',
 ARRAY['tree_of_thoughts', 'structured_output'],
 '{"tree_of_thoughts": 0.92, "structured_output": 0.88}'::jsonb,
 178,
 389,
 'gpt-4',
 5),

-- Bob's simple prompt
('950e8400-e29b-41d4-a716-446655440004',
 '550e8400-e29b-41d4-a716-446655440004',
 'session_003',
 'req_004',
 'What is machine learning?',
 'Machine learning is a type of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.

Here''s a simple breakdown:

1. **What it does**: Instead of following pre-written rules, ML systems find patterns in data and make decisions based on those patterns.

2. **How it works**: 
   - You feed the system lots of examples
   - It identifies patterns in these examples
   - It uses these patterns to make predictions about new data

3. **Real-world examples**:
   - Email spam filters learning to identify junk mail
   - Netflix recommending shows based on your viewing history
   - Voice assistants understanding your speech

4. **Key point**: The system gets better with more data and experience, just like how humans learn from practice!

Would you like me to explain any specific aspect in more detail?',
 'learning',
 0.91,
 'simple',
 ARRAY['step_by_step', 'analogical'],
 '{"step_by_step": 0.88, "analogical": 0.82}'::jsonb,
 98,
 234,
 'gpt-3.5',
 4);

-- =====================================================
-- Saved Prompts
-- =====================================================

INSERT INTO prompts.saved_prompts (id, user_id, history_id, title, description, tags, is_public) VALUES
('A50e8400-e29b-41d4-a716-446655440001', 
 '550e8400-e29b-41d4-a716-446655440002',
 '950e8400-e29b-41d4-a716-446655440001',
 'Sustainable Living Blog Template',
 'Great template for writing blog posts about sustainability topics',
 ARRAY['writing', 'blog', 'sustainability'],
 true),

('A50e8400-e29b-41d4-a716-446655440002',
 '550e8400-e29b-41d4-a716-446655440002',
 '950e8400-e29b-41d4-a716-446655440002',
 'Binary Search Tree Implementation',
 'Complete Python implementation with explanations',
 ARRAY['programming', 'python', 'data-structures'],
 false);

-- =====================================================
-- Collections
-- =====================================================

INSERT INTO prompts.collections (id, user_id, name, description, color, icon) VALUES
('B50e8400-e29b-41d4-a716-446655440001',
 '550e8400-e29b-41d4-a716-446655440002',
 'Programming Templates',
 'Useful prompts for coding tasks',
 '#3B82F6',
 'code'),

('B50e8400-e29b-41d4-a716-446655440002',
 '550e8400-e29b-41d4-a716-446655440002',
 'Writing Helpers',
 'Templates for various writing tasks',
 '#10B981',
 'edit');

-- Add prompts to collections
INSERT INTO prompts.collection_prompts (collection_id, saved_prompt_id, position) VALUES
('B50e8400-e29b-41d4-a716-446655440001', 'A50e8400-e29b-41d4-a716-446655440002', 1),
('B50e8400-e29b-41d4-a716-446655440002', 'A50e8400-e29b-41d4-a716-446655440001', 1);

-- =====================================================
-- Technique Effectiveness Data
-- =====================================================

INSERT INTO analytics.technique_effectiveness (
    id, technique, intent, success_count, total_count, 
    average_feedback, average_processing_time_ms, date
) VALUES
-- Chain of Thought effectiveness
('C50e8400-e29b-41d4-a716-446655440001', 'chain_of_thought', 'creative_writing', 45, 50, 4.5, 142, CURRENT_DATE - INTERVAL '1 day'),
('C50e8400-e29b-41d4-a716-446655440002', 'chain_of_thought', 'problem_solving', 38, 45, 4.2, 156, CURRENT_DATE - INTERVAL '1 day'),
('C50e8400-e29b-41d4-a716-446655440003', 'chain_of_thought', 'analysis', 42, 48, 4.4, 168, CURRENT_DATE - INTERVAL '1 day'),

-- Few-Shot effectiveness
('C50e8400-e29b-41d4-a716-446655440004', 'few_shot', 'learning', 52, 55, 4.7, 134, CURRENT_DATE - INTERVAL '1 day'),
('C50e8400-e29b-41d4-a716-446655440005', 'few_shot', 'problem_solving', 40, 50, 4.0, 145, CURRENT_DATE - INTERVAL '1 day'),

-- Tree of Thoughts effectiveness
('C50e8400-e29b-41d4-a716-446655440006', 'tree_of_thoughts', 'analysis', 48, 52, 4.6, 189, CURRENT_DATE - INTERVAL '1 day'),
('C50e8400-e29b-41d4-a716-446655440007', 'tree_of_thoughts', 'planning', 44, 50, 4.4, 198, CURRENT_DATE - INTERVAL '1 day'),

-- Today's data
('C50e8400-e29b-41d4-a716-446655440008', 'chain_of_thought', 'creative_writing', 12, 15, 4.3, 138, CURRENT_DATE),
('C50e8400-e29b-41d4-a716-446655440009', 'step_by_step', 'learning', 18, 20, 4.5, 125, CURRENT_DATE);

-- =====================================================
-- Daily Statistics
-- =====================================================

INSERT INTO analytics.daily_stats (
    id, date, total_requests, unique_users, new_users,
    total_enhancements, average_response_time_ms, error_count,
    by_technique, by_intent, by_hour
) VALUES
('D50e8400-e29b-41d4-a716-446655440001',
 CURRENT_DATE - INTERVAL '2 days',
 450, 125, 8, 445, 152, 5,
 '{"chain_of_thought": 120, "few_shot": 85, "tree_of_thoughts": 65, "step_by_step": 100, "self_consistency": 45, "structured_output": 30}'::jsonb,
 '{"creative_writing": 95, "problem_solving": 120, "analysis": 80, "learning": 100, "planning": 55}'::jsonb,
 '{"9": 35, "10": 45, "11": 52, "12": 38, "13": 44, "14": 56, "15": 62, "16": 58, "17": 48, "18": 12}'::jsonb),

('D50e8400-e29b-41d4-a716-446655440002',
 CURRENT_DATE - INTERVAL '1 day',
 520, 142, 12, 515, 148, 5,
 '{"chain_of_thought": 140, "few_shot": 95, "tree_of_thoughts": 72, "step_by_step": 115, "self_consistency": 52, "structured_output": 41}'::jsonb,
 '{"creative_writing": 108, "problem_solving": 135, "analysis": 92, "learning": 115, "planning": 65}'::jsonb,
 '{"9": 42, "10": 51, "11": 58, "12": 45, "13": 49, "14": 62, "15": 68, "16": 65, "17": 55, "18": 25}'::jsonb);

-- =====================================================
-- Some sample embeddings (normally these would be generated by the ML model)
-- =====================================================

-- Note: In production, these would be actual 768-dimensional vectors from DeBERTa
-- For testing, we'll use smaller placeholder vectors
INSERT INTO prompts.embeddings (id, source_type, source_id, embedding, model_version) VALUES
('E50e8400-e29b-41d4-a716-446655440001', 
 'prompt_history', 
 '950e8400-e29b-41d4-a716-446655440001',
 '[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]',
 'deberta-v3-base-v1'),

('E50e8400-e29b-41d4-a716-446655440002',
 'prompt_history',
 '950e8400-e29b-41d4-a716-446655440002',
 '[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]',
 'deberta-v3-base-v1');

-- =====================================================
-- Grant permissions for test user
-- =====================================================

-- Ensure the betterprompts user has access to all data
GRANT ALL ON ALL TABLES IN SCHEMA auth TO betterprompts;
GRANT ALL ON ALL TABLES IN SCHEMA prompts TO betterprompts;
GRANT ALL ON ALL TABLES IN SCHEMA analytics TO betterprompts;