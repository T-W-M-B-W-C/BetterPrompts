import { test, expect } from '@playwright/test';

test.describe('Direct Enhancement Page Test', () => {
  test('should handle enhancement directly', async ({ page, context }) => {
    // Enable console logging
    page.on('console', msg => {
      if (msg.type() === 'error' || msg.text().includes('error')) {
        console.log(`CONSOLE ${msg.type()}: ${msg.text()}`);
      }
    });
    
    // Enable network logging
    page.on('response', response => {
      if (response.status() >= 400 || response.url().includes('/api/')) {
        console.log(`RESPONSE: ${response.status()} ${response.url()}`);
      }
    });
    
    page.on('requestfailed', request => {
      console.log(`REQUEST FAILED: ${request.url()} - ${request.failure()?.errorText}`);
    });
    
    // Login first
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'Test123456!');
    await page.click('button[type="submit"]');
    await page.waitForURL((url) => !url.href.includes('/login'), { timeout: 10000 });
    
    // Go to enhance page
    await page.goto('http://localhost:3000/enhance');
    
    // Wait for page to load
    await page.waitForTimeout(2000);
    
    // Check if there are any error messages already visible
    const errorMessages = await page.locator('[role="alert"], .error-message, .alert-destructive').all();
    for (const error of errorMessages) {
      const text = await error.textContent();
      console.log('ERROR ON PAGE:', text);
    }
    
    // Try to enhance
    await page.fill('textarea', 'Write a sorting algorithm');
    
    // Click enhance button
    await Promise.all([
      page.waitForResponse(response => 
        response.url().includes('/enhance') || 
        response.url().includes('/techniques'),
        { timeout: 10000 }
      ).catch(err => console.log('No response received:', err)),
      page.click('button:has-text("Enhance Prompt")')
    ]);
    
    // Wait a bit for any results or errors
    await page.waitForTimeout(5000);
    
    // Check final state
    const hasResults = await page.locator('[data-testid="enhancement-results"], .enhancement-results').count() > 0;
    const hasError = await page.locator('[role="alert"], .error-message').count() > 0;
    
    console.log('Has results:', hasResults);
    console.log('Has error:', hasError);
    
    if (hasError) {
      const errorText = await page.locator('[role="alert"], .error-message').first().textContent();
      console.log('Error text:', errorText);
    }
    
    // Take screenshot
    await page.screenshot({ path: 'enhance-direct-test.png' });
  });
});