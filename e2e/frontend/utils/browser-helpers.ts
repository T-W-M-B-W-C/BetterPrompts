/**
 * Browser-specific helpers for E2E tests
 */

export const browserConfig = {
  firefox: {
    // Firefox needs more time for certain operations
    inputDelay: 100,
    navigationTimeout: 30000,
    performanceMultiplier: 2.5, // Firefox is slower in CI/test environments
  },
  webkit: {
    inputDelay: 50,
    navigationTimeout: 20000,
    performanceMultiplier: 1.5,
  },
  chromium: {
    inputDelay: 0,
    navigationTimeout: 15000,
    performanceMultiplier: 1,
  },
};

export function getBrowserConfig(browserName: string) {
  return browserConfig[browserName as keyof typeof browserConfig] || browserConfig.chromium;
}

export async function typeWithBrowserDelay(page: any, selector: string, text: string, browserName: string) {
  const config = getBrowserConfig(browserName);
  const input = page.locator(selector);
  
  if (config.inputDelay > 0) {
    // Type character by character with delay for browsers that need it
    for (const char of text) {
      await input.type(char);
      await page.waitForTimeout(config.inputDelay);
    }
  } else {
    await input.fill(text);
  }
}

export function adjustPerformanceExpectation(baseTime: number, browserName: string): number {
  const config = getBrowserConfig(browserName);
  return Math.ceil(baseTime * config.performanceMultiplier);
}