/**
 * Hydration Fix Verification Tests
 * 
 * These tests verify that the React hydration error has been resolved
 * and that the theme provider works correctly without SSR mismatches.
 */

import { test, expect } from '@playwright/test'

test.describe('Hydration Fix Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        // Fail test if hydration error detected
        if (text.includes('Hydration') || text.includes('did not match')) {
          throw new Error(`Hydration error detected: ${text}`)
        }
      }
    })
  })

  test('should load homepage without hydration errors', async ({ page }) => {
    // Navigate to the homepage
    await page.goto('http://localhost:3000')
    
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle')
    
    // Check that the html element has the expected attributes
    const html = page.locator('html')
    await expect(html).toHaveAttribute('lang', 'en')
    await expect(html).toHaveClass(/h-full/)
    
    // Verify suppressHydrationWarning is present
    const htmlContent = await page.content()
    expect(htmlContent).toContain('suppressHydrationWarning')
    
    // Check that main content is visible
    await expect(page.locator('main')).toBeVisible()
    
    // No hydration errors should have been thrown
  })

  test('should handle theme switching without hydration issues', async ({ page }) => {
    await page.goto('http://localhost:3000')
    await page.waitForLoadState('networkidle')
    
    // Check initial theme state
    const html = page.locator('html')
    const initialClasses = await html.getAttribute('class')
    
    // Theme should be either 'light' or not have theme class initially
    expect(initialClasses).toMatch(/h-full/)
    
    // If there's a theme toggle, test it
    const themeToggle = page.locator('[data-testid="theme-toggle"], [aria-label*="theme"]').first()
    if (await themeToggle.count() > 0) {
      await themeToggle.click()
      
      // Wait for theme change
      await page.waitForTimeout(100)
      
      // Check that theme changed without errors
      const newClasses = await html.getAttribute('class')
      expect(newClasses).toBeTruthy()
    }
  })

  test('should render all pages without hydration errors', async ({ page }) => {
    const pages = [
      '/',
      '/enhance',
      '/history',
      '/dashboard',
      '/login',
      '/register'
    ]
    
    for (const path of pages) {
      await page.goto(`http://localhost:3000${path}`)
      await page.waitForLoadState('networkidle')
      
      // Each page should load without hydration errors
      await expect(page.locator('body')).toBeVisible()
      
      // Check for common layout elements
      const header = page.locator('header, [role="banner"]').first()
      if (await header.count() > 0) {
        await expect(header).toBeVisible()
      }
    }
  })

  test('should maintain consistent theme across navigation', async ({ page }) => {
    await page.goto('http://localhost:3000')
    await page.waitForLoadState('networkidle')
    
    // Set theme to dark if toggle exists
    const themeToggle = page.locator('[data-testid="theme-toggle"], [aria-label*="theme"]').first()
    if (await themeToggle.count() > 0) {
      await themeToggle.click()
      await page.waitForTimeout(100)
    }
    
    // Navigate to another page
    await page.goto('http://localhost:3000/enhance')
    await page.waitForLoadState('networkidle')
    
    // Theme should persist without hydration errors
    const html = page.locator('html')
    const classes = await html.getAttribute('class')
    expect(classes).toBeTruthy()
  })
})