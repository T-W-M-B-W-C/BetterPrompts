import { test, expect } from '@playwright/test';

test('debug login error', async ({ page }) => {
  // Go to login page
  await page.goto('http://localhost:3000/login');
  
  // Fill in form with wrong password
  await page.locator('input#email').fill('test@example.com');
  await page.locator('input#password').fill('WrongPassword123!');
  
  // Submit form
  await page.locator('button[type="submit"]').click();
  
  // Wait for response
  await page.waitForTimeout(2000);
  
  // Try to find error messages
  const alerts = await page.locator('[role="alert"]').all();
  console.log(`Found ${alerts.length} alerts`);
  
  for (const alert of alerts) {
    const text = await alert.textContent();
    const isVisible = await alert.isVisible();
    console.log(`Alert text: "${text}", visible: ${isVisible}`);
  }
  
  // Try other error selectors
  const errors = await page.locator('.text-red-500, .text-destructive').all();
  console.log(`Found ${errors.length} error elements`);
  
  for (const error of errors) {
    const text = await error.textContent();
    const isVisible = await error.isVisible();
    console.log(`Error text: "${text}", visible: ${isVisible}`);
  }
  
  // Take screenshot
  await page.screenshot({ path: 'login-error.png', fullPage: true });
});