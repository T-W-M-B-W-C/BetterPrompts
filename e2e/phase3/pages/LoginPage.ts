import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

/**
 * Enhanced Login Page Object Model
 * Comprehensive login functionality and validation
 */
export class LoginPage extends BasePage {
  // Locators
  private readonly emailInput = 'input#email[name="email"], input[name="email"], input[type="email"]';
  private readonly passwordInput = 'input#password[name="password"], input[name="password"], input[type="password"]';
  private readonly submitButton = 'button[type="submit"]:has-text("Sign in"), button[type="submit"]:has-text("Log In"), button[type="submit"]:has-text("Sign In")';
  private readonly rememberMeCheckbox = '[role="checkbox"]#rememberMe, input#rememberMe[type="checkbox"], input[type="checkbox"][name="remember"], input[type="checkbox"][name="rememberMe"]';
  private readonly forgotPasswordLink = 'a:has-text("Forgot password"), a:has-text("Forgot Password")';
  private readonly signUpLink = 'a:has-text("Sign up"), a:has-text("Create account")';
  private readonly errorMessage = '[data-testid="error-message"], [role="alert"], .error-message, div[role="alert"]';
  private readonly successMessage = '[data-testid="success-message"], .success-message';
  private readonly loadingSpinner = '[data-testid="loading-spinner"], .spinner, .loading';
  
  // OAuth buttons
  private readonly googleButton = 'button:has-text("Continue with Google"), button:has-text("Sign in with Google")';
  private readonly githubButton = 'button:has-text("Continue with GitHub"), button:has-text("Sign in with GitHub")';
  
  // Form validation
  private readonly emailError = '[data-testid="email-error"], #email-error';
  private readonly passwordError = '[data-testid="password-error"], #password-error';
  private readonly generalError = '[data-testid="general-error"], .form-error';
  
  // Security elements
  private readonly captchaContainer = '[data-testid="captcha"], .g-recaptcha';
  private readonly twoFactorInput = 'input[name="code"], input[name="totp"]';
  private readonly rateLimitMessage = '[data-testid="rate-limit-message"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to login page
   */
  async goto() {
    await super.goto('/login');
    await this.waitForPageLoad();
    await this.verifyPageLoaded();
  }

  /**
   * Verify login page loaded completely
   */
  async verifyPageLoaded() {
    await this.waitForElement(this.emailInput);
    await this.waitForElement(this.passwordInput);
    await this.waitForElement(this.submitButton);
    
    // Verify no loading state
    const isLoading = await this.page.locator(this.loadingSpinner).isVisible().catch(() => false);
    expect(isLoading).toBe(false);
  }

  /**
   * Fill login form with credentials
   */
  async fillLoginForm(credentials: LoginCredentials) {
    await this.clearAndFillInput(this.emailInput, credentials.email);
    await this.clearAndFillInput(this.passwordInput, credentials.password);
    
    if (credentials.rememberMe !== undefined) {
      await this.setRememberMe(credentials.rememberMe);
    }
  }

  /**
   * Clear and fill input (handles autofill issues)
   */
  private async clearAndFillInput(selector: string, value: string) {
    const input = this.page.locator(selector);
    await input.click();
    await input.clear();
    await input.fill(value);
    
    // Verify value was set
    await expect(input).toHaveValue(value);
  }

  /**
   * Submit login form and wait for response
   */
  async submitLogin() {
    // Wait for any pending API calls
    await this.waitForNetworkIdle();
    
    // Submit form
    const responsePromise = this.page.waitForResponse(
      resp => resp.url().includes('/api/v1/auth/login') || resp.url().includes('/auth/login'),
      { timeout: 10000 }
    );
    
    await this.clickWithRetry(this.submitButton);
    
    return await responsePromise;
  }

  /**
   * Complete login flow with response validation
   */
  async login(credentials: LoginCredentials) {
    await this.fillLoginForm(credentials);
    const response = await this.submitLogin();
    
    return {
      status: response.status(),
      data: await response.json().catch(() => null)
    };
  }

  /**
   * Set remember me checkbox state
   */
  async setRememberMe(checked: boolean) {
    const checkbox = this.page.locator(this.rememberMeCheckbox);
    const isChecked = await checkbox.isChecked();
    
    if (isChecked !== checked) {
      await checkbox.click();
    }
    
    // Verify state
    await expect(checkbox).toBeChecked({ checked });
  }

  /**
   * Get current remember me state
   */
  async getRememberMeState(): Promise<boolean> {
    return await this.page.locator(this.rememberMeCheckbox).isChecked();
  }

  /**
   * Click forgot password link
   */
  async clickForgotPassword() {
    await this.clickWithRetry(this.forgotPasswordLink);
    await this.page.waitForURL('**/forgot-password', { timeout: 5000 });
  }

  /**
   * Navigate to sign up page
   */
  async navigateToSignUp() {
    await this.clickWithRetry(this.signUpLink);
    await this.page.waitForURL('**/signup', { timeout: 5000 });
  }

  /**
   * Get error message with fallback
   */
  async getErrorMessage(): Promise<string | null> {
    try {
      // Wait for any alert to be visible
      await this.page.waitForSelector('[role="alert"]', { state: 'visible', timeout: 5000 });
      
      // Get all alerts and find the one with actual text content
      const alerts = await this.page.locator('[role="alert"]').all();
      
      for (const alert of alerts) {
        const isVisible = await alert.isVisible();
        if (isVisible) {
          const text = await alert.textContent();
          if (text && text.trim() && !text.trim().match(/^\s*$/)) {
            return text.trim();
          }
        }
      }
      
      // If no alert has text, try the specific .text-red-500 or .text-destructive elements
      const errorElements = await this.page.locator('.text-red-500, .text-destructive').all();
      for (const element of errorElements) {
        const isVisible = await element.isVisible();
        if (isVisible) {
          const text = await element.textContent();
          if (text && text.trim()) {
            return text.trim();
          }
        }
      }
      
    } catch (error) {
      console.log('Error getting alert message:', error);
    }
    
    // Try specific field errors as fallback
    const specificError = await this.page.locator(this.emailError).textContent().catch(() => null) ||
                         await this.page.locator(this.passwordError).textContent().catch(() => null);
    
    if (specificError) return specificError.trim();
    
    // Try general error selectors as final fallback
    const generalError = await this.page.locator(this.errorMessage).textContent().catch(() => null);
    return generalError ? generalError.trim() : null;
  }

  /**
   * Get field-specific error
   */
  async getFieldError(field: 'email' | 'password'): Promise<string | null> {
    const selector = field === 'email' ? this.emailError : this.passwordError;
    const error = await this.page.locator(selector).textContent().catch(() => null);
    return error ? error.trim() : null;
  }

  /**
   * Check if error is displayed
   */
  async isErrorDisplayed(): Promise<boolean> {
    const errorLocator = this.page.locator(this.errorMessage);
    return await errorLocator.isVisible().catch(() => false);
  }

  /**
   * Check if rate limited
   */
  async isRateLimited(): Promise<boolean> {
    const rateLimitLocator = this.page.locator(this.rateLimitMessage);
    return await rateLimitLocator.isVisible().catch(() => false);
  }

  /**
   * Get rate limit message
   */
  async getRateLimitMessage(): Promise<string | null> {
    const message = await this.page.locator(this.rateLimitMessage).textContent().catch(() => null);
    return message ? message.trim() : null;
  }

  /**
   * Check if CAPTCHA is displayed
   */
  async isCaptchaDisplayed(): Promise<boolean> {
    return await this.page.locator(this.captchaContainer).isVisible().catch(() => false);
  }

  /**
   * Check if two-factor authentication is required
   */
  async isTwoFactorRequired(): Promise<boolean> {
    return await this.page.locator(this.twoFactorInput).isVisible().catch(() => false);
  }

  /**
   * Enter two-factor code
   */
  async enterTwoFactorCode(code: string) {
    await this.fillInput(this.twoFactorInput, code);
    await this.page.keyboard.press('Enter');
  }

  /**
   * Validate form shows proper validation
   */
  async validateEmptyForm() {
    await this.submitLogin();
    
    // Check for validation messages
    const emailError = await this.getFieldError('email');
    const passwordError = await this.getFieldError('password');
    
    return {
      emailRequired: emailError !== null && emailError.toLowerCase().includes('required'),
      passwordRequired: passwordError !== null && passwordError.toLowerCase().includes('required'),
      formSubmitted: false // Should not submit with empty fields
    };
  }

  /**
   * Test SQL injection in login fields
   */
  async testSQLInjection() {
    const injections = [
      "' OR '1'='1",
      "admin'--",
      "1' OR '1' = '1'",
      "'; DROP TABLE users;--",
      "' UNION SELECT * FROM users--"
    ];
    
    const results = [];
    
    for (const injection of injections) {
      await this.fillLoginForm({
        email: injection,
        password: injection
      });
      
      const response = await this.submitLogin();
      
      results.push({
        injection,
        status: response.status(),
        blocked: response.status() !== 200 && response.status() !== 201
      });
      
      // Clear form for next test
      await this.page.reload();
    }
    
    return results;
  }

  /**
   * Test XSS in error messages
   */
  async testXSSInErrorMessages() {
    const xssPayloads = [
      '<script>alert("XSS")</script>',
      '<img src=x onerror=alert("XSS")>',
      '"><script>alert(document.cookie)</script>',
      'javascript:alert("XSS")'
    ];
    
    for (const payload of xssPayloads) {
      await this.fillLoginForm({
        email: payload,
        password: 'test'
      });
      
      await this.submitLogin();
      
      // Check if script executed
      const alertDialog = this.page.locator('dialog');
      const hasAlert = await alertDialog.isVisible().catch(() => false);
      
      if (hasAlert) {
        throw new Error(`XSS vulnerability detected with payload: ${payload}`);
      }
    }
    
    return true; // No XSS detected
  }

  /**
   * Wait for successful login redirect
   */
  async waitForLoginSuccess(expectedUrl: string = '/dashboard') {
    await this.page.waitForURL(`**${expectedUrl}`, { timeout: 10000 });
    
    // Verify we're actually logged in
    const isLoggedIn = await this.page.evaluate(() => {
      return localStorage.getItem('access_token') !== null ||
             document.cookie.includes('access_token');
    });
    
    expect(isLoggedIn).toBe(true);
  }

  /**
   * Login with OAuth provider
   */
  async loginWithOAuth(provider: 'google' | 'github') {
    const button = provider === 'google' ? this.googleButton : this.githubButton;
    
    // Handle popup
    const [popup] = await Promise.all([
      this.page.waitForEvent('popup'),
      this.clickWithRetry(button)
    ]);
    
    // Wait for OAuth flow
    await popup.waitForLoadState();
    
    return popup;
  }

  /**
   * Check password visibility toggle
   */
  async togglePasswordVisibility(): Promise<boolean> {
    const toggleButton = this.page.locator('[data-testid="password-toggle"], button[aria-label*="password"]');
    const passwordInput = this.page.locator(this.passwordInput);
    
    await toggleButton.click();
    
    const inputType = await passwordInput.getAttribute('type');
    return inputType === 'text';
  }

  /**
   * Measure login performance
   */
  async measureLoginPerformance(credentials: LoginCredentials) {
    const startTime = Date.now();
    
    await this.fillLoginForm(credentials);
    
    const fillTime = Date.now() - startTime;
    
    const response = await this.submitLogin();
    const apiTime = Date.now() - startTime - fillTime;
    
    await this.waitForLoginSuccess();
    const totalTime = Date.now() - startTime;
    
    return {
      fillTime,
      apiTime,
      redirectTime: totalTime - fillTime - apiTime,
      totalTime,
      status: response.status()
    };
  }

  /**
   * Check browser password manager integration
   */
  async checkPasswordManagerIntegration() {
    const emailInput = this.page.locator(this.emailInput);
    const passwordInput = this.page.locator(this.passwordInput);
    
    // Check autocomplete attributes
    const emailAutocomplete = await emailInput.getAttribute('autocomplete');
    const passwordAutocomplete = await passwordInput.getAttribute('autocomplete');
    
    return {
      emailAutocomplete: emailAutocomplete || 'not set',
      passwordAutocomplete: passwordAutocomplete || 'not set',
      hasProperAttributes: emailAutocomplete === 'email' && 
                          (passwordAutocomplete === 'current-password' || passwordAutocomplete === 'password')
    };
  }
}