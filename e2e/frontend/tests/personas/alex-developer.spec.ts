import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/auth/login.page';
import { DashboardPage } from '../../pages/dashboard.page';
import { EnhancePage } from '../../pages/enhance.page';
import { HistoryPage } from '../../pages/history.page';
import { testUsers } from '../../fixtures/users';
import { testPrompts } from '../../fixtures/prompts';
import * as helpers from '../../utils/test-helpers';

/**
 * Alex - Software Developer Test Suite
 * Power user persona focused on API integration and code enhancement
 * User Stories: US-004, US-005, US-006
 */

test.describe('Alex - Software Developer User Journey', () => {
  const alex = testUsers.alex;
  const alexPrompts = [
    testPrompts.alexSimple,
    testPrompts.alexModerate,
    testPrompts.alexComplex,
  ];

  test.describe('US-004: API Integration', () => {
    test.use({
      storageState: 'auth-alex.json',
    });

    test.beforeAll(async ({ browser }) => {
      // Create authenticated session for Alex
      const context = await helpers.createAuthenticatedContext(browser, alex);
      await context.close();
    });

    test('@critical @alex @api Access and manage API keys', async ({ page }) => {
      const dashboardPage = new DashboardPage(page);
      
      await dashboardPage.goto();
      
      // Verify API section is visible for power user
      const apiSectionVisible = await dashboardPage.isAPIKeySectionVisible();
      expect(apiSectionVisible).toBe(true);
      
      // Get current API key
      const currentKey = await dashboardPage.getAPIKey();
      expect(currentKey).toMatch(/^test_api_key_/);
      
      // Regenerate API key
      await dashboardPage.regenerateAPIKey();
      
      // Verify new key is different
      await page.waitForTimeout(1000); // Wait for regeneration
      const newKey = await dashboardPage.getAPIKey();
      expect(newKey).not.toBe(currentKey);
      
      // Take screenshot for documentation
      await helpers.takeScreenshot(page, 'alex-api-key-management');
    });

    test('@critical @alex @api Test API endpoint with authentication', async ({ page, request }) => {
      // Direct API test using Playwright's request context
      const response = await request.post('/api/v1/enhance', {
        headers: {
          'Authorization': `Bearer ${alex.apiKey}`,
          'Content-Type': 'application/json',
        },
        data: {
          prompt: alexPrompts[0].text,
          techniques: ['code_structure'],
        },
      });
      
      expect(response.ok()).toBe(true);
      const data = await response.json();
      
      // Verify API response structure
      expect(data).toHaveProperty('enhanced_prompt');
      expect(data).toHaveProperty('techniques_applied');
      expect(data).toHaveProperty('request_id');
      expect(data.techniques_applied).toContain('code_structure');
    });

    test('@regression @alex @api Handle API rate limiting', async ({ page, request }) => {
      // Make multiple rapid requests to trigger rate limiting
      const requests = [];
      
      for (let i = 0; i < 15; i++) {
        requests.push(
          request.post('/api/v1/enhance', {
            headers: {
              'Authorization': `Bearer ${alex.apiKey}`,
              'Content-Type': 'application/json',
            },
            data: {
              prompt: `Test request ${i}`,
            },
          })
        );
      }
      
      const responses = await Promise.all(requests);
      
      // Check if rate limiting kicked in
      const rateLimited = responses.some(r => r.status() === 429);
      expect(rateLimited).toBe(true);
      
      // Verify rate limit headers
      const limitedResponse = responses.find(r => r.status() === 429);
      expect(limitedResponse?.headers()['x-ratelimit-limit']).toBeTruthy();
      expect(limitedResponse?.headers()['x-ratelimit-remaining']).toBe('0');
      expect(limitedResponse?.headers()['x-ratelimit-reset']).toBeTruthy();
    });

    test('@regression @alex @api Batch processing via API', async ({ request }) => {
      const batchRequest = {
        prompts: alexPrompts.map(p => ({
          id: p.id,
          text: p.text,
          techniques: p.expectedTechniques,
        })),
      };
      
      const response = await request.post('/api/v1/enhance/batch', {
        headers: {
          'Authorization': `Bearer ${alex.apiKey}`,
          'Content-Type': 'application/json',
        },
        data: batchRequest,
      });
      
      expect(response.ok()).toBe(true);
      const data = await response.json();
      
      // Verify batch response
      expect(data.results).toHaveLength(alexPrompts.length);
      expect(data.results[0]).toHaveProperty('id', alexPrompts[0].id);
      expect(data.results[0]).toHaveProperty('enhanced_prompt');
      expect(data.results[0]).toHaveProperty('status', 'completed');
    });
  });

  test.describe('US-005: Code Enhancement Features', () => {
    test.use({
      storageState: 'auth-alex.json',
    });

    test('@critical @alex @code Enhance code documentation', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Enter code snippet
      const codePrompt = `
        function validateEmail(email) {
          const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          return re.test(email);
        }
        
        Add comprehensive JSDoc comments
      `;
      
      await enhancePage.enterPrompt(codePrompt);
      
      // Select code documentation technique
      await enhancePage.selectTechnique('Code Documentation');
      
      // Enhance
      await enhancePage.clickEnhance();
      await enhancePage.waitForEnhancement();
      
      const result = await enhancePage.getEnhancedOutput();
      
      // Verify documentation was added
      expect(result).toContain('@param');
      expect(result).toContain('@returns');
      expect(result).toContain('@example');
      expect(result).toMatch(/\/\*\*/); // JSDoc comment format
      
      // Download result
      const download = await enhancePage.downloadOutput();
      expect(download.suggestedFilename()).toContain('.js');
    });

    test('@critical @alex @code Generate unit tests', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Complex code for test generation
      await enhancePage.enterPrompt(alexPrompts[1].text);
      
      // Select test generation technique
      await enhancePage.selectTechnique('Test Generation');
      await enhancePage.selectTechnique('Code Coverage');
      
      // Enhance
      const result = await enhancePage.enhancePrompt(
        alexPrompts[1].text,
        'Test Generation'
      );
      
      // Verify test structure
      expect(result).toMatch(/describe\(|test\(|it\(/); // Test framework syntax
      expect(result).toContain('expect'); // Assertions
      expect(result).toMatch(/mock|stub|spy/i); // Mocking concepts
    });

    test('@regression @alex @code Architecture and design patterns', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Complex architecture prompt
      await enhancePage.enterPrompt(alexPrompts[2].text);
      
      // Select multiple techniques
      await enhancePage.selectTechnique('System Design');
      await enhancePage.selectTechnique('Scalability Patterns');
      await enhancePage.selectTechnique('Best Practices');
      
      // Enhance
      await enhancePage.clickEnhance();
      
      // Monitor progress for complex enhancement
      let progress = '0';
      for (let i = 0; i < 10; i++) {
        progress = await enhancePage.getProgress();
        if (parseInt(progress) === 100) break;
        await page.waitForTimeout(500);
      }
      
      await enhancePage.waitForEnhancement();
      const result = await enhancePage.getEnhancedOutput();
      
      // Verify architecture components
      expect(result).toMatch(/microservice|service|api/i);
      expect(result).toMatch(/database|cache|queue/i);
      expect(result).toMatch(/scalability|performance|load/i);
      
      // Should include diagrams or structure
      expect(result.split('\n').length).toBeGreaterThan(20);
    });
  });

  test.describe('US-006: Custom Technique Selection', () => {
    test.use({
      storageState: 'auth-alex.json',
    });

    test('@critical @alex Create custom technique combination', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Enter prompt
      await enhancePage.enterPrompt('Create a REST API for user management');
      
      // Select multiple complementary techniques
      const techniques = [
        'API Design',
        'Security Patterns',
        'Error Handling',
        'Documentation',
      ];
      
      for (const technique of techniques) {
        await enhancePage.selectTechnique(technique);
      }
      
      // Verify all selected
      const selected = await enhancePage.getSelectedTechniques();
      expect(selected.length).toBe(techniques.length);
      
      // Enhance with combination
      await enhancePage.clickEnhance();
      await enhancePage.waitForEnhancement();
      
      const result = await enhancePage.getEnhancedOutput();
      
      // Verify all aspects are covered
      expect(result).toMatch(/GET|POST|PUT|DELETE/); // REST methods
      expect(result).toMatch(/auth|token|security/i); // Security
      expect(result).toMatch(/error|exception|status/i); // Error handling
      expect(result).toMatch(/endpoint|route|path/i); // API structure
    });

    test('@regression @alex Save and reuse technique presets', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      const dashboardPage = new DashboardPage(page);
      
      await enhancePage.goto();
      
      // Create a preset
      await enhancePage.selectTechnique('Code Structure');
      await enhancePage.selectTechnique('Performance Optimization');
      await enhancePage.selectTechnique('Security Patterns');
      
      // Save as preset
      const savePresetButton = page.locator('button:has-text("Save as Preset")');
      await savePresetButton.click();
      
      const presetModal = page.locator('[data-testid="preset-modal"]');
      await presetModal.locator('input[name="presetName"]').fill('Backend Best Practices');
      await presetModal.locator('button:has-text("Save")').click();
      
      // Navigate away and back
      await dashboardPage.goto();
      await enhancePage.goto();
      
      // Load preset
      const presetSelector = page.locator('[data-testid="preset-selector"]');
      await presetSelector.click();
      await page.locator('text="Backend Best Practices"').click();
      
      // Verify techniques are loaded
      const selected = await enhancePage.getSelectedTechniques();
      expect(selected).toContain('Code Structure');
      expect(selected).toContain('Performance Optimization');
      expect(selected).toContain('Security Patterns');
    });
  });

  test.describe('Developer-Specific Features', () => {
    test.use({
      storageState: 'auth-alex.json',
    });

    test('@regression @alex @integration GitHub integration', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Import from GitHub
      const importButton = page.locator('button:has-text("Import from GitHub")');
      await importButton.click();
      
      const githubModal = page.locator('[data-testid="github-import-modal"]');
      await githubModal.locator('input[name="repoUrl"]').fill('https://github.com/example/repo');
      await githubModal.locator('input[name="filePath"]').fill('src/index.js');
      
      // Mock GitHub API response
      await helpers.mockAPIResponse(page, 'github/import', {
        content: 'function example() { return "test"; }',
        path: 'src/index.js',
      });
      
      await githubModal.locator('button:has-text("Import")').click();
      
      // Verify code is imported
      await page.waitForTimeout(1000);
      const promptContent = await page.locator('textarea[data-testid="prompt-input"]').inputValue();
      expect(promptContent).toContain('function example()');
    });

    test('@regression @alex Export enhancement history', async ({ page }) => {
      const historyPage = new HistoryPage(page);
      
      await historyPage.goto();
      
      // Filter by code enhancements
      await historyPage.filterByTechnique('Code');
      
      // Select all items
      await historyPage.selectAllItems();
      
      // Export as JSON for processing
      const download = await historyPage.exportSelected('json');
      expect(download.suggestedFilename()).toContain('.json');
      
      // Verify download completed
      const path = await download.path();
      expect(path).toBeTruthy();
    });

    test('@performance @alex Load test with large code files', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Generate large code snippet (5KB)
      const largeCode = `
        class ComplexSystem {
          ${Array(100).fill(0).map((_, i) => `
            method${i}() {
              // Complex logic here
              const result = this.calculate${i}();
              return this.process${i}(result);
            }
          `).join('\n')}
        }
      `;
      
      await enhancePage.enterPrompt(largeCode + '\n\nOptimize this code');
      
      // Measure enhancement time
      const startTime = Date.now();
      await enhancePage.clickEnhance();
      await enhancePage.waitForEnhancement();
      const endTime = Date.now();
      
      // Should handle large input efficiently
      expect(endTime - startTime).toBeLessThan(10000); // 10s max
      
      const result = await enhancePage.getEnhancedOutput();
      expect(result).toBeTruthy();
      expect(result.length).toBeGreaterThan(1000);
    });
  });

  test.describe('Visual Regression for Developer UI', () => {
    test.use({
      storageState: 'auth-alex.json',
    });

    test('@visual @alex Code enhancement interface', async ({ page }) => {
      const enhancePage = new EnhancePage(page);
      
      await enhancePage.goto();
      
      // Set up code enhancement scenario
      await enhancePage.enterPrompt(alexPrompts[0].text);
      await enhancePage.selectTechnique('Code Structure');
      
      // Visual regression test
      await helpers.compareScreenshots(page, 'alex-code-enhancement-ui', {
        fullPage: true,
        mask: ['.timestamp', '.user-avatar'], // Mask dynamic elements
      });
      
      // Start enhancement and capture loading state
      await enhancePage.clickEnhance();
      await page.waitForTimeout(500); // Capture mid-enhancement
      
      await helpers.compareScreenshots(page, 'alex-enhancement-progress', {
        fullPage: false,
        clip: { x: 0, y: 200, width: 800, height: 400 },
      });
    });
  });
});