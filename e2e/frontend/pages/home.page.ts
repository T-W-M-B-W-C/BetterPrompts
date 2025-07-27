import { Page } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Home Page Object Model
 * Handles landing page interactions
 */
export class HomePage extends BasePage {
  // Locators
  private readonly heroTitle = 'h1';
  private readonly getStartedButton = 'text=Start Enhancing';
  private readonly tryDemoButton = 'text=Learn More';
  private readonly loginButton = 'a:has-text("Log In")';
  private readonly signUpButton = 'a:has-text("Sign Up")';
  
  // Feature section locators
  private readonly featuresSection = '[data-testid="features-section"]';
  private readonly featureCards = '[data-testid="feature-card"]';
  
  // CTA section locators
  private readonly ctaSection = '[data-testid="cta-section"]';
  private readonly ctaTitle = '[data-testid="cta-title"]';
  private readonly ctaButton = '[data-testid="cta-button"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to home page
   */
  async goto() {
    await super.goto('/');
    await this.waitForElement(this.heroTitle);
  }

  /**
   * Click Get Started button
   */
  async clickGetStarted() {
    await this.clickWithRetry(this.getStartedButton);
  }

  /**
   * Click Try Demo button
   */
  async clickTryDemo() {
    await this.clickWithRetry(this.tryDemoButton);
  }

  /**
   * Navigate to login
   */
  async navigateToLogin() {
    await this.clickWithRetry(this.loginButton);
  }

  /**
   * Navigate to sign up
   */
  async navigateToSignUp() {
    await this.clickWithRetry(this.signUpButton);
  }

  /**
   * Get feature cards count
   */
  async getFeatureCardsCount(): Promise<number> {
    await this.waitForElement(this.featuresSection);
    return await this.page.locator(this.featureCards).count();
  }

  /**
   * Get feature card by index
   */
  async getFeatureCard(index: number) {
    const cards = this.page.locator(this.featureCards);
    return {
      title: await cards.nth(index).locator('h3').textContent(),
      description: await cards.nth(index).locator('p').textContent(),
    };
  }

  /**
   * Check if CTA section is visible
   */
  async isCTASectionVisible(): Promise<boolean> {
    return await this.isVisible(this.ctaSection);
  }

  /**
   * Get CTA title text
   */
  async getCTATitle(): Promise<string> {
    return await this.getText(this.ctaTitle);
  }

  /**
   * Click CTA button
   */
  async clickCTAButton() {
    await this.page.locator(this.ctaSection).scrollIntoViewIfNeeded();
    await this.clickWithRetry(this.ctaButton);
  }

  /**
   * Verify home page loaded correctly
   */
  async verifyPageLoaded() {
    await this.expectToBeVisible(this.heroTitle);
    await this.expectToBeVisible(this.getStartedButton);
    await this.expectToBeVisible(this.featuresSection);
  }

  /**
   * Check hero section performance
   */
  async checkHeroPerformance() {
    const metrics = await this.getPerformanceMetrics();
    return {
      heroVisible: await this.page.locator(this.heroTitle).isVisible(),
      loadTime: metrics.loadComplete,
      firstPaint: metrics.firstPaint,
    };
  }
}