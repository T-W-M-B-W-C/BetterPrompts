"""
Complete database service for Python microservices
"""
import json
import uuid
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager
import logging

import asyncpg
from asyncpg import Pool, Connection
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Async database service using asyncpg"""
    
    def __init__(self, dsn: Optional[str] = None):
        """Initialize database service"""
        self.dsn = dsn or self._build_dsn()
        self.pool: Optional[Pool] = None
    
    def _build_dsn(self) -> str:
        """Build DSN from settings"""
        return (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
    
    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=5,
                max_size=20,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
                # Enable pgvector extension types
                server_settings={
                    'search_path': 'public, auth, prompts, analytics'
                }
            )
            
            # Register custom types
            await self._register_custom_types()
            
            logger.info("Database connection pool created")
    
    async def _register_custom_types(self):
        """Register custom types like vector"""
        async with self.pool.acquire() as conn:
            # Register vector type if pgvector is installed
            try:
                await conn.set_type_codec(
                    'vector',
                    encoder=self._encode_vector,
                    decoder=self._decode_vector,
                    schema='public'
                )
            except Exception as e:
                logger.warning(f"Could not register vector type: {e}")
    
    @staticmethod
    def _encode_vector(value):
        """Encode numpy array to vector"""
        if isinstance(value, np.ndarray):
            return f"[{','.join(map(str, value.tolist()))}]"
        return value
    
    @staticmethod
    def _decode_vector(value):
        """Decode vector to numpy array"""
        if value and value.startswith('[') and value.endswith(']'):
            return np.array([float(x) for x in value[1:-1].split(',')])
        return value
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        async with self.pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def transaction(self):
        """Execute queries in a transaction"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # =====================================================
    # Intent Patterns
    # =====================================================
    
    async def save_intent_pattern(
        self,
        pattern: str,
        intent: str,
        sub_intent: Optional[str] = None,
        confidence: float = 1.0,
        source: str = "ml_predicted"
    ) -> str:
        """Save an intent pattern"""
        pattern_id = str(uuid.uuid4())
        normalized = pattern.lower().strip()
        
        query = """
            INSERT INTO prompts.intent_patterns (
                id, pattern, normalized_pattern, intent, sub_intent,
                confidence, source
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        
        async with self.acquire() as conn:
            result = await conn.fetchval(
                query,
                pattern_id, pattern, normalized, intent, sub_intent,
                confidence, source
            )
        
        return result
    
    async def get_intent_patterns(
        self,
        intent: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get intent patterns"""
        query = """
            SELECT id, pattern, intent, sub_intent, confidence, 
                   is_verified, source, created_at
            FROM prompts.intent_patterns
            WHERE confidence >= $1
        """
        params = [min_confidence]
        
        if intent:
            query += " AND intent = $2"
            params.append(intent)
        
        query += " ORDER BY confidence DESC, created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def search_similar_patterns(
        self,
        pattern: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar patterns using trigram similarity"""
        query = """
            SELECT id, pattern, intent, sub_intent, confidence,
                   similarity(normalized_pattern, $1) as sim_score
            FROM prompts.intent_patterns
            WHERE similarity(normalized_pattern, $1) > 0.3
            ORDER BY sim_score DESC
            LIMIT $2
        """
        
        normalized = pattern.lower().strip()
        
        async with self.acquire() as conn:
            # Enable pg_trgm extension if needed
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            rows = await conn.fetch(query, normalized, limit)
        
        return [dict(row) for row in rows]
    
    # =====================================================
    # Prompt History
    # =====================================================
    
    async def save_prompt_history(
        self,
        original_input: str,
        enhanced_output: str,
        intent: Optional[str] = None,
        intent_confidence: Optional[float] = None,
        complexity: Optional[str] = None,
        techniques_used: Optional[List[str]] = None,
        technique_scores: Optional[Dict[str, float]] = None,
        processing_time_ms: Optional[int] = None,
        token_count: Optional[int] = None,
        model_used: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save prompt enhancement history"""
        history_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO prompts.history (
                id, user_id, session_id, request_id, original_input,
                enhanced_output, intent, intent_confidence, complexity,
                techniques_used, technique_scores, processing_time_ms,
                token_count, model_used, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
            ) RETURNING id
        """
        
        async with self.acquire() as conn:
            result = await conn.fetchval(
                query,
                history_id, user_id, session_id, request_id, original_input,
                enhanced_output, intent, intent_confidence, complexity,
                techniques_used or [], json.dumps(technique_scores or {}),
                processing_time_ms, token_count, model_used,
                json.dumps(metadata or {})
            )
        
        return result
    
    async def get_prompt_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get prompt history"""
        query = """
            SELECT id, user_id, session_id, request_id, original_input,
                   enhanced_output, intent, intent_confidence, complexity,
                   techniques_used, technique_scores, processing_time_ms,
                   token_count, model_used, feedback_score, feedback_text,
                   is_favorite, metadata, created_at
            FROM prompts.history
        """
        params = []
        
        if user_id:
            query += " WHERE user_id = $1"
            params.append(user_id)
        
        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            result['technique_scores'] = json.loads(result['technique_scores'])
            result['metadata'] = json.loads(result['metadata'])
            results.append(result)
        
        return results
    
    async def update_prompt_feedback(
        self,
        history_id: str,
        feedback_score: int,
        feedback_text: Optional[str] = None
    ) -> bool:
        """Update feedback for a prompt"""
        query = """
            UPDATE prompts.history
            SET feedback_score = $2, feedback_text = $3
            WHERE id = $1
        """
        
        async with self.acquire() as conn:
            result = await conn.execute(query, history_id, feedback_score, feedback_text)
        
        return result != "UPDATE 0"
    
    # =====================================================
    # Embeddings
    # =====================================================
    
    async def save_embedding(
        self,
        source_type: str,
        source_id: str,
        embedding: np.ndarray,
        model_version: str
    ) -> str:
        """Save vector embedding"""
        embedding_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO prompts.embeddings (
                id, source_type, source_id, embedding, model_version
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (source_type, source_id) 
            DO UPDATE SET embedding = $4, model_version = $5
            RETURNING id
        """
        
        async with self.acquire() as conn:
            # Convert numpy array to list for storage
            embedding_list = embedding.tolist()
            result = await conn.fetchval(
                query,
                embedding_id, source_type, source_id,
                embedding_list, model_version
            )
        
        return result
    
    async def search_similar_embeddings(
        self,
        query_embedding: np.ndarray,
        source_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings using cosine similarity"""
        query = """
            SELECT e.id, e.source_type, e.source_id, e.model_version,
                   1 - (e.embedding <=> $1::vector) as similarity
            FROM prompts.embeddings e
        """
        params = [query_embedding.tolist()]
        where_clauses = []
        
        if source_type:
            where_clauses.append(f"e.source_type = ${len(params) + 1}")
            params.append(source_type)
        
        where_clauses.append(f"1 - (e.embedding <=> $1::vector) > ${len(params) + 1}")
        params.append(similarity_threshold)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += f" ORDER BY similarity DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    # =====================================================
    # Technique Effectiveness
    # =====================================================
    
    async def update_technique_effectiveness(
        self,
        technique: str,
        intent: str,
        feedback_score: float,
        processing_time_ms: Optional[int] = None
    ):
        """Update technique effectiveness metrics"""
        success = 1 if feedback_score >= 4 else 0
        
        query = """
            INSERT INTO analytics.technique_effectiveness (
                id, technique, intent, success_count, total_count,
                average_feedback, average_processing_time_ms, date
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, CURRENT_DATE
            )
            ON CONFLICT (technique, intent, date) DO UPDATE
            SET 
                success_count = technique_effectiveness.success_count + $4,
                total_count = technique_effectiveness.total_count + 1,
                average_feedback = (
                    (technique_effectiveness.average_feedback * technique_effectiveness.total_count) + $6
                ) / (technique_effectiveness.total_count + 1),
                average_processing_time_ms = CASE 
                    WHEN $7 IS NOT NULL THEN (
                        (COALESCE(technique_effectiveness.average_processing_time_ms, 0) * technique_effectiveness.total_count) + $7
                    ) / (technique_effectiveness.total_count + 1)
                    ELSE technique_effectiveness.average_processing_time_ms
                END
        """
        
        async with self.acquire() as conn:
            await conn.execute(
                query,
                str(uuid.uuid4()), technique, intent, success,
                1, feedback_score, processing_time_ms
            )
    
    async def get_technique_effectiveness(
        self,
        days: int = 30,
        min_samples: int = 10
    ) -> List[Dict[str, Any]]:
        """Get technique effectiveness metrics"""
        query = """
            SELECT technique, intent, 
                   SUM(success_count) as success_count,
                   SUM(total_count) as total_count,
                   AVG(average_feedback) as average_feedback,
                   AVG(average_processing_time_ms) as average_processing_time_ms,
                   CASE 
                       WHEN SUM(total_count) > 0 
                       THEN CAST(SUM(success_count) AS FLOAT) / SUM(total_count)
                       ELSE 0
                   END as success_rate
            FROM analytics.technique_effectiveness
            WHERE date >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY technique, intent
            HAVING SUM(total_count) >= %s
            ORDER BY success_rate DESC, technique, intent
        """
        
        async with self.acquire() as conn:
            rows = await conn.fetch(query % (days, min_samples))
        
        return [dict(row) for row in rows]
    
    # =====================================================
    # Analytics
    # =====================================================
    
    async def record_user_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_data: Dict[str, Any],
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Record user activity"""
        activity_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO analytics.user_activity (
                id, user_id, activity_type, activity_data,
                session_id, ip_address, user_agent
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        async with self.acquire() as conn:
            await conn.execute(
                query,
                activity_id, user_id, activity_type,
                json.dumps(activity_data), session_id,
                ip_address, user_agent
            )
    
    async def update_daily_stats(self):
        """Update daily statistics (typically run as a scheduled job)"""
        query = """
            INSERT INTO analytics.daily_stats (
                id, date, total_requests, unique_users, new_users,
                total_enhancements, average_response_time_ms, error_count,
                by_technique, by_intent, by_hour
            )
            SELECT 
                $1,
                CURRENT_DATE,
                COUNT(*) as total_requests,
                COUNT(DISTINCT h.user_id) as unique_users,
                COUNT(DISTINCT CASE 
                    WHEN u.created_at::date = CURRENT_DATE THEN u.id 
                END) as new_users,
                COUNT(*) as total_enhancements,
                AVG(h.processing_time_ms) as average_response_time_ms,
                0 as error_count,
                json_object_agg(
                    DISTINCT unnest(h.techniques_used), 
                    COUNT(*) FILTER (WHERE unnest(h.techniques_used) IS NOT NULL)
                ) as by_technique,
                json_object_agg(
                    DISTINCT h.intent,
                    COUNT(*) FILTER (WHERE h.intent IS NOT NULL)
                ) as by_intent,
                json_object_agg(
                    EXTRACT(HOUR FROM h.created_at)::text,
                    COUNT(*)
                ) as by_hour
            FROM prompts.history h
            LEFT JOIN auth.users u ON h.user_id = u.id
            WHERE h.created_at::date = CURRENT_DATE
            GROUP BY CURRENT_DATE
            ON CONFLICT (date) DO UPDATE
            SET 
                total_requests = EXCLUDED.total_requests,
                unique_users = EXCLUDED.unique_users,
                new_users = EXCLUDED.new_users,
                total_enhancements = EXCLUDED.total_enhancements,
                average_response_time_ms = EXCLUDED.average_response_time_ms,
                by_technique = EXCLUDED.by_technique,
                by_intent = EXCLUDED.by_intent,
                by_hour = EXCLUDED.by_hour
        """
        
        async with self.acquire() as conn:
            await conn.execute(query, str(uuid.uuid4()))
    
    async def get_daily_stats(
        self,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily statistics"""
        query = """
            SELECT date, total_requests, unique_users, new_users,
                   total_enhancements, average_response_time_ms,
                   error_count, by_technique, by_intent, by_hour
            FROM analytics.daily_stats
            WHERE date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY date DESC
        """
        
        async with self.acquire() as conn:
            rows = await conn.fetch(query % days)
        
        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            result['by_technique'] = json.loads(result['by_technique']) if result['by_technique'] else {}
            result['by_intent'] = json.loads(result['by_intent']) if result['by_intent'] else {}
            result['by_hour'] = json.loads(result['by_hour']) if result['by_hour'] else {}
            results.append(result)
        
        return results
    
    # =====================================================
    # Templates
    # =====================================================
    
    async def get_prompt_templates(
        self,
        technique: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get prompt templates"""
        query = """
            SELECT id, name, slug, description, technique, category,
                   template_text, variables, examples, metadata,
                   effectiveness_score, usage_count, is_active, is_public
            FROM prompts.templates
            WHERE is_active = $1
        """
        params = [is_active]
        
        if technique:
            query += f" AND technique = ${len(params) + 1}"
            params.append(technique)
        
        if category:
            query += f" AND category = ${len(params) + 1}"
            params.append(category)
        
        query += f" ORDER BY effectiveness_score DESC, usage_count DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            result['variables'] = json.loads(result['variables'])
            result['examples'] = json.loads(result['examples'])
            result['metadata'] = json.loads(result['metadata'])
            results.append(result)
        
        return results
    
    async def increment_template_usage(self, template_id: str):
        """Increment template usage count"""
        query = """
            UPDATE prompts.templates
            SET usage_count = usage_count + 1
            WHERE id = $1
        """
        
        async with self.acquire() as conn:
            await conn.execute(query, template_id)


# Global database instance
_db_instance: Optional[DatabaseService] = None


async def get_database() -> DatabaseService:
    """Get database service instance"""
    global _db_instance
    
    if not _db_instance:
        _db_instance = DatabaseService()
        await _db_instance.connect()
    
    return _db_instance


async def close_database():
    """Close database connection"""
    global _db_instance
    
    if _db_instance:
        await _db_instance.close()
        _db_instance = None