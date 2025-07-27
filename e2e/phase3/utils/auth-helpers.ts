import { Page, BrowserContext, expect, APIRequestContext } from '@playwright/test';
import jwt from 'jsonwebtoken';

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface DecodedToken {
  userId: string;
  email: string;
  exp: number;
  iat: number;
  type: 'access' | 'refresh';
}

/**
 * Authentication Helper Utilities
 * Manages JWT tokens and authentication state
 */
export class AuthHelpers {
  private page: Page;
  private context: BrowserContext;
  
  constructor(page: Page, context: BrowserContext) {
    this.page = page;
    this.context = context;
  }

  /**
   * Extract JWT tokens from cookies or local storage
   */
  async getStoredTokens(): Promise<AuthTokens | null> {
    // Check cookies first
    const cookies = await this.context.cookies();
    const accessTokenCookie = cookies.find(c => c.name === 'access_token');
    const refreshTokenCookie = cookies.find(c => c.name === 'refresh_token');
    
    if (accessTokenCookie && refreshTokenCookie) {
      return {
        accessToken: accessTokenCookie.value,
        refreshToken: refreshTokenCookie.value
      };
    }

    // Check local storage
    const tokens = await this.page.evaluate(() => {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (accessToken && refreshToken) {
        return { accessToken, refreshToken };
      }
      
      // Check session storage as fallback
      const sessionAccess = sessionStorage.getItem('access_token');
      const sessionRefresh = sessionStorage.getItem('refresh_token');
      
      if (sessionAccess && sessionRefresh) {
        return { accessToken: sessionAccess, refreshToken: sessionRefresh };
      }
      
      return null;
    });

    return tokens;
  }

  /**
   * Decode JWT token (without verification)
   */
  decodeToken(token: string): DecodedToken | null {
    try {
      const decoded = jwt.decode(token) as any;
      if (!decoded) return null;
      
      return {
        userId: decoded.sub || decoded.userId,
        email: decoded.email,
        exp: decoded.exp,
        iat: decoded.iat,
        type: decoded.type || 'access'
      };
    } catch (error) {
      console.error('Failed to decode token:', error);
      return null;
    }
  }

  /**
   * Check if token is expired
   */
  isTokenExpired(token: string): boolean {
    const decoded = this.decodeToken(token);
    if (!decoded) return true;
    
    const now = Math.floor(Date.now() / 1000);
    return decoded.exp < now;
  }

  /**
   * Get remaining token lifetime in seconds
   */
  getTokenLifetime(token: string): number {
    const decoded = this.decodeToken(token);
    if (!decoded) return 0;
    
    const now = Math.floor(Date.now() / 1000);
    return Math.max(0, decoded.exp - now);
  }

  /**
   * Verify authentication state
   */
  async verifyAuthState(): Promise<boolean> {
    const tokens = await this.getStoredTokens();
    if (!tokens) return false;
    
    // Check if access token is valid
    if (this.isTokenExpired(tokens.accessToken)) {
      console.log('Access token expired');
      return false;
    }
    
    // Verify API accepts the token
    const response = await this.page.request.get('/api/v1/auth/verify', {
      headers: {
        'Authorization': `Bearer ${tokens.accessToken}`
      }
    });
    
    return response.ok();
  }

  /**
   * Clear all authentication data
   */
  async clearAuthData(): Promise<void> {
    // Clear cookies
    await this.context.clearCookies();
    
    // Clear storage only if we're on a page
    try {
      const url = this.page.url();
      // Only clear storage if we've navigated somewhere
      if (url && url !== 'about:blank') {
        await this.page.evaluate(() => {
          localStorage.clear();
          sessionStorage.clear();
        });
      }
    } catch (error) {
      // Ignore errors if page isn't ready
      console.log('Could not clear storage - page not ready');
    }
  }

  /**
   * Set authentication tokens manually (for testing)
   */
  async setAuthTokens(tokens: AuthTokens): Promise<void> {
    // Set cookies
    await this.context.addCookies([
      {
        name: 'access_token',
        value: tokens.accessToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false, // Set to true in production
        sameSite: 'Lax'
      },
      {
        name: 'refresh_token',
        value: tokens.refreshToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false, // Set to true in production
        sameSite: 'Lax'
      }
    ]);
    
    // Also set in local storage for redundancy
    await this.page.evaluate((tokens) => {
      localStorage.setItem('access_token', tokens.accessToken);
      localStorage.setItem('refresh_token', tokens.refreshToken);
    }, tokens);
  }

  /**
   * Simulate token expiration
   */
  async expireAccessToken(): Promise<void> {
    const tokens = await this.getStoredTokens();
    if (!tokens) return;
    
    // Create an expired token
    const expiredToken = jwt.sign(
      { 
        sub: 'test-user',
        email: 'test@example.com',
        type: 'access'
      },
      'test-secret',
      { expiresIn: '-1h' } // Expired 1 hour ago
    );
    
    await this.setAuthTokens({
      accessToken: expiredToken,
      refreshToken: tokens.refreshToken
    });
  }

  /**
   * Monitor token refresh
   */
  async waitForTokenRefresh(timeout: number = 10000): Promise<boolean> {
    const initialTokens = await this.getStoredTokens();
    if (!initialTokens) return false;
    
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      await this.page.waitForTimeout(100);
      const currentTokens = await this.getStoredTokens();
      
      if (currentTokens && currentTokens.accessToken !== initialTokens.accessToken) {
        return true; // Token was refreshed
      }
    }
    
    return false;
  }

  /**
   * Verify multi-tab session sync
   */
  async verifyMultiTabSync(otherPage: Page): Promise<boolean> {
    const thisTokens = await this.getStoredTokens();
    
    const otherTokens = await otherPage.evaluate(() => {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      return { accessToken, refreshToken };
    });
    
    return thisTokens?.accessToken === otherTokens?.accessToken &&
           thisTokens?.refreshToken === otherTokens?.refreshToken;
  }

  /**
   * Create expired refresh token for testing
   */
  createExpiredRefreshToken(): string {
    return jwt.sign(
      { 
        sub: 'test-user',
        email: 'test@example.com',
        type: 'refresh'
      },
      'test-secret',
      { expiresIn: '-1d' } // Expired 1 day ago
    );
  }

  /**
   * Create tampered token for security testing
   */
  createTamperedToken(validToken: string): string {
    // Decode the token
    const parts = validToken.split('.');
    if (parts.length !== 3) return validToken + 'tampered';
    
    // Modify the payload
    const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
    payload.userId = 'hacker';
    payload.role = 'admin';
    
    // Re-encode without proper signature
    const newPayload = Buffer.from(JSON.stringify(payload)).toString('base64');
    return `${parts[0]}.${newPayload}.invalidsignature`;
  }

  /**
   * Test rate limiting
   */
  async testRateLimit(endpoint: string, limit: number = 5): Promise<boolean> {
    const tokens = await this.getStoredTokens();
    if (!tokens) return false;
    
    let rateLimited = false;
    
    for (let i = 0; i < limit + 2; i++) {
      const response = await this.page.request.post(endpoint, {
        headers: {
          'Authorization': `Bearer ${tokens.accessToken}`
        },
        data: { test: true }
      });
      
      if (response.status() === 429) {
        rateLimited = true;
        break;
      }
    }
    
    return rateLimited;
  }

  /**
   * Get CSRF token
   */
  async getCSRFToken(): Promise<string | null> {
    // Check meta tag
    const metaToken = await this.page.locator('meta[name="csrf-token"]').getAttribute('content');
    if (metaToken) return metaToken;
    
    // Check cookie
    const cookies = await this.context.cookies();
    const csrfCookie = cookies.find(c => c.name === 'csrf_token' || c.name === '_csrf');
    if (csrfCookie) return csrfCookie.value;
    
    // Check form input
    const inputToken = await this.page.locator('input[name="_csrf"]').inputValue().catch(() => null);
    return inputToken;
  }
}

/**
 * Create mock JWT tokens for testing
 */
export function createMockTokens(userId: string, email: string): AuthTokens {
  const accessToken = jwt.sign(
    { 
      sub: userId,
      email: email,
      type: 'access'
    },
    'test-secret',
    { expiresIn: '15m' }
  );
  
  const refreshToken = jwt.sign(
    { 
      sub: userId,
      email: email,
      type: 'refresh'
    },
    'test-secret',
    { expiresIn: '7d' }
  );
  
  return { accessToken, refreshToken };
}

/**
 * Verify protected route behavior
 */
export async function verifyProtectedRoute(
  page: Page,
  protectedUrl: string,
  expectedRedirect: string = '/login'
): Promise<boolean> {
  // Navigate to protected route
  await page.goto(protectedUrl);
  
  // Check if redirected to login
  await page.waitForURL(`**${expectedRedirect}*`, { timeout: 5000 });
  
  // Verify redirect URL contains return path
  const currentUrl = page.url();
  const url = new URL(currentUrl);
  const returnTo = url.searchParams.get('returnTo') || url.searchParams.get('redirect');
  
  return returnTo?.includes(protectedUrl) || false;
}

/**
 * Test session timeout behavior
 */
export async function testSessionTimeout(
  page: Page,
  context: BrowserContext,
  timeoutMs: number = 5000
): Promise<boolean> {
  const authHelpers = new AuthHelpers(page, context);
  
  // Get initial tokens
  const initialTokens = await authHelpers.getStoredTokens();
  if (!initialTokens) return false;
  
  // Wait for timeout
  await page.waitForTimeout(timeoutMs);
  
  // Try to access protected resource
  const response = await page.request.get('/api/v1/user/profile', {
    headers: {
      'Authorization': `Bearer ${initialTokens.accessToken}`
    }
  });
  
  // Should be unauthorized if session timed out
  return response.status() === 401;
}