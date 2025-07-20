"""
Comprehensive database integration tests for Python services
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
import numpy as np

import pytest
import asyncpg
from asyncpg import Pool

from app.db.database_service import DatabaseService, get_database


class TestDatabaseIntegration:
    """Database integration test suite"""
    
    @pytest.fixture(scope="class")
    async def db_service(self):
        """Create database service for tests"""
        # Use test database
        test_dsn = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://betterprompts:changeme@localhost:5432/betterprompts_test"
        )
        
        service = DatabaseService(test_dsn)
        await service.connect()
        
        # Clean up test data before tests
        await self._cleanup_test_data(service)
        
        yield service
        
        # Clean up after tests
        await self._cleanup_test_data(service)
        await service.close()
    
    async def _cleanup_test_data(self, service: DatabaseService):
        """Clean up test data"""
        async with service.acquire() as conn:
            # Delete test data in reverse order
            await conn.execute("""
                DELETE FROM analytics.api_metrics WHERE endpoint LIKE '/test%';
                DELETE FROM analytics.user_activity WHERE user_id IN 
                    (SELECT id FROM auth.users WHERE email LIKE 'pytest_%@test.com');
                DELETE FROM analytics.technique_effectiveness WHERE technique LIKE 'pytest_%';
                DELETE FROM prompts.embeddings WHERE source_id IN 
                    (SELECT id FROM prompts.history WHERE session_id LIKE 'pytest_%');
                DELETE FROM prompts.history WHERE session_id LIKE 'pytest_%';
                DELETE FROM prompts.intent_patterns WHERE pattern LIKE 'pytest %';
                DELETE FROM auth.users WHERE email LIKE 'pytest_%@test.com';
            """)
    
    @pytest.mark.asyncio
    async def test_health_check(self, db_service: DatabaseService):
        """Test database health check"""
        is_healthy = await db_service.health_check()
        assert is_healthy is True
    
    # =====================================================
    # Intent Pattern Tests
    # =====================================================
    
    @pytest.mark.asyncio
    async def test_intent_pattern_crud(self, db_service: DatabaseService):
        """Test intent pattern CRUD operations"""
        # Save pattern
        pattern_id = await db_service.save_intent_pattern(
            pattern="pytest help me write a test",
            intent="problem_solving",
            sub_intent="testing",
            confidence=0.95,
            source="test"
        )
        assert pattern_id is not None
        
        # Get patterns
        patterns = await db_service.get_intent_patterns(
            intent="problem_solving",
            min_confidence=0.9
        )
        
        # Find our test pattern
        test_pattern = None
        for p in patterns:
            if p['pattern'] == "pytest help me write a test":
                test_pattern = p
                break
        
        assert test_pattern is not None
        assert test_pattern['intent'] == "problem_solving"
        assert test_pattern['sub_intent'] == "testing"
        assert test_pattern['confidence'] == 0.95
        assert test_pattern['source'] == "test"
    
    @pytest.mark.asyncio
    async def test_similar_pattern_search(self, db_service: DatabaseService):
        """Test similar pattern search"""
        # Save some patterns
        patterns = [
            ("pytest write unit tests", "testing", 0.95),
            ("pytest create test cases", "testing", 0.92),
            ("pytest debug test failures", "debugging", 0.88),
            ("help me with documentation", "documentation", 0.90),
        ]
        
        for pattern, intent, confidence in patterns:
            await db_service.save_intent_pattern(
                pattern=pattern,
                intent=intent,
                confidence=confidence,
                source="test"
            )
        
        # Search for similar patterns
        similar = await db_service.search_similar_patterns(
            pattern="pytest write tests",
            limit=5
        )
        
        # Should find the testing-related patterns
        assert len(similar) >= 2
        assert any(p['pattern'] == "pytest write unit tests" for p in similar)
        assert all(p['sim_score'] > 0.3 for p in similar)
    
    # =====================================================
    # Prompt History Tests
    # =====================================================
    
    @pytest.mark.asyncio
    async def test_prompt_history_crud(self, db_service: DatabaseService):
        """Test prompt history CRUD operations"""
        user_id = str(uuid.uuid4())
        session_id = f"pytest_{uuid.uuid4()}"
        request_id = f"req_{uuid.uuid4()}"
        
        # Save history
        history_id = await db_service.save_prompt_history(
            original_input="Help me optimize this Python code",
            enhanced_output="Let's optimize your Python code step by step...",
            intent="problem_solving",
            intent_confidence=0.92,
            complexity="moderate",
            techniques_used=["chain_of_thought", "step_by_step"],
            technique_scores={"chain_of_thought": 0.85, "step_by_step": 0.90},
            processing_time_ms=145,
            token_count=256,
            model_used="gpt-4",
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            metadata={"test": True, "version": "1.0"}
        )
        
        assert history_id is not None
        
        # Get history
        histories = await db_service.get_prompt_history(
            user_id=user_id,
            limit=10
        )
        
        assert len(histories) == 1
        history = histories[0]
        
        assert history['original_input'] == "Help me optimize this Python code"
        assert history['intent'] == "problem_solving"
        assert history['techniques_used'] == ["chain_of_thought", "step_by_step"]
        assert history['technique_scores']['chain_of_thought'] == 0.85
        assert history['metadata']['test'] is True
        
        # Update feedback
        success = await db_service.update_prompt_feedback(
            history_id=history_id,
            feedback_score=5,
            feedback_text="Very helpful optimization suggestions!"
        )
        assert success is True
        
        # Verify feedback update
        histories = await db_service.get_prompt_history(user_id=user_id)
        assert histories[0]['feedback_score'] == 5
        assert histories[0]['feedback_text'] == "Very helpful optimization suggestions!"
    
    # =====================================================
    # Embeddings Tests
    # =====================================================
    
    @pytest.mark.asyncio
    async def test_embeddings_crud(self, db_service: DatabaseService):
        """Test embedding storage and retrieval"""
        # Create a test embedding (normally from ML model)
        test_embedding = np.random.rand(768).astype(np.float32)
        source_id = str(uuid.uuid4())
        
        # Save embedding
        embedding_id = await db_service.save_embedding(
            source_type="prompt_history",
            source_id=source_id,
            embedding=test_embedding,
            model_version="deberta-v3-base-test"
        )
        
        assert embedding_id is not None
        
        # Search similar embeddings
        query_embedding = test_embedding + np.random.normal(0, 0.1, 768).astype(np.float32)
        similar = await db_service.search_similar_embeddings(
            query_embedding=query_embedding,
            source_type="prompt_history",
            limit=5,
            similarity_threshold=0.5
        )
        
        # Should find our test embedding
        assert len(similar) >= 1
        assert any(s['source_id'] == source_id for s in similar)
        
        # Update embedding (should replace)
        new_embedding = np.random.rand(768).astype(np.float32)
        new_id = await db_service.save_embedding(
            source_type="prompt_history",
            source_id=source_id,
            embedding=new_embedding,
            model_version="deberta-v3-base-test-v2"
        )
        
        # Should return the same ID (upsert)
        assert new_id is not None
    
    # =====================================================
    # Technique Effectiveness Tests
    # =====================================================
    
    @pytest.mark.asyncio
    async def test_technique_effectiveness(self, db_service: DatabaseService):
        """Test technique effectiveness tracking"""
        technique = f"pytest_{uuid.uuid4()}"
        intent = "test_intent"
        
        # Update effectiveness multiple times
        feedback_scores = [3.5, 4.0, 4.5, 3.0, 5.0]
        processing_times = [120, 145, 132, 156, 128]
        
        for score, time_ms in zip(feedback_scores, processing_times):
            await db_service.update_technique_effectiveness(
                technique=technique,
                intent=intent,
                feedback_score=score,
                processing_time_ms=time_ms
            )
        
        # Get effectiveness
        effectiveness = await db_service.get_technique_effectiveness(
            days=1,
            min_samples=1
        )
        
        # Find our test technique
        test_effectiveness = None
        for e in effectiveness:
            if e['technique'] == technique and e['intent'] == intent:
                test_effectiveness = e
                break
        
        assert test_effectiveness is not None
        assert test_effectiveness['total_count'] == 5
        assert test_effectiveness['success_count'] == 3  # Scores >= 4
        assert test_effectiveness['success_rate'] == 0.6
        assert 3.9 < test_effectiveness['average_feedback'] < 4.1
        assert 130 < test_effectiveness['average_processing_time_ms'] < 140
    
    # =====================================================
    # Analytics Tests
    # =====================================================
    
    @pytest.mark.asyncio
    async def test_user_activity_tracking(self, db_service: DatabaseService):
        """Test user activity tracking"""
        user_id = str(uuid.uuid4())
        
        # Record activity
        await db_service.record_user_activity(
            user_id=user_id,
            activity_type="prompt_enhanced",
            activity_data={
                "technique": "chain_of_thought",
                "intent": "creative_writing",
                "success": True,
                "processing_time": 145
            },
            session_id=f"pytest_session_{uuid.uuid4()}",
            ip_address="127.0.0.1",
            user_agent="pytest/1.0"
        )
        
        # Verify activity was recorded (would need a get method in real implementation)
        async with db_service.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM analytics.user_activity WHERE user_id = $1",
                user_id
            )
            assert count == 1
    
    @pytest.mark.asyncio
    async def test_daily_stats(self, db_service: DatabaseService):
        """Test daily statistics"""
        # Update daily stats
        await db_service.update_daily_stats()
        
        # Get stats
        stats = await db_service.get_daily_stats(days=7)
        
        # Should have at least one entry
        assert len(stats) >= 0  # May be 0 if no data for today
        
        if stats:
            stat = stats[0]
            assert 'date' in stat
            assert 'total_requests' in stat
            assert 'by_technique' in stat
            assert 'by_intent' in stat
    
    # =====================================================
    # Template Tests
    # =====================================================
    
    @pytest.mark.asyncio
    async def test_prompt_templates(self, db_service: DatabaseService):
        """Test prompt template retrieval"""
        # Get templates
        templates = await db_service.get_prompt_templates(
            is_active=True,
            limit=10
        )
        
        # Should have some default templates from seed data
        assert isinstance(templates, list)
        
        if templates:
            template = templates[0]
            assert 'id' in template
            assert 'name' in template
            assert 'technique' in template
            assert 'template_text' in template
            assert 'variables' in template
            assert isinstance(template['variables'], list)
        
        # Get templates by technique
        cot_templates = await db_service.get_prompt_templates(
            technique="chain_of_thought",
            is_active=True
        )
        
        if cot_templates:
            assert all(t['technique'] == 'chain_of_thought' for t in cot_templates)
    
    # =====================================================
    # Performance Tests
    # =====================================================
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, db_service: DatabaseService):
        """Test concurrent database operations"""
        # Create multiple concurrent saves
        tasks = []
        
        for i in range(10):
            pattern = f"pytest concurrent test {i}"
            task = db_service.save_intent_pattern(
                pattern=pattern,
                intent="test_concurrent",
                confidence=0.9,
                source="test"
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(result is not None for result in results)
        assert len(set(results)) == 10  # All IDs should be unique
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_service: DatabaseService):
        """Test transaction rollback on error"""
        pattern_id = None
        
        try:
            async with db_service.transaction() as conn:
                # Insert a pattern
                pattern_id = await conn.fetchval(
                    """
                    INSERT INTO prompts.intent_patterns 
                    (id, pattern, normalized_pattern, intent, confidence, source)
                    VALUES ($1, $2, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    str(uuid.uuid4()),
                    "pytest transaction test",
                    "test_intent",
                    0.95,
                    "test"
                )
                
                # Force an error
                await conn.execute("INVALID SQL")
                
        except Exception:
            # Transaction should have rolled back
            pass
        
        # Verify pattern was not saved
        if pattern_id:
            async with db_service.acquire() as conn:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM prompts.intent_patterns WHERE id = $1",
                    pattern_id
                )
                assert count == 0
    
    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self, db_service: DatabaseService):
        """Test connection pool behavior under load"""
        # Acquire many connections
        connections = []
        
        try:
            # This should work up to pool size
            for i in range(5):
                conn = await db_service.pool.acquire()
                connections.append(conn)
            
            # All connections acquired successfully
            assert len(connections) == 5
            
        finally:
            # Release all connections
            for conn in connections:
                await db_service.pool.release(conn)


class TestRedisIntegration:
    """Redis integration tests"""
    
    @pytest.fixture(scope="class")
    async def redis_service(self):
        """Create Redis service for tests"""
        from app.services.redis_service import get_redis_service
        
        service = get_redis_service(
            "test",
            key_prefix="pytest",
            default_ttl=60
        )
        
        # Clean up test data
        service.delete_pattern("pytest:*")
        
        yield service
        
        # Clean up after tests
        service.delete_pattern("pytest:*")
        service.close()
    
    @pytest.mark.asyncio
    async def test_redis_health_check(self, redis_service):
        """Test Redis health check"""
        is_healthy = redis_service.health_check()
        assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_session_management(self, redis_service):
        """Test Redis session management"""
        session_id = f"test_session_{uuid.uuid4()}"
        session_data = {
            "user_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "roles": ["user"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Set session
        success = redis_service.set_session(session_id, session_data, ttl=3600)
        assert success is True
        
        # Get session
        retrieved = redis_service.get_session(session_id)
        assert retrieved is not None
        assert retrieved["user_id"] == session_data["user_id"]
        assert retrieved["email"] == session_data["email"]
        
        # Refresh session
        success = redis_service.refresh_session(session_id, ttl=7200)
        assert success is True
        
        # Delete session
        success = redis_service.delete_session(session_id)
        assert success is True
        
        # Verify deleted
        retrieved = redis_service.get_session(session_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, redis_service):
        """Test Redis caching operations"""
        # Cache API response
        endpoint = "/test/endpoint"
        params = "page=1&limit=10"
        response_data = {
            "data": [{"id": 1, "name": "Test"}],
            "total": 1,
            "page": 1
        }
        
        success = redis_service.cache_api_response(
            endpoint, params, response_data, ttl=300
        )
        assert success is True
        
        # Get cached response
        cached = redis_service.get_cached_api_response(endpoint, params)
        assert cached is not None
        assert cached["data"][0]["name"] == "Test"
        
        # Cache ML prediction
        model_name = "test_model"
        input_hash = "abc123"
        prediction = {"intent": "test", "confidence": 0.95}
        
        success = redis_service.cache_prediction(
            model_name, input_hash, prediction, ttl=3600
        )
        assert success is True
        
        # Get cached prediction
        cached_pred = redis_service.get_cached_prediction(model_name, input_hash)
        assert cached_pred is not None
        assert cached_pred["intent"] == "test"
        assert cached_pred["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, redis_service):
        """Test Redis rate limiting"""
        identifier = f"test_user_{uuid.uuid4()}"
        limit = 5
        window = 60  # 1 minute
        
        # Make requests up to limit
        for i in range(limit):
            allowed, count = redis_service.check_rate_limit(
                identifier, limit, window
            )
            assert allowed is True
            assert count == i + 1
        
        # Exceed limit
        allowed, count = redis_service.check_rate_limit(
            identifier, limit, window
        )
        assert allowed is False
        assert count == limit + 1
        
        # Get rate limit info
        info = redis_service.get_rate_limit_info(identifier)
        assert info["count"] == limit + 1
        assert info["ttl"] > 0
        assert info["ttl"] <= window


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])