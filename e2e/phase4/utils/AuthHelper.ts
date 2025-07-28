import { Page, BrowserContext } from '@playwright/test';

export interface TestUser {
  id?: string;
  email: string;
  password: string;
  name?: string;
  role?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

/**
 * Authentication Helper for Phase 4 tests
 * Helps with authenticated user scenarios using real backend
 */
export class AuthHelper {
  private page: Page;
  private context: BrowserContext;
  
  // Default test users - these should exist in the test database
  static readonly TEST_USERS = {
    regular: {
      email: 'test@example.com',
      password: 'Test123456!',
      name: 'Test User'
    },
    powerUser: {
      email: 'power@example.com', 
      password: 'Power123456!',
      name: 'Power User'
    },
    newUser: {
      email: 'new@example.com',
      password: 'New123456!',
      name: 'New User'
    }
  };

  constructor(page: Page, context: BrowserContext) {
    this.page = page;
    this.context = context;
  }

  /**
   * Login a user and get authenticated
   */
  async loginUser(user: TestUser): Promise<AuthTokens> {
    // Navigate to login page
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
    
    // Wait for login form to be ready
    // Try multiple possible selectors for email field
    const emailSelectors = [
      'input[name="email"]',
      'input[name="email_or_username"]',
      'input[type="email"]',
      'input[placeholder*="Email"]',
      'input[id="email"]'
    ];
    
    let emailSelector = '';
    for (const selector of emailSelectors) {
      const count = await this.page.locator(selector).count();
      if (count > 0) {
        emailSelector = selector;
        break;
      }
    }
    
    if (!emailSelector) {
      throw new Error('Could not find email input field');
    }
    
    await this.page.waitForSelector(emailSelector, { state: 'visible' });
    
    // Fill login form
    await this.page.fill(emailSelector, user.email);
    await this.page.fill('input[type="password"]', user.password);
    
    // Submit form - handle navigation more gracefully
    const submitButton = this.page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();
    
    // Wait for button to be enabled (in case there's validation)
    await submitButton.waitFor({ state: 'visible' });
    await this.page.waitForTimeout(500); // Give form validation time to complete
    
    await submitButton.click();
    
    // Wait for either navigation or error message
    try {
      await this.page.waitForURL((url) => !url.href.includes('/login'), { 
        timeout: 10000,
        waitUntil: 'networkidle' 
      });
    } catch (error) {
      // Check if we're still on login page with an error
      const currentUrl = this.page.url();
      if (currentUrl.includes('/login')) {
        // Look for error message
        const hasError = await this.page.locator('[role="alert"], .alert-destructive').count() > 0;
        if (!hasError) {
          throw new Error('Login failed - no navigation occurred and no error message');
        }
      }
    }
    
    // Verify we're logged in
    const url = this.page.url();
    if (url.includes('/login')) {
      // Check for error message
      const errorSelectors = [
        '[role="alert"]',
        '.error-message',
        '.alert-destructive',
        'div:has-text("Invalid email or password")',
        'div:has-text("1 Issue")'
      ];
      
      for (const selector of errorSelectors) {
        const errorElement = await this.page.locator(selector).first();
        if (await errorElement.count() > 0) {
          const errorText = await errorElement.textContent();
          console.log(`Found error with selector ${selector}: ${errorText}`);
          throw new Error(`Login failed: ${errorText || 'Unknown error'}`);
        }
      }
      throw new Error('Login failed - still on login page with no visible error');
    }
    
    // Extract tokens
    return await this.getStoredTokens();
  }


  /**
   * Get stored authentication tokens
   */
  async getStoredTokens(): Promise<AuthTokens> {
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
    
    // Check localStorage as fallback
    const tokens = await this.page.evaluate(() => {
      return {
        accessToken: localStorage.getItem('access_token') || '',
        refreshToken: localStorage.getItem('refresh_token') || ''
      };
    });
    
    return tokens;
  }

  /**
   * Clear all authentication data
   */
  async clearAuth(): Promise<void> {
    // Clear cookies
    await this.context.clearCookies();
    
    // Clear localStorage only if we're on a page
    try {
      const url = this.page.url();
      if (url && url !== 'about:blank') {
        await this.page.evaluate(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
        });
      }
    } catch (e) {
      // Ignore errors if page is not loaded
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const tokens = await this.getStoredTokens();
    return !!(tokens.accessToken && tokens.refreshToken);
  }

  /**
   * Get current user info from storage
   */
  async getCurrentUser(): Promise<any> {
    return await this.page.evaluate(() => {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    });
  }

  /**
   * Wait for authentication to complete
   */
  async waitForAuth(timeout: number = 10000): Promise<void> {
    await this.page.waitForFunction(
      () => {
        return !!(localStorage.getItem('access_token') || 
                 document.cookie.includes('access_token'));
      },
      { timeout }
    );
  }
  
  /**
   * Logout the current user
   */
  async logout(): Promise<void> {
    // Clear auth data first
    await this.clearAuth();
    
    // Navigate to login page to confirm logout
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
  }
}