import { test, expect } from '@playwright/test';
import { AuthHelper } from './utils/AuthHelper';

test.describe('Debug Auth Storage', () => {
  test('check auth token storage', async ({ page, context }) => {
    const authHelper = new AuthHelper(page, context);
    
    // Login
    const tokens = await authHelper.loginUser(AuthHelper.TEST_USERS.regular);
    console.log('Login successful');
    
    // Check cookies
    const cookies = await context.cookies();
    console.log('Cookies:', cookies.map(c => ({ name: c.name, value: c.value ? 'present' : 'missing' })));
    
    // Check localStorage
    const localStorageData = await page.evaluate(() => {
      return {
        accessToken: localStorage.getItem('access_token'),
        refreshToken: localStorage.getItem('refresh_token'),
        user: localStorage.getItem('user')
      };
    });
    console.log('LocalStorage:', {
      accessToken: localStorageData.accessToken ? 'present' : 'missing',
      refreshToken: localStorageData.refreshToken ? 'present' : 'missing',
      user: localStorageData.user ? 'present' : 'missing'
    });
    
    // Make an authenticated API call
    const response = await page.request.get('/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${tokens.accessToken}`
      }
    });
    console.log('API /auth/me status:', response.status());
    
    if (response.ok()) {
      const data = await response.json();
      console.log('User data:', data);
    } else {
      console.log('API error:', await response.text());
    }
    
    // Try to access a protected page with the token in header
    await page.setExtraHTTPHeaders({
      'Authorization': `Bearer ${tokens.accessToken}`
    });
    
    await page.goto('/enhance');
    const finalUrl = page.url();
    console.log('Final URL after /enhance with auth header:', finalUrl);
  });
});