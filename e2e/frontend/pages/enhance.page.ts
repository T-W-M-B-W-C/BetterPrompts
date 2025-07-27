import { Page } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Enhance Page Object Model
 * Core functionality for prompt enhancement
 */
export class EnhancePage extends BasePage {
  // Input section locators
  private readonly promptInput = 'textarea[data-testid="prompt-input"]';
  private readonly enhanceButton = 'button[data-testid="enhance-button"]';
  private readonly clearButton = 'button[data-testid="clear-button"]';
  private readonly characterCount = '[data-testid="character-count"]';
  
  // Technique selection locators
  private readonly techniqueSelector = '[data-testid="technique-selector"]';
  private readonly techniqueCard = '[data-testid="technique-card"]';
  private readonly selectedTechnique = '[data-testid="selected-technique"]';
  
  // Output section locators
  private readonly enhancedOutput = '[data-testid="enhanced-output"]';
  private readonly copyButton = 'button[data-testid="copy-button"]';
  private readonly downloadButton = 'button[data-testid="download-button"]';
  private readonly feedbackButton = 'button[data-testid="feedback-button"]';
  
  // Loading states
  private readonly loadingSpinner = '[data-testid="loading-spinner"]';
  private readonly progressBar = '[data-testid="progress-bar"]';
  
  // Templates
  private readonly templateButton = 'button[data-testid="template-button"]';
  private readonly templateModal = '[data-testid="template-modal"]';
  private readonly templateItem = '[data-testid="template-item"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to enhance page
   */
  async goto() {
    await super.goto('/enhance');
    await this.waitForElement(this.promptInput);
  }

  /**
   * Enter prompt text
   */
  async enterPrompt(prompt: string) {
    await this.fillInput(this.promptInput, prompt);
  }

  /**
   * Click enhance button
   */
  async clickEnhance() {
    await this.expectToBeEnabled(this.enhanceButton);
    await this.clickWithRetry(this.enhanceButton);
  }

  /**
   * Clear prompt input
   */
  async clearPrompt() {
    await this.clickWithRetry(this.clearButton);
  }

  /**
   * Get character count
   */
  async getCharacterCount(): Promise<string> {
    return await this.getText(this.characterCount);
  }

  /**
   * Select technique by name
   */
  async selectTechnique(techniqueName: string) {
    const techniqueCards = this.page.locator(this.techniqueCard);
    const count = await techniqueCards.count();
    
    for (let i = 0; i < count; i++) {
      const card = techniqueCards.nth(i);
      const title = await card.locator('h3').textContent();
      if (title?.includes(techniqueName)) {
        await card.click();
        break;
      }
    }
  }

  /**
   * Get selected techniques
   */
  async getSelectedTechniques(): Promise<string[]> {
    const selected = await this.page.locator(this.selectedTechnique).allTextContents();
    return selected;
  }

  /**
   * Wait for enhancement to complete
   */
  async waitForEnhancement() {
    await this.page.waitForSelector(this.loadingSpinner, { state: 'visible' });
    await this.page.waitForSelector(this.loadingSpinner, { state: 'hidden', timeout: 30000 });
    await this.waitForElement(this.enhancedOutput);
  }

  /**
   * Get enhanced output text
   */
  async getEnhancedOutput(): Promise<string> {
    return await this.getText(this.enhancedOutput);
  }

  /**
   * Copy enhanced output
   */
  async copyOutput() {
    await this.clickWithRetry(this.copyButton);
  }

  /**
   * Download enhanced output
   */
  async downloadOutput() {
    const [download] = await Promise.all([
      this.page.waitForEvent('download'),
      this.page.click(this.downloadButton),
    ]);
    return download;
  }

  /**
   * Open feedback dialog
   */
  async openFeedback() {
    await this.clickWithRetry(this.feedbackButton);
  }

  /**
   * Select template
   */
  async selectTemplate(templateName: string) {
    await this.clickWithRetry(this.templateButton);
    await this.waitForElement(this.templateModal);
    
    const templates = this.page.locator(this.templateItem);
    const count = await templates.count();
    
    for (let i = 0; i < count; i++) {
      const template = templates.nth(i);
      const name = await template.textContent();
      if (name?.includes(templateName)) {
        await template.click();
        break;
      }
    }
  }

  /**
   * Check if enhancement is in progress
   */
  async isEnhancing(): Promise<boolean> {
    return await this.isVisible(this.loadingSpinner);
  }

  /**
   * Get progress percentage
   */
  async getProgress(): Promise<string> {
    const progressElement = this.page.locator(this.progressBar);
    return await progressElement.getAttribute('aria-valuenow') || '0';
  }

  /**
   * Perform complete enhancement flow
   */
  async enhancePrompt(prompt: string, technique?: string) {
    await this.enterPrompt(prompt);
    
    if (technique) {
      await this.selectTechnique(technique);
    }
    
    await this.clickEnhance();
    await this.waitForEnhancement();
    
    return await this.getEnhancedOutput();
  }

  /**
   * Verify page loaded correctly
   */
  async verifyPageLoaded() {
    await this.expectToBeVisible(this.promptInput);
    await this.expectToBeVisible(this.enhanceButton);
    await this.expectToBeVisible(this.techniqueSelector);
  }

  /**
   * Check enhancement performance
   */
  async measureEnhancementTime() {
    const startTime = Date.now();
    await this.waitForEnhancement();
    const endTime = Date.now();
    
    return {
      duration: endTime - startTime,
      output: await this.getEnhancedOutput(),
    };
  }
}