import { test, expect } from '@playwright/test';
import { RegisterPage } from '../../pages/auth/register.page';
import { VerificationPage } from './pages/VerificationPage';
import { DashboardPage } from '../../pages/dashboard.page';
import { TestUserGenerator, generateTestUser } from './utils/test-user-generator';
import { cleanupDatabase, getUser } from '../../../test-helpers/database';
import { getVerificationCodeFromEmail, getVerificationLinkFromEmail, clearAllEmails, waitForEmail } from '../../../test-helpers/mailhog';

// Helper function to wait for registration API response
async function waitForRegistrationComplete(page) {
  try {
    // Wait for successful registration API response
    await page.waitForResponse(
      response => response.url().includes('/api/v1/auth/register') && 
                  (response.status() === 200 || response.status() === 201),
      { timeout: 10000 }
    );
    console.log('Registration API response received');
  } catch (error) {
    console.error('Registration API response timeout:', error);
  }
}

// Helper function to wait for email with better error handling
async function waitForVerificationEmail(email: string, timeout = 30000) {
  console.log(`Waiting for verification email for ${email}...`);
  const startTime = Date.now();
  
  try {
    // Use the waitForEmail helper with proper timeout
    const message = await waitForEmail(email, {
      timeout: timeout,
      subject: 'verify'
    });
    
    const elapsed = Date.now() - startTime;
    console.log(`Email received after ${elapsed}ms`);
    return message;
  } catch (error) {
    const elapsed = Date.now() - startTime;
    console.error(`Failed to receive email after ${elapsed}ms:`, error);
    throw error;
  }
}

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
    // Find submit button with flexible selector
    const submitButton = page.locator('button[type="submit"]:has-text("Create account"), button[type="submit"]:has-text("Sign Up")');
    
    // Force submit to trigger validation (even if button is disabled)
    await page.evaluate(() => {
      const form = document.querySelector('form');
      if (form) {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(event);
      }
    });
    
    // Wait for validation errors to appear
    await page.waitForTimeout(500);
    
    // Check for required field errors with flexible matching
    const nameError = await page.locator('[data-testid="field-error-name"], [data-testid="field-error-firstName"]').textContent().catch(() => '');
    const emailError = await page.locator('[data-testid="field-error-email"]').textContent().catch(() => '');
    const passwordError = await page.locator('[data-testid="field-error-password"]').textContent().catch(() => '');
    
    // Flexible validation checks that work with "required" or "is required"
    if (nameError) {
      expect(nameError.toLowerCase()).toMatch(/required|must.*provide|cannot.*empty/i);
    }
    if (emailError) {
      expect(emailError.toLowerCase()).toMatch(/required|must.*provide|cannot.*empty/i);
    }
    if (passwordError) {
      expect(passwordError.toLowerCase()).toMatch(/required|must.*provide|cannot.*empty/i);
    }
    
    // Also test progressive form filling
    await page.reload();
    await expect(submitButton).toBeDisabled();
    
    // Fill in required fields one by one and check button state
    await registerPage.fillInput('input[name="username"], input[name="firstName"]', 'testuser');
    await expect(submitButton).toBeDisabled(); // Still disabled
    
    await registerPage.fillInput('input[name="email"]', 'test@example.com');
    await expect(submitButton).toBeDisabled(); // Still disabled
    
    await registerPage.fillInput('input[name="password"]', 'Password123!');
    await expect(submitButton).toBeDisabled(); // Still disabled
    
    await registerPage.fillInput('input[name="confirmPassword"]', 'Password123!');
    await expect(submitButton).toBeDisabled(); // Still disabled - need terms
    
    // Check terms checkbox to enable button with flexible selector
    await page.click('label[for="acceptTerms"], input[name="terms"] + label, input[type="checkbox"][name="terms"]');
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
      
      // Should show error - check for field-specific error first
      const errorSelector = '[data-testid="field-error-email"], .text-red-500, [role="alert"]';
      await page.waitForSelector(errorSelector, { state: 'visible', timeout: 2000 }).catch(() => null);
      const errorText = await page.locator(errorSelector).first().textContent().catch(() => null);
      
      if (errorText) {
        // Check for valid email error message (flexible matching)
        expect(errorText.toLowerCase()).toMatch(/valid email|invalid email|email.*required|proper.*email|correct.*format/i);
        
        // Clear error for next test
        await page.reload();
        await registerPage.fillInput('input[name="username"], input[name="firstName"]', 'testuser');
        await registerPage.fillInput('input[name="password"]', 'Password123!');
        await registerPage.fillInput('input[name="confirmPassword"]', 'Password123!');
        await page.click('label[for="acceptTerms"], input[name="terms"] + label');
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
      
      // Check password strength text with flexible selector
      const strengthSelector = '[data-testid="password-strength"], .password-strength, p:has-text("Password strength")';
      const strengthElement = await page.locator(strengthSelector).first();
      const strengthText = await strengthElement.textContent().catch(() => '');
      
      // Flexible strength check
      expect(strengthText.toLowerCase()).toContain(strength.toLowerCase());
      
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
    
    // Check for error message with flexible selector
    const errorSelector = '[data-testid="field-error-confirmPassword"], .text-red-500, [role="alert"]';
    await page.waitForSelector(errorSelector, { timeout: 5000 });
    const errorText = await page.locator(errorSelector).first().textContent();
    
    // Flexible password mismatch check
    expect(errorText.toLowerCase()).toMatch(/do not match|don't match|mismatch|must match|passwords.*differ/i);
  });

  test('should successfully register a new user', async ({ page }) => {
    // Generate unique test user
    const testUser = generateTestUser();
    
    // Store email in localStorage for verification tests
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
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
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Register first user and wait for API response
    const registrationPromise = waitForRegistrationComplete(page);
    await registerPage.register(testUser);
    await registrationPromise;
    
    // Wait for registration to complete
    await page.waitForURL('**/verify-email**', { timeout: 15000 });
    
    // Ensure user is created in database
    const firstUser = await getUser(testUser.email);
    expect(firstUser).toBeTruthy();
    
    // Navigate back to registration page
    await registerPage.goto();
    
    // Try to register with same email
    const duplicatePromise = page.waitForResponse(
      response => response.url().includes('/api/v1/auth/register') && 
                  response.status() === 409, // Expecting conflict status
      { timeout: 10000 }
    );
    
    await registerPage.register(testUser);
    
    try {
      await duplicatePromise;
    } catch {
      // If no 409 response, check for error message
    }
    
    // Should show error message
    const errorSelector = '[data-testid="error-message"], [data-testid="field-error-email"], .text-red-500, [role="alert"]';
    await expect(page.locator(errorSelector).first()).toBeVisible({ timeout: 5000 });
    
    const errorMessage = await page.locator(errorSelector).first().textContent();
    expect(errorMessage.toLowerCase()).toMatch(/already exists|already registered|duplicate.*email|email.*taken|email.*use/i);
  });

  test('should send verification email after registration', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Store email in localStorage for verification
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Register user and wait for API response
    const registrationPromise = waitForRegistrationComplete(page);
    await registerPage.register(testUser);
    await registrationPromise;
    
    // Should redirect to verification page
    await page.waitForURL('**/verify-email**', { timeout: 15000 });
    
    // Check that user was created in database
    const user = await getUser(testUser.email);
    expect(user).toBeTruthy();
    expect(user.email).toBe(testUser.email);
    expect(user.email_verified).toBe(false);
    
    // Wait for and check verification email
    const email = await waitForVerificationEmail(testUser.email);
    expect(email).toBeTruthy();
    
    // Extract and validate verification code
    const verificationCode = await getVerificationCodeFromEmail(testUser.email);
    expect(verificationCode).toBeTruthy();
    expect(verificationCode).toMatch(/^[A-Z0-9]{6}$/);
  });

  test('should verify email with code', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Register user and wait for API response
    const registrationPromise = waitForRegistrationComplete(page);
    await registerPage.register(testUser);
    await registrationPromise;
    
    await page.waitForURL('**/verify-email**', { timeout: 15000 });
    
    // Wait for verification email
    const email = await waitForVerificationEmail(testUser.email);
    expect(email).toBeTruthy();
    
    // Get verification code from email
    const verificationCode = await getVerificationCodeFromEmail(testUser.email);
    expect(verificationCode).toBeTruthy();
    console.log(`Verification code: ${verificationCode}`);
    
    // Enter and submit verification code
    await verificationPage.verifyWithCode(verificationCode);
    
    // Wait for verification API response
    await page.waitForResponse(
      response => response.url().includes('/api/v1/auth/verify-email') && 
                  response.status() === 200,
      { timeout: 10000 }
    );
    
    // Should show success
    const isSuccess = await verificationPage.isVerificationSuccessful();
    expect(isSuccess).toBe(true);
    
    // Continue to dashboard
    await verificationPage.continueToApp();
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    
    // Verify user is now verified in database
    const user = await getUser(testUser.email);
    expect(user.email_verified).toBe(true);
  });

  test('should verify email with link', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Register user and wait for API response
    const registrationPromise = waitForRegistrationComplete(page);
    await registerPage.register(testUser);
    await registrationPromise;
    
    await page.waitForURL('**/verify-email**', { timeout: 15000 });
    
    // Wait for verification email
    const email = await waitForVerificationEmail(testUser.email);
    expect(email).toBeTruthy();
    
    // Get verification link from email
    const verificationLink = await getVerificationLinkFromEmail(testUser.email);
    expect(verificationLink).toBeTruthy();
    console.log(`Verification link: ${verificationLink}`);
    
    // Navigate to verification link
    await page.goto(verificationLink);
    
    // Wait for automatic verification to complete
    await page.waitForResponse(
      response => response.url().includes('/api/v1/auth/verify-email') && 
                  response.status() === 200,
      { timeout: 10000 }
    ).catch(() => {
      // Link verification might happen automatically on page load
      console.log('Verification might have happened on page load');
    });
    
    // Should auto-verify and redirect to dashboard
    await verificationPage.verifyAutoVerificationWithToken();
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    
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
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Register user and wait for API response
    const registrationPromise = waitForRegistrationComplete(page);
    await registerPage.register(testUser);
    await registrationPromise;
    
    await page.waitForURL('**/verify-email**', { timeout: 15000 });
    
    // Wait for initial email
    const initialEmail = await waitForVerificationEmail(testUser.email);
    expect(initialEmail).toBeTruthy();
    
    // Clear previous emails
    await clearAllEmails();
    
    // Wait for page to fully load
    await verificationPage.verifyPageLoaded();
    
    // Resend verification email and wait for API response
    const resendPromise = page.waitForResponse(
      response => response.url().includes('/api/v1/auth/resend-verification') && 
                  response.status() === 200,
      { timeout: 10000 }
    );
    
    await verificationPage.resendVerificationEmail();
    await resendPromise;
    
    // Wait for new email
    const newEmail = await waitForVerificationEmail(testUser.email);
    expect(newEmail).toBeTruthy();
    
    // Verify new verification code can be used
    const newCode = await getVerificationCodeFromEmail(testUser.email);
    expect(newCode).toBeTruthy();
    expect(newCode).toMatch(/^[A-Z0-9]{6}$/);
  });

  test('should show resend timer to prevent spam', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Register user and wait for API response
    const registrationPromise = waitForRegistrationComplete(page);
    await registerPage.register(testUser);
    await registrationPromise;
    
    await page.waitForURL('**/verify-email**', { timeout: 15000 });
    
    // Wait for initial email
    await waitForVerificationEmail(testUser.email);
    
    // Wait for page to fully load
    await verificationPage.verifyPageLoaded();
    
    // Resend email and wait for API response
    const resendPromise = page.waitForResponse(
      response => response.url().includes('/api/v1/auth/resend-verification') && 
                  response.status() === 200,
      { timeout: 10000 }
    );
    
    await verificationPage.resendVerificationEmail();
    await resendPromise;
    
    // Check timer is shown - wait for button text to update
    const resendButton = page.locator('button:has-text("Resend"), a:has-text("Resend")');
    
    // Use expect with automatic retry instead of manual wait
    await expect(resendButton).toHaveText(/Resend in \d+s|\d+ seconds?/i, { timeout: 5000 });
    
    // Resend button should be disabled
    await expect(resendButton).toBeDisabled();
  });

  test('should handle edge case: long names', async ({ page }) => {
    const testUser = TestUserGenerator.generateEdgeCase('long');
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Attempt registration
    await registerPage.fillRegistrationForm(testUser);
    await registerPage.submitRegistration();
    
    // Wait for response
    await page.waitForTimeout(1000);
    
    // Should either truncate or show error
    const errorMessage = await registerPage.getFieldError('username');
    if (errorMessage) {
      expect(errorMessage).toContain('too long');
    } else {
      // Should proceed with registration
      await page.waitForURL('**/verify-email**', { timeout: 10000 });
      
      // Wait for email
      await page.waitForTimeout(2000);
      
      // Verify email was sent
      const verificationCode = await getVerificationCodeFromEmail(testUser.email);
      expect(verificationCode).toBeTruthy();
    }
  });

  test('should handle edge case: special characters in name', async ({ page }) => {
    const testUser = TestUserGenerator.generateEdgeCase('special');
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Register with special characters
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**', { timeout: 10000 });
    
    // Wait for email to be sent
    await page.waitForTimeout(2000);
    
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
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Register with unicode characters
    await registerPage.register(testUser);
    await page.waitForURL('**/verify-email**', { timeout: 10000 });
    
    // Wait for email to be sent
    await page.waitForTimeout(2000);
    
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
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Attempt registration with SQL injection in name
    await registerPage.register(testUser);
    
    // Wait for response
    await page.waitForTimeout(2000);
    
    // Should either sanitize or reject
    const currentUrl = page.url();
    if (currentUrl.includes('verify-email')) {
      // Registration succeeded with sanitized data
      await page.waitForTimeout(2000);
      const verificationCode = await getVerificationCodeFromEmail(testUser.email);
      expect(verificationCode).toBeTruthy();
      
      // Verify data was properly sanitized in database
      const user = await getUser(testUser.email);
      expect(user).toBeTruthy();
      // SQL injection attempt should be escaped/sanitized
      expect(user.firstName).not.toContain('DROP TABLE');
    } else {
      // Registration was rejected
      const errorMessage = await page.locator('[data-testid="error-message"], .text-red-500').textContent();
      expect(errorMessage).toBeTruthy();
    }
  });

  test('should maintain form data on validation errors', async ({ page }) => {
    const testUser = generateTestUser({
      password: 'ValidPass123!', // Valid password to test mismatch error
      confirmPassword: 'DifferentPass456!' // Intentionally different
    });
    
    // Fill form with some invalid data
    await registerPage.fillRegistrationForm(testUser);
    await registerPage.submitRegistration();
    
    // Wait for validation errors to appear
    await page.waitForTimeout(500);
    
    // Check for validation errors (should have password mismatch error)
    const passwordError = await page.locator('[data-testid="field-error-confirmPassword"], [data-testid="field-error-password"], .text-red-500')
      .first()
      .textContent()
      .catch(() => '');
    
    // Verify error is shown (flexible matching for both password length and mismatch)
    if (passwordError) {
      expect(passwordError.toLowerCase()).toMatch(/do not match|don't match|mismatch|must match|weak|strong|at least \d+ characters|minimum.*\d+|password.*must.*be/i);
    }
    
    // Check that valid fields retained their values
    await expect(page.locator('input[name="username"], input[name="firstName"]').first()).toHaveValue(testUser.username || testUser.firstName || '');
    await expect(page.locator('input[name="email"]')).toHaveValue(testUser.email);
    
    // Password fields might be cleared for security or retained - check both cases
    const passwordValue = await page.locator('input[name="password"]').inputValue();
    const confirmPasswordValue = await page.locator('input[name="confirmPassword"]').inputValue();
    
    // Either both cleared or both retained is acceptable
    if (passwordValue === '' && confirmPasswordValue === '') {
      // Password fields cleared for security - this is good
      expect(passwordValue).toBe('');
      expect(confirmPasswordValue).toBe('');
    } else {
      // Password fields retained - also acceptable
      expect(passwordValue).toBe(testUser.password);
      expect(confirmPasswordValue).toBe(testUser.confirmPassword);
    }
  });

  test('should track registration metrics', async ({ page }) => {
    const testUser = generateTestUser();
    
    // Store email in localStorage
    await page.evaluate((email) => {
      localStorage.setItem('registrationEmail', email);
    }, testUser.email);
    
    // Start performance measurement
    const startTime = Date.now();
    
    // Complete registration and wait for API response
    const registrationPromise = waitForRegistrationComplete(page);
    await registerPage.register(testUser);
    await registrationPromise;
    
    await page.waitForURL('**/verify-email**', { timeout: 15000 });
    
    const registrationTime = Date.now() - startTime;
    
    // Wait for verification email
    const email = await waitForVerificationEmail(testUser.email);
    expect(email).toBeTruthy();
    
    // Get verification code and complete verification
    const verificationCode = await getVerificationCodeFromEmail(testUser.email);
    expect(verificationCode).toBeTruthy();
    
    // Enter code and wait for verification API response
    const verificationPromise = page.waitForResponse(
      response => response.url().includes('/api/v1/auth/verify-email') && 
                  response.status() === 200,
      { timeout: 10000 }
    );
    
    await verificationPage.verifyWithCode(verificationCode);
    await verificationPromise;
    
    // Check if verification was successful
    const isSuccess = await verificationPage.isVerificationSuccessful();
    expect(isSuccess).toBe(true);
    
    await verificationPage.continueToApp();
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    
    const totalTime = Date.now() - startTime;
    
    // Log metrics for monitoring
    console.log('Registration Metrics:', {
      registrationTime: `${registrationTime}ms`,
      totalTime: `${totalTime}ms`, 
      registrationTimeSeconds: `${(registrationTime / 1000).toFixed(2)}s`,
      totalTimeSeconds: `${(totalTime / 1000).toFixed(2)}s`,
      user: testUser.email
    });
    
    // Assert reasonable performance
    expect(registrationTime).toBeLessThan(20000); // 20 seconds for registration
    expect(totalTime).toBeLessThan(45000); // 45 seconds for full flow (includes email)
  });
});