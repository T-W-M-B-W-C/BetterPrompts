import { test, expect } from '@playwright/test';

test('simple login test', async ({ page }) => {
  // Go to login page
  await page.goto('http://localhost:3000/login');
  
  // Fill in form
  await page.locator('input#email').fill('test@example.com');
  await page.locator('input#password').fill('Test123!@#');
  
  // Enable network logging
  page.on('request', request => {
    if (request.url().includes('/api')) {
      console.log('Request:', request.method(), request.url());
      console.log('Headers:', request.headers());
      console.log('Body:', request.postData());
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/api')) {
      console.log('Response:', response.status(), response.url());
      response.text().then(body => {
        console.log('Response body:', body);
      });
    }
  });
  
  // Submit form
  await page.locator('button[type="submit"]').click();
  
  // Wait a bit to see what happens
  await page.waitForTimeout(5000);
  
  // Check current URL
  console.log('Current URL:', page.url());
  
  // Take screenshot
  await page.screenshot({ path: 'login-result.png' });
});