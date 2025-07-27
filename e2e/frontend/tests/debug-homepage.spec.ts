import { test, expect } from '@playwright/test';

test('debug homepage structure', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Take screenshot
  await page.screenshot({ path: 'test-results/debug-home.png', fullPage: true });
  
  // Log all data-testid elements
  const testIdElements = await page.locator('[data-testid]').all();
  console.log(`Found ${testIdElements.length} elements with data-testid`);
  
  for (const element of testIdElements) {
    const testId = await element.getAttribute('data-testid');
    const tagName = await element.evaluate(el => el.tagName.toLowerCase());
    const isVisible = await element.isVisible();
    console.log(`- [data-testid="${testId}"] <${tagName}> visible: ${isVisible}`);
  }
  
  // Check for features section specifically
  const hasFeatures = await page.locator('[data-testid="features-section"]').count();
  console.log(`Features section found: ${hasFeatures > 0}`);
  
  // Check for any section with features
  const sections = await page.locator('section').all();
  console.log(`\nFound ${sections.length} sections:`);
  for (let i = 0; i < sections.length; i++) {
    const section = sections[i];
    const className = await section.getAttribute('class') || '';
    const id = await section.getAttribute('id') || '';
    const testId = await section.getAttribute('data-testid') || '';
    const text = await section.textContent() || '';
    console.log(`Section ${i}: class="${className}" id="${id}" data-testid="${testId}"`);
    if (text.toLowerCase().includes('feature')) {
      console.log(`  - Contains "feature" text`);
    }
  }
  
  // Check buttons
  const buttons = await page.locator('button, a[role="button"]').all();
  console.log(`\nFound ${buttons.length} buttons:`);
  for (const button of buttons) {
    const text = await button.textContent();
    const testId = await button.getAttribute('data-testid') || '';
    console.log(`- "${text?.trim()}" data-testid="${testId}"`);
  }
});