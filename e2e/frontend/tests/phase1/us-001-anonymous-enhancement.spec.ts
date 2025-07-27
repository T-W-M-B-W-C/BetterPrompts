import { test, expect } from '@playwright/test';
import { HomePage } from '../../pages/home.page';
import { EnhanceSection } from '../../pages/enhance-section.page';
import { 
  anonymousTestPrompts, 
  getExceedingLimitPrompt,
  performanceScenarios,
  getPromptsByCategory 
} from './test-data-anonymous';
import { adjustPerformanceExpectation } from '../../utils/browser-helpers';

test.describe('US-001: Anonymous Prompt Enhancement Flow', () => {
  let homePage: HomePage;
  let enhanceSection: EnhanceSection;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    enhanceSection = new EnhanceSection(page);
    
    // Navigate to homepage
    await homePage.goto();
  });

  test.describe('Homepage Navigation', () => {
    test('should load homepage and display prompt input', async ({ page }) => {
      // Verify basic homepage elements loaded
      await expect(page.locator('h1')).toBeVisible();
      
      // Check enhance section is visible
      await expect(page.locator('[data-testid="homepage-enhance-section"]')).toBeVisible();
      
      // Verify enhance section components
      await enhanceSection.verifyEnhanceSectionLoaded();
      
      // Check initial state
      const characterCount = await enhanceSection.getCharacterCount();
      expect(characterCount).toBe('0/2000');
      
      // Enhance button should be disabled initially
      const isEnabled = await enhanceSection.isEnhanceButtonEnabled();
      expect(isEnabled).toBe(false);
    });

    test('should work on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Verify page still loads correctly
      await expect(page.locator('h1')).toBeVisible();
      
      // Scroll to enhance section
      await enhanceSection.scrollToEnhanceSection();
      
      // Verify enhance section is visible and functional
      await enhanceSection.verifyEnhanceSectionLoaded();
    });

    test('should work on desktop viewport', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      // Verify page loads correctly
      await expect(page.locator('h1')).toBeVisible();
      await enhanceSection.verifyEnhanceSectionLoaded();
    });
  });

  test.describe('Prompt Input Validation', () => {
    test('should handle empty prompt', async () => {
      // Try to click enhance with empty prompt
      const isEnabled = await enhanceSection.isEnhanceButtonEnabled();
      expect(isEnabled).toBe(false);
      
      // Enter and clear text
      await enhanceSection.enterPrompt('Test');
      expect(await enhanceSection.isEnhanceButtonEnabled()).toBe(true);
      
      await enhanceSection.clearPrompt();
      expect(await enhanceSection.isEnhanceButtonEnabled()).toBe(false);
    });

    test('should handle valid prompts', async () => {
      const validPrompts = getPromptsByCategory('valid');
      
      // Test first 3 valid prompts
      for (const prompt of validPrompts.slice(0, 3)) {
        await enhanceSection.clearPrompt();
        await enhanceSection.enterPrompt(prompt.text);
        
        // Verify character count updates
        const count = await enhanceSection.getCharacterCount();
        expect(count).toBe(`${prompt.text.length}/2000`);
        
        // Verify enhance button is enabled
        expect(await enhanceSection.isEnhanceButtonEnabled()).toBe(true);
      }
    });

    test('should enforce 2000 character limit', async () => {
      const maxLengthPrompt = 'a'.repeat(2000);
      await enhanceSection.enterPrompt(maxLengthPrompt);
      
      // Should show exactly 2000/2000
      const count = await enhanceSection.getCharacterCount();
      expect(count).toBe('2000/2000');
      expect(await enhanceSection.isEnhanceButtonEnabled()).toBe(true);
      
      // Try to exceed limit
      const exceedingPrompt = getExceedingLimitPrompt();
      await enhanceSection.clearPrompt();
      await enhanceSection.enterPrompt(exceedingPrompt);
      
      // Should be truncated to 2000
      const promptText = await enhanceSection.getPromptText();
      expect(promptText.length).toBe(2000);
    });

    test('should update character count in real-time', async ({ page, browserName }) => {
      const textarea = page.locator('textarea[data-testid="anonymous-prompt-input"]');
      
      // Clear any existing text and focus
      await textarea.clear();
      await textarea.focus();
      
      // Use fill instead of type for more reliable results
      const testText = 'Hello World';
      
      for (let i = 0; i < testText.length; i++) {
        const currentText = testText.substring(0, i + 1);
        await textarea.fill(currentText);
        
        // Firefox and WebKit may need a small delay
        if (browserName !== 'chromium') {
          await page.waitForTimeout(100);
        }
        
        const count = await enhanceSection.getCharacterCount();
        expect(count).toBe(`${currentText.length}/2000`);
      }
    });
  });

  test.describe('Enhancement API Integration', () => {
    test('should successfully enhance a simple prompt', async () => {
      const testPrompt = anonymousTestPrompts[0]; // Simple question
      
      // Enter prompt and enhance
      const result = await enhanceSection.enhancePrompt(testPrompt.text);
      
      // Verify output
      expect(result.output).toBeTruthy();
      expect(result.output.length).toBeGreaterThan(testPrompt.text.length);
      
      // Verify techniques were applied
      expect(result.techniques.length).toBeGreaterThan(0);
      
      // Verify technique explanation is shown
      const explanation = await enhanceSection.getTechniqueExplanation();
      expect(explanation).toBeTruthy();
    });

    test('should handle multiple enhancement requests', async () => {
      const prompts = getPromptsByCategory('valid').slice(0, 2);
      
      for (const prompt of prompts) {
        await enhanceSection.clearPrompt();
        const result = await enhanceSection.enhancePrompt(prompt.text);
        
        expect(result.output).toBeTruthy();
        expect(result.techniques.length).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Loading States and Error Handling', () => {
    test('should show loading state during enhancement', async () => {
      const testPrompt = anonymousTestPrompts[1];
      
      await enhanceSection.enterPrompt(testPrompt.text);
      
      // Start enhancement and immediately check loading state
      const enhancePromise = enhanceSection.clickEnhance();
      
      // Should show loading spinner
      await expect(async () => {
        const isLoading = await enhanceSection.isLoading();
        expect(isLoading).toBe(true);
      }).toPass({ timeout: 2000 });
      
      // Wait for completion
      await enhancePromise;
      await enhanceSection.waitForEnhancement();
      
      // Loading should be hidden
      expect(await enhanceSection.isLoading()).toBe(false);
    });

    test('should handle network errors gracefully', async ({ page, context }) => {
      // Simulate network error
      await page.evaluate(() => {
        (window as any).__simulateError = true;
      });
      
      const testPrompt = anonymousTestPrompts[0];
      await enhanceSection.enterPrompt(testPrompt.text);
      await enhanceSection.clickEnhance();
      
      // Should show error message
      await expect(async () => {
        const hasError = await enhanceSection.isErrorDisplayed();
        expect(hasError).toBe(true);
      }).toPass({ timeout: 5000 });
      
      const errorMsg = await enhanceSection.getErrorMessage();
      expect(errorMsg).toContain('error');
      
      // Clean up
      await page.evaluate(() => {
        delete (window as any).__simulateError;
      });
    });

    test('should allow retry after error', async ({ page, context }) => {
      // First simulate error
      await page.evaluate(() => {
        (window as any).__simulateError = true;
      });
      
      const testPrompt = anonymousTestPrompts[0];
      await enhanceSection.enterPrompt(testPrompt.text);
      await enhanceSection.clickEnhance();
      
      // Wait for error
      await expect(async () => {
        const hasError = await enhanceSection.isErrorDisplayed();
        expect(hasError).toBe(true);
      }).toPass({ timeout: 5000 });
      
      // Remove error simulation
      await page.evaluate(() => {
        delete (window as any).__simulateError;
      });
      
      // Click retry
      await enhanceSection.clickRetry();
      
      // Should complete successfully
      await enhanceSection.waitForEnhancement();
      expect(await enhanceSection.isOutputVisible()).toBe(true);
    });
  });

  test.describe('Response Display', () => {
    test('should display enhanced prompt correctly', async () => {
      const testPrompt = anonymousTestPrompts[2]; // Business email
      
      const result = await enhanceSection.enhancePrompt(testPrompt.text);
      
      // Verify output container is visible
      expect(await enhanceSection.isOutputVisible()).toBe(true);
      
      // Verify output has content
      expect(result.output).toContain(testPrompt.text);
      
      // Verify techniques are listed
      const techniques = await enhanceSection.getAppliedTechniques();
      expect(techniques.length).toBeGreaterThan(0);
      
      // Verify copy button is available
      const copyButton = await enhanceSection.page.locator('button[data-testid="anonymous-copy-button"]');
      await expect(copyButton).toBeVisible();
    });

    test('should show sign-up CTA after enhancement', async () => {
      const testPrompt = anonymousTestPrompts[0];
      
      await enhanceSection.enhancePrompt(testPrompt.text);
      
      // Should show sign-up CTA
      expect(await enhanceSection.isSignUpCTAVisible()).toBe(true);
    });

    test('should allow copying enhanced output', async ({ page, context, browserName }) => {
      // Grant clipboard permissions (only works in Chromium-based browsers)
      if (browserName === 'chromium' || browserName === 'webkit') {
        try {
          await context.grantPermissions(['clipboard-read', 'clipboard-write']);
        } catch (e) {
          // Ignore permission errors for browsers that don't support it
        }
      }
      
      const testPrompt = anonymousTestPrompts[0];
      const result = await enhanceSection.enhancePrompt(testPrompt.text);
      
      // Copy output
      await enhanceSection.copyOutput();
      
      // Verify the copy button works (we can't verify clipboard in all browsers)
      const copyButton = page.locator('button[data-testid="anonymous-copy-button"]');
      await expect(copyButton).toBeVisible();
      await expect(copyButton).toBeEnabled();
    });
  });

  test.describe('Performance Requirements', () => {
    test('should enhance simple prompts within 2 seconds', async ({ browserName }) => {
      const scenario = performanceScenarios[0]; // Simple prompt
      
      // First enter the prompt
      await enhanceSection.enterPrompt(scenario.prompt.text);
      
      // Measure only the enhancement time (click to result)
      const startTime = Date.now();
      await enhanceSection.clickEnhance();
      await enhanceSection.waitForEnhancement();
      const endTime = Date.now();
      
      const duration = endTime - startTime;
      const adjustedExpectation = adjustPerformanceExpectation(scenario.expectedMaxTime, browserName);
      expect(duration).toBeLessThan(adjustedExpectation);
      
      // Verify output exists
      const output = await enhanceSection.getEnhancedOutput();
      expect(output).toBeTruthy();
    });

    test('should enhance complex prompts within 2 seconds', async ({ browserName }) => {
      const scenario = performanceScenarios[1]; // Complex prompt
      
      // First enter the prompt
      await enhanceSection.enterPrompt(scenario.prompt.text);
      
      // Measure only the enhancement time (click to result)
      const startTime = Date.now();
      await enhanceSection.clickEnhance();
      await enhanceSection.waitForEnhancement();
      const endTime = Date.now();
      
      const duration = endTime - startTime;
      const adjustedExpectation = adjustPerformanceExpectation(scenario.expectedMaxTime, browserName);
      expect(duration).toBeLessThan(adjustedExpectation);
      
      // Verify output exists
      const output = await enhanceSection.getEnhancedOutput();
      expect(output).toBeTruthy();
    });

    test('should handle rapid sequential enhancements', async ({ browserName }) => {
      const scenario = performanceScenarios[2]; // Sequential prompts
      
      for (const prompt of scenario.prompts) {
        await enhanceSection.clearPrompt();
        
        const startTime = Date.now();
        await enhanceSection.enhancePrompt(prompt.text);
        const endTime = Date.now();
        
        const duration = endTime - startTime;
        const adjustedExpectation = adjustPerformanceExpectation(scenario.expectedMaxTimeEach, browserName);
        expect(duration).toBeLessThanOrEqual(adjustedExpectation);
      }
    });

    test('should measure page load performance', async ({ page, browserName }) => {
      // Navigate and measure
      const navigationStart = Date.now();
      await page.goto('/');
      await expect(page.locator('h1')).toBeVisible();
      const navigationEnd = Date.now();
      
      const loadTime = navigationEnd - navigationStart;
      const adjustedExpectation = adjustPerformanceExpectation(3000, browserName);
      expect(loadTime).toBeLessThan(adjustedExpectation); // Adjusted for browser performance
      
      // Check performance metrics
      const metrics = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        return {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        };
      });
      
      expect(metrics.domContentLoaded).toBeLessThan(1000);
      expect(metrics.loadComplete).toBeLessThan(2000);
    });
  });

  test.describe('Cross-browser Compatibility', () => {
    // These tests will run on all configured browsers in playwright.config.ts
    test('should work across different browsers', async ({ browserName }) => {
      const testPrompt = anonymousTestPrompts[0];
      
      // Basic functionality should work in all browsers
      const result = await enhanceSection.enhancePrompt(testPrompt.text);
      
      expect(result.output).toBeTruthy();
      expect(result.techniques.length).toBeGreaterThan(0);
      
      console.log(`✓ Test passed on ${browserName}`);
    });
  });
});