const { chromium } = require('@playwright/test');

async function testEnhance() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error' || text.includes('error') || text.includes('Error')) {
      console.log(`PAGE ${type.toUpperCase()}:`, text);
    }
  });
  
  page.on('pageerror', error => console.log('PAGE ERROR:', error));
  
  // Enable network logging
  page.on('response', response => {
    if (response.url().includes('/enhance') || response.status() >= 400) {
      console.log(`RESPONSE: ${response.status()} ${response.url()}`);
    }
  });
  
  try {
    // First login
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('networkidle');
    
    // Fill form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'Test123456!');
    await page.click('button[type="submit"]');
    
    // Wait for navigation
    await page.waitForURL((url) => !url.href.includes('/login'), { timeout: 10000 });
    console.log('Login successful, navigated to:', page.url());
    
    // Go to enhance page
    await page.goto('http://localhost:3000/enhance');
    await page.waitForLoadState('networkidle');
    console.log('On enhance page');
    
    // Fill in prompt
    await page.fill('textarea', 'Write a sorting algorithm');
    console.log('Filled prompt');
    
    // Click enhance button
    const enhanceButton = page.locator('button:has-text("Enhance Prompt")').first();
    await enhanceButton.click();
    console.log('Clicked enhance button');
    
    // Wait for response or error
    await page.waitForTimeout(5000);
    
    // Check for results
    const hasResults = await page.locator('[data-testid="enhancement-results"], .enhancement-results').count() > 0;
    const hasError = await page.locator('.error-message, [role="alert"]').count() > 0;
    
    console.log('Has results:', hasResults);
    console.log('Has error:', hasError);
    
    if (hasError) {
      const errorText = await page.locator('.error-message, [role="alert"]').first().textContent();
      console.log('Error text:', errorText);
    }
    
    // Take screenshot
    await page.screenshot({ path: 'enhance-test-result.png' });
    console.log('Screenshot saved as enhance-test-result.png');
    
  } catch (error) {
    console.error('Test error:', error);
  } finally {
    await browser.close();
  }
}

testEnhance();