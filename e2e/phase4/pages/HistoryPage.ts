import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export interface HistoryItem {
  id?: string;
  originalPrompt: string;
  enhancedPrompt: string;
  intent?: string;
  techniques: string[];
  date: string;
  complexity?: string;
  confidence?: number;
}

export interface PaginationInfo {
  currentPage: number;
  totalItems: number;
  itemsPerPage: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

/**
 * History Page Object Model
 * Handles user's prompt history functionality
 */
export class HistoryPage extends BasePage {
  // Locators
  private readonly pageTitle = 'h1:has-text("Prompt History")';
  private readonly emptyState = ':has-text("No prompts in your history yet"), :has-text("No prompts found")';
  
  // Filters
  private readonly searchInput = 'input[placeholder*="Search"], input[type="search"]';
  private readonly intentFilter = 'select:has(option:has-text("All intents"))';
  private readonly techniqueFilter = 'select:has(option:has-text("All techniques"))';
  
  // History items
  private readonly historyCard = '.space-y-4 > div.relative.hover\\:bg-accent\\/50, [data-testid="history-item"]';
  private readonly originalPromptText = ':has-text("Original Prompt:") + p, .original-prompt';
  private readonly enhancedPromptText = ':has-text("Enhanced Prompt:") + p, .enhanced-prompt';
  private readonly techniqueTag = '.px-2.py-1.bg-secondary.rounded-full, [data-testid="technique-tag"]';
  private readonly dateText = '.text-muted-foreground:has-text("202"), [data-testid="date"]';
  private readonly intentText = '.text-lg:not(:has-text("Prompt History")), [data-testid="intent"]';
  
  // Actions
  private readonly viewDetailsButton = 'button[title="View details"]';
  private readonly copyButton = 'button[title="Copy enhanced prompt"]';
  private readonly deleteButton = 'button[title="Delete"]';
  
  // Pagination
  private readonly paginationInfo = ':has-text("Showing") + :has-text("of")';
  private readonly previousButton = 'button:has-text("Previous")';
  private readonly nextButton = 'button:has-text("Next")';
  
  // Loading states
  private readonly loadingIndicator = '.space-y-4 > div > div > div.h-4.w-32, [data-testid="loading"]';
  private readonly errorMessage = '[role="alert"], .error-message';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to history page
   */
  async goto() {
    await super.goto('/history');
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
   * Check if history is empty
   */
  async isEmpty(): Promise<boolean> {
    // Wait a bit for loading to complete
    try {
      await this.page.waitForSelector(this.loadingIndicator, { 
        state: 'hidden',
        timeout: 5000
      });
    } catch {
      // Loading might not appear
    }
    
    return await this.elementExists(this.emptyState);
  }

  /**
   * Get all history items on current page
   */
  async getHistoryItems(): Promise<HistoryItem[]> {
    // Wait for loading to complete
    await this.waitForHistoryToLoad();
    
    const items: HistoryItem[] = [];
    const cards = await this.page.locator(this.historyCard).all();
    
    for (const card of cards) {
      // Extract original prompt
      const originalPromptElement = card.locator(this.originalPromptText);
      const originalPrompt = await originalPromptElement.textContent() || '';
      
      // Extract enhanced prompt
      const enhancedPromptElement = card.locator(this.enhancedPromptText);
      const enhancedPrompt = await enhancedPromptElement.textContent() || '';
      
      // Extract intent
      const intentElement = card.locator(this.intentText).first();
      const intent = await intentElement.textContent() || undefined;
      
      // Extract techniques
      const techniques: string[] = [];
      const techElements = await card.locator(this.techniqueTag).all();
      for (const tech of techElements) {
        const text = await tech.textContent();
        if (text && !text.includes('complexity') && !text.includes('%')) {
          techniques.push(text.trim());
        }
      }
      
      // Extract date
      const dateElement = card.locator(this.dateText);
      const date = await dateElement.textContent() || '';
      
      // Extract complexity if available
      let complexity: string | undefined;
      const complexityTag = await card.locator(':has-text("complexity")').textContent();
      if (complexityTag) {
        complexity = complexityTag.replace(' complexity', '').trim();
      }
      
      // Extract confidence if available
      let confidence: number | undefined;
      const confidenceTag = await card.locator(':has-text("%")').textContent();
      if (confidenceTag) {
        const match = confidenceTag.match(/(\d+)%/);
        if (match) {
          confidence = parseInt(match[1]) / 100;
        }
      }
      
      items.push({
        originalPrompt: originalPrompt.trim(),
        enhancedPrompt: enhancedPrompt.trim(),
        intent,
        techniques,
        date: date.trim(),
        complexity,
        confidence
      });
    }
    
    return items;
  }

  /**
   * Wait for history to load
   */
  private async waitForHistoryToLoad() {
    // Wait for loading indicators to disappear
    try {
      await this.page.waitForSelector(this.loadingIndicator, { 
        state: 'hidden',
        timeout: 10000
      });
    } catch {
      // Loading might not appear or might be too quick
    }
    
    // Wait for either cards or empty state
    await this.page.waitForSelector(`${this.historyCard}, ${this.emptyState}`, {
      timeout: 10000
    });
  }

  /**
   * Search for prompts
   */
  async searchPrompts(query: string) {
    await this.fillInput(this.searchInput, query);
    
    // Wait for debounce (500ms according to the code)
    await this.page.waitForTimeout(600);
    
    // Wait for results to update
    await this.waitForHistoryToLoad();
  }

  /**
   * Filter by intent
   */
  async filterByIntent(intent: string) {
    await this.page.selectOption(this.intentFilter, intent);
    await this.waitForHistoryToLoad();
  }

  /**
   * Filter by technique
   */
  async filterByTechnique(technique: string) {
    await this.page.selectOption(this.techniqueFilter, technique);
    await this.waitForHistoryToLoad();
  }

  /**
   * Get pagination info
   */
  async getPaginationInfo(): Promise<PaginationInfo | null> {
    if (!await this.elementExists(this.paginationInfo)) {
      return null;
    }
    
    const paginationText = await this.page.locator(':has-text("Showing")').textContent() || '';
    
    // Parse "Showing 1 - 20 of 150"
    const match = paginationText.match(/Showing (\d+) - (\d+) of (\d+)/);
    if (!match) {
      return null;
    }
    
    const start = parseInt(match[1]);
    const end = parseInt(match[2]);
    const total = parseInt(match[3]);
    const itemsPerPage = end - start + 1;
    const currentPage = Math.ceil(start / itemsPerPage);
    
    const hasNext = !await this.page.locator(this.nextButton).isDisabled();
    const hasPrevious = !await this.page.locator(this.previousButton).isDisabled();
    
    return {
      currentPage,
      totalItems: total,
      itemsPerPage,
      hasNext,
      hasPrevious
    };
  }

  /**
   * Go to next page
   */
  async goToNextPage() {
    await this.clickElement(this.nextButton);
    await this.waitForHistoryToLoad();
  }

  /**
   * Go to previous page
   */
  async goToPreviousPage() {
    await this.clickElement(this.previousButton);
    await this.waitForHistoryToLoad();
  }

  /**
   * View details of a specific history item
   */
  async viewItemDetails(index: number = 0) {
    const cards = await this.page.locator(this.historyCard).all();
    if (index >= cards.length) {
      throw new Error(`History item at index ${index} not found`);
    }
    
    const viewButton = cards[index].locator(this.viewDetailsButton);
    await viewButton.click();
    
    // Wait for navigation to details page
    await this.page.waitForURL('**/history/**');
  }

  /**
   * Delete a history item
   */
  async deleteItem(index: number = 0) {
    const cards = await this.page.locator(this.historyCard).all();
    if (index >= cards.length) {
      throw new Error(`History item at index ${index} not found`);
    }
    
    const deleteButton = cards[index].locator(this.deleteButton);
    await deleteButton.click();
    
    // Wait for deletion to complete
    await this.waitForHistoryToLoad();
  }

  /**
   * Copy enhanced prompt from history
   */
  async copyEnhancedPrompt(index: number = 0) {
    const cards = await this.page.locator(this.historyCard).all();
    if (index >= cards.length) {
      throw new Error(`History item at index ${index} not found`);
    }
    
    const copyButton = cards[index].locator(this.copyButton);
    await copyButton.click();
    
    // Wait for copy confirmation
    await this.page.waitForSelector(':has-text("copied")', {
      state: 'visible',
      timeout: 3000
    }).catch(() => {
      // Some implementations might not show confirmation
    });
  }

  /**
   * Get available intents from filter dropdown
   */
  async getAvailableIntents(): Promise<string[]> {
    const options = await this.page.locator(`${this.intentFilter} option`).all();
    const intents: string[] = [];
    
    for (const option of options) {
      const value = await option.getAttribute('value');
      const text = await option.textContent();
      if (value && value !== 'all' && text) {
        intents.push(text.trim());
      }
    }
    
    return intents;
  }

  /**
   * Get available techniques from filter dropdown
   */
  async getAvailableTechniques(): Promise<string[]> {
    const options = await this.page.locator(`${this.techniqueFilter} option`).all();
    const techniques: string[] = [];
    
    for (const option of options) {
      const value = await option.getAttribute('value');
      const text = await option.textContent();
      if (value && value !== 'all' && text) {
        techniques.push(text.trim());
      }
    }
    
    return techniques;
  }
}