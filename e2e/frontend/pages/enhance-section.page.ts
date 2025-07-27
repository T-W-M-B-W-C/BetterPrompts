import { Page } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Enhance Section Page Object Model
 * Handles the enhancement section on homepage for anonymous users
 */
export class EnhanceSection extends BasePage {
  // Input section locators
  private readonly enhanceSection = '[data-testid="homepage-enhance-section"]';
  private readonly promptInput = 'textarea[data-testid="anonymous-prompt-input"]';
  private readonly enhanceButton = 'button[data-testid="anonymous-enhance-button"]';
  private readonly characterCount = '[data-testid="anonymous-character-count"]';
  private readonly characterLimit = '[data-testid="anonymous-character-limit"]';
  
  // Output section locators
  private readonly enhancedOutput = '[data-testid="anonymous-enhanced-output"]';
  private readonly outputContainer = '[data-testid="anonymous-output-container"]';
  private readonly techniqueExplanation = '[data-testid="technique-explanation"]';
  private readonly techniqueList = '[data-testid="applied-techniques"]';
  private readonly copyButton = 'button[data-testid="anonymous-copy-button"]';
  
  // Loading and error states
  private readonly loadingSpinner = '[data-testid="anonymous-loading-spinner"]';
  private readonly loadingMessage = '[data-testid="loading-message"]';
  private readonly errorMessage = '[data-testid="error-message"]';
  private readonly errorRetryButton = 'button[data-testid="retry-button"]';
  
  // CTA elements
  private readonly signUpCTA = '[data-testid="signup-cta"]';
  private readonly learnMoreLink = 'a[data-testid="learn-more-link"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Check if enhance section is visible
   */
  async isEnhanceSectionVisible(): Promise<boolean> {
    return await this.isVisible(this.enhanceSection);
  }

  /**
   * Scroll to enhance section
   */
  async scrollToEnhanceSection() {
    try {
      // Only scroll if the element exists and is attached to DOM
      const element = this.page.locator(this.enhanceSection);
      await element.waitFor({ state: 'attached', timeout: 5000 });
      await element.scrollIntoViewIfNeeded();
    } catch (e) {
      // Element might not need scrolling or already in view
      console.log('Scroll not needed or element not found');
    }
  }

  /**
   * Enter prompt text
   */
  async enterPrompt(prompt: string) {
    // Only scroll if needed
    const input = this.page.locator(this.promptInput);
    const isVisible = await input.isVisible();
    if (!isVisible) {
      await this.scrollToEnhanceSection();
    }
    await input.click();
    await input.fill(prompt);
    // Trigger input event to ensure React detects the change
    // Only add/remove space if we're not at the character limit
    if (prompt.length < 2000) {
      await input.press('Space');
      await input.press('Backspace');
    } else {
      // For max length text, just dispatch an input event
      await input.dispatchEvent('input');
    }
  }

  /**
   * Get current prompt text
   */
  async getPromptText(): Promise<string> {
    return await this.page.locator(this.promptInput).inputValue();
  }

  /**
   * Clear prompt input
   */
  async clearPrompt() {
    await this.page.locator(this.promptInput).clear();
  }

  /**
   * Click enhance button
   */
  async clickEnhance() {
    // Wait for button to be enabled with a shorter timeout
    await this.page.waitForSelector(this.enhanceButton + ':not([disabled])', { timeout: 5000 });
    await this.clickWithRetry(this.enhanceButton);
  }

  /**
   * Check if enhance button is enabled
   */
  async isEnhanceButtonEnabled(): Promise<boolean> {
    return await this.page.locator(this.enhanceButton).isEnabled();
  }

  /**
   * Get character count display
   */
  async getCharacterCount(): Promise<string> {
    return await this.getText(this.characterCount);
  }

  /**
   * Get character limit
   */
  async getCharacterLimit(): Promise<string> {
    return await this.getText(this.characterLimit);
  }

  /**
   * Check if loading spinner is visible
   */
  async isLoading(): Promise<boolean> {
    return await this.isVisible(this.loadingSpinner);
  }

  /**
   * Get loading message
   */
  async getLoadingMessage(): Promise<string> {
    return await this.getText(this.loadingMessage);
  }

  /**
   * Wait for enhancement to complete
   */
  async waitForEnhancement(timeout = 10000) {
    try {
      // Wait for loading to start
      await this.page.waitForSelector(this.loadingSpinner, { 
        state: 'visible',
        timeout: 5000 
      });
    } catch (e) {
      // Loading might be too fast to catch, continue
    }
    
    // Wait for loading to complete
    await this.page.waitForSelector(this.loadingSpinner, { 
      state: 'hidden',
      timeout: timeout 
    });
    
    // Wait for output to appear
    await this.waitForElement(this.outputContainer);
  }

  /**
   * Get enhanced output text
   */
  async getEnhancedOutput(): Promise<string> {
    await this.waitForElement(this.enhancedOutput);
    return await this.getText(this.enhancedOutput);
  }

  /**
   * Check if output is visible
   */
  async isOutputVisible(): Promise<boolean> {
    return await this.isVisible(this.outputContainer);
  }

  /**
   * Get technique explanation
   */
  async getTechniqueExplanation(): Promise<string> {
    return await this.getText(this.techniqueExplanation);
  }

  /**
   * Get applied techniques list
   */
  async getAppliedTechniques(): Promise<string[]> {
    const techniques = await this.page.locator(`${this.techniqueList} li`).allTextContents();
    return techniques;
  }

  /**
   * Copy enhanced output
   */
  async copyOutput() {
    await this.clickWithRetry(this.copyButton);
  }

  /**
   * Check if error message is displayed
   */
  async isErrorDisplayed(): Promise<boolean> {
    return await this.isVisible(this.errorMessage);
  }

  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string> {
    return await this.getText(this.errorMessage);
  }

  /**
   * Click retry button after error
   */
  async clickRetry() {
    await this.clickWithRetry(this.errorRetryButton);
  }

  /**
   * Check if sign-up CTA is visible
   */
  async isSignUpCTAVisible(): Promise<boolean> {
    return await this.isVisible(this.signUpCTA);
  }

  /**
   * Click learn more link
   */
  async clickLearnMore() {
    await this.clickWithRetry(this.learnMoreLink);
  }

  /**
   * Perform complete enhancement flow
   */
  async enhancePrompt(prompt: string): Promise<{
    output: string;
    techniques: string[];
    duration: number;
  }> {
    const startTime = Date.now();
    
    await this.enterPrompt(prompt);
    await this.clickEnhance();
    await this.waitForEnhancement();
    
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    const output = await this.getEnhancedOutput();
    const techniques = await this.getAppliedTechniques();
    
    return { output, techniques, duration };
  }

  /**
   * Verify enhancement section loaded correctly
   */
  async verifyEnhanceSectionLoaded() {
    await this.expectToBeVisible(this.enhanceSection);
    await this.expectToBeVisible(this.promptInput);
    await this.expectToBeVisible(this.enhanceButton);
    await this.expectToBeVisible(this.characterCount);
  }

  /**
   * Check if prompt is within character limit
   */
  async isWithinCharacterLimit(): Promise<boolean> {
    const count = await this.getCharacterCount();
    const [current, limit] = count.split('/').map(s => parseInt(s.trim()));
    return current <= limit;
  }

  /**
   * Measure response time for enhancement
   */
  async measureResponseTime(): Promise<number> {
    const startTime = performance.now();
    await this.waitForEnhancement();
    const endTime = performance.now();
    return endTime - startTime;
  }
}