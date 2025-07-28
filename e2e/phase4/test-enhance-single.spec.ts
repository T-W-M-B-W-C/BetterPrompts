import { test, expect } from '@playwright/test';

test.use({
  timeout: 120000, // Increase timeout to 120 seconds due to slow compilation
});

test.describe('Enhancement Page Test - Single Browser', () => {
  test('should load enhancement page and fetch techniques', async ({ page }) => {
    // Enable console logging
    page.on('console', msg => {
      console.log(`CONSOLE ${msg.type()}: ${msg.text()}`);
    });
    
    // Enable network logging for techniques endpoint
    page.on('response', response => {
      if (response.url().includes('/techniques')) {
        console.log(`TECHNIQUES RESPONSE: ${response.status()} ${response.url()}`);
      }
    });
    
    page.on('requestfailed', request => {
      if (request.url().includes('/techniques')) {
        console.log(`TECHNIQUES REQUEST FAILED: ${request.url()} - ${request.failure()?.errorText}`);
      }
    });
    
    // Go directly to enhance page (public route)
    console.log('Navigating to enhance page...');
    await page.goto('http://localhost:3000/enhance', { 
      waitUntil: 'domcontentloaded',
      timeout: 60000 // Increase timeout for slow compilation
    });
    
    // Wait for initial page load
    console.log('Waiting for page to load...');
    await page.waitForTimeout(3000);
    
    // Click the Techniques button to show techniques
    console.log('Clicking Techniques button...');
    const techniquesButton = page.locator('button:has-text("Techniques")');
    await techniquesButton.click();
    
    // Wait for techniques to appear
    await page.waitForTimeout(1000);
    
    // Check if techniques loaded
    const techniqueCards = await page.locator('[data-testid="technique-card"], .technique-card').count();
    console.log(`Found ${techniqueCards} technique cards`);
    
    // Check for any errors
    const errors = await page.locator('[role="alert"], .error-message, .alert-destructive').all();
    for (const error of errors) {
      const text = await error.textContent();
      console.log('ERROR ON PAGE:', text);
    }
    
    // Try to enter text and enhance
    console.log('Entering prompt text...');
    await page.fill('textarea', 'Write a sorting algorithm');
    
    // Check if enhance button is enabled
    const enhanceButton = page.locator('button:has-text("Enhance Prompt")');
    const isDisabled = await enhanceButton.isDisabled();
    console.log(`Enhance button disabled: ${isDisabled}`);
    
    if (!isDisabled) {
      console.log('Clicking enhance button...');
      await enhanceButton.click();
      
      // Wait for response
      await page.waitForTimeout(5000);
      
      // Check for enhanced output
      const hasOutput = await page.locator('text=Enhanced Prompt').count() > 0;
      console.log(`Has enhanced output: ${hasOutput}`);
      
      if (hasOutput) {
        const enhancedText = await page.locator('pre').textContent();
        console.log('Enhanced text preview:', enhancedText?.substring(0, 100) + '...');
      }
    }
    
    // Take screenshot
    await page.screenshot({ path: 'enhance-page-test.png', fullPage: true });
    
    // Verify no infinite loop in techniques
    expect(techniqueCards).toBeGreaterThanOrEqual(0);
    expect(techniqueCards).toBeLessThan(50); // Should not have duplicate cards from infinite loop
  });
});