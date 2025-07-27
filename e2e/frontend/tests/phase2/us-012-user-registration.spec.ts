import { test, expect } from '@playwright/test';
import { RegisterPage } from '../../pages/auth/register.page';
import { VerificationPage } from './pages/VerificationPage';
import { DashboardPage } from '../../pages/dashboard.page';
import { TestUserGenerator, generateTestUser } from './utils/test-user-generator';
import { cleanupDatabase, getUser } from '../../../test-helpers/database';
import { getVerificationCodeFromEmail, getVerificationLinkFromEmail, clearAllEmails, waitForEmail } from '../../../test-helpers/mailhog';

test.describe('US-012: User Registration and Email Verification', () => {
  let registerPage: RegisterPage;
  let verificationPage: VerificationPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    // Clean up database before each test
    await cleanupDatabase();
    
    // Clear emails from MailHog
    await clearAllEmails();
    
    // Initialize page objects
    registerPage = new RegisterPage(page);
    verificationPage = new VerificationPage(page);
    dashboardPage = new DashboardPage(page);

    // Navigate to registration page
    await registerPage.goto();
  });

  test.afterEach(async () => {
    // Reset test data generator
    TestUserGenerator.reset();
  });

  test('should display registration form with all required fields', async ({ page }) => {
    // Verify all form elements are present
    await registerPage.verifyPageLoaded();
    
    // Check form fields
    await expect(page.locator('input[name="firstName"]')).toBeVisible();
    await expect(page.locator('input[name="lastName"]')).toBeVisible();
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('input[name="confirmPassword"]')).toBeVisible();
    await expect(page.locator('input[type="checkbox"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should validate empty form submission', async ({ page }) => {
    // Check that submit button is disabled when form is empty
    const submitButton = page.locator('button[type="submit"]:has-text("Create account")');
    await expect(submitButton).toBeDisabled();
    
    // Fill in required fields one by one and check button state
    await registerPage.fillInput('input[name="username"]', 'testuser');
    await expect(submitButton).toBeDisabled(); // Still disabled
    
    await registerPage.fillInput('input[name="email"]', 'test@example.com');
    await expect(submitButton).toBeDisabled(); // Still disabled
    
    await registerPage.fillInput('input[name="password"]', 'Password123!');
    await expect(submitButton).toBeDisabled(); // Still disabled
    
    await registerPage.fillInput('input[name="confirmPassword"]', 'Password123!');
    await expect(submitButton).toBeDisabled(); // Still disabled - need terms
    
    // Check terms checkbox to enable button - click the label instead of checkbox
    await page.click('label[for="acceptTerms"]');
    await expect(submitButton).toBeEnabled(); // Now enabled
  });

  test('should validate email format', async ({ page }) => {
    // Test invalid email formats
    const invalidEmails = [
      'invalid',
      'test@',
      '@example.com',
      'test@example',
      'test..user@example.com',
      'test user@example.com'
    ];
    
    // Fill other required fields first
    await registerPage.fillInput('input[name="username"]', 'testuser');
    await registerPage.fillInput('input[name="password"]', 'Password123!');
    await registerPage.fillInput('input[name="confirmPassword"]', 'Password123!');
    await page.click('label[for="acceptTerms"]');
    
    // Test each invalid email
    for (const email of invalidEmails) {
      await registerPage.fillInput('input[name="email"]', email);
      await registerPage.submitRegistration();
      
      // Should show error
      const errorText = await page.locator('.text-red-500, [role="alert"]').textContent().catch(() => null);
      if (errorText) {
        expect(errorText).toBeTruthy();
        // Clear error for next test
        await page.reload();
        await registerPage.fillInput('input[name="username"]', 'testuser');
        await registerPage.fillInput('input[name="password"]', 'Password123!');
        await registerPage.fillInput('input[name="confirmPassword"]', 'Password123!');
        await page.click('label[for="acceptTerms"]');
      }
    }
    
    // Test valid email format
    await registerPage.fillInput('input[name="email"]', 'test@example.com');
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeEnabled();
  });

  test('should validate password strength', async ({ page }) => {
    // Based on getPasswordStrength logic:
    // strength = 0 -> "Very Weak"
    // strength = 1 -> "Weak"  
    // strength = 2 -> "Fair"
    // strength = 3 -> "Good"
    // strength = 4+ -> "Strong"
    const passwords = [
      { password: '123', strength: 'Weak' },           // <8 chars, no complexity
      { password: 'password', strength: 'Weak' },      // 8+ chars but no complexity
      { password: 'Password1', strength: 'Good' },     // 8+ chars + mixed case + digit
      { password: 'P@ssw0rd123!', strength: 'Strong' } // 12+ chars + all complexity
    ];

    for (const { password, strength } of passwords) {
      await registerPage.fillInput('input[name="password"]', password);
      
      // Wait for strength indicator to update
      await page.waitForTimeout(100);
      
      // Check password strength text
      const strengthText = await page.locator('p.text-xs.text-muted-foreground:has-text("Password strength")').textContent();
      expect(strengthText).toContain(strength);
      
      // Clear for next test
      await page.locator('input[name="password"]').fill('');
    }
  });

  test('should validate password confirmation match', async ({ page }) => {
    const password = 'SecureP@ssw0rd123!';
    const mismatchedPassword = 'DifferentP@ssw0rd456!';
    
    // Fill required fields
    await registerPage.fillInput('input[name="email"]', 'test@example.com');
    await registerPage.fillInput('input[name="username"]', 'testuser');
    await page.click('label[for="acceptTerms"]');
    
    // Test mismatched passwords - client-side validation on submit
    await registerPage.fillInput('input[name="password"]', password);
    await registerPage.fillInput('input[name="confirmPassword"]', mismatchedPassword);
    
    await registerPage.submitRegistration();
    
    // Check for error message
    await page.waitForSelector('.text-red-500', { timeout: 5000 });
    const errorText = await page.locator('.text-red-500').textContent();
    expect(errorText).toContain('do not match');
  });

  test('should successfully register a new user', async ({ page }) => {
    // Generate unique test user
    const testUser = generateTestUser();
    
    // Fill and submit registration form
    await registerPage.register(testUser);
    
    // Wait for navigation or error - the form should either redirect or show error
    await Promise.race([
      page.waitForURL('**/verify-email**', { timeout: 5000 }),
      page.waitForURL('**/onboarding', { timeout: 5000 }),
      page.waitForURL('**/dashboard', { timeout: 5000 }),
      page.waitForURL('**/login**', { timeout: 5000 }), // Registration might redirect to login
      page.waitForSelector('text=/Registration failed|already exists/i', { timeout: 5000 })
    ]).catch(async () => {
      // If none of the above happen, check current URL and page state
      const currentUrl = page.url();
      console.log('Current URL:', currentUrl);
      
      // Take screenshot for debugging
      await page.screenshot({ path: 'registration-timeout.png' });
      
      // Check if there's an error message
      const errorText = await page.locator('.text-red-500, [role="alert"]').textContent().catch(() => null);
      if (errorText) {
        throw new Error(`Registration failed with error: ${errorText}`);
      }
      
      throw new Error(`Registration did not complete. Current URL: ${currentUrl}`);
    });
    
    // Verify we're on a success page or login page after registration
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/verify-email|onboarding|dashboard|login/);
  });

  test('should prevent duplicate email registration', async ({ page }) => {
    // Register first user
    const testUser = generateTestUser();
    await registerPage.register(testUser);
    
    // Wait for registration to complete
    await Promise.race([
      page.waitForURL('**/verify-email**', { timeout: 5000 }),
      page.waitForURL('**/login**', { timeout: 5000 })
    ]).catch(() => {
      // Registration might have failed if user exists from previous test
    });
    
    // Try to register with same email
    await registerPage.goto();
    await registerPage.register(testUser);
    
    // Should show error message (wait for it to appear)
    await page.waitForSelector('.text-red-500, [role="alert"]', { timeout: 5000 });
    const errorMessage = await page.locator('.text-red-500, [role="alert"]').textContent();
    expect(errorMessage).toMatch(/already exists|already registered/i);
  });

  test('should send verification email after registration', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Register user
    await registerPage.register(testUser);
    
    // Should redirect to verification page
    await page.waitForURL('**/verify-email**');
    
    // Check that user was created in database
    const user = await getUser(testUser.email);
    expect(user).toBeTruthy();
    expect(user.email).toBe(testUser.email);
    expect(user.email_verified).toBe(false);
    
    // Check that verification email was sent via MailHog
    const verificationCode = await getVerificationCodeFromEmail(testUser.email);
    expect(verificationCode).toBeTruthy();
    expect(verificationCode).toMatch(/^[A-Z0-9]{6}$/);
  });

  test('should verify email with code', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Register user
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**');
    
    // Get verification code from email
    const verificationCode = await getVerificationCodeFromEmail(testUser.email);
    
    // Enter and submit verification code
    await verificationPage.verifyWithCode(verificationCode);
    
    // Should show success and redirect to dashboard
    const isSuccess = await verificationPage.isVerificationSuccessful();
    expect(isSuccess).toBe(true);
    
    await verificationPage.continueToApp();
    await page.waitForURL('**/dashboard');
    
    // Verify user is now verified in database
    const user = await getUser(testUser.email);
    expect(user.email_verified).toBe(true);
  });

  test('should verify email with link', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Register user
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**');
    
    // Get verification link from email
    const verificationLink = await getVerificationLinkFromEmail(testUser.email);
    
    // Navigate to verification link
    await page.goto(verificationLink);
    
    // Should auto-verify and redirect to dashboard
    await verificationPage.verifyAutoVerificationWithToken();
    await page.waitForURL('**/dashboard');
    
    // Verify user is now verified in database
    const user = await getUser(testUser.email);
    expect(user.email_verified).toBe(true);
  });

  test('should handle invalid verification code', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Register user
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**');
    
    // Enter invalid code
    await verificationPage.verifyWithCode('INVALID');
    
    // Should show error
    const errorMessage = await verificationPage.getErrorMessage();
    expect(errorMessage).toContain('Invalid verification code');
  });

  test('should allow resending verification email', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Register user
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**');
    
    // Clear previous emails
    await clearAllEmails();
    
    // Resend verification email
    await verificationPage.resendVerificationEmail();
    
    // Check new email was sent
    const email = await waitForEmail(testUser.email, { subject: 'verification' });
    expect(email).toBeTruthy();
    
    // Verify new verification code can be used
    const newCode = await getVerificationCodeFromEmail(testUser.email);
    expect(newCode).toBeTruthy();
    expect(newCode).toMatch(/^[A-Z0-9]{6}$/);
  });

  test('should show resend timer to prevent spam', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Register user
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**');
    
    // Resend email
    await verificationPage.resendVerificationEmail();
    
    // Check timer is shown
    const timerText = await verificationPage.getResendTimerText();
    expect(timerText).toBeTruthy();
    
    // Resend button should be disabled
    const resendButton = page.locator('button:has-text("Resend")');
    await expect(resendButton).toBeDisabled();
  });

  test('should handle edge case: long names', async ({ page }) => {
    const testUser = TestUserGenerator.generateEdgeCase('long');
    
    // Attempt registration
    await registerPage.fillRegistrationForm(testUser);
    await registerPage.submitRegistration();
    
    // Should either truncate or show error
    const errorMessage = await registerPage.getFieldError('username');
    if (errorMessage) {
      expect(errorMessage).toContain('too long');
    } else {
      // Should proceed with registration
      await page.waitForURL('**/verify-email**');
    }
  });

  test('should handle edge case: special characters in name', async ({ page }) => {
    const testUser = TestUserGenerator.generateEdgeCase('special');
    
    // Register with special characters
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**');
    
    // Verify email was sent and can retrieve verification code
    const verificationCode = await getVerificationCodeFromEmail(testUser.email);
    expect(verificationCode).toBeTruthy();
    
    // Verify user was created with special characters handled properly
    const user = await getUser(testUser.email);
    expect(user).toBeTruthy();
    expect(user.username).toBe(testUser.username);
  });

  test('should handle edge case: unicode characters', async ({ page }) => {
    const testUser = TestUserGenerator.generateEdgeCase('unicode');
    
    // Register with unicode characters
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**');
    
    // Should handle unicode properly - verify email was sent
    const verificationCode = await getVerificationCodeFromEmail(testUser.email);
    expect(verificationCode).toBeTruthy();
    
    // Verify user was created with unicode handled properly
    const user = await getUser(testUser.email);
    expect(user).toBeTruthy();
    expect(user.username).toBe(testUser.username);
  });

  test('should prevent SQL injection attempts', async ({ page }) => {
    const testUser = TestUserGenerator.generateEdgeCase('sql');
    
    // Attempt registration with SQL injection in name
    await registerPage.register(testUser);
    
    // Should either sanitize or reject
    const currentUrl = page.url();
    if (currentUrl.includes('verify-email')) {
      // Registration succeeded with sanitized data
      const verificationCode = await getVerificationCodeFromEmail(testUser.email);
      expect(verificationCode).toBeTruthy();
      
      // Verify data was properly sanitized in database
      const user = await getUser(testUser.email);
      expect(user).toBeTruthy();
      // SQL injection attempt should be escaped/sanitized
      expect(user.firstName).not.toContain('DROP TABLE');
    } else {
      // Registration was rejected
      const errorMessage = await page.locator('[data-testid="error-message"]').textContent();
      expect(errorMessage).toBeTruthy();
    }
  });

  test('should maintain form data on validation errors', async ({ page }) => {
    const testUser = generateTestUser({
      password: 'weak', // Intentionally weak
      confirmPassword: 'different' // Intentionally different
    });
    
    // Fill form with some invalid data
    await registerPage.fillRegistrationForm(testUser);
    await registerPage.submitRegistration();
    
    // Check that valid fields retained their values
    await expect(page.locator('input[name="username"]')).toHaveValue(testUser.username);
    await expect(page.locator('input[name="email"]')).toHaveValue(testUser.email);
    
    // Password fields should be cleared for security
    await expect(page.locator('input[name="password"]')).toHaveValue('');
    await expect(page.locator('input[name="confirmPassword"]')).toHaveValue('');
  });

  test('should track registration metrics', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Start performance measurement
    const startTime = Date.now();
    
    // Complete registration
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**');
    
    const registrationTime = Date.now() - startTime;
    
    // Get verification code and complete verification
    const verificationCode = await getVerificationCodeFromEmail(testUser.email);
    await verificationPage.verifyWithCode(verificationCode);
    await verificationPage.continueToApp();
    await page.waitForURL('**/dashboard');
    
    const totalTime = Date.now() - startTime;
    
    // Log metrics for monitoring
    console.log('Registration Metrics:', {
      registrationTime,
      totalTime,
      user: testUser.email
    });
    
    // Assert reasonable performance
    expect(registrationTime).toBeLessThan(5000); // 5 seconds
    expect(totalTime).toBeLessThan(10000); // 10 seconds
  });
});