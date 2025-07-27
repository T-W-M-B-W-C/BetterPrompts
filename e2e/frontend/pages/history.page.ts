import { Page } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * History Page Object Model
 * Enhancement history and management
 */
export class HistoryPage extends BasePage {
  // Filter and search locators
  private readonly searchInput = 'input[data-testid="history-search"]';
  private readonly dateFilter = 'select[data-testid="date-filter"]';
  private readonly techniqueFilter = 'select[data-testid="technique-filter"]';
  private readonly statusFilter = 'select[data-testid="status-filter"]';
  private readonly clearFiltersButton = 'button:has-text("Clear filters")';
  
  // History list locators
  private readonly historyList = '[data-testid="history-list"]';
  private readonly historyItem = '[data-testid="history-item"]';
  private readonly loadMoreButton = 'button:has-text("Load more")';
  private readonly emptyState = '[data-testid="empty-state"]';
  
  // Bulk actions locators
  private readonly selectAllCheckbox = 'input[data-testid="select-all"]';
  private readonly bulkActionsMenu = '[data-testid="bulk-actions"]';
  private readonly exportSelectedButton = 'button:has-text("Export selected")';
  private readonly deleteSelectedButton = 'button:has-text("Delete selected")';
  
  // History item actions
  private readonly viewDetailsButton = 'button[data-testid="view-details"]';
  private readonly copyButton = 'button[data-testid="copy"]';
  private readonly downloadButton = 'button[data-testid="download"]';
  private readonly deleteButton = 'button[data-testid="delete"]';
  private readonly favoriteButton = 'button[data-testid="favorite"]';
  
  // Export modal locators
  private readonly exportModal = '[data-testid="export-modal"]';
  private readonly exportFormatSelect = 'select[data-testid="export-format"]';
  private readonly exportButton = 'button[data-testid="confirm-export"]';
  
  // Pagination locators
  private readonly paginationInfo = '[data-testid="pagination-info"]';
  private readonly previousButton = 'button[data-testid="previous-page"]';
  private readonly nextButton = 'button[data-testid="next-page"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to history page
   */
  async goto() {
    await super.goto('/history');
    await this.waitForElement(this.historyList);
  }

  /**
   * Search history
   */
  async searchHistory(query: string) {
    await this.fillInput(this.searchInput, query);
    await this.page.keyboard.press('Enter');
    await this.waitForNetworkIdle();
  }

  /**
   * Filter by date
   */
  async filterByDate(dateRange: 'today' | 'week' | 'month' | 'year' | 'all') {
    await this.page.selectOption(this.dateFilter, dateRange);
    await this.waitForNetworkIdle();
  }

  /**
   * Filter by technique
   */
  async filterByTechnique(technique: string) {
    await this.page.selectOption(this.techniqueFilter, technique);
    await this.waitForNetworkIdle();
  }

  /**
   * Filter by status
   */
  async filterByStatus(status: 'all' | 'successful' | 'failed' | 'pending') {
    await this.page.selectOption(this.statusFilter, status);
    await this.waitForNetworkIdle();
  }

  /**
   * Clear all filters
   */
  async clearFilters() {
    await this.clickWithRetry(this.clearFiltersButton);
    await this.waitForNetworkIdle();
  }

  /**
   * Get history item count
   */
  async getHistoryItemCount(): Promise<number> {
    return await this.page.locator(this.historyItem).count();
  }

  /**
   * Get history item details
   */
  async getHistoryItem(index: number) {
    const item = this.page.locator(this.historyItem).nth(index);
    
    return {
      title: await item.locator('[data-testid="item-title"]').textContent(),
      date: await item.locator('[data-testid="item-date"]').textContent(),
      technique: await item.locator('[data-testid="item-technique"]').textContent(),
      status: await item.locator('[data-testid="item-status"]').textContent(),
      preview: await item.locator('[data-testid="item-preview"]').textContent(),
    };
  }

  /**
   * Select history item
   */
  async selectHistoryItem(index: number) {
    const checkbox = this.page.locator(this.historyItem).nth(index).locator('input[type="checkbox"]');
    await checkbox.check();
  }

  /**
   * Select all items
   */
  async selectAllItems() {
    await this.page.check(this.selectAllCheckbox);
  }

  /**
   * View item details
   */
  async viewItemDetails(index: number) {
    const item = this.page.locator(this.historyItem).nth(index);
    await item.locator(this.viewDetailsButton).click();
  }

  /**
   * Copy item
   */
  async copyItem(index: number) {
    const item = this.page.locator(this.historyItem).nth(index);
    await item.locator(this.copyButton).click();
  }

  /**
   * Download item
   */
  async downloadItem(index: number) {
    const item = this.page.locator(this.historyItem).nth(index);
    const [download] = await Promise.all([
      this.page.waitForEvent('download'),
      item.locator(this.downloadButton).click(),
    ]);
    return download;
  }

  /**
   * Delete item
   */
  async deleteItem(index: number) {
    const item = this.page.locator(this.historyItem).nth(index);
    await item.locator(this.deleteButton).click();
    await this.page.click('[data-testid="confirm-delete"]');
    await this.waitForNetworkIdle();
  }

  /**
   * Toggle favorite
   */
  async toggleFavorite(index: number) {
    const item = this.page.locator(this.historyItem).nth(index);
    await item.locator(this.favoriteButton).click();
  }

  /**
   * Export selected items
   */
  async exportSelected(format: 'json' | 'csv' | 'pdf' = 'json') {
    await this.clickWithRetry(this.exportSelectedButton);
    await this.waitForElement(this.exportModal);
    await this.page.selectOption(this.exportFormatSelect, format);
    
    const [download] = await Promise.all([
      this.page.waitForEvent('download'),
      this.page.click(this.exportButton),
    ]);
    
    return download;
  }

  /**
   * Delete selected items
   */
  async deleteSelected() {
    await this.clickWithRetry(this.deleteSelectedButton);
    await this.page.click('[data-testid="confirm-bulk-delete"]');
    await this.waitForNetworkIdle();
  }

  /**
   * Load more items
   */
  async loadMore() {
    const isVisible = await this.isVisible(this.loadMoreButton);
    if (isVisible) {
      await this.clickWithRetry(this.loadMoreButton);
      await this.waitForNetworkIdle();
    }
  }

  /**
   * Navigate to next page
   */
  async nextPage() {
    await this.clickWithRetry(this.nextButton);
    await this.waitForNetworkIdle();
  }

  /**
   * Navigate to previous page
   */
  async previousPage() {
    await this.clickWithRetry(this.previousButton);
    await this.waitForNetworkIdle();
  }

  /**
   * Get pagination info
   */
  async getPaginationInfo(): Promise<string> {
    return await this.getText(this.paginationInfo);
  }

  /**
   * Check if history is empty
   */
  async isEmpty(): Promise<boolean> {
    return await this.isVisible(this.emptyState);
  }

  /**
   * Get empty state message
   */
  async getEmptyStateMessage(): Promise<string> {
    return await this.getText(this.emptyState);
  }

  /**
   * Verify page loaded
   */
  async verifyPageLoaded() {
    await this.expectToBeVisible(this.searchInput);
    await this.expectToBeVisible(this.dateFilter);
    const isEmpty = await this.isEmpty();
    if (!isEmpty) {
      await this.expectToBeVisible(this.historyList);
    }
  }

  /**
   * Check filtered results
   */
  async checkFilteredResults(expectedCount?: number) {
    const count = await this.getHistoryItemCount();
    const paginationInfo = await this.getPaginationInfo();
    
    return {
      itemCount: count,
      paginationInfo,
      hasResults: count > 0,
      matchesExpected: expectedCount ? count === expectedCount : true,
    };
  }
}