import { Page } from '@playwright/test';
import { BasePage } from '../base.page';

/**
 * Register Page Object Model
 * New user registration flows
 */
export class RegisterPage extends BasePage {
  // Form field locators
  private readonly firstNameInput = 'input[name="firstName"]';
  private readonly lastNameInput = 'input[name="lastName"]';
  private readonly usernameInput = 'input[name="username"]';
  private readonly emailInput = 'input[name="email"]';
  private readonly passwordInput = 'input[name="password"]';
  private readonly confirmPasswordInput = 'input[name="confirmPassword"]';
  private readonly termsCheckbox = 'input[type="checkbox"]';
  private readonly submitButton = 'button[type="submit"]:has-text("Create account")';
  
  // Link locators
  private readonly loginLink = 'a:has-text("Sign in")';
  private readonly termsLink = 'a:has-text("Terms of Service")';
  private readonly privacyLink = 'a:has-text("Privacy Policy")';
  
  // Message locators
  private readonly errorMessage = '.text-red-500';
  private readonly generalError = '[role="alert"]';
  private readonly passwordStrengthText = '.text-xs.text-muted-foreground:has-text("Password strength")';

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
    firstName?: string;
    lastName?: string;
    username: string;
    email: string;
    password: string;
    confirmPassword?: string;
    acceptTerms?: boolean;
  }) {
    if (data.firstName) {
      await this.fillInput(this.firstNameInput, data.firstName);
    }
    if (data.lastName) {
      await this.fillInput(this.lastNameInput, data.lastName);
    }
    await this.fillInput(this.usernameInput, data.username);
    await this.fillInput(this.emailInput, data.email);
    await this.fillInput(this.passwordInput, data.password);
    await this.fillInput(this.confirmPasswordInput, data.confirmPassword || data.password);
    
    if (data.acceptTerms !== false) {
      await this.page.click('label[for="acceptTerms"]');
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
    username: string;
    email: string;
    password: string;
    confirmPassword?: string;
    firstName?: string;
    lastName?: string;
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
    // Errors are shown as <p> elements after the input field
    const field = this.page.locator(`input[name="${fieldName}"]`);
    const error = field.locator('~ p.text-red-500').first();
    const isVisible = await error.isVisible().catch(() => false);
    if (!isVisible) return '';
    return await error.textContent() || '';
  }

  /**
   * Check password strength indicator
   */
  async getPasswordStrength(): Promise<string> {
    const strengthText = await this.page.locator(this.passwordStrengthText).textContent();
    if (!strengthText) return 'weak';
    
    // Extract strength from "Password strength: Strong" text
    const match = strengthText.match(/Password strength: (\w+)/);
    return match ? match[1].toLowerCase() : 'weak';
  }

  /**
   * Verify form validation
   */
  async verifyFormValidation() {
    // Submit empty form
    await this.submitRegistration();
    
    // Check for required field errors
    const usernameError = await this.getFieldError('username');
    const emailError = await this.getFieldError('email');
    const passwordError = await this.getFieldError('password');
    const termsError = await this.page.locator('p.text-red-500:has-text("accept the terms")').isVisible();
    
    return {
      usernameRequired: usernameError.includes('3 characters') || usernameError.includes('required'),
      emailRequired: emailError.includes('valid') || emailError.includes('required'),
      passwordRequired: passwordError.includes('8 characters') || passwordError.includes('required'),
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
    await this.page.click('body'); // Click elsewhere to trigger blur
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
    await this.expectToBeVisible(this.usernameInput);
    await this.expectToBeVisible(this.emailInput);
    await this.expectToBeVisible(this.passwordInput);
    await this.expectToBeVisible(this.confirmPasswordInput);
    await this.expectToBeVisible(this.termsCheckbox);
    await this.expectToBeVisible(this.submitButton);
  }
}