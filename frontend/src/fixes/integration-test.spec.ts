/**
 * Enhancement-to-History Integration Tests
 * 
 * These tests verify that enhancements are properly saved to history
 * for authenticated users and that the full integration flow works.
 */

import { test, expect } from '@playwright/test'

test.describe('Enhancement-to-History Integration', () => {
  // Helper to login
  async function login(page: any, email: string, password: string) {
    await page.goto('http://localhost:3000/login')
    await page.fill('input[name="email"], input[type="email"]', email)
    await page.fill('input[name="password"], input[type="password"]', password)
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard', { timeout: 10000 })
  }

  test('should save enhancement to history for authenticated users', async ({ page }) => {
    // Login first
    await login(page, 'test@example.com', 'Test123!')
    
    // Navigate to enhance page
    await page.goto('http://localhost:3000/enhance')
    await page.waitForLoadState('networkidle')
    
    // Enter a prompt
    const testPrompt = 'Help me write a blog post about AI ethics'
    await page.fill('textarea[placeholder*="Enter your prompt"]', testPrompt)
    
    // Click enhance button
    await page.click('button:has-text("Enhance Prompt")')
    
    // Wait for enhancement to complete
    await page.waitForSelector('[data-testid="enhanced-output"], .enhanced-prompt', { 
      timeout: 30000 
    })
    
    // Verify enhancement completed
    const enhancedContent = await page.locator('[data-testid="enhanced-output"], .enhanced-prompt').first()
    await expect(enhancedContent).toBeVisible()
    
    // Navigate to history page
    await page.goto('http://localhost:3000/history')
    await page.waitForLoadState('networkidle')
    
    // Check that the enhancement appears in history
    await expect(page.locator('text=' + testPrompt.substring(0, 30))).toBeVisible({ 
      timeout: 10000 
    })
  })

  test('should not save enhancement to history for unauthenticated users', async ({ page }) => {
    // Make sure we're logged out
    await page.goto('http://localhost:3000/logout')
    
    // Navigate to enhance page
    await page.goto('http://localhost:3000/enhance')
    await page.waitForLoadState('networkidle')
    
    // Enter a prompt
    const testPrompt = 'Help me understand quantum computing'
    await page.fill('textarea[placeholder*="Enter your prompt"]', testPrompt)
    
    // Click enhance button
    await page.click('button:has-text("Enhance Prompt")')
    
    // Wait for enhancement to complete
    await page.waitForSelector('[data-testid="enhanced-output"], .enhanced-prompt', { 
      timeout: 30000 
    })
    
    // Try to navigate to history (should redirect to login or show empty)
    await page.goto('http://localhost:3000/history')
    
    // Should either redirect to login or show empty history
    const url = page.url()
    if (!url.includes('/login')) {
      // If we can access history, it should be empty
      await expect(page.locator('text="No history items"')).toBeVisible()
    }
  })

  test('should display technique information in history', async ({ page }) => {
    // Login first
    await login(page, 'test@example.com', 'Test123!')
    
    // Navigate to enhance page
    await page.goto('http://localhost:3000/enhance')
    await page.waitForLoadState('networkidle')
    
    // Expand techniques section
    await page.click('button:has-text("Techniques")')
    await page.waitForTimeout(500)
    
    // Select a specific technique if available
    const techniqueCard = page.locator('.technique-card, [data-testid*="technique"]').first()
    if (await techniqueCard.count() > 0) {
      await techniqueCard.click()
    }
    
    // Enter a prompt and enhance
    const testPrompt = 'Explain machine learning to a beginner'
    await page.fill('textarea[placeholder*="Enter your prompt"]', testPrompt)
    await page.click('button:has-text("Enhance Prompt")')
    
    // Wait for enhancement
    await page.waitForSelector('[data-testid="enhanced-output"], .enhanced-prompt', { 
      timeout: 30000 
    })
    
    // Navigate to history
    await page.goto('http://localhost:3000/history')
    await page.waitForLoadState('networkidle')
    
    // Find the history item
    const historyItem = page.locator(`text=${testPrompt.substring(0, 30)}`).locator('..')
    
    // Check that technique information is displayed
    await expect(historyItem.locator('text=/technique|method/i')).toBeVisible()
  })

  test('should handle enhancement errors gracefully', async ({ page }) => {
    // Login first
    await login(page, 'test@example.com', 'Test123!')
    
    // Navigate to enhance page
    await page.goto('http://localhost:3000/enhance')
    await page.waitForLoadState('networkidle')
    
    // Enter an extremely long prompt that might cause an error
    const longPrompt = 'Test '.repeat(10000)
    await page.fill('textarea[placeholder*="Enter your prompt"]', longPrompt)
    
    // Click enhance button
    await page.click('button:has-text("Enhance Prompt")')
    
    // Should either show error or handle gracefully
    const result = await Promise.race([
      page.waitForSelector('[data-testid="error-message"], .error', { timeout: 30000 }),
      page.waitForSelector('[data-testid="enhanced-output"], .enhanced-prompt', { timeout: 30000 })
    ])
    
    // Verify some result was shown
    await expect(result).toBeVisible()
  })

  test('should display technique cards correctly', async ({ page }) => {
    await page.goto('http://localhost:3000/enhance')
    await page.waitForLoadState('networkidle')
    
    // Click techniques button to expand
    const techniquesButton = page.locator('button:has-text("Techniques")')
    await techniquesButton.click()
    
    // Wait for techniques to load
    await page.waitForTimeout(1000)
    
    // Check if technique cards are displayed
    const techniqueCards = page.locator('.technique-card, [class*="technique"], [data-testid*="technique"]')
    const count = await techniqueCards.count()
    
    // Should have at least one technique card
    expect(count).toBeGreaterThan(0)
    
    // Verify technique cards have required elements
    if (count > 0) {
      const firstCard = techniqueCards.first()
      
      // Should have a name/title
      const title = firstCard.locator('h3, h4, [class*="title"], [class*="name"]')
      await expect(title).toBeVisible()
      
      // Should have a description
      const description = firstCard.locator('p, [class*="description"]')
      await expect(description).toBeVisible()
      
      // Should be clickable
      await firstCard.click()
      
      // Should show selected state (border color change, background, etc.)
      const classes = await firstCard.getAttribute('class')
      expect(classes).toMatch(/selected|active|blue|primary/)
    }
  })
})