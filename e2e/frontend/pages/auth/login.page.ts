import { Page } from '@playwright/test';
import { BasePage } from '../base.page';

/**
 * Login Page Object Model
 * Handles authentication flows
 */
export class LoginPage extends BasePage {
  // Locators
  private readonly emailInput = 'input[name="email"]';
  private readonly passwordInput = 'input[name="password"]';
  private readonly submitButton = 'button[type="submit"]:has-text("Log In")';
  private readonly rememberMeCheckbox = 'input[type="checkbox"][name="remember"]';
  private readonly forgotPasswordLink = 'a:has-text("Forgot password?")';
  private readonly signUpLink = 'a:has-text("Sign up")';
  private readonly errorMessage = '[data-testid="error-message"]';
  private readonly successMessage = '[data-testid="success-message"]';
  
  // OAuth buttons
  private readonly googleButton = 'button:has-text("Continue with Google")';
  private readonly githubButton = 'button:has-text("Continue with GitHub")';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to login page
   */
  async goto() {
    await super.goto('/login');
    await this.waitForElement(this.emailInput);
  }

  /**
   * Fill login form
   */
  async fillLoginForm(email: string, password: string) {
    await this.fillInput(this.emailInput, email);
    await this.fillInput(this.passwordInput, password);
  }

  /**
   * Submit login form
   */
  async submitLogin() {
    await this.clickWithRetry(this.submitButton);
  }

  /**
   * Complete login flow
   */
  async login(email: string, password: string) {
    await this.fillLoginForm(email, password);
    await this.submitLogin();
  }

  /**
   * Toggle remember me
   */
  async toggleRememberMe() {
    await this.page.click(this.rememberMeCheckbox);
  }

  /**
   * Click forgot password
   */
  async clickForgotPassword() {
    await this.clickWithRetry(this.forgotPasswordLink);
  }

  /**
   * Navigate to sign up
   */
  async navigateToSignUp() {
    await this.clickWithRetry(this.signUpLink);
  }

  /**
   * Login with Google
   */
  async loginWithGoogle() {
    await this.clickWithRetry(this.googleButton);
  }

  /**
   * Login with GitHub
   */
  async loginWithGitHub() {
    await this.clickWithRetry(this.githubButton);
  }

  /**
   * Get error message
   */
  async getErrorMessage(): Promise<string> {
    await this.waitForElement(this.errorMessage);
    return await this.getText(this.errorMessage);
  }

  /**
   * Get success message
   */
  async getSuccessMessage(): Promise<string> {
    await this.waitForElement(this.successMessage);
    return await this.getText(this.successMessage);
  }

  /**
   * Check if error is displayed
   */
  async isErrorDisplayed(): Promise<boolean> {
    return await this.isVisible(this.errorMessage);
  }

  /**
   * Verify login page loaded
   */
  async verifyPageLoaded() {
    await this.expectToBeVisible(this.emailInput);
    await this.expectToBeVisible(this.passwordInput);
    await this.expectToBeVisible(this.submitButton);
  }

  /**
   * Check form validation
   */
  async checkFormValidation() {
    // Submit empty form
    await this.submitLogin();
    
    // Check for validation messages
    const emailValidation = await this.page.locator(this.emailInput).getAttribute('aria-invalid');
    const passwordValidation = await this.page.locator(this.passwordInput).getAttribute('aria-invalid');
    
    return {
      emailInvalid: emailValidation === 'true',
      passwordInvalid: passwordValidation === 'true',
    };
  }

  /**
   * Wait for successful login redirect
   */
  async waitForLoginSuccess() {
    await this.page.waitForURL('**/dashboard', { timeout: 10000 });
  }
}