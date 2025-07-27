/**
 * User Test Data Fixtures
 * Based on Wave 1 Architecture - 5 Personas
 */

export interface TestUser {
  email: string;
  password: string;
  name: string;
  role: 'user' | 'power_user' | 'admin' | 'enterprise';
  persona: 'sarah' | 'alex' | 'chen' | 'maria' | 'techcorp';
  apiKey?: string;
  features?: string[];
}

export const testUsers: Record<string, TestUser> = {
  // Sarah - Marketing Manager (Basic User)
  sarah: {
    email: 'sarah.marketing@example.com',
    password: 'Test123!@#',
    name: 'Sarah Johnson',
    role: 'user',
    persona: 'sarah',
    features: ['basic_enhancement', 'save_favorites', 'view_history'],
  },
  
  // Alex - Software Developer (Power User)
  alex: {
    email: 'alex.developer@example.com',
    password: 'Dev123!@#',
    name: 'Alex Chen',
    role: 'power_user',
    persona: 'alex',
    apiKey: 'test_api_key_alex_123',
    features: ['api_access', 'code_enhancement', 'custom_techniques', 'batch_processing'],
  },
  
  // Dr. Chen - Data Scientist (Power User)
  drChen: {
    email: 'dr.chen@university.edu',
    password: 'Research123!@#',
    name: 'Dr. Emily Chen',
    role: 'power_user',
    persona: 'chen',
    apiKey: 'test_api_key_chen_456',
    features: ['batch_processing', 'metrics_export', 'advanced_techniques', 'api_access'],
  },
  
  // Maria - Content Creator (Power User)
  maria: {
    email: 'maria.content@agency.com',
    password: 'Content123!@#',
    name: 'Maria Rodriguez',
    role: 'power_user',
    persona: 'maria',
    features: ['template_library', 'bulk_export', 'team_sharing', 'custom_techniques'],
  },
  
  // TechCorp - Enterprise User
  techcorp: {
    email: 'admin@techcorp.com',
    password: 'Enterprise123!@#',
    name: 'TechCorp Admin',
    role: 'enterprise',
    persona: 'techcorp',
    apiKey: 'test_api_key_enterprise_789',
    features: ['sso', 'audit_logs', 'rate_limits', 'team_management', 'compliance'],
  },
  
  // Additional test users
  newUser: {
    email: 'new.user@example.com',
    password: 'NewUser123!@#',
    name: 'New User',
    role: 'user',
    persona: 'sarah',
    features: [],
  },
  
  blockedUser: {
    email: 'blocked@example.com',
    password: 'Blocked123!@#',
    name: 'Blocked User',
    role: 'user',
    persona: 'sarah',
    features: [],
  },
  
  adminUser: {
    email: 'admin@betterprompts.com',
    password: 'Admin123!@#',
    name: 'System Admin',
    role: 'admin',
    persona: 'techcorp',
    features: ['all'],
  },
};

/**
 * Get user by persona
 */
export function getUserByPersona(persona: string): TestUser {
  return Object.values(testUsers).find(user => user.persona === persona) || testUsers.sarah;
}

/**
 * Get users by role
 */
export function getUsersByRole(role: string): TestUser[] {
  return Object.values(testUsers).filter(user => user.role === role);
}

/**
 * Generate unique test user
 */
export function generateTestUser(prefix: string = 'test'): TestUser {
  const timestamp = Date.now();
  return {
    email: `${prefix}.${timestamp}@example.com`,
    password: 'Test123!@#',
    name: `Test User ${timestamp}`,
    role: 'user',
    persona: 'sarah',
    features: ['basic_enhancement'],
  };
}