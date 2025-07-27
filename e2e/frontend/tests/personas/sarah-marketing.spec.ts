import { test, expect } from '@playwright/test';
import { HomePage } from '../../pages/home.page';
import { LoginPage } from '../../pages/auth/login.page';
import { RegisterPage } from '../../pages/auth/register.page';
import { DashboardPage } from '../../pages/dashboard.page';
import { EnhancePage } from '../../pages/enhance.page';
import { HistoryPage } from '../../pages/history.page';
import { testUsers } from '../../fixtures/users';
import { testPrompts } from '../../fixtures/prompts';
import * as helpers from '../../utils/test-helpers';

/**
 * Sarah - Marketing Manager Test Suite
 * Basic user persona focused on simple prompt enhancement
 * User Stories: US-001, US-002, US-003
 */

test.describe('Sarah - Marketing Manager User Journey', () => {
  const sarah = testUsers.sarah;
  const sarahPrompts = [
    testPrompts.sarahSimple,
    testPrompts.sarahModerate,
    testPrompts.sarahComplex,
  ];

  test.beforeEach(async ({ page }) => {
    // Start from home page
    const homePage = new HomePage(page);
    await homePage.goto();
  });

  test.describe('US-001: First-time User Experience', () => {
    test('@critical @sarah First-time visitor can explore and sign up', async ({ page }) => {
      const homePage = new HomePage(page);
      const registerPage = new RegisterPage(page);
      
      // Verify landing page
      await homePage.verifyPageLoaded();
      await expect(page).toHaveTitle(/BetterPrompts/);
      
      // Check features section
      const featureCount = await homePage.getFeatureCardsCount();
      expect(featureCount).toBeGreaterThanOrEqual(3);
      
      // Navigate to sign up
      await homePage.clickGetStarted();
      await page.waitForURL('**/register');
      
      // Complete registration
      const uniqueEmail = helpers.generateUniqueEmail('sarah');
      await registerPage.register({
        name: sarah.name,
        email: uniqueEmail,
        password: sarah.password,
      });
      
      // Verify successful registration
      await registerPage.waitForRegistrationSuccess();
      
      // Take screenshot for visual regression
      await helpers.compareScreenshots(page, 'sarah-registration-success');
    });

    test('@smoke @sarah Navigate to learn more', async ({ page }) => {
      const homePage = new HomePage(page);
      
      // Click learn more
      await homePage.clickTryDemo(); // This clicks "Learn More" button
      await page.waitForURL('**/docs');
      
      // Verify docs page loaded
      await expect(page).toHaveURL(/.*\/docs/);
      await expect(page.locator('h1')).toBeVisible();
    });
  });

  test.describe('US-002: Basic Prompt Enhancement', () => {
    test.use({
      storageState: 'auth-sarah.json',
    });

    test.beforeAll(async ({ browser }) => {
      // Create authenticated session
      const context = await helpers.createAuthenticatedContext(browser, sarah);
      await context.close();
    });

    test('@critical @sarah @smoke Enhance marketing copy', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      // Navigate to enhance page
      await enhancePage.goto();
      
      // Enter marketing prompt
      await enhancePage.enterPrompt(sarahPrompts[0].text);
      
      // Check character count
      const charCount = await enhancePage.getCharacterCount();
      expect(charCount).toContain(sarahPrompts[0].text.length.toString());
      
      // Enhance prompt
      await enhancePage.clickEnhance();
      
      // Measure enhancement time
      const { duration, output } = await enhancePage.measureEnhancementTime();
      expect(duration).toBeLessThan(3000); // Should complete within 3s
      
      // Verify enhancement
      expect(output).toBeTruthy();
      expect(output).not.toBe(sarahPrompts[0].text);
      
      // Check suggested techniques
      const techniques = await enhancePage.getSelectedTechniques();
      expect(techniques).toContain('audience_targeting');
      
      // Copy result
      await enhancePage.copyOutput();
      
      // Verify clipboard (if supported)
      if (page.context().grantPermissions) {
        await page.context().grantPermissions(['clipboard-read']);
        const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
        expect(clipboardText).toBe(output);
      }
    });

    test('@regression @sarah Select specific technique', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Select emotional appeal technique
      await enhancePage.selectTechnique('Emotional Appeal');
      
      // Enhance with selected technique
      const result = await enhancePage.enhancePrompt(
        sarahPrompts[1].text,
        'Emotional Appeal'
      );
      
      // Verify technique was applied
      expect(result.toLowerCase()).toMatch(/feel|emotion|connect|inspire/);
    });

    test('@regression @sarah Handle long prompts', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Enter complex marketing prompt
      await enhancePage.enterPrompt(sarahPrompts[2].text);
      
      // Enhance
      await enhancePage.clickEnhance();
      
      // Check progress indicator
      const progress = await enhancePage.getProgress();
      expect(parseInt(progress)).toBeGreaterThan(0);
      
      // Wait for completion
      await enhancePage.waitForEnhancement();
      
      // Verify structured output
      const output = await enhancePage.getEnhancedOutput();
      expect(output).toContain('market'); // Should maintain context
      expect(output.split('\n').length).toBeGreaterThan(5); // Should be structured
    });
  });

  test.describe('US-003: Save and Access Favorites', () => {
    test.use({
      storageState: 'auth-sarah.json',
    });

    test('@critical @sarah Save enhancement to favorites', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      const historyPage = new HistoryPage(page);
      
      // Create enhancement
      await enhancePage.goto();
      await enhancePage.enhancePrompt(sarahPrompts[0].text);
      
      // Open feedback/save dialog
      await enhancePage.openFeedback();
      
      // Save as favorite
      const favoriteButton = page.locator('button:has-text("Save as Favorite")');
      await favoriteButton.click();
      
      // Navigate to history
      await historyPage.goto();
      
      // Filter by favorites
      await historyPage.filterByStatus('all'); // Reset first
      const favoriteFilter = page.locator('input[data-testid="favorites-only"]');
      await favoriteFilter.check();
      
      // Verify favorite is shown
      const itemCount = await historyPage.getHistoryItemCount();
      expect(itemCount).toBeGreaterThanOrEqual(1);
      
      // Check favorite item
      const item = await historyPage.getHistoryItem(0);
      expect(item.preview).toContain(sarahPrompts[0].text.substring(0, 50));
    });

    test('@regression @sarah Access from dashboard quick actions', async ({ page }) => {
      const dashboardPage = new DashboardPage(page);
      
      await dashboardPage.goto();
      
      // Check favorite techniques section
      const favCount = await dashboardPage.getFavoriteTechniquesCount();
      expect(favCount).toBeGreaterThanOrEqual(0);
      
      // Use quick enhance
      await dashboardPage.quickEnhance('Quick social media post');
      
      // Wait for result
      await page.waitForSelector('[data-testid="quick-enhance-result"]');
      const result = await page.locator('[data-testid="quick-enhance-result"]').textContent();
      expect(result).toBeTruthy();
    });
  });

  test.describe('Edge Cases and Error Handling', () => {
    test.use({
      storageState: 'auth-sarah.json',
    });

    test('@regression @sarah Handle empty prompt', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Try to enhance without entering prompt
      await enhancePage.clickEnhance();
      
      // Should show validation error
      const error = page.locator('[data-testid="prompt-error"]');
      await expect(error).toBeVisible();
      await expect(error).toHaveText(/enter a prompt/i);
    });

    test('@regression @sarah Handle network error gracefully', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      // Mock network error
      await page.route('**/api/v1/enhance', (route) => {
        route.abort('failed');
      });
      
      await enhancePage.goto();
      await enhancePage.enterPrompt(sarahPrompts[0].text);
      await enhancePage.clickEnhance();
      
      // Should show error message
      const errorMessage = page.locator('[data-testid="error-message"]');
      await expect(errorMessage).toBeVisible();
      await expect(errorMessage).toHaveText(/try again/i);
    });
  });

  test.describe('Performance and Accessibility', () => {
    test('@performance @sarah Check page load performance', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Check performance metrics
      await helpers.checkPerformance(page, {
        lcp: 2500, // 2.5s
        ttfb: 800, // 800ms
      });
    });

    test('@accessibility @sarah Verify accessibility compliance', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Run accessibility checks
      await helpers.checkAccessibility(page, {
        detailedReport: true,
        includedImpacts: ['critical', 'serious'],
      });
      
      // Check keyboard navigation
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBeTruthy();
      
      // Check ARIA labels
      const enhanceButton = page.locator('button[data-testid="enhance-button"]');
      const ariaLabel = await enhanceButton.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
    });
  });
});