import { test, expect } from '@playwright/test';

const API_BASE_URL = 'http://localhost:8000/api/v1';
const NGINX_URL = 'http://localhost/api/v1';

test.describe('API Gateway Integration Tests', () => {
  test.describe('Health Checks', () => {
    test('health endpoint returns healthy status', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/health`);
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body).toEqual({
        status: 'healthy',
        service: 'api-gateway'
      });
    });

    test('readiness endpoint validates all services', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/ready`);
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body).toEqual({
        status: 'ready',
        service: 'api-gateway'
      });
    });

    test('nginx proxy routes health endpoint correctly', async ({ request }) => {
      const response = await request.get(`${NGINX_URL}/health`);
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body.status).toBe('healthy');
    });
  });

  test.describe('Authentication Flow', () => {
    const testUser = {
      email: `test${Date.now()}@example.com`,
      username: `testuser${Date.now()}`,
      password: 'SecurePass123!',
      firstName: 'Test',
      lastName: 'User'
    };

    let authToken: string;
    let refreshToken: string;

    test('register new user', async ({ request }) => {
      const response = await request.post(`${API_BASE_URL}/auth/register`, {
        data: testUser
      });
      
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body).toHaveProperty('user');
      expect(body).toHaveProperty('access_token');
      expect(body).toHaveProperty('refresh_token');
      expect(body.user.email).toBe(testUser.email);
      
      authToken = body.access_token;
      refreshToken = body.refresh_token;
    });

    test('login with credentials', async ({ request }) => {
      const response = await request.post(`${API_BASE_URL}/auth/login`, {
        data: {
          email: testUser.email,
          password: testUser.password
        }
      });
      
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body).toHaveProperty('access_token');
      expect(body).toHaveProperty('refresh_token');
    });

    test('get user profile with auth token', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body.email).toBe(testUser.email);
      expect(body.username).toBe(testUser.username);
    });

    test('refresh token flow', async ({ request }) => {
      const response = await request.post(`${API_BASE_URL}/auth/refresh`, {
        data: {
          refresh_token: refreshToken
        }
      });
      
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body).toHaveProperty('access_token');
      expect(body).toHaveProperty('refresh_token');
    });
  });

  test.describe('Intent Analysis', () => {
    test('analyze intent without authentication', async ({ request }) => {
      const response = await request.post(`${API_BASE_URL}/analyze`, {
        data: {
          text: 'Explain the concept of quantum computing in simple terms'
        }
      });
      
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body).toHaveProperty('intent');
      expect(body).toHaveProperty('complexity');
      expect(body).toHaveProperty('suggestedTechniques');
      expect(body.suggestedTechniques).toBeInstanceOf(Array);
    });
  });

  test.describe('Service Integration', () => {
    test('intent classifier service is accessible', async ({ request }) => {
      const response = await request.get('http://localhost:8001/health');
      expect(response.ok()).toBeTruthy();
    });

    test('technique selector service is accessible', async ({ request }) => {
      const response = await request.get('http://localhost:8002/health');
      expect(response.ok()).toBeTruthy();
    });

    test('prompt generator service is accessible', async ({ request }) => {
      const response = await request.get('http://localhost:8003/health');
      expect(response.ok()).toBeTruthy();
    });

    test('torchserve model server is accessible', async ({ request }) => {
      const response = await request.get('http://localhost:8080/ping');
      expect(response.ok()).toBeTruthy();
    });
  });

  test.describe('Error Handling', () => {
    test('returns 404 for unknown endpoints', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/unknown-endpoint`);
      expect(response.status()).toBe(404);
    });

    test('returns 401 for protected endpoints without auth', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/history`);
      expect(response.status()).toBe(401);
    });

    test('returns 400 for invalid request body', async ({ request }) => {
      const response = await request.post(`${API_BASE_URL}/auth/register`, {
        data: {
          // Missing required fields
          email: 'invalid-email'
        }
      });
      expect(response.status()).toBe(400);
    });
  });

  test.describe('Performance Checks', () => {
    test('health endpoint responds within 200ms', async ({ request }) => {
      const start = Date.now();
      await request.get(`${API_BASE_URL}/health`);
      const duration = Date.now() - start;
      expect(duration).toBeLessThan(200);
    });

    test('readiness check completes within 500ms', async ({ request }) => {
      const start = Date.now();
      await request.get(`${API_BASE_URL}/ready`);
      const duration = Date.now() - start;
      expect(duration).toBeLessThan(500);
    });
  });
});