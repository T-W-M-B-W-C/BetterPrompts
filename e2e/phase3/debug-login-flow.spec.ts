import { test, expect } from '@playwright/test';

test('debug login flow', async ({ page }) => {
  // Enable console logging
  page.on('console', msg => console.log('Console:', msg.text()));
  
  // Enable network logging
  page.on('request', request => {
    if (request.url().includes('/api')) {
      console.log('Request:', request.method(), request.url());
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/api')) {
      console.log('Response:', response.status(), response.url());
      response.text().then(body => {
        console.log('Response body:', body);
      }).catch(() => {});
    }
  });

  // Go to login page
  await page.goto('http://localhost:3000/login');
  
  // Fill in form
  await page.locator('input#email').fill('test@example.com');
  await page.locator('input#password').fill('Test123!@#');
  
  // Submit form
  await page.locator('button[type="submit"]').click();
  
  // Wait for response
  await page.waitForTimeout(3000);
  
  // Check where we ended up
  console.log('Final URL:', page.url());
  
  // Check localStorage
  const tokens = await page.evaluate(() => {
    return {
      accessToken: localStorage.getItem('access_token'),
      refreshToken: localStorage.getItem('refresh_token'),
      user: localStorage.getItem('user')
    };
  });
  
  console.log('Stored tokens:', tokens);
});