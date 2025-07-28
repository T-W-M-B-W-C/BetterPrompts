import { test, expect } from '@playwright/test';
import { AuthHelper } from './utils/AuthHelper';

test.describe('Debug Authentication', () => {
  test('can login and access pages', async ({ page, context }) => {
    const authHelper = new AuthHelper(page, context);
    
    // Try to login
    console.log('Attempting login...');
    try {
      const tokens = await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
      console.log('Login successful, tokens received:', !!tokens.accessToken);
    } catch (error) {
      console.error('Login failed:', error);
      
      // Take screenshot
      await page.screenshot({ path: 'login-error.png' });
      
      // Check for error messages
      const errorText = await page.locator('[role="alert"], .error-message, .text-red-500').textContent().catch(() => null);
      console.log('Error message on page:', errorText);
      
      throw error;
    }
    
    // Check where we are
    const currentUrl = page.url();
    console.log('Current URL after login:', currentUrl);
    
    // Try to navigate to enhance page
    await page.goto('/enhance');
    await page.waitForLoadState('networkidle');
    
    const enhanceUrl = page.url();
    console.log('URL after navigating to /enhance:', enhanceUrl);
    
    // Check if we can find enhancement form
    const textareas = await page.locator('textarea').all();
    console.log('Number of textareas found:', textareas.length);
    
    if (textareas.length > 0) {
      for (let i = 0; i < textareas.length; i++) {
        const placeholder = await textareas[i].getAttribute('placeholder');
        const name = await textareas[i].getAttribute('name');
        const id = await textareas[i].getAttribute('id');
        console.log(`Textarea ${i}: placeholder="${placeholder}", name="${name}", id="${id}"`);
      }
    }
    
    // Check if we're on home page
    if (enhanceUrl.endsWith('/')) {
      console.log('We are on home page, looking for enhancement section...');
      const enhanceSection = await page.locator('section:has-text("Enhance Your Prompts")').count();
      console.log('Enhancement section found:', enhanceSection > 0);
    }
  });
});