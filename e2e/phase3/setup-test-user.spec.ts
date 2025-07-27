import { test, expect } from '@playwright/test';

test('create test user', async ({ page }) => {
  // Go to registration page
  await page.goto('http://localhost:3000/register');
  
  // Fill registration form
  const timestamp = Date.now();
  const testEmail = `test_${timestamp}@example.com`;
  
  await page.locator('input[name="firstName"]').fill('Test');
  await page.locator('input[name="lastName"]').fill('User');
  await page.locator('input[name="username"]').fill(`testuser_${timestamp}`);
  await page.locator('input[name="email"]').fill(testEmail);
  await page.locator('input[name="password"]').fill('Test123!@#');
  await page.locator('input[name="confirmPassword"]').fill('Test123!@#');
  
  // Accept terms
  await page.locator('input[name="terms"], input[type="checkbox"]').click();
  
  // Submit
  await page.locator('button[type="submit"]').click();
  
  // Wait for navigation
  await page.waitForURL('**/verify-email**', { timeout: 10000 });
  
  console.log('Test user created:', testEmail);
  console.log('Password: Test123!@#');
});