import { test, expect } from '@playwright/test';
import { HistoryPage } from './pages/HistoryPage';
import { EnhancementPage } from './pages/EnhancementPage';
import { EnhancementDetailsPage } from './pages/EnhancementDetailsPage';
import { AuthHelper } from './utils/AuthHelper';
import { HistoryDataGenerator } from './utils/HistoryDataGenerator';
import { SearchTestUtils } from './utils/SearchTestUtils';

// Performance SLAs
const PERFORMANCE_SLA = {
  historyLoad: 2000, // 2 seconds
  searchResponse: 500, // 500ms
  paginationSwitch: 200, // 200ms
  detailsLoad: 1000, // 1 second
  enhancementSave: 1000, // 1 second
};

test.describe('History Performance Tests', () => {
  let historyPage: HistoryPage;
  let enhancementPage: EnhancementPage;
  let detailsPage: EnhancementDetailsPage;
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page, context }) => {
    // Initialize page objects
    historyPage = new HistoryPage(page);
    enhancementPage = new EnhancementPage(page);
    detailsPage = new EnhancementDetailsPage(page);
    authHelper = new AuthHelper(page, context);

    // Login as test user
    await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
  });

  test.describe('Page Load Performance', () => {
    test('should load history page within SLA', async ({ page }) => {
      const startTime = Date.now();
      
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(PERFORMANCE_SLA.historyLoad);
      console.log(`History page loaded in ${loadTime}ms (SLA: ${PERFORMANCE_SLA.historyLoad}ms)`);
    });

    test('should load enhancement details within SLA', async ({ page }) => {
      // Navigate to history first
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Ensure we have at least one item
      const items = await historyPage.getHistoryItems();
      if (items.length === 0) {
        // Create one if needed
        await enhancementPage.goto();
        await enhancementPage.enhancePrompt('Test prompt for performance');
        await historyPage.goto();
      }
      
      // Measure details page load time
      const startTime = Date.now();
      
      await historyPage.viewItemDetails(0);
      await detailsPage.verifyPageLoaded();
      
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(PERFORMANCE_SLA.detailsLoad);
      console.log(`Details page loaded in ${loadTime}ms (SLA: ${PERFORMANCE_SLA.detailsLoad}ms)`);
    });
  });

  test.describe('Search Performance', () => {
    test('should respond to search queries within SLA', async ({ page }) => {
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Measure search performance
      const searchPerf = await SearchTestUtils.measureSearchPerformance(page, async () => {
        await historyPage.searchPrompts('test');
        await SearchTestUtils.waitForSearchDebounce(page);
      });
      
      expect(searchPerf.withinSLA).toBe(true);
      console.log(`Search completed in ${searchPerf.duration}ms (SLA: ${searchPerf.SLA}ms)`);
    });

    test('should handle rapid search queries efficiently', async ({ page }) => {
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Simulate rapid typing
      const queries = ['t', 'te', 'tes', 'test', 'test p', 'test pr', 'test pro', 'test prom'];
      const searchTimes = [];
      
      for (const query of queries) {
        const startTime = Date.now();
        await page.fill('input[placeholder*="Search"]', query);
        // Don't wait for debounce on rapid typing
        await page.waitForTimeout(100);
        searchTimes.push(Date.now() - startTime);
      }
      
      // Final search should complete within SLA after debounce
      await SearchTestUtils.waitForSearchDebounce(page);
      
      // Average response time should be reasonable
      const avgTime = searchTimes.reduce((a, b) => a + b, 0) / searchTimes.length;
      expect(avgTime).toBeLessThan(200); // Quick response to typing
      console.log(`Average typing response: ${avgTime}ms`);
    });

    test('should handle complex search queries efficiently', async ({ page }) => {
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Test various complex queries
      const complexQueries = SearchTestUtils.getEdgeCaseQueries().slice(0, 5);
      
      for (const query of complexQueries) {
        const searchPerf = await SearchTestUtils.measureSearchPerformance(page, async () => {
          await historyPage.searchPrompts(query);
          await SearchTestUtils.waitForSearchDebounce(page);
        });
        
        expect(searchPerf.duration).toBeLessThan(PERFORMANCE_SLA.searchResponse * 2); // Allow 2x for edge cases
      }
    });
  });

  test.describe('Pagination Performance', () => {
    test('should switch pages within SLA', async ({ page }) => {
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      const paginationInfo = await historyPage.getPaginationInfo();
      
      if (paginationInfo && paginationInfo.hasNext) {
        const startTime = Date.now();
        
        await historyPage.goToNextPage();
        
        const switchTime = Date.now() - startTime;
        
        expect(switchTime).toBeLessThan(PERFORMANCE_SLA.paginationSwitch);
        console.log(`Page switch completed in ${switchTime}ms (SLA: ${PERFORMANCE_SLA.paginationSwitch}ms)`);
      } else {
        test.skip();
      }
    });

    test('should handle rapid pagination efficiently', async ({ page }) => {
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      const paginationInfo = await historyPage.getPaginationInfo();
      
      if (paginationInfo && paginationInfo.totalItems > paginationInfo.itemsPerPage * 3) {
        // Navigate forward and back rapidly
        const navigationTimes = [];
        
        for (let i = 0; i < 3; i++) {
          const startTime = Date.now();
          await historyPage.goToNextPage();
          navigationTimes.push(Date.now() - startTime);
        }
        
        for (let i = 0; i < 3; i++) {
          const startTime = Date.now();
          await historyPage.goToPreviousPage();
          navigationTimes.push(Date.now() - startTime);
        }
        
        const avgNavTime = navigationTimes.reduce((a, b) => a + b, 0) / navigationTimes.length;
        expect(avgNavTime).toBeLessThan(PERFORMANCE_SLA.paginationSwitch * 1.5);
        console.log(`Average pagination time: ${avgNavTime}ms`);
      } else {
        test.skip();
      }
    });
  });

  test.describe('Large Dataset Performance', () => {
    test('should handle large history efficiently', async ({ page }) => {
      // This test would require setup of a user with many history items
      // For now, we'll test with whatever data is available
      await historyPage.goto();
      
      const startTime = Date.now();
      await historyPage.verifyPageLoaded();
      const loadTime = Date.now() - startTime;
      
      const items = await historyPage.getHistoryItems();
      console.log(`Loaded ${items.length} items in ${loadTime}ms`);
      
      // Performance should not degrade significantly with more items
      expect(loadTime).toBeLessThan(PERFORMANCE_SLA.historyLoad * 1.5);
    });

    test('should filter large datasets efficiently', async ({ page }) => {
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Test filter performance
      const intents = await historyPage.getAvailableIntents();
      
      if (intents.length > 0) {
        const startTime = Date.now();
        await historyPage.filterByIntent(intents[0]);
        const filterTime = Date.now() - startTime;
        
        expect(filterTime).toBeLessThan(PERFORMANCE_SLA.searchResponse);
        console.log(`Filter applied in ${filterTime}ms`);
      }
    });
  });

  test.describe('Enhancement Save Performance', () => {
    test('should save enhancements quickly', async ({ page }) => {
      await enhancementPage.goto();
      await enhancementPage.verifyPageLoaded();
      
      const prompt = 'Performance test prompt';
      
      // Measure time from enhancement completion to history availability
      const startTime = Date.now();
      
      await enhancementPage.enhancePrompt(prompt);
      
      // Navigate to history immediately
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      
      // Verify the enhancement is saved
      const items = await historyPage.getHistoryItems();
      const saved = items.some(item => item.originalPrompt.includes(prompt));
      
      const saveTime = Date.now() - startTime;
      
      expect(saved).toBe(true);
      expect(saveTime).toBeLessThan(PERFORMANCE_SLA.enhancementSave + PERFORMANCE_SLA.historyLoad);
      console.log(`Enhancement saved and available in ${saveTime}ms`);
    });

    test('should handle concurrent saves efficiently', async ({ page, context }) => {
      // Open multiple tabs
      const pages = [page];
      for (let i = 0; i < 2; i++) {
        pages.push(await context.newPage());
      }
      
      // Create enhancement pages for each tab
      const enhancementPages = pages.map(p => new EnhancementPage(p));
      
      // Navigate all to enhancement page
      await Promise.all(enhancementPages.map(ep => ep.goto()));
      
      // Enhance prompts concurrently
      const startTime = Date.now();
      
      const results = await Promise.all(
        enhancementPages.map((ep, i) => 
          ep.enhancePrompt(`Concurrent performance test ${i}`)
        )
      );
      
      const concurrentTime = Date.now() - startTime;
      
      // All should succeed
      results.forEach(result => {
        expect(result.enhancedPrompt).toBeTruthy();
      });
      
      // Time should not scale linearly with concurrent requests
      expect(concurrentTime).toBeLessThan(PERFORMANCE_SLA.enhancementSave * 2);
      console.log(`${pages.length} concurrent enhancements completed in ${concurrentTime}ms`);
      
      // Cleanup
      for (let i = 1; i < pages.length; i++) {
        await pages[i].close();
      }
    });
  });

  test.describe('Memory and Resource Usage', () => {
    test('should not leak memory during extended use', async ({ page }) => {
      // Perform multiple operations
      for (let i = 0; i < 5; i++) {
        // Navigate to history
        await historyPage.goto();
        await historyPage.verifyPageLoaded();
        
        // Perform search
        await historyPage.searchPrompts(`test ${i}`);
        await SearchTestUtils.waitForSearchDebounce(page);
        
        // Clear search
        await historyPage.searchPrompts('');
        await SearchTestUtils.waitForSearchDebounce(page);
        
        // Navigate to enhancement
        await enhancementPage.goto();
        await enhancementPage.enhancePrompt(`Memory test prompt ${i}`);
      }
      
      // Check that performance hasn't degraded
      const finalLoadStart = Date.now();
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      const finalLoadTime = Date.now() - finalLoadStart;
      
      expect(finalLoadTime).toBeLessThan(PERFORMANCE_SLA.historyLoad);
      console.log(`Final load time after extended use: ${finalLoadTime}ms`);
    });
  });

  test.describe('Network Optimization', () => {
    test('should cache static resources effectively', async ({ page }) => {
      // First load
      const firstLoadStart = Date.now();
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      const firstLoadTime = Date.now() - firstLoadStart;
      
      // Navigate away and back
      await enhancementPage.goto();
      
      // Second load should be faster due to caching
      const secondLoadStart = Date.now();
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      const secondLoadTime = Date.now() - secondLoadStart;
      
      // Second load should be noticeably faster
      expect(secondLoadTime).toBeLessThanOrEqual(firstLoadTime);
      console.log(`First load: ${firstLoadTime}ms, Second load: ${secondLoadTime}ms`);
    });

    test('should handle network latency gracefully', async ({ page }) => {
      // Simulate slow network
      await page.route('**/api/v1/history**', async route => {
        await page.waitForTimeout(500); // Add 500ms latency
        await route.continue();
      });
      
      const startTime = Date.now();
      await historyPage.goto();
      await historyPage.verifyPageLoaded();
      const loadTime = Date.now() - startTime;
      
      // Should still load within reasonable time despite latency
      expect(loadTime).toBeLessThan(PERFORMANCE_SLA.historyLoad * 2);
      console.log(`Loaded with network latency in ${loadTime}ms`);
    });
  });

  test.describe('Performance Baselines', () => {
    test('should establish performance baselines', async ({ page }) => {
      const baselines = {
        historyLoad: [],
        search: [],
        pagination: [],
        detailsLoad: [],
      };
      
      // Collect multiple samples
      for (let i = 0; i < 3; i++) {
        // History load
        let start = Date.now();
        await historyPage.goto();
        await historyPage.verifyPageLoaded();
        baselines.historyLoad.push(Date.now() - start);
        
        // Search
        start = Date.now();
        await historyPage.searchPrompts('test');
        await SearchTestUtils.waitForSearchDebounce(page);
        baselines.search.push(Date.now() - start);
        
        // Clear search
        await historyPage.searchPrompts('');
        await SearchTestUtils.waitForSearchDebounce(page);
      }
      
      // Calculate averages
      const avgHistoryLoad = baselines.historyLoad.reduce((a, b) => a + b, 0) / baselines.historyLoad.length;
      const avgSearch = baselines.search.reduce((a, b) => a + b, 0) / baselines.search.length;
      
      console.log('Performance Baselines:');
      console.log(`- History Load: ${avgHistoryLoad.toFixed(0)}ms (SLA: ${PERFORMANCE_SLA.historyLoad}ms)`);
      console.log(`- Search: ${avgSearch.toFixed(0)}ms (SLA: ${PERFORMANCE_SLA.searchResponse}ms)`);
      
      // All averages should be within SLA
      expect(avgHistoryLoad).toBeLessThan(PERFORMANCE_SLA.historyLoad);
      expect(avgSearch).toBeLessThan(PERFORMANCE_SLA.searchResponse);
    });
  });
});