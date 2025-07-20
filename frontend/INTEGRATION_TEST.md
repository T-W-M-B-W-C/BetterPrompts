# Frontend-Backend Integration Test Guide

## Prerequisites

1. Ensure backend services are running:
   ```bash
   docker compose up -d
   ```

2. Create a `.env.local` file in the frontend directory:
   ```bash
   cp .env.example .env.local
   ```

3. Verify the API URL is correct in `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost/api/v1
   ```

## Testing Steps

### 1. API Connection Test
- Open the enhance page
- Check for the connection status indicator
- If offline banner shows, verify backend is running

### 2. Technique Loading Test
- Techniques should load automatically on page load
- Skeleton loaders should appear while loading
- Error message should show if API fails

### 3. Enhancement Test
- Enter a test prompt: "Help me write a blog post about sustainable living"
- Click "Enhance Prompt" button
- Verify:
  - Loading state shows while processing
  - Enhanced prompt appears after completion
  - Error handling works if API fails

### 4. Error Handling Test
- Stop the backend: `docker compose down`
- Refresh the page
- Verify:
  - Connection issue banner appears
  - Enhance button shows "Offline" state
  - Appropriate error messages display

### 5. Retry Logic Test
- With backend stopped, try to enhance a prompt
- Start backend: `docker compose up -d`
- Try enhancement again (should work after retry)

## Common Issues

### "Network error" message
- Check if backend is running: `docker compose ps`
- Verify API URL in `.env.local`
- Check CORS configuration in API gateway

### "401 Unauthorized" errors
- Authentication may be required
- Check if JWT_SECRET is set in backend
- Verify auth token handling in frontend

### Techniques not loading
- Check `/api/v1/techniques` endpoint directly
- Verify technique-selector service is running
- Check for database connection issues

## API Endpoints to Test

```bash
# Health check
curl http://localhost/api/v1/health

# Get techniques
curl http://localhost/api/v1/techniques

# Test enhancement (requires auth token)
curl -X POST http://localhost/api/v1/enhance \
  -H "Content-Type: application/json" \
  -d '{"text": "Help me write a blog post"}'
```