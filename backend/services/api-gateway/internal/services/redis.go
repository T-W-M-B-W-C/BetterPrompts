package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// RedisService provides Redis operations for caching and session management
type RedisService struct {
	client       *redis.Client
	defaultTTL   time.Duration
	keyPrefix    string
}

// RedisConfig holds Redis configuration
type RedisConfig struct {
	Address      string
	Password     string
	DB           int
	PoolSize     int
	MinIdleConns int
	MaxRetries   int
	KeyPrefix    string
	DefaultTTL   time.Duration
}

// NewRedisService creates a new Redis service
func NewRedisService(config RedisConfig) (*RedisService, error) {
	client := redis.NewClient(&redis.Options{
		Addr:         config.Address,
		Password:     config.Password,
		DB:           config.DB,
		PoolSize:     config.PoolSize,
		MinIdleConns: config.MinIdleConns,
		MaxRetries:   config.MaxRetries,
		DialTimeout:  5 * time.Second,
		ReadTimeout:  3 * time.Second,
		WriteTimeout: 3 * time.Second,
		PoolTimeout:  4 * time.Second,
	})

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	return &RedisService{
		client:     client,
		defaultTTL: config.DefaultTTL,
		keyPrefix:  config.KeyPrefix,
	}, nil
}

// Close closes the Redis connection
func (r *RedisService) Close() error {
	return r.client.Close()
}

// buildKey constructs a key with the service prefix
func (r *RedisService) buildKey(namespace, key string) string {
	if r.keyPrefix != "" {
		return fmt.Sprintf("%s:%s:%s", r.keyPrefix, namespace, key)
	}
	return fmt.Sprintf("%s:%s", namespace, key)
}

// Session Management Methods

// SetSession stores a session
func (r *RedisService) SetSession(ctx context.Context, sessionID string, data interface{}, ttl time.Duration) error {
	key := r.buildKey("session", sessionID)
	
	jsonData, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("failed to marshal session data: %w", err)
	}

	if ttl == 0 {
		ttl = 24 * time.Hour // Default session TTL
	}

	return r.client.Set(ctx, key, jsonData, ttl).Err()
}

// GetSession retrieves a session
func (r *RedisService) GetSession(ctx context.Context, sessionID string, dest interface{}) error {
	key := r.buildKey("session", sessionID)
	
	data, err := r.client.Get(ctx, key).Result()
	if err == redis.Nil {
		return fmt.Errorf("session not found")
	} else if err != nil {
		return fmt.Errorf("failed to get session: %w", err)
	}

	if err := json.Unmarshal([]byte(data), dest); err != nil {
		return fmt.Errorf("failed to unmarshal session data: %w", err)
	}

	return nil
}

// DeleteSession removes a session
func (r *RedisService) DeleteSession(ctx context.Context, sessionID string) error {
	key := r.buildKey("session", sessionID)
	return r.client.Del(ctx, key).Err()
}

// RefreshSession extends session TTL
func (r *RedisService) RefreshSession(ctx context.Context, sessionID string, ttl time.Duration) error {
	key := r.buildKey("session", sessionID)
	
	if ttl == 0 {
		ttl = 24 * time.Hour
	}

	return r.client.Expire(ctx, key, ttl).Err()
}

// API Response Cache Methods

// CacheAPIResponse caches an API response
func (r *RedisService) CacheAPIResponse(ctx context.Context, endpoint string, params string, response interface{}) error {
	key := r.buildKey("api:response", fmt.Sprintf("%s:%s", endpoint, params))
	
	jsonData, err := json.Marshal(response)
	if err != nil {
		return fmt.Errorf("failed to marshal response: %w", err)
	}

	ttl := 5 * time.Minute // API response cache TTL
	return r.client.Set(ctx, key, jsonData, ttl).Err()
}

// GetCachedAPIResponse retrieves a cached API response
func (r *RedisService) GetCachedAPIResponse(ctx context.Context, endpoint string, params string, dest interface{}) error {
	key := r.buildKey("api:response", fmt.Sprintf("%s:%s", endpoint, params))
	
	data, err := r.client.Get(ctx, key).Result()
	if err == redis.Nil {
		return fmt.Errorf("cache miss")
	} else if err != nil {
		return err
	}

	return json.Unmarshal([]byte(data), dest)
}

// Rate Limiting Methods

// CheckRateLimit checks if a request is within rate limits
func (r *RedisService) CheckRateLimit(ctx context.Context, identifier string, limit int, window time.Duration) (bool, int, error) {
	key := r.buildKey("ratelimit", identifier)
	
	pipe := r.client.Pipeline()
	
	// Increment counter
	incr := pipe.Incr(ctx, key)
	
	// Set expiry on first request
	pipe.Expire(ctx, key, window)
	
	_, err := pipe.Exec(ctx)
	if err != nil {
		return false, 0, err
	}

	count := int(incr.Val())
	
	if count > limit {
		return false, count, nil
	}

	return true, count, nil
}

// GetRateLimitInfo gets current rate limit status
func (r *RedisService) GetRateLimitInfo(ctx context.Context, identifier string) (count int, ttl time.Duration, err error) {
	key := r.buildKey("ratelimit", identifier)
	
	// Get current count
	countVal, err := r.client.Get(ctx, key).Int()
	if err == redis.Nil {
		return 0, 0, nil
	} else if err != nil {
		return 0, 0, err
	}

	// Get TTL
	ttlVal, err := r.client.TTL(ctx, key).Result()
	if err != nil {
		return countVal, 0, err
	}

	return countVal, ttlVal, nil
}

// Generic Cache Methods

// Set stores a value with optional TTL
func (r *RedisService) Set(ctx context.Context, namespace, key string, value interface{}, ttl time.Duration) error {
	fullKey := r.buildKey(namespace, key)
	
	var data []byte
	var err error

	switch v := value.(type) {
	case string:
		data = []byte(v)
	case []byte:
		data = v
	default:
		data, err = json.Marshal(value)
		if err != nil {
			return fmt.Errorf("failed to marshal value: %w", err)
		}
	}

	if ttl == 0 {
		ttl = r.defaultTTL
	}

	return r.client.Set(ctx, fullKey, data, ttl).Err()
}

// Get retrieves a value
func (r *RedisService) Get(ctx context.Context, namespace, key string, dest interface{}) error {
	fullKey := r.buildKey(namespace, key)
	
	data, err := r.client.Get(ctx, fullKey).Result()
	if err == redis.Nil {
		return fmt.Errorf("key not found")
	} else if err != nil {
		return err
	}

	// Handle string destination
	if strDest, ok := dest.(*string); ok {
		*strDest = data
		return nil
	}

	// Handle []byte destination
	if byteDest, ok := dest.(*[]byte); ok {
		*byteDest = []byte(data)
		return nil
	}

	// Otherwise unmarshal as JSON
	return json.Unmarshal([]byte(data), dest)
}

// Delete removes a key
func (r *RedisService) Delete(ctx context.Context, namespace, key string) error {
	fullKey := r.buildKey(namespace, key)
	return r.client.Del(ctx, fullKey).Err()
}

// DeletePattern removes all keys matching a pattern
func (r *RedisService) DeletePattern(ctx context.Context, pattern string) error {
	var cursor uint64
	var keys []string

	// Scan for keys matching pattern
	for {
		var err error
		var scanKeys []string
		scanKeys, cursor, err = r.client.Scan(ctx, cursor, pattern, 100).Result()
		if err != nil {
			return fmt.Errorf("failed to scan keys: %w", err)
		}

		keys = append(keys, scanKeys...)

		if cursor == 0 {
			break
		}
	}

	// Delete keys in batches
	if len(keys) > 0 {
		pipe := r.client.Pipeline()
		for _, key := range keys {
			pipe.Del(ctx, key)
		}
		_, err := pipe.Exec(ctx)
		if err != nil {
			return fmt.Errorf("failed to delete keys: %w", err)
		}
	}

	return nil
}

// Exists checks if a key exists
func (r *RedisService) Exists(ctx context.Context, namespace, key string) (bool, error) {
	fullKey := r.buildKey(namespace, key)
	
	count, err := r.client.Exists(ctx, fullKey).Result()
	if err != nil {
		return false, err
	}

	return count > 0, nil
}

// SetNX sets a key only if it doesn't exist (useful for distributed locks)
func (r *RedisService) SetNX(ctx context.Context, namespace, key string, value interface{}, ttl time.Duration) (bool, error) {
	fullKey := r.buildKey(namespace, key)
	
	var data []byte
	var err error

	switch v := value.(type) {
	case string:
		data = []byte(v)
	case []byte:
		data = v
	default:
		data, err = json.Marshal(value)
		if err != nil {
			return false, fmt.Errorf("failed to marshal value: %w", err)
		}
	}

	if ttl == 0 {
		ttl = r.defaultTTL
	}

	return r.client.SetNX(ctx, fullKey, data, ttl).Result()
}

// Increment atomically increments a counter
func (r *RedisService) Increment(ctx context.Context, namespace, key string) (int64, error) {
	fullKey := r.buildKey(namespace, key)
	return r.client.Incr(ctx, fullKey).Result()
}

// IncrementBy atomically increments a counter by a specific value
func (r *RedisService) IncrementBy(ctx context.Context, namespace, key string, value int64) (int64, error) {
	fullKey := r.buildKey(namespace, key)
	return r.client.IncrBy(ctx, fullKey, value).Result()
}

// Health check
func (r *RedisService) Health(ctx context.Context) error {
	return r.client.Ping(ctx).Err()
}