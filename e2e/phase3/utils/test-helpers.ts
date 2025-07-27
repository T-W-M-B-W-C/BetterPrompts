/**
 * Test helper utilities for Phase 3 E2E tests
 */

/**
 * Generate a unique email address for testing
 */
export function generateUniqueEmail(prefix: string = 'test'): string {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 1000);
  return `${prefix}_${timestamp}_${random}@example.com`;
}

/**
 * Generate a unique username for testing
 */
export function generateUniqueUsername(prefix: string = 'user'): string {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 1000);
  return `${prefix}_${timestamp}_${random}`;
}

/**
 * Generate test user data
 */
export function generateTestUser(overrides: Partial<any> = {}) {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 1000);
  
  return {
    firstName: 'Test',
    lastName: 'User',
    username: `testuser_${timestamp}_${random}`,
    email: `test_${timestamp}_${random}@example.com`,
    password: 'Test123!@#',
    confirmPassword: 'Test123!@#',
    acceptTerms: true,
    ...overrides
  };
}

/**
 * Wait for a specific duration (use sparingly, prefer condition-based waiting)
 */
export async function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Format date for display
 */
export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Mock API response helper
 */
export function createMockResponse(data: any, status: number = 200) {
  return {
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: {
      'content-type': 'application/json'
    },
    body: JSON.stringify(data)
  };
}