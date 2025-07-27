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

  test.describe('Basic Authentication Tests', () => {
    test('should display login form with all required elements', async ({ page }) => {
      // Verify all form elements
      await expect(page.locator('input#email[name="email"]')).toBeVisible();
      await expect(page.locator('input#password[name="password"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
      await expect(page.locator('[role="checkbox"]#rememberMe, input#rememberMe[type="checkbox"]')).toBeVisible();
      await expect(page.locator('a:has-text("Forgot password")')).toBeVisible();
      await expect(page.locator('a:has-text("Sign up")')).toBeVisible();
    });

    test('should validate empty form submission', async ({ page }) => {
      // Try to submit without filling the form
      await page.locator('button[type="submit"]').click();
      
      // Check HTML5 validation - the form should not submit
      const url = page.url();
      expect(url).toContain('/login'); // Should still be on login page
      
      // Check if inputs show validation (HTML5 required attribute)
      const emailInput = page.locator('input#email');
      const passwordInput = page.locator('input#password');
      
      // HTML5 validation should prevent form submission
      await expect(emailInput).toHaveAttribute('required', '');
      await expect(passwordInput).toHaveAttribute('required', '');
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
});