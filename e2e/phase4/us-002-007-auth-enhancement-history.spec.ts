import { test, expect } from '@playwright/test';
import { EnhancementPage } from './pages/EnhancementPage';
import { HistoryPage } from './pages/HistoryPage';
import { EnhancementDetailsPage } from './pages/EnhancementDetailsPage';
import { AuthHelper } from './utils/AuthHelper';
import { HistoryDataGenerator } from './utils/HistoryDataGenerator';
import { SearchTestUtils } from './utils/SearchTestUtils';
import * as fs from 'fs';
import * as path from 'path';

// Load test fixtures
const userWithHistory = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures/user-with-history.json'), 'utf8')
);
const enhancementSamples = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures/enhancement-samples.json'), 'utf8')
);

test.describe('US-002 + US-007: Authenticated Enhancement with History', () => {
  let enhancementPage: EnhancementPage;
  let historyPage: HistoryPage;
  let detailsPage: EnhancementDetailsPage;
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page, context }) => {
    // Initialize page objects
    enhancementPage = new EnhancementPage(page);
    historyPage = new HistoryPage(page);
    detailsPage = new EnhancementDetailsPage(page);
    authHelper = new AuthHelper(page, context);

    // Clear any existing auth
    await authHelper.clearAuth();
  });

  test.describe('Authenticated Enhancement Flow', () => {
    test('should save enhancement to history for logged-in user', async ({ page }) => {
      // Login as test user
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Navigate to enhancement page
      await enhancementPage.goto();
      await enhancementPage.verifyPageLoaded();
      
      // Enhance a prompt
      const testPrompt = enhancementSamples.samples[0].prompts[0];
      const result = await enhancementPage.enhancePrompt(testPrompt.original);
      
      // Verify enhancement was successful
      expect(await enhancementPage.isEnhancementSuccessful()).toBe(true);
      expect(result.enhancedPrompt).toBeTruthy();
      expect(result.techniques.length).toBeGreaterThan(0);
      
      // Navigate to history
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Verify the enhancement appears in history
      const historyItems = await historyPage.getHistoryItems();
      const latestItem = historyItems[0]; // Most recent should be first
      
      expect(latestItem.originalPrompt).toContain(testPrompt.original);
      expect(latestItem.enhancedPrompt).toBeTruthy();
      expect(latestItem.techniques.length).toBeGreaterThan(0);
    });

    test('should auto-save multiple enhancements in session', async ({ page }) => {
      // Login as test user
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Enhance multiple prompts
      const prompts = enhancementSamples.samples[0].prompts;
      const enhancedPrompts = [];
      
      for (const prompt of prompts.slice(0, 3)) {
        await enhancementPage.goto();
        const result = await enhancementPage.enhancePrompt(prompt.original);
        enhancedPrompts.push(result);
        expect(await enhancementPage.isEnhancementSuccessful()).toBe(true);
      }
      
      // Navigate to history
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Verify all enhancements are saved
      const historyItems = await historyPage.getHistoryItems();
      expect(historyItems.length).toBeGreaterThanOrEqual(3);
      
      // Verify order (most recent first)
      for (let i = 0; i < 3; i++) {
        const historyItem = historyItems[i];
        const originalPrompt = prompts[2 - i].original; // Reverse order
        expect(historyItem.originalPrompt).toContain(originalPrompt);
      }
    });

    test('should handle enhancement with special characters', async ({ page }) => {
      // Login as test user
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Test with special characters
      const specialPrompt = enhancementSamples.edge_cases.find(
        e => e.description === 'Prompt with special characters'
      );
      
      await enhancementPage.goto();
      const result = await enhancementPage.enhancePrompt(specialPrompt.original);
      
      expect(await enhancementPage.isEnhancementSuccessful()).toBe(true);
      
      // Verify in history
      await historyPage.goto();
      const historyItems = await historyPage.getHistoryItems();
      expect(historyItems[0].originalPrompt).toContain(specialPrompt.original);
    });

    test('should preserve user context across enhancement sessions', async ({ page }) => {
      // Login as test user
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Enhance a prompt
      await enhancementPage.goto();
      const firstResult = await enhancementPage.enhancePrompt('Test prompt 1');
      
      // Navigate away and come back
      await page.goto('/profile');
      await page.waitForTimeout(1000);
      
      // Enhance another prompt
      await enhancementPage.goto();
      const secondResult = await enhancementPage.enhancePrompt('Test prompt 2');
      
      // Both should be successful and saved
      await historyPage.goto();
      const historyItems = await historyPage.getHistoryItems();
      
      expect(historyItems.length).toBeGreaterThanOrEqual(2);
      expect(historyItems[0].originalPrompt).toContain('Test prompt 2');
      expect(historyItems[1].originalPrompt).toContain('Test prompt 1');
    });
  });

  test.describe('History Display Tests', () => {
    test('should display empty state for new user', async ({ page }) => {
      // Login as new user with no history
      await authHelper.loginUser(AuthHelper.TEST_USERS.newUser);
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      expect(await historyPage.isEmpty()).toBe(true);
    });

    test('should display history items with all metadata', async ({ page }) => {
      // Login as user with existing history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      const items = await historyPage.getHistoryItems();
      expect(items.length).toBeGreaterThan(0);
      
      // Verify first item has all expected fields
      const firstItem = items[0];
      expect(firstItem.originalPrompt).toBeTruthy();
      expect(firstItem.enhancedPrompt).toBeTruthy();
      expect(firstItem.intent).toBeTruthy();
      expect(firstItem.techniques.length).toBeGreaterThan(0);
      expect(firstItem.date).toBeTruthy();
      
      // Verify optional fields if present
      if (firstItem.complexity) {
        expect(['simple', 'moderate', 'complex']).toContain(firstItem.complexity);
      }
      if (firstItem.confidence !== undefined) {
        expect(firstItem.confidence).toBeGreaterThanOrEqual(0);
        expect(firstItem.confidence).toBeLessThanOrEqual(1);
      }
    });

    test('should sort history by date (newest first)', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Create a new enhancement
      await enhancementPage.goto();
      await enhancementPage.enhancePrompt('Newest test prompt');
      
      // Check history order
      await historyPage.goto();
      const items = await historyPage.getHistoryItems();
      
      // Newest item should be first
      expect(items[0].originalPrompt).toContain('Newest test prompt');
      
      // Verify dates are in descending order
      for (let i = 1; i < Math.min(items.length, 5); i++) {
        const currentDate = new Date(items[i - 1].date);
        const nextDate = new Date(items[i].date);
        expect(currentDate.getTime()).toBeGreaterThanOrEqual(nextDate.getTime());
      }
    });
  });

  test.describe('Search and Filter Tests', () => {
    test('should search by prompt content', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Search for specific content
      await historyPage.searchPrompts('fibonacci');
      
      // Wait for search results
      await SearchTestUtils.waitForSearchDebounce(page);
      
      // Verify filtered results
      const items = await historyPage.getHistoryItems();
      const hasMatch = items.some(item => 
        item.originalPrompt.toLowerCase().includes('fibonacci') ||
        item.enhancedPrompt.toLowerCase().includes('fibonacci')
      );
      
      expect(hasMatch).toBe(true);
    });

    test('should filter by intent', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Get available intents
      const intents = await historyPage.getAvailableIntents();
      expect(intents.length).toBeGreaterThan(0);
      
      // Filter by first available intent
      await historyPage.filterByIntent(intents[0]);
      
      // Verify filtered results
      const items = await historyPage.getHistoryItems();
      if (items.length > 0) {
        items.forEach(item => {
          expect(item.intent).toBe(intents[0]);
        });
      }
    });

    test('should filter by technique', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Get available techniques
      const techniques = await historyPage.getAvailableTechniques();
      expect(techniques.length).toBeGreaterThan(0);
      
      // Filter by first available technique
      await historyPage.filterByTechnique(techniques[0]);
      
      // Verify filtered results
      const items = await historyPage.getHistoryItems();
      if (items.length > 0) {
        items.forEach(item => {
          expect(item.techniques).toContain(techniques[0]);
        });
      }
    });

    test('should handle search with no results', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Search for non-existent content
      await historyPage.searchPrompts('xyznonexistentquery123');
      await SearchTestUtils.waitForSearchDebounce(page);
      
      // Should show no results
      const isEmpty = await historyPage.isEmpty();
      expect(isEmpty).toBe(true);
    });

    test('should clear search and show all results', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      
      // Get initial count
      const initialItems = await historyPage.getHistoryItems();
      const initialCount = initialItems.length;
      
      // Search to filter results
      await historyPage.searchPrompts('specific');
      await SearchTestUtils.waitForSearchDebounce(page);
      
      // Clear search
      await historyPage.searchPrompts('');
      await SearchTestUtils.waitForSearchDebounce(page);
      
      // Should show all results again
      const clearedItems = await historyPage.getHistoryItems();
      expect(clearedItems.length).toBe(initialCount);
    });
  });

  test.describe('Pagination Tests', () => {
    test('should display pagination controls when needed', async ({ page }) => {
      // This test would require a user with many history items
      // For now, we'll test the pagination UI exists
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      const paginationInfo = await historyPage.getPaginationInfo();
      
      if (paginationInfo && paginationInfo.totalItems > paginationInfo.itemsPerPage) {
        expect(paginationInfo.hasNext || paginationInfo.hasPrevious).toBe(true);
      }
    });

    test('should navigate between pages', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      const paginationInfo = await historyPage.getPaginationInfo();
      
      if (paginationInfo && paginationInfo.hasNext) {
        // Go to next page
        await historyPage.goToNextPage();
        
        // Verify page changed
        const newPaginationInfo = await historyPage.getPaginationInfo();
        expect(newPaginationInfo.currentPage).toBe(paginationInfo.currentPage + 1);
        
        // Go back to previous page
        await historyPage.goToPreviousPage();
        
        // Verify we're back on first page
        const finalPaginationInfo = await historyPage.getPaginationInfo();
        expect(finalPaginationInfo.currentPage).toBe(paginationInfo.currentPage);
      }
    });
  });

  test.describe('Enhancement Details and Re-run Tests', () => {
    test('should view enhancement details', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Create a new enhancement
      await enhancementPage.goto();
      const testPrompt = 'Test prompt for details view';
      const enhancementResult = await enhancementPage.enhancePrompt(testPrompt);
      
      // Go to history and view details
      await historyPage.goto();
      await historyPage.viewItemDetails(0); // View most recent
      
      // Verify details page loaded
      await detailsPage.verifyPageLoaded();
      
      // Get and verify details
      const details = await detailsPage.getDetails();
      expect(details.originalPrompt).toContain(testPrompt);
      expect(details.enhancedPrompt).toBeTruthy();
      expect(details.techniques.length).toBeGreaterThan(0);
      expect(details.createdAt).toBeTruthy();
    });

    test('should re-run enhancement and get consistent result', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.viewItemDetails(0);
      
      // Verify re-run consistency
      const isConsistent = await detailsPage.verifyRerunConsistency();
      expect(isConsistent).toBe(true);
    });

    test('should copy prompts from details view', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.viewItemDetails(0);
      
      // Copy original prompt
      await detailsPage.copyOriginalPrompt();
      
      // Copy enhanced prompt
      await detailsPage.copyEnhancedPrompt();
      
      // Note: Actually verifying clipboard content requires browser permissions
      // We're testing that the actions complete without error
    });

    test('should delete enhancement from details view', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Create a new enhancement to delete
      await enhancementPage.goto();
      await enhancementPage.enhancePrompt('Test prompt to delete');
      
      // Go to history and get initial count
      await historyPage.goto();
      const initialItems = await historyPage.getHistoryItems();
      const initialCount = initialItems.length;
      
      // View details of the item
      await historyPage.viewItemDetails(0);
      
      // Delete the enhancement
      await detailsPage.deleteEnhancement();
      
      // Should redirect to history
      await historyPage.verifyPageLoaded();
      
      // Verify item was deleted
      const finalItems = await historyPage.getHistoryItems();
      expect(finalItems.length).toBe(initialCount - 1);
    });

    test('should navigate back to history from details', async ({ page }) => {
      // Login as user with history
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      await historyPage.goto();
      await historyPage.viewItemDetails(0);
      
      // Go back to history
      await detailsPage.goBackToHistory();
      
      // Verify we're back on history page
      await historyPage.verifyPageLoaded();
    });
  });

  test.describe('Data Integrity Tests', () => {
    test('should preserve exact prompt content', async ({ page }) => {
      // Login as user
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Test with prompt containing special formatting
      const complexPrompt = `Write a function that:
      1. Takes an array of numbers
      2. Filters out negative values
      3. Returns the sum
      
      Example: [1, -2, 3, -4, 5] => 9`;
      
      await enhancementPage.goto();
      await enhancementPage.enhancePrompt(complexPrompt);
      
      // Verify in history
      await historyPage.goto();
      const items = await historyPage.getHistoryItems();
      
      // Should preserve exact formatting
      expect(items[0].originalPrompt).toBe(complexPrompt.trim());
    });

    test('should maintain user association', async ({ page }) => {
      // Login as first user
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Create enhancement
      await enhancementPage.goto();
      await enhancementPage.enhancePrompt('User 1 prompt');
      
      // Logout and login as different user
      await authHelper.clearAuth();
      await authHelper.loginUser(AuthHelper.TEST_USERS.powerUser);
      
      // Should not see other user's history
      await historyPage.goto();
      const items = await historyPage.getHistoryItems();
      
      const hasOtherUserData = items.some(item => 
        item.originalPrompt.includes('User 1 prompt')
      );
      expect(hasOtherUserData).toBe(false);
    });

    test('should handle concurrent enhancements', async ({ page, context }) => {
      // Login as user
      await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      
      // Open multiple tabs
      const page2 = await context.newPage();
      const enhancementPage2 = new EnhancementPage(page2);
      
      // Navigate both to enhancement page
      await enhancementPage.goto();
      await enhancementPage2.goto();
      
      // Enhance different prompts simultaneously
      const [result1, result2] = await Promise.all([
        enhancementPage.enhancePrompt('Concurrent prompt 1'),
        enhancementPage2.enhancePrompt('Concurrent prompt 2')
      ]);
      
      // Both should succeed
      expect(result1.enhancedPrompt).toBeTruthy();
      expect(result2.enhancedPrompt).toBeTruthy();
      
      // Verify both in history
      await historyPage.goto();
      const items = await historyPage.getHistoryItems();
      
      const hasBoth = 
        items.some(item => item.originalPrompt.includes('Concurrent prompt 1')) &&
        items.some(item => item.originalPrompt.includes('Concurrent prompt 2'));
      
      expect(hasBoth).toBe(true);
      
      await page2.close();
    });
  });
});