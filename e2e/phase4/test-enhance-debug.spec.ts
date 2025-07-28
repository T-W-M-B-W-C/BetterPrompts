import { test, expect } from '@playwright/test';

test.describe('Enhancement Page Debug Test', () => {
  test('debug enhancement page loading', async ({ page }) => {
    console.log('1. Navigating to enhance page...');
    await page.goto('http://localhost:3000/enhance', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'debug-1-initial.png' });
    
    console.log('2. Checking page title...');
    const title = await page.locator('h1').textContent();
    console.log('Page title:', title);
    
    console.log('3. Looking for textarea...');
    const textareaCount = await page.locator('textarea').count();
    console.log('Textarea count:', textareaCount);
    
    if (textareaCount > 0) {
      const textareaVisible = await page.locator('textarea').isVisible();
      console.log('Textarea visible:', textareaVisible);
    }
    
    console.log('4. Looking for Techniques button...');
    const techButton = page.locator('button:has-text("Techniques")');
    const techButtonCount = await techButton.count();
    console.log('Techniques button count:', techButtonCount);
    
    if (techButtonCount > 0) {
      console.log('5. Clicking Techniques button...');
      await techButton.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'debug-2-after-techniques-click.png' });
      
      console.log('6. Looking for technique cards...');
      const cardCount = await page.locator('[data-testid="technique-card"]').count();
      console.log('Technique cards found:', cardCount);
      
      // Also try other selectors
      const anyCards = await page.locator('button[aria-label*="technique"]').count();
      console.log('Buttons with technique in aria-label:', anyCards);
      
      const divCards = await page.locator('div:has-text("Chain of Thought")').count();
      console.log('Divs with "Chain of Thought" text:', divCards);
    }
    
    console.log('7. Looking for enhance button...');
    const enhanceButton = page.locator('button:has-text("Enhance")');
    const enhanceCount = await enhanceButton.count();
    console.log('Enhance button count:', enhanceCount);
    
    // Try alternate selectors
    const anyEnhanceButton = await page.locator('button').filter({ hasText: /Enhance/ }).count();
    console.log('Any button with Enhance text:', anyEnhanceButton);
    
    const allButtons = await page.locator('button').allTextContents();
    console.log('All button texts:', allButtons);
    
    if (enhanceCount > 0) {
      const enhanceDisabled = await enhanceButton.isDisabled();
      console.log('Enhance button disabled:', enhanceDisabled);
    }
    
    console.log('8. Checking for errors...');
    const errors = await page.locator('[role="alert"], .error-message').all();
    for (const error of errors) {
      const text = await error.textContent();
      console.log('ERROR:', text);
    }
    
    console.log('9. Page HTML preview:');
    const bodyText = await page.locator('body').textContent();
    console.log(bodyText?.substring(0, 500) + '...');
    
    // Final screenshot
    await page.screenshot({ path: 'debug-3-final.png', fullPage: true });
  });
});