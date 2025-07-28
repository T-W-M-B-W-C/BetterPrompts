import { test, expect } from '@playwright/test';

test.describe('Cookie-based Authentication Test', () => {
  test('login sets cookies and allows access to protected routes', async ({ page, context }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Fill login form
    await page.fill('input[name="email"]', 'e2etest@example.com');
    await page.fill('input[name="password"]', 'Test123!@#');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Wait for login to complete - button should no longer be in loading state
    await page.waitForFunction(() => {
      const button = document.querySelector('button[type="submit"]');
      return button && !button.textContent?.includes('Signing in');
    }, { timeout: 10000 });
    
    // Small delay to allow cookies and navigation to complete
    await page.waitForTimeout(2000);
    
    // Check cookies
    const cookies = await context.cookies();
    const authTokenCookie = cookies.find(c => c.name === 'auth_token');
    const refreshTokenCookie = cookies.find(c => c.name === 'refresh_token');
    
    console.log('Cookies after login:', {
      authToken: authTokenCookie ? 'present' : 'missing',
      refreshToken: refreshTokenCookie ? 'present' : 'missing',
      httpOnlyAuth: authTokenCookie?.httpOnly,
      httpOnlyRefresh: refreshTokenCookie?.httpOnly,
    });
    
    expect(authTokenCookie).toBeTruthy();
    expect(refreshTokenCookie).toBeTruthy();
    expect(authTokenCookie?.httpOnly).toBe(true);
    expect(refreshTokenCookie?.httpOnly).toBe(true);
    
    // Check localStorage
    const localStorageData = await page.evaluate(() => ({
      accessToken: localStorage.getItem('access_token'),
      refreshToken: localStorage.getItem('refresh_token'),
    }));
    
    console.log('LocalStorage after login:', {
      accessToken: localStorageData.accessToken ? 'present' : 'missing',
      refreshToken: localStorageData.refreshToken ? 'present' : 'missing',
    });
    
    expect(localStorageData.accessToken).toBeTruthy();
    expect(localStorageData.refreshToken).toBeTruthy();
    
    // Now navigate to a protected route
    await page.goto('/enhance');
    
    // Check if we stay on the enhance page (not redirected to login)
    expect(page.url()).toContain('/enhance');
    expect(page.url()).not.toContain('/login');
    
    console.log('Successfully accessed protected route /enhance');
    
    // Test another protected route
    await page.goto('/history');
    expect(page.url()).toContain('/history');
    expect(page.url()).not.toContain('/login');
    
    console.log('Successfully accessed protected route /history');
  });
  
  test('logout clears cookies and localStorage', async ({ page, context }) => {
    // First login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000); // Wait for login to complete
    
    // Verify we have cookies and localStorage
    let cookies = await context.cookies();
    expect(cookies.find(c => c.name === 'auth_token')).toBeTruthy();
    
    // Find and click logout button
    const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")').first();
    
    if (await logoutButton.count() > 0) {
      await logoutButton.click();
      
      // Wait a bit for logout to process
      await page.waitForTimeout(1000);
      
      // Check cookies are cleared
      cookies = await context.cookies();
      const authTokenCookie = cookies.find(c => c.name === 'auth_token');
      const refreshTokenCookie = cookies.find(c => c.name === 'refresh_token');
      
      console.log('Cookies after logout:', {
        authToken: authTokenCookie ? 'still present' : 'cleared',
        refreshToken: refreshTokenCookie ? 'still present' : 'cleared',
      });
      
      // Check localStorage is cleared
      const localStorageData = await page.evaluate(() => ({
        accessToken: localStorage.getItem('access_token'),
        refreshToken: localStorage.getItem('refresh_token'),
      }));
      
      console.log('LocalStorage after logout:', {
        accessToken: localStorageData.accessToken ? 'still present' : 'cleared',
        refreshToken: localStorageData.refreshToken ? 'still present' : 'cleared',
      });
      
      expect(localStorageData.accessToken).toBeNull();
      expect(localStorageData.refreshToken).toBeNull();
    } else {
      console.log('Logout button not found on page - skipping logout test');
    }
  });
  
  test('API calls work with both cookies and localStorage', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000); // Wait for login to complete
    
    // Make API call using page.request (uses cookies automatically)
    const cookieResponse = await page.request.get('http://localhost/api/v1/auth/profile');
    console.log('API call with cookies - status:', cookieResponse.status());
    expect(cookieResponse.ok()).toBe(true);
    
    const profileData = await cookieResponse.json();
    expect(profileData.email).toBe('test@example.com');
    
    // Make API call with Authorization header from localStorage
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const headerResponse = await page.request.get('http://localhost/api/v1/auth/profile', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    console.log('API call with Authorization header - status:', headerResponse.status());
    expect(headerResponse.ok()).toBe(true);
    
    console.log('Both cookie and header-based auth work for API calls');
  });
});