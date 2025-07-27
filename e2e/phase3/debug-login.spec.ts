import { test, expect } from '@playwright/test';

test('debug login page', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Take screenshot
  await page.screenshot({ path: 'login-page.png', fullPage: true });
  
  // Log all checkboxes
  const checkboxes = await page.locator('input[type="checkbox"]').all();
  console.log(`Found ${checkboxes.length} checkboxes`);
  
  for (const checkbox of checkboxes) {
    const id = await checkbox.getAttribute('id');
    const name = await checkbox.getAttribute('name');
    const visible = await checkbox.isVisible();
    console.log(`Checkbox: id="${id}", name="${name}", visible=${visible}`);
  }
  
  // Check for Radix UI checkbox
  const radixCheckboxes = await page.locator('[role="checkbox"]').all();
  console.log(`Found ${radixCheckboxes.length} Radix UI checkboxes`);
  
  for (const checkbox of radixCheckboxes) {
    const id = await checkbox.getAttribute('id');
    const ariaChecked = await checkbox.getAttribute('aria-checked');
    const visible = await checkbox.isVisible();
    console.log(`Radix Checkbox: id="${id}", aria-checked="${ariaChecked}", visible=${visible}`);
  }
});