# Prompt History API Documentation

## Overview

This document describes the Phase 4 Prompt History API endpoints implemented for the BetterPrompts project. These endpoints provide user-specific prompt history with search, filtering, and rerun capabilities.

## Endpoints

### 1. GET /api/v1/prompts/history

Retrieves the authenticated user's prompt history with pagination and filtering support.

**Authentication**: Required (JWT token)

**Query Parameters**:
- `page` (int, default: 1) - Page number for pagination
- `limit` (int, default: 20, max: 100) - Number of items per page
- `search` (string) - Search term to filter prompts by content
- `technique` (string) - Filter by specific technique used
- `date_from` (RFC3339) - Filter prompts created after this date
- `date_to` (RFC3339) - Filter prompts created before this date
- `sort_by` (string, default: "created_at") - Field to sort by
- `sort_direction` (string, default: "desc") - Sort direction ("asc" or "desc")

**Response**:
```json
{
  "data": [
    {
      "id": "string",
      "original_input": "string",
      "enhanced_output": "string",
      "intent": "string",
      "complexity": "string",
      "techniques_used": ["string"],
      "created_at": "2025-01-23T10:00:00Z",
      "feedback_score": 5,
      "feedback_text": "string"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_pages": 5,
    "total_records": 100,
    "has_previous": false,
    "has_next": true
  }
}
```

**Performance**: <2s for 1000 items

### 2. GET /api/v1/prompts/{id}

Retrieves a specific prompt by ID.

**Authentication**: Required (JWT token)
**Authorization**: User must be the owner of the prompt

**Path Parameters**:
- `id` (string) - The prompt ID

**Response**:
```json
{
  "id": "string",
  "user_id": "string",
  "original_input": "string",
  "enhanced_output": "string",
  "intent": "string",
  "complexity": "string",
  "techniques_used": ["string"],
  "metadata": {
    "model_version": "string",
    "processing_time_ms": 123
  },
  "created_at": "2025-01-23T10:00:00Z",
  "updated_at": "2025-01-23T10:00:00Z"
}
```

**Error Responses**:
- 404: Prompt not found or user doesn't own it
- 403: Access denied

### 3. POST /api/v1/prompts/{id}/rerun

Reruns a prompt enhancement using the same technique.

**Authentication**: Required (JWT token)
**Authorization**: User must be the owner of the prompt

**Path Parameters**:
- `id` (string) - The prompt ID to rerun

**Response**:
```json
{
  "id": "new-prompt-id",
  "original_text": "string",
  "enhanced_text": "string",
  "enhanced_prompt": "string",
  "intent": "string",
  "complexity": "string",
  "techniques": ["string"],
  "techniques_used": ["string"],
  "confidence": 0.95,
  "enhanced": true,
  "metadata": {
    "tokens_used": 123,
    "model_version": "string",
    "rerun_from": "original-prompt-id"
  }
}
```

**Behavior**:
- Creates a new history entry
- Preserves the original prompt
- Uses the same techniques as the original enhancement

## Database Schema

### Prompts Table

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_prompt TEXT NOT NULL,
    enhanced_prompt TEXT NOT NULL,
    task_type VARCHAR(50),
    intent VARCHAR(50),
    complexity VARCHAR(20),
    techniques JSONB,
    metadata JSONB,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

- Full-text search indexes on `original_prompt` and `enhanced_prompt`
- Trigram indexes for fuzzy searching
- Composite indexes for common query patterns
- JSONB index on `techniques` for filtering

## Implementation Details

### Security
- All endpoints require JWT authentication
- User ownership validation on detail/rerun endpoints
- SQL injection protection through parameterized queries

### Performance Optimizations
- Indexed columns for fast filtering
- Pagination to limit result sets
- Efficient query patterns with proper joins

### Integration Points
- Enhancement service updated to save prompts with user_id
- Existing enhance endpoint returns history ID in response
- Backward compatibility maintained with legacy history endpoints

## Migration Instructions

Run the following migrations in order:
1. `000008_add_search_indexes.up.sql` - Adds full-text search and performance indexes

## Testing

Example requests:

```bash
# Get history with search
GET /api/v1/prompts/history?search=python&page=1&limit=10

# Get specific prompt
GET /api/v1/prompts/abc123

# Rerun a prompt
POST /api/v1/prompts/abc123/rerun
```