import { test, expect } from '@playwright/test';

test('basic app loading test', async ({ page }) => {
  // Navigate to the app
  await page.goto('http://localhost:3000');
  
  // Wait for the app to load
  await page.waitForLoadState('networkidle');
  
  // Debug: Take a screenshot
  await page.screenshot({ path: 'test-results/debug-home.png' });
  
  // Wait for any h1 element
  const h1 = await page.waitForSelector('h1', { timeout: 60000 });
  const h1Text = await h1.textContent();
  console.log('Found h1 with text:', h1Text);
  
  // Check for any link
  const links = await page.$$('a');
  console.log('Found', links.length, 'links');
  
  // Log page content
  const content = await page.content();
  console.log('Page length:', content.length);
});