const { chromium } = require('@playwright/test');

async function testLogin() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Enable console logging
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error));
  
  // Enable request logging
  page.on('request', request => {
    if (request.url().includes('auth')) {
      console.log('REQUEST:', request.method(), request.url());
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('auth')) {
      console.log('RESPONSE:', response.status(), response.url());
    }
  });
  
  try {
    // Navigate to login page
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('networkidle');
    
    // Fill form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'Test123456!');
    
    console.log('Form filled, clicking submit...');
    
    // Click login button
    const promise = page.waitForResponse(response => 
      response.url().includes('/auth/login') && response.request().method() === 'POST',
      { timeout: 10000 }
    );
    
    await page.click('button[type="submit"]');
    
    const response = await promise;
    console.log('Login response status:', response.status());
    
    const responseBody = await response.json().catch(e => response.text());
    console.log('Response body:', responseBody);
    
    // Check cookies
    const cookies = await context.cookies();
    console.log('Cookies:', cookies.map(c => ({ name: c.name, value: c.value.substring(0, 10) + '...' })));
    
    // Check if we navigated away from login
    await page.waitForTimeout(2000);
    console.log('Current URL:', page.url());
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

testLogin();