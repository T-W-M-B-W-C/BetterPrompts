import { Page } from '@playwright/test';
import { BasePage } from '../base.page';

/**
 * Register Page Object Model
 * New user registration flows
 */
export class RegisterPage extends BasePage {
  // Form field locators
  private readonly nameInput = 'input[name="name"]';
  private readonly emailInput = 'input[name="email"]';
  private readonly passwordInput = 'input[name="password"]';
  private readonly confirmPasswordInput = 'input[name="confirmPassword"]';
  private readonly termsCheckbox = 'input[type="checkbox"][name="terms"]';
  private readonly marketingCheckbox = 'input[type="checkbox"][name="marketing"]';
  private readonly submitButton = 'button[type="submit"]:has-text("Sign Up")';
  
  // Link locators
  private readonly loginLink = 'a:has-text("Log in")';
  private readonly termsLink = 'a:has-text("Terms of Service")';
  private readonly privacyLink = 'a:has-text("Privacy Policy")';
  
  // Message locators
  private readonly errorMessage = '[data-testid="error-message"]';
  private readonly successMessage = '[data-testid="success-message"]';
  private readonly fieldError = '[data-testid="field-error"]';
  
  // OAuth buttons
  private readonly googleButton = 'button:has-text("Sign up with Google")';
  private readonly githubButton = 'button:has-text("Sign up with GitHub")';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to register page
   */
  async goto() {
    await super.goto('/register');
    await this.waitForElement(this.emailInput);
  }

  /**
   * Fill registration form
   */
  async fillRegistrationForm(data: {
    name: string;
    email: string;
    password: string;
    confirmPassword?: string;
    acceptTerms?: boolean;
    acceptMarketing?: boolean;
  }) {
    await this.fillInput(this.nameInput, data.name);
    await this.fillInput(this.emailInput, data.email);
    await this.fillInput(this.passwordInput, data.password);
    await this.fillInput(this.confirmPasswordInput, data.confirmPassword || data.password);
    
    if (data.acceptTerms !== false) {
      await this.page.check(this.termsCheckbox);
    }
    
    if (data.acceptMarketing) {
      await this.page.check(this.marketingCheckbox);
    }
  }

  /**
   * Submit registration
   */
  async submitRegistration() {
    await this.clickWithRetry(this.submitButton);
  }

  /**
   * Complete registration flow
   */
  async register(data: {
    name: string;
    email: string;
    password: string;
    confirmPassword?: string;
  }) {
    await this.fillRegistrationForm({
      ...data,
      acceptTerms: true,
    });
    await this.submitRegistration();
  }

  /**
   * Navigate to login
   */
  async navigateToLogin() {
    await this.clickWithRetry(this.loginLink);
  }

  /**
   * Open terms of service
   */
  async openTerms() {
    const [newPage] = await Promise.all([
      this.page.context().waitForEvent('page'),
      this.page.click(this.termsLink),
    ]);
    return newPage;
  }

  /**
   * Open privacy policy
   */
  async openPrivacy() {
    const [newPage] = await Promise.all([
      this.page.context().waitForEvent('page'),
      this.page.click(this.privacyLink),
    ]);
    return newPage;
  }

  /**
   * Sign up with Google
   */
  async signUpWithGoogle() {
    await this.clickWithRetry(this.googleButton);
  }

  /**
   * Sign up with GitHub
   */
  async signUpWithGitHub() {
    await this.clickWithRetry(this.githubButton);
  }

  /**
   * Get field error message
   */
  async getFieldError(fieldName: string): Promise<string> {
    const fieldContainer = this.page.locator(`input[name="${fieldName}"]`).locator('..');
    const error = fieldContainer.locator(this.fieldError);
    return await error.textContent() || '';
  }

  /**
   * Check password strength indicator
   */
  async getPasswordStrength(): Promise<string> {
    const strengthIndicator = this.page.locator('[data-testid="password-strength"]');
    return await strengthIndicator.getAttribute('data-strength') || 'weak';
  }

  /**
   * Verify form validation
   */
  async verifyFormValidation() {
    // Submit empty form
    await this.submitRegistration();
    
    // Check for required field errors
    const nameError = await this.getFieldError('name');
    const emailError = await this.getFieldError('email');
    const passwordError = await this.getFieldError('password');
    const termsError = await this.page.locator(this.termsCheckbox).locator('..').locator(this.fieldError).isVisible();
    
    return {
      nameRequired: nameError.includes('required'),
      emailRequired: emailError.includes('required'),
      passwordRequired: passwordError.includes('required'),
      termsRequired: termsError,
    };
  }

  /**
   * Verify email validation
   */
  async verifyEmailValidation(email: string) {
    await this.fillInput(this.emailInput, email);
    await this.page.locator(this.passwordInput).click(); // Trigger blur
    const error = await this.getFieldError('email');
    return error.includes('valid email');
  }

  /**
   * Verify password match validation
   */
  async verifyPasswordMatch(password: string, confirmPassword: string) {
    await this.fillInput(this.passwordInput, password);
    await this.fillInput(this.confirmPasswordInput, confirmPassword);
    await this.page.locator(this.termsCheckbox).click(); // Trigger blur
    const error = await this.getFieldError('confirmPassword');
    return error.includes('match');
  }

  /**
   * Wait for registration success
   */
  async waitForRegistrationSuccess() {
    // Could redirect to email verification or dashboard
    await this.page.waitForURL(/(verify-email|dashboard|welcome)/, { timeout: 10000 });
  }

  /**
   * Verify page loaded
   */
  async verifyPageLoaded() {
    await this.expectToBeVisible(this.nameInput);
    await this.expectToBeVisible(this.emailInput);
    await this.expectToBeVisible(this.passwordInput);
    await this.expectToBeVisible(this.confirmPasswordInput);
    await this.expectToBeVisible(this.termsCheckbox);
    await this.expectToBeVisible(this.submitButton);
  }
}