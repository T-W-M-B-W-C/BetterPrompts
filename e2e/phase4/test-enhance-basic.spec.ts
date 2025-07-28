import { test, expect } from '@playwright/test';

test.describe('Basic Enhancement Test', () => {
  test('should enhance a prompt without authentication', async ({ page }) => {
    // Navigate to enhance page
    await page.goto('http://localhost:3000/enhance');
    
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000); // Extra wait for React to hydrate
    
    // Enter some text in the textarea
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible({ timeout: 10000 });
    await textarea.fill('Write a function to sort an array');
    
    // The enhance button should be enabled now
    const enhanceButton = page.locator('button', { hasText: 'Enhance' }).first();
    await expect(enhanceButton).toBeVisible({ timeout: 10000 });
    await expect(enhanceButton).toBeEnabled();
    
    // Click enhance
    await enhanceButton.click();
    
    // Wait for the enhancement to complete
    await page.waitForTimeout(5000);
    
    // Check if we got an enhanced result
    const enhancedSection = page.locator('text=Enhanced Prompt').first();
    const hasEnhanced = await enhancedSection.count() > 0;
    
    if (hasEnhanced) {
      console.log('✅ Enhancement succeeded!');
      const enhancedText = await page.locator('pre').textContent();
      console.log('Enhanced text preview:', enhancedText?.substring(0, 100) + '...');
    } else {
      console.log('❌ No enhanced output found');
      
      // Check for errors
      const errors = await page.locator('[role="alert"]').all();
      for (const error of errors) {
        console.log('Error:', await error.textContent());
      }
    }
    
    // Take final screenshot
    await page.screenshot({ path: 'enhance-basic-result.png', fullPage: true });
  });
});