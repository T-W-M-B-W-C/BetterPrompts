import { test, expect } from '@playwright/test';

test.describe('Phase 4: History API Tests', () => {
  const API_BASE = 'http://localhost/api/v1';
  
  test('history endpoints work with dev auth bypass', async ({ request }) => {
    // Test 1: Get history with dev auth bypass
    const historyResponse = await request.get(`${API_BASE}/prompts/history`, {
      headers: {
        'X-Test-Mode': 'true',
        'Content-Type': 'application/json'
      },
      params: {
        page: 1,
        limit: 10
      }
    });
    
    expect(historyResponse.ok()).toBe(true);
    const historyData = await historyResponse.json();
    
    // Check response structure
    expect(historyData).toHaveProperty('data');
    expect(historyData).toHaveProperty('pagination');
    expect(historyData.pagination).toHaveProperty('page');
    expect(historyData.pagination).toHaveProperty('limit');
    expect(historyData.pagination).toHaveProperty('total_records');
    
    console.log('History response:', JSON.stringify(historyData, null, 2));
    
    // Test 2: Search functionality
    const searchResponse = await request.get(`${API_BASE}/prompts/history`, {
      headers: {
        'X-Test-Mode': 'true',
        'Content-Type': 'application/json'
      },
      params: {
        page: 1,
        limit: 10,
        search: 'test'
      }
    });
    
    expect(searchResponse.ok()).toBe(true);
    const searchData = await searchResponse.json();
    expect(searchData).toHaveProperty('data');
    expect(Array.isArray(searchData.data)).toBe(true);
    
    // Test 3: Filter by intent
    const intentResponse = await request.get(`${API_BASE}/prompts/history`, {
      headers: {
        'X-Test-Mode': 'true',
        'Content-Type': 'application/json'
      },
      params: {
        page: 1,
        limit: 10,
        intent: 'code_generation'
      }
    });
    
    expect(intentResponse.ok()).toBe(true);
    const intentData = await intentResponse.json();
    expect(intentData).toHaveProperty('data');
    
    // Test 4: Get specific prompt if we have any
    if (historyData.data && historyData.data.length > 0) {
      const promptId = historyData.data[0].id;
      
      const detailResponse = await request.get(`${API_BASE}/prompts/${promptId}`, {
        headers: {
          'X-Test-Mode': 'true',
          'Content-Type': 'application/json'
        }
      });
      
      expect(detailResponse.ok()).toBe(true);
      const detailData = await detailResponse.json();
      expect(detailData).toHaveProperty('id');
      expect(detailData).toHaveProperty('original_input');
      expect(detailData).toHaveProperty('enhanced_output');
      
      console.log('Detail response:', JSON.stringify(detailData, null, 2));
      
      // Test 5: Rerun prompt
      const rerunResponse = await request.post(`${API_BASE}/prompts/${promptId}/rerun`, {
        headers: {
          'X-Test-Mode': 'true',
          'Content-Type': 'application/json'
        }
      });
      
      // Rerun might fail due to ML services, but should at least return proper error
      if (rerunResponse.ok()) {
        const rerunData = await rerunResponse.json();
        expect(rerunData).toHaveProperty('id');
      } else {
        // Should get a structured error response
        const errorData = await rerunResponse.json();
        expect(errorData).toHaveProperty('error');
      }
    }
  });
  
  test('frontend history page loads and displays data', async ({ page }) => {
    // Navigate to history page
    await page.goto('http://localhost:3000/history');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check page title
    await expect(page.locator('h1')).toContainText('Prompt History');
    
    // Check for filters
    await expect(page.locator('input[placeholder*="Search prompts"]')).toBeVisible();
    
    // Check for history items or empty state
    const historyItems = page.locator('[class*="card"]').filter({ hasText: 'Original Prompt' });
    const itemCount = await historyItems.count();
    
    if (itemCount > 0) {
      console.log(`Found ${itemCount} history items`);
      
      // Click on first item
      await historyItems.first().click();
      
      // Should navigate to detail page
      await page.waitForURL(/\/history\/[a-f0-9-]+/);
      
      // Check detail page elements
      await expect(page.locator('h1')).toContainText('Prompt Details');
      await expect(page.locator('text=Original Prompt')).toBeVisible();
      await expect(page.locator('text=Enhanced Prompt')).toBeVisible();
      
      // Check for action buttons
      await expect(page.locator('button:has-text("Rerun")')).toBeVisible();
      await expect(page.locator('button:has-text("Export")')).toBeVisible();
      await expect(page.locator('button:has-text("Delete")')).toBeVisible();
    } else {
      // Check empty state
      await expect(page.locator('text=No prompts in your history yet')).toBeVisible();
    }
  });
});