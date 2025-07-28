import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export interface EnhancementRequest {
  prompt: string;
}

export interface EnhancementResult {
  originalPrompt: string;
  enhancedPrompt: string;
  intent?: string;
  techniques: string[];
  confidence?: number;
}

/**
 * Enhancement Page Object Model
 * Handles the prompt enhancement functionality
 */
export class EnhancementPage extends BasePage {
  // Locators
  private readonly promptInput = 'textarea[name="prompt"], textarea[placeholder*="Enter your prompt"], #prompt-input';
  private readonly enhanceButton = 'button:has-text("Enhance"), button[type="submit"]:has-text("Enhance")';
  private readonly loadingIndicator = '[data-testid="loading"], .loading-spinner, [role="progressbar"]';
  private readonly errorMessage = '[data-testid="error-message"], [role="alert"], .error-message';
  private readonly successMessage = '[data-testid="success-message"], .success-message';
  
  // Results section
  private readonly resultsContainer = '[data-testid="enhancement-results"], .enhancement-results, .results-container';
  private readonly originalPromptDisplay = '[data-testid="original-prompt"], .original-prompt';
  private readonly enhancedPromptDisplay = '[data-testid="enhanced-prompt"], .enhanced-prompt';
  private readonly intentDisplay = '[data-testid="intent"], .intent-display';
  private readonly techniquesDisplay = '[data-testid="techniques"], .techniques-list';
  private readonly confidenceDisplay = '[data-testid="confidence"], .confidence-score';
  
  // Technique cards
  private readonly techniqueCard = '.technique-card, [data-testid="technique-card"]';
  private readonly copyButton = 'button:has-text("Copy"), button[aria-label="Copy"]';
  private readonly viewHistoryButton = 'button:has-text("View History"), a:has-text("View History")';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to the enhancement page
   */
  async goto() {
    await super.goto('/enhance');
    await this.waitForPageLoad();
    
    // Check if we were redirected to login
    const currentUrl = this.page.url();
    if (currentUrl.includes('/login')) {
      throw new Error('Not authenticated - redirected to login page');
    }
  }

  /**
   * Navigate to home page (where anonymous enhancement is available)
   */
  async gotoHome() {
    await super.goto('/');
    await this.waitForPageLoad();
  }

  /**
   * Verify the page is loaded
   */
  async verifyPageLoaded() {
    // Try multiple possible selectors
    const selectors = [
      this.promptInput,
      'textarea#prompt',
      'textarea[data-testid="prompt-input"]',
      '.enhancement-form textarea',
      'form textarea'
    ];
    
    let found = false;
    for (const selector of selectors) {
      if (await this.page.locator(selector).count() > 0) {
        found = true;
        await this.waitForElement(selector);
        break;
      }
    }
    
    if (!found) {
      throw new Error('Could not find prompt input on page');
    }
    
    await expect(this.page.locator(this.enhanceButton)).toBeVisible();
  }

  /**
   * Enhance a prompt
   */
  async enhancePrompt(prompt: string): Promise<EnhancementResult> {
    // Clear and fill the prompt input
    await this.fillInput(this.promptInput, prompt);
    
    // Click enhance button
    await this.clickElement(this.enhanceButton);
    
    // Wait for the enhancement to complete
    await this.waitForEnhancement();
    
    // Extract and return the results
    return await this.getEnhancementResults();
  }

  /**
   * Wait for enhancement to complete
   */
  private async waitForEnhancement() {
    // Wait for loading to appear and disappear
    try {
      await this.page.waitForSelector(this.loadingIndicator, { 
        state: 'visible', 
        timeout: 5000 
      });
    } catch {
      // Loading might be too quick to catch
    }
    
    // Wait for loading to disappear
    await this.page.waitForSelector(this.loadingIndicator, { 
      state: 'hidden',
      timeout: 30000
    });
    
    // Wait for results to appear
    await this.waitForElement(this.resultsContainer);
  }

  /**
   * Get enhancement results
   */
  async getEnhancementResults(): Promise<EnhancementResult> {
    // Wait for results to be visible
    await this.waitForElement(this.resultsContainer);
    
    // Extract original prompt
    const originalPrompt = await this.getElementText(this.originalPromptDisplay);
    
    // Extract enhanced prompt
    const enhancedPrompt = await this.getElementText(this.enhancedPromptDisplay);
    
    // Extract intent if available
    let intent: string | undefined;
    if (await this.elementExists(this.intentDisplay)) {
      intent = await this.getElementText(this.intentDisplay);
    }
    
    // Extract techniques
    const techniques: string[] = [];
    const techniqueElements = await this.page.locator(this.techniqueCard).all();
    for (const element of techniqueElements) {
      const text = await element.textContent();
      if (text) {
        techniques.push(text.trim());
      }
    }
    
    // Extract confidence if available
    let confidence: number | undefined;
    if (await this.elementExists(this.confidenceDisplay)) {
      const confidenceText = await this.getElementText(this.confidenceDisplay);
      const match = confidenceText.match(/(\d+)%?/);
      if (match) {
        confidence = parseInt(match[1]) / 100;
      }
    }
    
    return {
      originalPrompt,
      enhancedPrompt,
      intent,
      techniques,
      confidence
    };
  }

  /**
   * Check if enhancement was successful
   */
  async isEnhancementSuccessful(): Promise<boolean> {
    return await this.elementExists(this.resultsContainer) && 
           !await this.elementExists(this.errorMessage);
  }

  /**
   * Get error message if any
   */
  async getErrorMessage(): Promise<string | null> {
    if (await this.elementExists(this.errorMessage)) {
      return await this.getElementText(this.errorMessage);
    }
    return null;
  }

  /**
   * Copy enhanced prompt to clipboard
   */
  async copyEnhancedPrompt() {
    await this.clickElement(this.copyButton);
    
    // Wait for copy confirmation (if any)
    try {
      await this.page.waitForSelector(':has-text("Copied")', { 
        state: 'visible',
        timeout: 3000
      });
    } catch {
      // Some implementations might not show confirmation
    }
  }

  /**
   * Navigate to history from enhancement results
   */
  async goToHistory() {
    await this.clickElement(this.viewHistoryButton);
    await this.page.waitForURL('**/history');
  }

  /**
   * Check if user is prompted to login to save
   */
  async hasLoginPrompt(): Promise<boolean> {
    return await this.elementExists('button:has-text("Login to save"), a:has-text("Login to save")');
  }
}