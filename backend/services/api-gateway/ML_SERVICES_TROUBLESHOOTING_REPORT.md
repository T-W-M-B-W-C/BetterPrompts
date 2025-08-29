# ML Services Troubleshooting Report

## Issue Summary

**Primary Error**: "Failed to analyze intent" - KeyError: 'suggested_techniques'

**Root Cause**: The intent-classifier service is returning classification results without the 'suggested_techniques' field, which the API endpoint expects.

## Detailed Analysis

### 1. Service Configuration Issues

#### TorchServe Status
- **Status**: Unhealthy (returning 500 errors on health checks)
- **Impact**: Not critical - intent-classifier is configured to NOT use TorchServe
- **Configuration**: `USE_TORCHSERVE=false` in docker-compose.yml

#### Intent-Classifier Configuration
- **Mode**: Using local models (not TorchServe)
- **Router**: Adaptive router (Wave 6) with multiple classifiers
- **Classifiers Available**:
  - Rule-based classifier
  - Hybrid classifier (rules + zero-shot)
  - Zero-shot classifier

### 2. Error Flow Analysis

1. **Request Flow**:
   ```
   API Gateway → Intent Classifier → Adaptive Router → Hybrid Classifier
   ```

2. **Error Location**: `/app/api/v1/intents.py` line 95
   ```python
   suggested_techniques=result["suggested_techniques"],  # KeyError here
   ```

3. **Missing Field Source**: The HybridClassifier returns:
   ```python
   {
       "intent": "...",
       "confidence": 0.227,
       "complexity": "...",
       "audience": "...",
       "method": "zero_shot",
       # NO 'suggested_techniques' field!
   }
   ```

### 3. Root Cause

The adaptive router's `_execute_classification` method doesn't ensure all required fields are present when using different classifiers:

- **Rule-based classifier**: Returns 'suggested_techniques' via `_convert_rule_result`
- **Hybrid classifier**: Does NOT return 'suggested_techniques'
- **TorchServe**: Would return 'suggested_techniques' but is disabled

## Recommended Fixes

### Option 1: Quick Fix (Immediate)
Add a default value in the API endpoint to handle missing field:

```python
# In /backend/services/intent-classifier/app/api/v1/intents.py
response = IntentResponse(
    intent=result["intent"],
    confidence=result["confidence"],
    complexity=result["complexity"],
    suggested_techniques=result.get("suggested_techniques", ["chain_of_thought"]),  # Default
    metadata={...}
)
```

### Option 2: Proper Fix (Recommended)
Update the adaptive router to ensure all classifiers return consistent format:

```python
# In adaptive_router.py _execute_classification method
elif model_type == ModelType.ZERO_SHOT:
    result = await self.hybrid_classifier.classify(text)
    # Ensure suggested_techniques is present
    if "suggested_techniques" not in result:
        # Get techniques based on intent
        result["suggested_techniques"] = self._get_techniques_for_intent(result["intent"])
    return result
```

### Option 3: Complete Solution
1. Fix the HybridClassifier to include suggested_techniques
2. Add validation in the adaptive router
3. Implement proper error handling in the API endpoint

## Temporary Workaround

While implementing the fix, you can:

1. **Enable Mock Mode**: The intent-classifier has a mock mode that returns consistent data
2. **Use Rule-Based Only**: Force the adaptive router to use only the rule-based classifier
3. **Add Error Handling**: Catch the KeyError and provide default techniques

## Performance Issues

- **Latency**: ~11 seconds for classification (very slow)
- **Cause**: Zero-shot model initialization on each request
- **Solution**: Ensure models are properly initialized at startup and cached

## Implementation Steps

1. **Immediate** (5 minutes):
   ```bash
   # Edit the intents.py file to add default value
   docker compose exec intent-classifier bash
   vi /app/app/api/v1/intents.py
   # Add .get() with default as shown above
   ```

2. **Short-term** (30 minutes):
   - Update adaptive router to ensure consistent output
   - Add validation for required fields
   - Implement proper error handling

3. **Long-term** (2 hours):
   - Fix model initialization to reduce latency
   - Enable TorchServe if ML models are available
   - Add comprehensive testing for all classifier paths

## Testing the Fix

After implementing the fix:

```bash
# Test the intent classifier directly
curl -X POST http://localhost:8001/api/v1/intents/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Write a function to sort an array"}'

# Test through API gateway
curl -X POST http://localhost/api/v1/enhance \
  -H "Content-Type: application/json" \
  -H "X-Test-Mode: true" \
  -d '{"text": "Write a function to sort an array"}'
```

## Conclusion

The ML services issue is a simple field mismatch between what the adaptive router returns and what the API expects. The system is functional but needs a small fix to ensure all classification paths return the required 'suggested_techniques' field.