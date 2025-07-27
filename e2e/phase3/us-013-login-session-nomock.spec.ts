import { test, expect, Browser, BrowserContext, Page } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { AuthHelpers } from './utils/auth-helpers';

test.describe('US-013: User Login with Real Backend', () => {
  let loginPage: LoginPage;
  let authHelpers: AuthHelpers;
  
  // Test user that exists in the database
  const validUser = {
    email: 'test@example.com',
    password: 'Test123!@#',
    name: 'Test User'
  };

  test.beforeEach(async ({ page, context }) => {
    loginPage = new LoginPage(page);
    authHelpers = new AuthHelpers(page, context);
    
    // Clear any existing auth data
    await authHelpers.clearAuthData();
    
    // Navigate to login page
    await loginPage.goto();
  });

  test('should successfully login with valid credentials', async ({ page, context }) => {
    // Use real backend - no mocking
    const result = await loginPage.login({
      email: validUser.email,
      password: validUser.password
    });

    expect(result.status).toBe(200);
    expect(result.data.access_token).toBeTruthy();
    expect(result.data.user.email).toBe(validUser.email);
    
    // Should redirect to homepage (/) after login
    await loginPage.waitForLoginSuccess('/');
    
    // Verify tokens are stored
    const tokens = await authHelpers.getStoredTokens();
    expect(tokens).toBeTruthy();
    expect(tokens?.accessToken).toBeTruthy();
  });

  test('should fail login with invalid password', async ({ page }) => {
    const result = await loginPage.login({
      email: validUser.email,
      password: 'WrongPassword123!'
    });

    // Backend may return 401 (Unauthorized) or 403 (Forbidden) depending on rate limiting
    expect([401, 403]).toContain(result.status);
    
    // Should show error message
    const errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage).toContain('Invalid email or password');
    
    // Should stay on login page
    expect(page.url()).toContain('/login');
  });

  test('should fail login with non-existent user', async ({ page }) => {
    const result = await loginPage.login({
      email: 'nonexistent@example.com',
      password: 'Test123!@#'
    });

    // Backend may return 401 (Unauthorized) or 403 (Forbidden) depending on rate limiting
    expect([401, 403]).toContain(result.status);
    
    // Should show error message
    const errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage).toContain('Invalid email or password');
    
    // Should stay on login page
    expect(page.url()).toContain('/login');
  });
});