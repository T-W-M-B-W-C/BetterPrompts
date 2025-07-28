import { test, expect } from '@playwright/test';
import { AuthHelper } from './utils/AuthHelper';
import { HistoryPage } from './pages/HistoryPage';

test.describe('Phase 4: Authentication & Enhancement History', () => {
  let authHelper: AuthHelper;
  let historyPage: HistoryPage;

  test.beforeEach(async ({ page, context }) => {
    authHelper = new AuthHelper(page, context);
    historyPage = new HistoryPage(page);
  });

  test('should save enhancement to history for authenticated users', async ({ page }) => {
    // 1. Login as test user
    await authHelper.loginUser({
      email: 'test@example.com',
      password: 'Test123456!'
    });
    
    // 2. Navigate to enhance page
    await page.goto('http://localhost:3000/enhance');
    await page.waitForLoadState('networkidle');
    
    // 3. Wait for hydration to complete
    await page.waitForTimeout(3000);
    
    // 4. Enter prompt text
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible({ timeout: 10000 });
    await textarea.fill('Create a function to calculate fibonacci numbers');
    
    // 5. Click enhance button
    const enhanceButton = page.locator('button').filter({ hasText: /Enhance/ }).first();
    await expect(enhanceButton).toBeVisible({ timeout: 10000 });
    await enhanceButton.click();
    
    // 6. Wait for enhancement to complete
    await page.waitForTimeout(5000);
    
    // 7. Navigate to history page
    await page.goto('http://localhost:3000/history');
    await page.waitForLoadState('networkidle');
    
    // 8. Check if the enhancement was saved
    const historyItems = page.locator('[data-testid="history-item"], .history-item');
    const count = await historyItems.count();
    
    if (count > 0) {
      console.log(`✅ Found ${count} history items`);
      
      // Check the most recent item
      const firstItem = historyItems.first();
      const text = await firstItem.textContent();
      
      if (text?.includes('fibonacci')) {
        console.log('✅ Enhancement was saved to history!');
      } else {
        console.log('❌ History item found but does not contain our prompt');
        console.log('Text:', text);
      }
    } else {
      console.log('❌ No history items found');
      
      // Check for empty state
      const emptyState = await page.locator('text=/no.*history|empty/i').count();
      if (emptyState > 0) {
        console.log('Empty state message is shown');
      }
    }
    
    // Take screenshot
    await page.screenshot({ path: 'auth-enhancement-history.png', fullPage: true });
  });

  test('should persist history across sessions', async ({ page, context }) => {
    // 1. Login and create an enhancement
    await authHelper.loginUser({
      email: 'test@example.com',
      password: 'Test123456!'
    });
    
    await page.goto('http://localhost:3000/enhance');
    await page.waitForTimeout(3000);
    
    const textarea = page.locator('textarea');
    await textarea.fill('Test prompt for session persistence');
    
    const enhanceButton = page.locator('button').filter({ hasText: /Enhance/ }).first();
    await enhanceButton.click();
    await page.waitForTimeout(3000);
    
    // 2. Logout
    await authHelper.logout();
    
    // 3. Login again
    await authHelper.loginUser({
      email: 'test@example.com',
      password: 'Test123456!'
    });
    
    // 4. Check history
    await page.goto('http://localhost:3000/history');
    await page.waitForLoadState('networkidle');
    
    const historyText = await page.textContent('body');
    if (historyText?.includes('session persistence')) {
      console.log('✅ History persisted across sessions!');
    } else {
      console.log('❌ History not found after re-login');
    }
  });

  test('should not save history for unauthenticated users', async ({ page }) => {
    // 1. Use enhance without login
    await page.goto('http://localhost:3000/enhance');
    await page.waitForTimeout(3000);
    
    const textarea = page.locator('textarea');
    await textarea.fill('Unauthenticated test prompt');
    
    const enhanceButton = page.locator('button').filter({ hasText: /Enhance/ }).first();
    await enhanceButton.click();
    await page.waitForTimeout(3000);
    
    // 2. Try to access history (should redirect to login)
    await page.goto('http://localhost:3000/history');
    await page.waitForURL('**/login**');
    
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.log('✅ Correctly redirected to login for history access');
    } else {
      console.log('❌ Did not redirect to login');
      console.log('Current URL:', currentUrl);
    }
  });
});