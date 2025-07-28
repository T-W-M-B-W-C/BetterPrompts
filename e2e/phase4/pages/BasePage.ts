import { Page, expect } from '@playwright/test';

/**
 * Base Page Object Model
 * Contains common functionality for all pages
 */
export class BasePage {
  protected page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to a specific path
   */
  async goto(path: string) {
    await this.page.goto(path);
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
      // If networkidle times out, at least wait for domcontentloaded
      return this.page.waitForLoadState('domcontentloaded');
    });
  }

  /**
   * Wait for a specific element to be visible
   */
  async waitForElement(selector: string, timeout?: number) {
    await this.page.waitForSelector(selector, { 
      state: 'visible',
      timeout: timeout || 30000
    });
  }

  /**
   * Check if an element exists on the page
   */
  async elementExists(selector: string): Promise<boolean> {
    return await this.page.locator(selector).count() > 0;
  }

  /**
   * Get text content of an element
   */
  async getElementText(selector: string): Promise<string> {
    const element = this.page.locator(selector);
    return await element.textContent() || '';
  }

  /**
   * Click an element with retry logic
   */
  async clickElement(selector: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.click();
  }

  /**
   * Fill an input field
   */
  async fillInput(selector: string, value: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.fill(value);
  }

  /**
   * Check if user is authenticated by checking for auth tokens
   */
  async isAuthenticated(): Promise<boolean> {
    const cookies = await this.page.context().cookies();
    const hasAccessToken = cookies.some(c => c.name === 'access_token');
    
    if (!hasAccessToken) {
      // Check localStorage as fallback
      const hasLocalStorageToken = await this.page.evaluate(() => {
        return !!localStorage.getItem('access_token');
      });
      return hasLocalStorageToken;
    }
    
    return hasAccessToken;
  }

  /**
   * Wait for API response
   */
  async waitForApiResponse(urlPattern: string | RegExp) {
    return await this.page.waitForResponse(
      response => {
        const matches = typeof urlPattern === 'string' 
          ? response.url().includes(urlPattern)
          : urlPattern.test(response.url());
        return matches && response.status() === 200;
      },
      { timeout: 30000 }
    );
  }

  /**
   * Take a screenshot for debugging
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true
    });
  }
}