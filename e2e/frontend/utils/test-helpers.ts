import { Page, expect, Browser, BrowserContext } from '@playwright/test';
import { testUsers, TestUser } from '../fixtures/users';

/**
 * Test Helper Utilities
 * Common functions for E2E tests
 */

/**
 * Login helper
 */
export async function login(page: Page, user: TestUser) {
  await page.goto('/login');
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');
  
  // Wait for successful login
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

/**
 * Logout helper
 */
export async function logout(page: Page) {
  await page.click('[data-testid="user-menu"]');
  await page.click('button:has-text("Log Out")');
  await page.waitForURL('**/login');
}

/**
 * Create authenticated context
 */
export async function createAuthenticatedContext(
  browser: Browser,
  user: TestUser
): Promise<BrowserContext> {
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await login(page, user);
  
  // Save authentication state
  await context.storageState({ path: `auth-${user.persona}.json` });
  await page.close();
  
  return context;
}

/**
 * Load authenticated state
 */
export async function loadAuthenticatedState(
  browser: Browser,
  persona: string
): Promise<BrowserContext> {
  return await browser.newContext({
    storageState: `auth-${persona}.json`,
  });
}

/**
 * Wait for API response
 */
export async function waitForAPI(
  page: Page,
  endpoint: string,
  method: string = 'POST'
): Promise<any> {
  const response = await page.waitForResponse(
    (resp) => resp.url().includes(endpoint) && resp.request().method() === method
  );
  
  return await response.json();
}

/**
 * Mock API response
 */
export async function mockAPIResponse(
  page: Page,
  endpoint: string,
  response: any,
  status: number = 200
) {
  await page.route(`**/${endpoint}`, (route) => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Check performance metrics
 */
export async function checkPerformance(page: Page, thresholds: {
  lcp?: number;
  fid?: number;
  cls?: number;
  ttfb?: number;
}) {
  const metrics = await page.evaluate(() => {
    return new Promise((resolve) => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const metrics: any = {};
        
        entries.forEach((entry) => {
          if (entry.entryType === 'largest-contentful-paint') {
            metrics.lcp = entry.startTime;
          }
        });
        
        resolve(metrics);
      }).observe({ entryTypes: ['largest-contentful-paint'] });
      
      // Also get navigation timing
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        ttfb: navigation.responseStart - navigation.requestStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        load: navigation.loadEventEnd - navigation.loadEventStart,
      };
    });
  });
  
  // Check against thresholds
  if (thresholds.lcp && metrics.lcp) {
    expect(metrics.lcp).toBeLessThan(thresholds.lcp);
  }
  if (thresholds.ttfb && metrics.ttfb) {
    expect(metrics.ttfb).toBeLessThan(thresholds.ttfb);
  }
  
  return metrics;
}

/**
 * Take screenshot with timestamp
 */
export async function takeScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({
    path: `test-results/screenshots/${name}-${timestamp}.png`,
    fullPage: true,
  });
}

/**
 * Check accessibility
 */
export async function checkAccessibility(page: Page, options?: {
  includedImpacts?: string[];
  excludedImpacts?: string[];
  detailedReport?: boolean;
}) {
  const { injectAxe, checkA11y, getViolations } = require('@axe-core/playwright');
  
  await injectAxe(page);
  
  if (options?.detailedReport) {
    const violations = await getViolations(page);
    console.log('Accessibility violations:', violations);
    expect(violations).toHaveLength(0);
  } else {
    await checkA11y(page, null, {
      includedImpacts: options?.includedImpacts || ['critical', 'serious'],
      detailedReport: false,
    });
  }
}

/**
 * Wait for network idle
 */
export async function waitForNetworkIdle(page: Page, timeout: number = 5000) {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Retry operation
 */
export async function retry<T>(
  operation: () => Promise<T>,
  retries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error | undefined;
  
  for (let i = 0; i < retries; i++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      if (i < retries - 1) {
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}

/**
 * Generate unique email
 */
export function generateUniqueEmail(prefix: string = 'test'): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `${prefix}.${timestamp}.${random}@example.com`;
}

/**
 * Format test report data
 */
export function formatTestReport(data: {
  testName: string;
  duration: number;
  status: 'passed' | 'failed' | 'skipped';
  error?: string;
}) {
  return {
    ...data,
    timestamp: new Date().toISOString(),
    environment: process.env.TEST_ENV || 'local',
    browser: process.env.BROWSER || 'chromium',
  };
}

/**
 * Setup test data via API
 */
export async function setupTestData(page: Page, data: {
  users?: TestUser[];
  prompts?: any[];
  settings?: any;
}) {
  // This would typically call backend APIs to set up test data
  // For now, we'll mock this functionality
  console.log('Setting up test data:', data);
}

/**
 * Cleanup test data
 */
export async function cleanupTestData(page: Page, userId?: string) {
  // This would typically call backend APIs to clean up test data
  console.log('Cleaning up test data for user:', userId);
}

/**
 * Visual regression comparison
 */
export async function compareScreenshots(
  page: Page,
  name: string,
  options?: {
    fullPage?: boolean;
    clip?: { x: number; y: number; width: number; height: number };
    mask?: string[];
    maxDiffPixels?: number;
    threshold?: number;
  }
) {
  await expect(page).toHaveScreenshot(`${name}.png`, {
    fullPage: options?.fullPage ?? true,
    clip: options?.clip,
    mask: options?.mask ? page.locator(options.mask.join(', ')) : undefined,
    maxDiffPixels: options?.maxDiffPixels ?? 100,
    threshold: options?.threshold ?? 0.2,
  });
}