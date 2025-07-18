# Prompt Patterns Database Design

## Database Architecture Overview

### Design Principles
- **Scalability**: Designed for millions of prompts and patterns
- **Performance**: Optimized for sub-50ms query times
- **Flexibility**: JSONB for extensible metadata
- **Reliability**: ACID compliance with PostgreSQL
- **Intelligence**: Vector embeddings for similarity search
- **Versioning**: Full audit trail and pattern evolution

## Technology Stack

```yaml
Primary Database:
  - PostgreSQL 15+ with extensions:
    - pgvector: Semantic similarity search
    - pg_trgm: Text similarity matching
    - btree_gin: Efficient JSONB indexing
    - timescaledb: Time-series analytics (optional)

Vector Database:
  - Pinecone/Weaviate for high-scale vector search
  - Fallback to pgvector for smaller deployments

Cache Layer:
  - Redis for hot data and session management
  - Materialized views for complex aggregations

Search:
  - Elasticsearch for full-text search (optional)
  - PostgreSQL FTS for basic search needs
```

## Core Database Schema

### 1. Techniques and Patterns

```sql
-- Prompt engineering techniques master table
CREATE TABLE techniques (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'cot', 'few_shot'
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    description TEXT NOT NULL,
    detailed_explanation TEXT,
    complexity_level INTEGER CHECK (complexity_level BETWEEN 1 AND 5),
    
    -- Effectiveness metrics
    base_effectiveness DECIMAL(3,2) DEFAULT 0.70,
    effectiveness_variance DECIMAL(3,2) DEFAULT 0.10,
    
    -- Usage guidelines
    when_to_use TEXT[],
    when_not_to_use TEXT[],
    prerequisites TEXT[],
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    is_experimental BOOLEAN DEFAULT false,
    requires_examples BOOLEAN DEFAULT false,
    min_context_length INTEGER DEFAULT 0,
    max_context_length INTEGER DEFAULT 10000,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', name), 'A') ||
        setweight(to_tsvector('english', description), 'B') ||
        setweight(to_tsvector('english', COALESCE(detailed_explanation, '')), 'C')
    ) STORED
);

CREATE INDEX idx_techniques_search ON techniques USING GIN(search_vector);
CREATE INDEX idx_techniques_category ON techniques(category, subcategory);
CREATE INDEX idx_techniques_complexity ON techniques(complexity_level);
CREATE INDEX idx_techniques_effectiveness ON techniques(base_effectiveness DESC);
```

```sql
-- Technique implementation patterns
CREATE TABLE technique_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technique_id UUID NOT NULL REFERENCES techniques(id) ON DELETE CASCADE,
    pattern_name VARCHAR(255) NOT NULL,
    
    -- Pattern template with placeholders
    template TEXT NOT NULL,
    template_vars JSONB DEFAULT '{}', -- {var_name: {type, description, default}}
    
    -- Pattern metadata
    intent_types TEXT[], -- ['analysis', 'creative', 'technical']
    optimal_for JSONB, -- {conditions: [...], scenarios: [...]}
    
    -- Performance tracking
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2),
    avg_user_rating DECIMAL(2,1),
    
    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uk_technique_pattern UNIQUE(technique_id, pattern_name, version)
);

CREATE INDEX idx_patterns_technique ON technique_patterns(technique_id);
CREATE INDEX idx_patterns_intent ON technique_patterns USING GIN(intent_types);
CREATE INDEX idx_patterns_active ON technique_patterns(is_active) WHERE is_active = true;
```

### 2. Intent Classification Data

```sql
-- Intent taxonomy hierarchy
CREATE TABLE intent_taxonomy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) UNIQUE NOT NULL, -- 'creative.writing.fiction'
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES intent_taxonomy(id),
    level INTEGER NOT NULL DEFAULT 1,
    path TEXT NOT NULL, -- materialized path for fast queries
    
    -- Intent characteristics
    typical_complexity INTEGER CHECK (typical_complexity BETWEEN 1 AND 5),
    requires_creativity BOOLEAN DEFAULT false,
    requires_analysis BOOLEAN DEFAULT false,
    requires_structure BOOLEAN DEFAULT false,
    
    -- Associated data
    keywords TEXT[],
    example_prompts TEXT[],
    description TEXT,
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    usage_frequency INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Hierarchical query optimization
    tree_sortkey VARCHAR(255) -- for efficient tree traversal
);

CREATE INDEX idx_intent_parent ON intent_taxonomy(parent_id);
CREATE INDEX idx_intent_path ON intent_taxonomy(path);
CREATE INDEX idx_intent_level ON intent_taxonomy(level);
CREATE INDEX idx_intent_keywords ON intent_taxonomy USING GIN(keywords);

-- Intent-Technique effectiveness mapping
CREATE TABLE intent_technique_effectiveness (
    intent_id UUID REFERENCES intent_taxonomy(id) ON DELETE CASCADE,
    technique_id UUID REFERENCES techniques(id) ON DELETE CASCADE,
    
    -- Effectiveness metrics
    effectiveness_score DECIMAL(3,2) NOT NULL,
    confidence_level DECIMAL(3,2) DEFAULT 0.80,
    sample_size INTEGER DEFAULT 0,
    
    -- Context-specific adjustments
    complexity_adjustment JSONB, -- {1: -0.1, 2: 0, 3: 0.1, 4: 0.15, 5: 0.2}
    domain_adjustments JSONB, -- {technical: 0.1, creative: -0.05}
    
    -- Performance tracking
    real_world_performance DECIMAL(3,2),
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (intent_id, technique_id)
);

CREATE INDEX idx_effectiveness_score ON intent_technique_effectiveness(effectiveness_score DESC);
```

### 3. Prompt Templates and Examples

```sql
-- Curated prompt templates
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    
    -- Template content
    template_text TEXT NOT NULL,
    variables JSONB NOT NULL, -- [{name, type, description, required, default}]
    
    -- Associations
    technique_ids UUID[] NOT NULL,
    intent_ids UUID[],
    
    -- Quality metrics
    quality_score DECIMAL(3,2) DEFAULT 0.80,
    community_rating DECIMAL(2,1),
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2),
    
    -- Metadata
    tags TEXT[],
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    estimated_tokens INTEGER,
    language VARCHAR(10) DEFAULT 'en',
    
    -- Authorship
    created_by UUID REFERENCES users(id),
    is_official BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT true,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_templates_category ON prompt_templates(category);
CREATE INDEX idx_templates_techniques ON prompt_templates USING GIN(technique_ids);
CREATE INDEX idx_templates_quality ON prompt_templates(quality_score DESC);
CREATE INDEX idx_templates_tags ON prompt_templates USING GIN(tags);

-- Concrete examples of successful prompts
CREATE TABLE prompt_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES prompt_templates(id),
    
    -- Example content
    original_prompt TEXT NOT NULL,
    enhanced_prompt TEXT NOT NULL,
    techniques_applied UUID[] NOT NULL,
    
    -- Context
    intent_classification JSONB NOT NULL,
    complexity_level INTEGER,
    domain VARCHAR(100),
    
    -- Results
    model_used VARCHAR(50),
    response_quality_score DECIMAL(3,2),
    user_satisfaction_score INTEGER CHECK (user_satisfaction_score BETWEEN 1 AND 5),
    
    -- Metadata
    explanation TEXT,
    key_improvements TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(50) -- 'user_generated', 'curated', 'synthetic'
);

CREATE INDEX idx_examples_template ON prompt_examples(template_id);
CREATE INDEX idx_examples_quality ON prompt_examples(response_quality_score DESC);
```

### 4. User Data and Personalization

```sql
-- User profiles with preferences
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    
    -- Profile data
    full_name VARCHAR(255),
    avatar_url TEXT,
    bio TEXT,
    
    -- Preferences
    preferences JSONB DEFAULT '{
        "complexity_preference": "moderate",
        "explanation_detail": "medium",
        "language": "en",
        "favorite_techniques": [],
        "ui_theme": "light"
    }',
    
    -- Subscription
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Account metadata
    email_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User learning profile
CREATE TABLE user_learning_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- Skill progression
    skill_level VARCHAR(50) DEFAULT 'beginner', -- beginner, intermediate, advanced, expert
    techniques_mastered UUID[] DEFAULT '{}',
    techniques_learning UUID[] DEFAULT '{}',
    
    -- Usage patterns
    primary_use_cases TEXT[],
    average_prompt_complexity DECIMAL(2,1),
    preferred_explanation_style VARCHAR(50),
    
    -- Learning metrics
    total_prompts_created INTEGER DEFAULT 0,
    successful_prompts INTEGER DEFAULT 0,
    techniques_tried INTEGER DEFAULT 0,
    learning_velocity DECIMAL(3,2), -- skill improvement rate
    
    -- Personalization vectors
    interest_vector vector(384), -- for content recommendation
    style_vector vector(384), -- for style matching
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_skill ON user_learning_profiles(skill_level);
CREATE INDEX idx_user_interests ON user_learning_profiles USING ivfflat(interest_vector vector_cosine_ops);
```

### 5. Usage History and Analytics

```sql
-- Prompt enhancement history
CREATE TABLE prompt_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    
    -- Request data
    original_prompt TEXT NOT NULL,
    original_length INTEGER NOT NULL,
    detected_intent_path TEXT,
    detected_complexity INTEGER,
    
    -- Enhancement data
    enhanced_prompt TEXT NOT NULL,
    enhanced_length INTEGER NOT NULL,
    techniques_applied UUID[] NOT NULL,
    enhancement_metadata JSONB,
    
    -- Performance metrics
    processing_time_ms INTEGER,
    model_confidence DECIMAL(3,2),
    
    -- User feedback
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    was_helpful BOOLEAN,
    
    -- Context
    client_type VARCHAR(50), -- 'web', 'api', 'mobile'
    api_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE prompt_history_2024_01 PARTITION OF prompt_history
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE INDEX idx_history_user_date ON prompt_history(user_id, created_at DESC);
CREATE INDEX idx_history_session ON prompt_history(session_id);
CREATE INDEX idx_history_techniques ON prompt_history USING GIN(techniques_applied);

-- Aggregated analytics
CREATE TABLE technique_performance_analytics (
    technique_id UUID REFERENCES techniques(id) ON DELETE CASCADE,
    date_bucket DATE NOT NULL,
    
    -- Usage metrics
    total_uses INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    
    -- Performance metrics
    avg_confidence DECIMAL(3,2),
    avg_rating DECIMAL(2,1),
    success_rate DECIMAL(3,2),
    
    -- Context distribution
    complexity_distribution JSONB, -- {1: 20, 2: 35, 3: 30, 4: 10, 5: 5}
    intent_distribution JSONB, -- {creative: 40, analytical: 30, ...}
    
    -- Computed metrics
    effectiveness_trend DECIMAL(4,3), -- change from previous period
    adoption_rate DECIMAL(3,2), -- % of users trying this technique
    
    PRIMARY KEY (technique_id, date_bucket)
);

CREATE INDEX idx_analytics_date ON technique_performance_analytics(date_bucket DESC);
```

### 6. Machine Learning Support

```sql
-- Training data for ML models
CREATE TABLE ml_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Input features
    prompt_text TEXT NOT NULL,
    prompt_embedding vector(384),
    linguistic_features JSONB NOT NULL,
    
    -- Labels
    intent_labels JSONB NOT NULL, -- {primary: 'creative.writing', secondary: [...]}
    complexity_label INTEGER NOT NULL,
    optimal_techniques UUID[] NOT NULL,
    
    -- Quality indicators
    is_validated BOOLEAN DEFAULT false,
    validation_score DECIMAL(3,2),
    validator_id UUID REFERENCES users(id),
    
    -- Source tracking
    source_type VARCHAR(50), -- 'production', 'synthetic', 'manual'
    source_id UUID, -- reference to prompt_history or other source
    
    -- Dataset management
    dataset_version VARCHAR(20),
    is_test_set BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ml_validated ON ml_training_data(is_validated, validation_score DESC);
CREATE INDEX idx_ml_dataset ON ml_training_data(dataset_version, is_test_set);
CREATE INDEX idx_ml_embedding ON ml_training_data USING ivfflat(prompt_embedding vector_cosine_ops);

-- Model performance tracking
CREATE TABLE ml_model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'intent_classifier', 'technique_selector'
    
    -- Performance metrics
    accuracy DECIMAL(4,3),
    precision_scores JSONB, -- per-class precision
    recall_scores JSONB, -- per-class recall
    f1_scores JSONB, -- per-class F1
    
    -- Model metadata
    training_dataset_version VARCHAR(20),
    training_samples INTEGER,
    parameters JSONB,
    
    -- Deployment info
    is_active BOOLEAN DEFAULT false,
    deployed_at TIMESTAMP WITH TIME ZONE,
    deprecated_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_model_active ON ml_model_performance(model_type, is_active);
```

### 7. Feedback and Improvement Loop

```sql
-- User feedback on enhancements
CREATE TABLE enhancement_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_history_id UUID REFERENCES prompt_history(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Feedback data
    overall_rating INTEGER NOT NULL CHECK (overall_rating BETWEEN 1 AND 5),
    technique_ratings JSONB, -- {technique_id: rating}
    
    -- Detailed feedback
    what_worked TEXT[],
    what_didnt_work TEXT[],
    suggestions TEXT,
    
    -- Improvement tracking
    resulted_in_success BOOLEAN,
    time_saved_estimate INTEGER, -- in minutes
    would_recommend BOOLEAN,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_prompt ON enhancement_feedback(prompt_history_id);
CREATE INDEX idx_feedback_rating ON enhancement_feedback(overall_rating DESC);

-- A/B testing experiments
CREATE TABLE ab_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Experiment configuration
    variant_a JSONB NOT NULL, -- control configuration
    variant_b JSONB NOT NULL, -- test configuration
    
    -- Targeting
    user_percentage DECIMAL(3,2) DEFAULT 0.50,
    user_segments JSONB, -- targeting criteria
    
    -- Metrics
    primary_metric VARCHAR(100) NOT NULL,
    secondary_metrics TEXT[],
    
    -- Results
    variant_a_results JSONB,
    variant_b_results JSONB,
    statistical_significance DECIMAL(4,3),
    winner VARCHAR(1), -- 'A', 'B', or NULL
    
    -- Lifecycle
    status VARCHAR(50) DEFAULT 'draft',
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_experiments_status ON ab_experiments(status);
CREATE INDEX idx_experiments_dates ON ab_experiments(started_at, ended_at);
```

### 8. Community and Sharing

```sql
-- Shared prompt library
CREATE TABLE community_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Prompt data
    title VARCHAR(255) NOT NULL,
    description TEXT,
    original_prompt TEXT NOT NULL,
    enhanced_prompt TEXT NOT NULL,
    techniques_used UUID[] NOT NULL,
    
    -- Categorization
    category VARCHAR(100) NOT NULL,
    tags TEXT[],
    language VARCHAR(10) DEFAULT 'en',
    
    -- Community metrics
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    remix_count INTEGER DEFAULT 0,
    
    -- Quality control
    is_featured BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    moderation_status VARCHAR(50) DEFAULT 'pending',
    
    -- Metadata
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_community_featured ON community_prompts(is_featured, likes DESC);
CREATE INDEX idx_community_category ON community_prompts(category);
CREATE INDEX idx_community_tags ON community_prompts USING GIN(tags);
CREATE INDEX idx_community_author ON community_prompts(author_id);

-- User interactions with community content
CREATE TABLE community_interactions (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prompt_id UUID REFERENCES community_prompts(id) ON DELETE CASCADE,
    
    -- Interaction types
    has_liked BOOLEAN DEFAULT false,
    has_saved BOOLEAN DEFAULT false,
    has_reported BOOLEAN DEFAULT false,
    
    -- Usage
    times_used INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Feedback
    private_notes TEXT,
    
    PRIMARY KEY (user_id, prompt_id)
);
```

## Database Functions and Procedures

### Intelligent Technique Selection

```sql
-- Function to get optimal techniques for a given intent and complexity
CREATE OR REPLACE FUNCTION get_optimal_techniques(
    p_intent_path TEXT,
    p_complexity INTEGER,
    p_user_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    technique_id UUID,
    technique_name VARCHAR(255),
    effectiveness_score DECIMAL(3,2),
    personalization_score DECIMAL(3,2),
    final_score DECIMAL(3,2)
) AS $$
DECLARE
    v_intent_id UUID;
    v_user_preferences JSONB;
BEGIN
    -- Get intent ID from path
    SELECT id INTO v_intent_id 
    FROM intent_taxonomy 
    WHERE path = p_intent_path;
    
    -- Get user preferences if provided
    IF p_user_id IS NOT NULL THEN
        SELECT preferences INTO v_user_preferences
        FROM users
        WHERE id = p_user_id;
    END IF;
    
    RETURN QUERY
    WITH technique_scores AS (
        SELECT 
            t.id,
            t.name,
            -- Base effectiveness from mapping
            COALESCE(ite.effectiveness_score, t.base_effectiveness) as base_score,
            
            -- Complexity adjustment
            CASE 
                WHEN p_complexity = t.complexity_level THEN 0.1
                WHEN ABS(p_complexity - t.complexity_level) = 1 THEN 0
                ELSE -0.1 * ABS(p_complexity - t.complexity_level)
            END as complexity_adj,
            
            -- User preference bonus
            CASE 
                WHEN v_user_preferences IS NOT NULL 
                AND t.id = ANY(
                    SELECT jsonb_array_elements_text(v_user_preferences->'favorite_techniques')::UUID
                ) THEN 0.15
                ELSE 0
            END as preference_bonus
            
        FROM techniques t
        LEFT JOIN intent_technique_effectiveness ite 
            ON ite.technique_id = t.id 
            AND ite.intent_id = v_intent_id
        WHERE t.is_active = true
    )
    SELECT 
        id as technique_id,
        name as technique_name,
        base_score as effectiveness_score,
        preference_bonus as personalization_score,
        LEAST(
            base_score + complexity_adj + preference_bonus,
            0.99
        ) as final_score
    FROM technique_scores
    ORDER BY final_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
```

### Analytics Aggregation

```sql
-- Procedure to update technique performance analytics
CREATE OR REPLACE PROCEDURE update_technique_analytics(
    p_date DATE DEFAULT CURRENT_DATE
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Insert or update analytics for the specified date
    INSERT INTO technique_performance_analytics (
        technique_id,
        date_bucket,
        total_uses,
        unique_users,
        avg_confidence,
        avg_rating,
        success_rate,
        complexity_distribution,
        intent_distribution
    )
    SELECT 
        t.id as technique_id,
        p_date as date_bucket,
        COUNT(*) as total_uses,
        COUNT(DISTINCT ph.user_id) as unique_users,
        AVG(ph.model_confidence) as avg_confidence,
        AVG(ph.user_rating::DECIMAL) as avg_rating,
        AVG(CASE WHEN ph.user_rating >= 4 THEN 1 ELSE 0 END) as success_rate,
        jsonb_object_agg(
            ph.detected_complexity::TEXT, 
            COUNT(*)
        ) FILTER (WHERE ph.detected_complexity IS NOT NULL) as complexity_distribution,
        jsonb_object_agg(
            SPLIT_PART(ph.detected_intent_path, '.', 1),
            COUNT(*)
        ) FILTER (WHERE ph.detected_intent_path IS NOT NULL) as intent_distribution
    FROM prompt_history ph
    CROSS JOIN LATERAL unnest(ph.techniques_applied) as t(id)
    WHERE DATE(ph.created_at) = p_date
    GROUP BY t.id
    ON CONFLICT (technique_id, date_bucket)
    DO UPDATE SET
        total_uses = EXCLUDED.total_uses,
        unique_users = EXCLUDED.unique_users,
        avg_confidence = EXCLUDED.avg_confidence,
        avg_rating = EXCLUDED.avg_rating,
        success_rate = EXCLUDED.success_rate,
        complexity_distribution = EXCLUDED.complexity_distribution,
        intent_distribution = EXCLUDED.intent_distribution;
    
    -- Update effectiveness trends
    UPDATE technique_performance_analytics tpa
    SET effectiveness_trend = (
        tpa.success_rate - 
        COALESCE(
            (SELECT success_rate 
             FROM technique_performance_analytics 
             WHERE technique_id = tpa.technique_id 
             AND date_bucket = tpa.date_bucket - INTERVAL '1 day'),
            tpa.success_rate
        )
    )
    WHERE date_bucket = p_date;
END;
$$;
```

## Indexes and Performance Optimization

### Additional Performance Indexes

```sql
-- Composite indexes for common queries
CREATE INDEX idx_prompt_history_user_created 
    ON prompt_history(user_id, created_at DESC) 
    INCLUDE (enhanced_prompt, techniques_applied);

CREATE INDEX idx_technique_effectiveness_lookup 
    ON intent_technique_effectiveness(intent_id, effectiveness_score DESC) 
    INCLUDE (technique_id);

-- Partial indexes for active records
CREATE INDEX idx_techniques_active_category 
    ON techniques(category, base_effectiveness DESC) 
    WHERE is_active = true;

CREATE INDEX idx_templates_public_quality 
    ON prompt_templates(quality_score DESC) 
    WHERE is_public = true;

-- Text search indexes
CREATE INDEX idx_community_search 
    ON community_prompts 
    USING GIN(to_tsvector('english', title || ' ' || description));

-- BRIN indexes for time-series data
CREATE INDEX idx_history_created_brin 
    ON prompt_history 
    USING BRIN(created_at);
```

### Materialized Views for Analytics

```sql
-- Daily active techniques view
CREATE MATERIALIZED VIEW mv_daily_active_techniques AS
SELECT 
    DATE(ph.created_at) as date,
    t.technique_id,
    tech.name as technique_name,
    tech.category,
    COUNT(DISTINCT ph.user_id) as unique_users,
    COUNT(*) as total_uses,
    AVG(ph.user_rating::DECIMAL) as avg_rating
FROM prompt_history ph
CROSS JOIN LATERAL unnest(ph.techniques_applied) as t(technique_id)
JOIN techniques tech ON tech.id = t.technique_id
WHERE ph.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(ph.created_at), t.technique_id, tech.name, tech.category;

CREATE UNIQUE INDEX idx_mv_daily_techniques 
    ON mv_daily_active_techniques(date, technique_id);

-- User technique affinity view
CREATE MATERIALIZED VIEW mv_user_technique_affinity AS
SELECT 
    ph.user_id,
    t.technique_id,
    COUNT(*) as usage_count,
    AVG(ph.user_rating::DECIMAL) as avg_rating,
    MAX(ph.created_at) as last_used
FROM prompt_history ph
CROSS JOIN LATERAL unnest(ph.techniques_applied) as t(technique_id)
WHERE ph.user_rating IS NOT NULL
GROUP BY ph.user_id, t.technique_id
HAVING COUNT(*) >= 3;

CREATE UNIQUE INDEX idx_mv_user_affinity 
    ON mv_user_technique_affinity(user_id, technique_id);
```

## Data Partitioning Strategy

### Time-based Partitioning

```sql
-- Automated partition management
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    start_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'prompt_history_' || TO_CHAR(start_date, 'YYYY_MM');
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF prompt_history 
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly partition creation
SELECT cron.schedule(
    'create-monthly-partition',
    '0 0 25 * *', -- Run on 25th of each month
    'SELECT create_monthly_partition()'
);
```

## Security and Access Control

### Row-Level Security

```sql
-- Enable RLS on sensitive tables
ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_learning_profiles ENABLE ROW LEVEL SECURITY;

-- User can only access their own data
CREATE POLICY user_own_prompts ON prompt_history
    FOR ALL TO application_user
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY user_own_profile ON user_learning_profiles
    FOR ALL TO application_user
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- Community content visibility
CREATE POLICY community_content_visibility ON community_prompts
    FOR SELECT TO application_user
    USING (
        is_public = true 
        OR author_id = current_setting('app.current_user_id')::UUID
        OR moderation_status = 'approved'
    );
```

## Database Maintenance

### Automated Maintenance Tasks

```sql
-- Vacuum and analyze schedule
SELECT cron.schedule(
    'vacuum-analyze-daily',
    '0 3 * * *', -- 3 AM daily
    $$
        VACUUM ANALYZE prompt_history;
        VACUUM ANALYZE technique_performance_analytics;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_active_techniques;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_technique_affinity;
    $$
);

-- Archive old data
CREATE OR REPLACE FUNCTION archive_old_prompts()
RETURNS void AS $$
BEGIN
    -- Move prompts older than 6 months to archive
    INSERT INTO prompt_history_archive
    SELECT * FROM prompt_history
    WHERE created_at < CURRENT_DATE - INTERVAL '6 months';
    
    DELETE FROM prompt_history
    WHERE created_at < CURRENT_DATE - INTERVAL '6 months';
END;
$$ LANGUAGE plpgsql;
```

## Monitoring and Health Checks

### Database Health Queries

```sql
-- Table size monitoring
CREATE VIEW v_table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY size_bytes DESC;

-- Query performance monitoring
CREATE VIEW v_slow_queries AS
SELECT 
    query,
    calls,
    mean_exec_time,
    total_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100 -- queries taking > 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Index usage statistics
CREATE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Backup and Recovery

### Backup Strategy

```yaml
backup_strategy:
  full_backup:
    frequency: daily
    retention: 30_days
    time: "02:00 UTC"
    
  incremental_backup:
    frequency: hourly
    retention: 7_days
    method: WAL_archiving
    
  point_in_time_recovery:
    enabled: true
    wal_retention: 7_days
    
  offsite_backup:
    provider: "AWS S3"
    region: "us-east-1"
    encryption: "AES-256"
    lifecycle: 
      - move_to_glacier_after: 90_days
      - delete_after: 365_days
```

## Conclusion

This database design provides a robust, scalable foundation for the Prompt Engineering Assistant with:

1. **Comprehensive schema** covering techniques, patterns, user data, and analytics
2. **Performance optimization** through strategic indexing and partitioning
3. **Machine learning support** with vector embeddings and training data management
4. **Analytics capabilities** via materialized views and time-series data
5. **Security features** including row-level security and audit trails
6. **Scalability** through partitioning and efficient query patterns

The design supports millions of users and prompts while maintaining sub-50ms query performance for critical operations.