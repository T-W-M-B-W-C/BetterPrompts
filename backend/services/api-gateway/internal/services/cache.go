package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/sirupsen/logrus"
)

// CacheService wraps Redis client with application-specific methods
type CacheService struct {
	client *redis.Client
	logger *logrus.Logger
	prefix string
}

// NewCacheService creates a new cache service
func NewCacheService(client *redis.Client, logger *logrus.Logger) *CacheService {
	return &CacheService{
		client: client,
		logger: logger,
		prefix: "betterprompts:",
	}
}

// Key generates a cache key with the service prefix
func (c *CacheService) Key(parts ...string) string {
	key := c.prefix
	for _, part := range parts {
		key += part + ":"
	}
	return key[:len(key)-1] // Remove trailing colon
}

// CacheEnhancedPrompt caches an enhanced prompt result
func (c *CacheService) CacheEnhancedPrompt(ctx context.Context, textHash string, techniques []string, result interface{}, ttl time.Duration) error {
	key := c.Key("enhanced", textHash, fmt.Sprintf("%v", techniques))
	
	data, err := json.Marshal(result)
	if err != nil {
		return fmt.Errorf("failed to marshal result: %w", err)
	}

	err = c.client.Set(ctx, key, data, ttl).Err()
	if err != nil {
		c.logger.WithError(err).Warn("Failed to cache enhanced prompt")
		return err
	}

	c.logger.WithFields(logrus.Fields{
		"key": key,
		"ttl": ttl,
	}).Debug("Cached enhanced prompt")

	return nil
}

// GetCachedEnhancedPrompt retrieves a cached enhanced prompt
func (c *CacheService) GetCachedEnhancedPrompt(ctx context.Context, textHash string, techniques []string, result interface{}) error {
	key := c.Key("enhanced", textHash, fmt.Sprintf("%v", techniques))

	data, err := c.client.Get(ctx, key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return fmt.Errorf("cache miss")
		}
		return fmt.Errorf("failed to get cached value: %w", err)
	}

	err = json.Unmarshal(data, result)
	if err != nil {
		return fmt.Errorf("failed to unmarshal cached value: %w", err)
	}

	c.logger.WithField("key", key).Debug("Cache hit for enhanced prompt")
	return nil
}

// CacheIntentClassification caches an intent classification result
func (c *CacheService) CacheIntentClassification(ctx context.Context, textHash string, result *IntentClassificationResult, ttl time.Duration) error {
	key := c.Key("intent", textHash)
	
	data, err := json.Marshal(result)
	if err != nil {
		return fmt.Errorf("failed to marshal result: %w", err)
	}

	err = c.client.Set(ctx, key, data, ttl).Err()
	if err != nil {
		c.logger.WithError(err).Warn("Failed to cache intent classification")
		return err
	}

	return nil
}

// GetCachedIntentClassification retrieves a cached intent classification
func (c *CacheService) GetCachedIntentClassification(ctx context.Context, textHash string) (*IntentClassificationResult, error) {
	key := c.Key("intent", textHash)

	data, err := c.client.Get(ctx, key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return nil, fmt.Errorf("cache miss")
		}
		return nil, fmt.Errorf("failed to get cached value: %w", err)
	}

	var result IntentClassificationResult
	err = json.Unmarshal(data, &result)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal cached value: %w", err)
	}

	c.logger.WithField("key", key).Debug("Cache hit for intent classification")
	return &result, nil
}

// StoreSession stores session data
func (c *CacheService) StoreSession(ctx context.Context, sessionID string, data interface{}, ttl time.Duration) error {
	key := c.Key("session", sessionID)
	
	jsonData, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("failed to marshal session data: %w", err)
	}

	err = c.client.Set(ctx, key, jsonData, ttl).Err()
	if err != nil {
		return fmt.Errorf("failed to store session: %w", err)
	}

	return nil
}

// GetSession retrieves session data
func (c *CacheService) GetSession(ctx context.Context, sessionID string, data interface{}) error {
	key := c.Key("session", sessionID)

	jsonData, err := c.client.Get(ctx, key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return fmt.Errorf("session not found")
		}
		return fmt.Errorf("failed to get session: %w", err)
	}

	err = json.Unmarshal(jsonData, data)
	if err != nil {
		return fmt.Errorf("failed to unmarshal session data: %w", err)
	}

	return nil
}

// ExtendSession extends the TTL of a session
func (c *CacheService) ExtendSession(ctx context.Context, sessionID string, ttl time.Duration) error {
	key := c.Key("session", sessionID)
	
	ok, err := c.client.Expire(ctx, key, ttl).Result()
	if err != nil {
		return fmt.Errorf("failed to extend session: %w", err)
	}
	
	if !ok {
		return fmt.Errorf("session not found")
	}
	
	return nil
}

// DeleteSession removes a session
func (c *CacheService) DeleteSession(ctx context.Context, sessionID string) error {
	key := c.Key("session", sessionID)
	
	err := c.client.Del(ctx, key).Err()
	if err != nil {
		return fmt.Errorf("failed to delete session: %w", err)
	}
	
	return nil
}

// RateLimitCheck checks if a user has exceeded the rate limit
func (c *CacheService) RateLimitCheck(ctx context.Context, userID string, limit int, window time.Duration) (bool, int, error) {
	key := c.Key("ratelimit", userID, fmt.Sprintf("%d", time.Now().Unix()/int64(window.Seconds())))
	
	// Increment counter
	count, err := c.client.Incr(ctx, key).Result()
	if err != nil {
		return false, 0, fmt.Errorf("failed to increment rate limit counter: %w", err)
	}
	
	// Set expiry on first increment
	if count == 1 {
		c.client.Expire(ctx, key, window)
	}
	
	// Check if limit exceeded
	if int(count) > limit {
		return false, limit - int(count) + 1, nil
	}
	
	return true, limit - int(count), nil
}

// InvalidateUserCache invalidates all cache entries for a user
func (c *CacheService) InvalidateUserCache(ctx context.Context, userID string) error {
	pattern := c.Key("*", userID, "*")
	
	// Use SCAN to find all keys matching the pattern
	iter := c.client.Scan(ctx, 0, pattern, 0).Iterator()
	var keys []string
	
	for iter.Next(ctx) {
		keys = append(keys, iter.Val())
	}
	
	if err := iter.Err(); err != nil {
		return fmt.Errorf("failed to scan keys: %w", err)
	}
	
	// Delete all found keys
	if len(keys) > 0 {
		err := c.client.Del(ctx, keys...).Err()
		if err != nil {
			return fmt.Errorf("failed to delete keys: %w", err)
		}
		
		c.logger.WithFields(logrus.Fields{
			"user_id": userID,
			"keys_deleted": len(keys),
		}).Info("Invalidated user cache")
	}
	
	return nil
}

// HealthCheck checks if the cache is healthy
func (c *CacheService) HealthCheck(ctx context.Context) error {
	return c.client.Ping(ctx).Err()
}