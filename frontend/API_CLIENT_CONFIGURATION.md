# Frontend API Client Configuration

## Overview

The frontend API client is configured to work with the BetterPrompts API Gateway, which runs on port 8090 internally and is exposed through multiple access points.

## Architecture

```
Frontend (3000) → Nginx (80) → API Gateway (8090) → Backend Services
                     ↓
                Direct Access (8000)
```

## Configuration Options

### 1. Default Configuration (Recommended)

Uses nginx proxy at `http://localhost/api/v1`:
- ✅ CORS properly configured
- ✅ Request rate limiting
- ✅ Load balancing ready
- ✅ Production-like setup

```env
NEXT_PUBLIC_API_URL=http://localhost/api/v1
```

### 2. Direct API Gateway Access

For development/debugging at `http://localhost:8000/api/v1`:
- ⚠️ May have CORS issues
- ⚠️ Bypasses nginx features
- ✅ Direct connection for debugging

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. Custom URL

For production or custom environments:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

## Port Reference

| Service | Internal Port | External Port | Access URL |
|---------|--------------|---------------|------------|
| Frontend | 3000 | 3000 | http://localhost:3000 |
| API Gateway | 8090 | 8000 | http://localhost:8000 |
| Nginx Proxy | 80 | 80 | http://localhost |

## API Endpoints

All endpoints are prefixed with `/api/v1`:

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `GET /auth/profile` - Get user profile (protected)
- `PUT /auth/profile` - Update profile (protected)
- `POST /auth/change-password` - Change password (protected)
- `POST /auth/verify-email` - Verify email address

### Prompt Enhancement
- `POST /analyze` - Analyze prompt (public, optional auth)
- `POST /enhance` - Enhance prompt (protected)
- `GET /techniques` - Get available techniques (protected)
- `POST /techniques/select` - Auto-select techniques (protected)

### History
- `GET /history` - Get prompt history (protected)
- `GET /history/:id` - Get specific item (protected)
- `DELETE /history/:id` - Delete item (protected)

### Feedback
- `POST /feedback` - Submit feedback (protected)

### Admin (requires admin role)
- `GET /admin/users` - List users
- `GET /admin/users/:id` - Get user details
- `PUT /admin/users/:id` - Update user
- `DELETE /admin/users/:id` - Delete user
- `GET /admin/metrics` - System metrics
- `GET /admin/metrics/usage` - Usage metrics
- `POST /admin/cache/clear` - Clear cache
- `POST /admin/cache/invalidate/:user_id` - Invalidate user cache

### Developer API (requires developer role)
- `POST /dev/api-keys` - Create API key
- `GET /dev/api-keys` - List API keys
- `DELETE /dev/api-keys/:id` - Delete API key
- `GET /dev/analytics/usage` - Usage analytics
- `GET /dev/analytics/performance` - Performance metrics

## Usage Examples

### Using the API Services

```typescript
import { api } from '@/lib/api/services'

// Login
const response = await api.auth.login({
  email: 'user@example.com',
  password: 'password123'
})

// Enhance a prompt
const enhanced = await api.prompts.enhance({
  text: 'Write a function to sort an array',
  intent: 'code_generation',
  complexity: 'moderate',
  techniques: ['chain_of_thought', 'few_shot']
})

// Get history
const history = await api.history.getHistory({
  limit: 10,
  offset: 0
})
```

### Using the Enhancement Hook

```typescript
import { useEnhancement } from '@/hooks/useEnhancement'

function MyComponent() {
  const { analyzeAndEnhance, isProcessing } = useEnhancement()
  
  const handleEnhance = async (text: string) => {
    const result = await analyzeAndEnhance(text, {
      autoEnhance: true,
      target_model: 'gpt-4'
    })
    
    console.log('Analysis:', result.analysis)
    console.log('Enhanced:', result.enhancement)
  }
}
```

## Troubleshooting

### CORS Issues

If you see CORS errors:
1. Ensure you're using the nginx proxy URL (default)
2. Check that the frontend URL is in the CORS allowed origins
3. Verify cookies/credentials are enabled

### Connection Errors

If the API is unreachable:
1. Check all services are running: `docker compose ps`
2. Verify the API Gateway health: `curl http://localhost/api/v1/health`
3. Check logs: `docker compose logs api-gateway`

### Authentication Issues

If authentication fails:
1. Ensure JWT secrets are configured in the API Gateway
2. Check that cookies are enabled in the browser
3. Verify the auth token is being sent in requests

## Development Tips

1. **Use the nginx proxy** for development to match production behavior
2. **Enable dev mode** for additional logging: `NEXT_PUBLIC_DEV_MODE=true`
3. **Check the network tab** in browser DevTools to debug API calls
4. **Use the API services module** instead of raw axios calls
5. **Handle errors consistently** using the provided error handler

## Security Notes

- Always use HTTPS in production
- Keep API keys and tokens secure
- Enable CORS only for trusted origins
- Use the authentication middleware for protected routes
- Implement rate limiting for public endpoints