import { Page, Locator, expect } from '@playwright/test';

/**
 * Base Page Object Model
 * Provides common functionality for all page objects
 */
export abstract class BasePage {
  protected page: Page;
  
  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to a specific URL
   */
  async goto(path: string = '') {
    await this.page.goto(path);
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get page title
   */
  async getTitle(): Promise<string> {
    return await this.page.title();
  }

  /**
   * Check if element is visible
   */
  async isVisible(selector: string): Promise<boolean> {
    return await this.page.isVisible(selector);
  }

  /**
   * Wait for element to be visible
   */
  async waitForElement(selector: string, timeout: number = 30000) {
    await this.page.waitForSelector(selector, { state: 'visible', timeout });
  }

  /**
   * Click element with retry logic
   */
  async clickWithRetry(selector: string, retries: number = 3) {
    for (let i = 0; i < retries; i++) {
      try {
        await this.page.click(selector);
        return;
      } catch (error) {
        if (i === retries - 1) throw error;
        await this.page.waitForTimeout(1000);
      }
    }
  }

  /**
   * Fill input field
   */
  async fillInput(selector: string, value: string) {
    await this.page.fill(selector, value);
  }

  /**
   * Get text content of element
   */
  async getText(selector: string): Promise<string> {
    return await this.page.textContent(selector) || '';
  }

  /**
   * Take screenshot for visual regression
   */
  async takeScreenshot(name: string) {
    return await this.page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true 
    });
  }

  /**
   * Check accessibility
   */
  async checkAccessibility(options?: any) {
    const { injectAxe, checkA11y } = require('@axe-core/playwright');
    await injectAxe(this.page);
    await checkA11y(this.page, null, options);
  }

  /**
   * Wait for API response
   */
  async waitForAPIResponse(url: string | RegExp) {
    return await this.page.waitForResponse(url);
  }

  /**
   * Get network response
   */
  async getAPIResponse(url: string | RegExp) {
    const response = await this.page.waitForResponse(url);
    return await response.json();
  }

  /**
   * Check performance metrics
   */
  async getPerformanceMetrics() {
    return await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
      };
    });
  }

  /**
   * Common assertions
   */
  async expectToBeVisible(selector: string) {
    await expect(this.page.locator(selector)).toBeVisible();
  }

  async expectToHaveText(selector: string, text: string) {
    await expect(this.page.locator(selector)).toHaveText(text);
  }

  async expectToHaveValue(selector: string, value: string) {
    await expect(this.page.locator(selector)).toHaveValue(value);
  }

  async expectToBeEnabled(selector: string) {
    await expect(this.page.locator(selector)).toBeEnabled();
  }

  async expectToBeDisabled(selector: string) {
    await expect(this.page.locator(selector)).toBeDisabled();
  }
}