# CORS Configuration for API Gateway

## Overview

The API Gateway implements comprehensive CORS (Cross-Origin Resource Sharing) configuration to ensure secure communication between the frontend and backend services while maintaining flexibility for development and production environments.

## Configuration

### Default Allowed Origins

The following origins are allowed by default:
- `http://localhost:3000` - Frontend development server
- `http://localhost:3001` - Alternative frontend port
- `http://localhost` - Production frontend through nginx
- `http://127.0.0.1:3000` - Alternative localhost notation
- `http://localhost:80` - Explicit port 80

### Environment Variables

#### `CORS_ALLOWED_ORIGINS`
Comma-separated list of additional allowed origins.
```bash
CORS_ALLOWED_ORIGINS=https://app.example.com,https://staging.example.com
```

#### `PRODUCTION_ORIGIN`
Single production origin to be added to the allowed list.
```bash
PRODUCTION_ORIGIN=https://app.betterprompts.io
```

#### `NODE_ENV`
When set to `development`, the CORS middleware is more permissive and allows any localhost origin.
```bash
NODE_ENV=development
```

## Features

### Security Features
- **Credentials Support**: `AllowCredentials: true` enables cookies and authentication headers
- **No Wildcards**: `AllowWildcard: false` prevents security vulnerabilities
- **Origin Validation**: Custom validation function for dynamic origin checking
- **Preflight Caching**: 12-hour cache for OPTIONS requests to reduce overhead

### Allowed Methods
- GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD

### Allowed Headers
- Standard headers: Origin, Content-Type, Content-Length, Accept, Accept-Encoding, Accept-Language
- Authentication: Authorization
- Custom headers: X-Session-ID, X-Request-ID, X-CSRF-Token, X-Requested-With
- Cache control: Cache-Control, Pragma

### Exposed Headers
- X-Request-ID - Request tracking
- X-Session-ID - Session management
- X-RateLimit-* - Rate limiting information
- Content-* - Content metadata

## Development Mode

In development mode (`NODE_ENV=development`), the CORS middleware automatically allows:
- Any `http://localhost:*` origin
- Any `http://127.0.0.1:*` origin
- Any `http://[::1]:*` origin (IPv6 localhost)

This provides flexibility during development while maintaining security in production.

## Docker Configuration

The docker-compose.yml includes CORS environment variables:
```yaml
environment:
  - CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost
  - PRODUCTION_ORIGIN=${PRODUCTION_ORIGIN:-}
  - NODE_ENV=development
```

## Testing CORS

### Test Preflight Request
```bash
curl -X OPTIONS http://localhost:8000/api/v1/enhance \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -v
```

### Test Actual Request with Credentials
```bash
curl -X POST http://localhost:8000/api/v1/enhance \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --cookie "session=YOUR_SESSION" \
  -d '{"text": "test prompt"}' \
  -v
```

### Expected Response Headers
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Expose-Headers: X-Request-ID,X-Session-ID,...
```

## Troubleshooting

### CORS Errors in Browser Console

1. **Origin not allowed**
   - Check if your frontend URL is in the allowed origins list
   - Add it via `CORS_ALLOWED_ORIGINS` environment variable
   - Ensure you're using the correct protocol (http vs https)

2. **Credentials not included**
   - Ensure `credentials: 'include'` in fetch requests
   - Check that `AllowCredentials: true` is set in CORS config
   - Verify cookies are being set with proper SameSite attributes

3. **Headers not allowed**
   - Add missing headers to `AllowHeaders` in cors.go
   - Check browser network tab for which headers are being sent

4. **Preflight failing**
   - Verify OPTIONS method is allowed
   - Check that preflight cache time is reasonable (12 hours)
   - Look for server errors during OPTIONS requests

### Debug Logging

The CORS middleware logs:
- Configuration on startup
- Rejected origins with reason
- Allowed origins in development mode

Check logs with:
```bash
docker compose logs api-gateway | grep -i cors
```

## Production Considerations

1. **Remove development origins** in production
2. **Set specific allowed origins** instead of using dynamic validation
3. **Use HTTPS** for all production origins
4. **Consider using a reverse proxy** for additional CORS handling
5. **Monitor CORS errors** in production logs

## Security Best Practices

1. **Never use wildcard (*) origins** in production
2. **Always validate origins** against a whitelist
3. **Use HTTPS** for all production traffic
4. **Limit exposed headers** to only what's necessary
5. **Set appropriate cache times** for preflight requests
6. **Regularly audit** allowed origins and remove unused ones