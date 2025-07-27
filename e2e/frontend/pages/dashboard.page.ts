import { Page } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Dashboard Page Object Model
 * User dashboard with stats and quick actions
 */
export class DashboardPage extends BasePage {
  // Navigation locators
  private readonly userMenu = '[data-testid="user-menu"]';
  private readonly notificationBell = '[data-testid="notification-bell"]';
  private readonly quickEnhanceButton = '[data-testid="quick-enhance"]';
  
  // Stats card locators
  private readonly totalEnhancementsCard = '[data-testid="stat-total-enhancements"]';
  private readonly techniqueUsageCard = '[data-testid="stat-technique-usage"]';
  private readonly savedTimeCard = '[data-testid="stat-saved-time"]';
  private readonly accuracyCard = '[data-testid="stat-accuracy"]';
  
  // Recent activity locators
  private readonly recentActivitySection = '[data-testid="recent-activity"]';
  private readonly activityItem = '[data-testid="activity-item"]';
  private readonly viewAllActivityLink = 'a:has-text("View all activity")';
  
  // Quick actions locators
  private readonly newEnhancementButton = 'button:has-text("New Enhancement")';
  private readonly viewHistoryButton = 'button:has-text("View History")';
  private readonly browseTemplatesButton = 'button:has-text("Browse Templates")';
  private readonly apiDocsButton = 'button:has-text("API Documentation")';
  
  // Favorite techniques locators
  private readonly favoriteTechniquesSection = '[data-testid="favorite-techniques"]';
  private readonly techniqueCard = '[data-testid="technique-card"]';
  private readonly manageTechniquesLink = 'a:has-text("Manage techniques")';
  
  // Persona-specific elements
  private readonly apiKeySection = '[data-testid="api-key-section"]'; // Alex, Dr. Chen
  private readonly teamSection = '[data-testid="team-section"]'; // Maria, TechCorp
  private readonly complianceSection = '[data-testid="compliance-section"]'; // TechCorp

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to dashboard
   */
  async goto() {
    await super.goto('/dashboard');
    await this.waitForElement(this.totalEnhancementsCard);
  }

  /**
   * Get stat value
   */
  async getStatValue(statType: 'enhancements' | 'techniques' | 'time' | 'accuracy'): Promise<string> {
    const statMap = {
      enhancements: this.totalEnhancementsCard,
      techniques: this.techniqueUsageCard,
      time: this.savedTimeCard,
      accuracy: this.accuracyCard,
    };
    
    const card = this.page.locator(statMap[statType]);
    const value = await card.locator('[data-testid="stat-value"]').textContent();
    return value || '0';
  }

  /**
   * Get all stats
   */
  async getAllStats() {
    return {
      totalEnhancements: await this.getStatValue('enhancements'),
      techniqueUsage: await this.getStatValue('techniques'),
      savedTime: await this.getStatValue('time'),
      accuracy: await this.getStatValue('accuracy'),
    };
  }

  /**
   * Get recent activity count
   */
  async getRecentActivityCount(): Promise<number> {
    return await this.page.locator(this.activityItem).count();
  }

  /**
   * Get recent activity item
   */
  async getActivityItem(index: number) {
    const item = this.page.locator(this.activityItem).nth(index);
    return {
      title: await item.locator('[data-testid="activity-title"]').textContent(),
      time: await item.locator('[data-testid="activity-time"]').textContent(),
      technique: await item.locator('[data-testid="activity-technique"]').textContent(),
    };
  }

  /**
   * Click view all activity
   */
  async viewAllActivity() {
    await this.clickWithRetry(this.viewAllActivityLink);
  }

  /**
   * Start new enhancement
   */
  async startNewEnhancement() {
    await this.clickWithRetry(this.newEnhancementButton);
  }

  /**
   * View enhancement history
   */
  async viewHistory() {
    await this.clickWithRetry(this.viewHistoryButton);
  }

  /**
   * Browse templates
   */
  async browseTemplates() {
    await this.clickWithRetry(this.browseTemplatesButton);
  }

  /**
   * Open API documentation
   */
  async openAPIDocs() {
    await this.clickWithRetry(this.apiDocsButton);
  }

  /**
   * Get favorite techniques count
   */
  async getFavoriteTechniquesCount(): Promise<number> {
    return await this.page.locator(this.favoriteTechniquesSection).locator(this.techniqueCard).count();
  }

  /**
   * Select favorite technique
   */
  async selectFavoriteTechnique(techniqueName: string) {
    const techniques = this.page.locator(this.favoriteTechniquesSection).locator(this.techniqueCard);
    const count = await techniques.count();
    
    for (let i = 0; i < count; i++) {
      const technique = techniques.nth(i);
      const name = await technique.locator('h4').textContent();
      if (name?.includes(techniqueName)) {
        await technique.click();
        break;
      }
    }
  }

  /**
   * Manage techniques
   */
  async manageTechniques() {
    await this.clickWithRetry(this.manageTechniquesLink);
  }

  /**
   * Open user menu
   */
  async openUserMenu() {
    await this.clickWithRetry(this.userMenu);
  }

  /**
   * Check notifications
   */
  async checkNotifications() {
    await this.clickWithRetry(this.notificationBell);
  }

  /**
   * Get notification count
   */
  async getNotificationCount(): Promise<number> {
    const badge = this.page.locator(this.notificationBell).locator('[data-testid="notification-count"]');
    const count = await badge.textContent();
    return parseInt(count || '0', 10);
  }

  /**
   * Quick enhance from dashboard
   */
  async quickEnhance(prompt: string) {
    await this.clickWithRetry(this.quickEnhanceButton);
    await this.page.fill('[data-testid="quick-enhance-input"]', prompt);
    await this.page.click('[data-testid="quick-enhance-submit"]');
  }

  /**
   * Check if API key section is visible (for developers)
   */
  async isAPIKeySectionVisible(): Promise<boolean> {
    return await this.isVisible(this.apiKeySection);
  }

  /**
   * Get API key
   */
  async getAPIKey(): Promise<string> {
    const keyElement = this.page.locator('[data-testid="api-key-value"]');
    return await keyElement.textContent() || '';
  }

  /**
   * Regenerate API key
   */
  async regenerateAPIKey() {
    await this.clickWithRetry('[data-testid="regenerate-api-key"]');
    await this.page.click('[data-testid="confirm-regenerate"]');
  }

  /**
   * Check if team section is visible (for team users)
   */
  async isTeamSectionVisible(): Promise<boolean> {
    return await this.isVisible(this.teamSection);
  }

  /**
   * Get team member count
   */
  async getTeamMemberCount(): Promise<number> {
    const count = await this.page.locator('[data-testid="team-member-count"]').textContent();
    return parseInt(count || '0', 10);
  }

  /**
   * Check if compliance section is visible (for enterprise)
   */
  async isComplianceSectionVisible(): Promise<boolean> {
    return await this.isVisible(this.complianceSection);
  }

  /**
   * Verify dashboard loaded
   */
  async verifyPageLoaded() {
    await this.expectToBeVisible(this.totalEnhancementsCard);
    await this.expectToBeVisible(this.recentActivitySection);
    await this.expectToBeVisible(this.newEnhancementButton);
  }

  /**
   * Check dashboard performance
   */
  async checkDashboardPerformance() {
    const metrics = await this.getPerformanceMetrics();
    const statsLoaded = await this.page.locator('[data-testid="stat-value"]').first().isVisible();
    
    return {
      loadTime: metrics.loadComplete,
      firstPaint: metrics.firstPaint,
      statsVisible: statsLoaded,
      activityLoaded: await this.isVisible(this.recentActivitySection),
    };
  }
}