import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export interface EnhancementDetails {
  id: string;
  originalPrompt: string;
  enhancedPrompt: string;
  intent?: string;
  complexity?: string;
  techniques: string[];
  confidence?: number;
  createdAt: string;
  metadata?: Record<string, any>;
}

/**
 * Enhancement Details Page Object Model
 * Handles viewing and re-running individual enhancement details
 */
export class EnhancementDetailsPage extends BasePage {
  // Locators
  private readonly backButton = 'button:has-text("Back"), a:has-text("Back to History")';
  private readonly pageTitle = 'h1:has-text("Enhancement Details")';
  
  // Details sections
  private readonly originalPromptSection = ':has-text("Original Prompt") + *, [data-testid="original-prompt"]';
  private readonly enhancedPromptSection = ':has-text("Enhanced Prompt") + *, [data-testid="enhanced-prompt"]';
  private readonly intentSection = ':has-text("Intent") + *, [data-testid="intent"]';
  private readonly complexitySection = ':has-text("Complexity") + *, [data-testid="complexity"]';
  private readonly confidenceSection = ':has-text("Confidence") + *, [data-testid="confidence"]';
  private readonly techniquesSection = ':has-text("Techniques Used") + *, [data-testid="techniques"]';
  private readonly createdAtSection = ':has-text("Created") + *, [data-testid="created-at"]';
  
  // Actions
  private readonly rerunButton = 'button:has-text("Re-run"), button:has-text("Enhance Again")';
  private readonly copyOriginalButton = 'button[aria-label="Copy original prompt"]';
  private readonly copyEnhancedButton = 'button[aria-label="Copy enhanced prompt"]';
  private readonly deleteButton = 'button:has-text("Delete")';
  private readonly shareButton = 'button:has-text("Share")';
  
  // Metadata section
  private readonly metadataSection = '[data-testid="metadata"], .metadata-section';
  
  // Loading and error states
  private readonly loadingIndicator = '[data-testid="loading"], .loading-spinner';
  private readonly errorMessage = '[role="alert"], .error-message';
  private readonly successMessage = '.success-message, [data-testid="success"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to a specific enhancement details page
   */
  async goto(enhancementId: string) {
    await super.goto(`/history/${enhancementId}`);
    await this.waitForPageLoad();
  }

  /**
   * Verify page is loaded
   */
  async verifyPageLoaded() {
    await this.waitForElement(this.pageTitle);
    await expect(this.page.locator(this.pageTitle)).toBeVisible();
  }

  /**
   * Get enhancement details
   */
  async getDetails(): Promise<EnhancementDetails> {
    // Wait for content to load
    await this.waitForDetailsToLoad();
    
    // Extract ID from URL
    const url = this.page.url();
    const idMatch = url.match(/\/history\/([^\/]+)/);
    const id = idMatch ? idMatch[1] : '';
    
    // Extract all details
    const originalPrompt = await this.getTextContent(this.originalPromptSection);
    const enhancedPrompt = await this.getTextContent(this.enhancedPromptSection);
    const intent = await this.getTextContentOrUndefined(this.intentSection);
    const complexity = await this.getTextContentOrUndefined(this.complexitySection);
    const createdAt = await this.getTextContent(this.createdAtSection);
    
    // Extract confidence
    let confidence: number | undefined;
    const confidenceText = await this.getTextContentOrUndefined(this.confidenceSection);
    if (confidenceText) {
      const match = confidenceText.match(/(\d+)%?/);
      if (match) {
        confidence = parseInt(match[1]) / 100;
      }
    }
    
    // Extract techniques
    const techniques: string[] = [];
    if (await this.elementExists(this.techniquesSection)) {
      const techContainer = this.page.locator(this.techniquesSection);
      const techElements = await techContainer.locator('.rounded-full, [data-testid="technique"]').all();
      for (const elem of techElements) {
        const text = await elem.textContent();
        if (text) {
          techniques.push(text.trim());
        }
      }
    }
    
    // Extract metadata if available
    let metadata: Record<string, any> | undefined;
    if (await this.elementExists(this.metadataSection)) {
      // Implementation depends on how metadata is displayed
      // For now, we'll leave it undefined
    }
    
    return {
      id,
      originalPrompt,
      enhancedPrompt,
      intent,
      complexity,
      techniques,
      confidence,
      createdAt,
      metadata
    };
  }

  /**
   * Helper to get text content or return empty string
   */
  private async getTextContent(selector: string): Promise<string> {
    if (await this.elementExists(selector)) {
      return (await this.getElementText(selector)).trim();
    }
    return '';
  }

  /**
   * Helper to get text content or return undefined
   */
  private async getTextContentOrUndefined(selector: string): Promise<string | undefined> {
    if (await this.elementExists(selector)) {
      const text = (await this.getElementText(selector)).trim();
      return text || undefined;
    }
    return undefined;
  }

  /**
   * Wait for details to load
   */
  private async waitForDetailsToLoad() {
    // Wait for loading to complete
    try {
      await this.page.waitForSelector(this.loadingIndicator, { 
        state: 'hidden',
        timeout: 10000
      });
    } catch {
      // Loading might not appear
    }
    
    // Wait for original prompt to be visible (indicates content loaded)
    await this.waitForElement(this.originalPromptSection);
  }

  /**
   * Re-run the enhancement
   */
  async rerunEnhancement() {
    await this.clickElement(this.rerunButton);
    
    // Wait for re-run to complete
    await this.page.waitForResponse(
      response => response.url().includes('/rerun') && response.ok(),
      { timeout: 30000 }
    );
    
    // Wait for page to update
    await this.waitForDetailsToLoad();
  }

  /**
   * Copy original prompt
   */
  async copyOriginalPrompt() {
    await this.clickElement(this.copyOriginalButton);
    await this.waitForCopyConfirmation();
  }

  /**
   * Copy enhanced prompt
   */
  async copyEnhancedPrompt() {
    await this.clickElement(this.copyEnhancedButton);
    await this.waitForCopyConfirmation();
  }

  /**
   * Wait for copy confirmation
   */
  private async waitForCopyConfirmation() {
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
   * Delete the enhancement
   */
  async deleteEnhancement() {
    await this.clickElement(this.deleteButton);
    
    // Handle confirmation dialog if present
    await this.page.on('dialog', async dialog => {
      await dialog.accept();
    });
    
    // Wait for deletion and redirect
    await this.page.waitForURL('**/history', { timeout: 10000 });
  }

  /**
   * Go back to history
   */
  async goBackToHistory() {
    await this.clickElement(this.backButton);
    await this.page.waitForURL('**/history');
  }

  /**
   * Check if re-run produces the same result
   */
  async verifyRerunConsistency(): Promise<boolean> {
    // Get current enhanced prompt
    const beforeRerun = await this.getTextContent(this.enhancedPromptSection);
    
    // Re-run the enhancement
    await this.rerunEnhancement();
    
    // Get new enhanced prompt
    const afterRerun = await this.getTextContent(this.enhancedPromptSection);
    
    // Compare results
    return beforeRerun === afterRerun;
  }

  /**
   * Check if user can perform actions (indicates ownership)
   */
  async canPerformActions(): Promise<boolean> {
    return await this.elementExists(this.rerunButton) && 
           await this.elementExists(this.deleteButton);
  }
}