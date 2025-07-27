/**
 * Test User Generator Utility
 * Generates unique test users for registration testing
 */

export interface TestUserData {
  firstName?: string;
  lastName?: string;
  username: string;
  email: string;
  password: string;
  confirmPassword?: string;
  acceptTerms?: boolean;
  acceptMarketing?: boolean;
  persona?: string;
  metadata?: Record<string, any>;
}

export class TestUserGenerator {
  private static counter = 0;
  
  /**
   * Generate a unique test user
   */
  static generate(overrides?: Partial<TestUserData>): TestUserData {
    const timestamp = Date.now();
    const uniqueId = `${timestamp}-${this.counter++}`;
    const randomString = Math.random().toString(36).substring(2, 8);
    
    const defaultUser: TestUserData = {
      firstName: 'Test',
      lastName: `User${uniqueId}`,
      username: `testuser${randomString}${uniqueId}`.toLowerCase().replace(/[^a-z0-9]/g, ''),
      email: `test.user.${uniqueId}.${randomString}@example.com`,
      password: 'SecureP@ssw0rd123!',
      acceptTerms: true,
      acceptMarketing: false,
      persona: 'tester',
      metadata: {
        createdAt: new Date().toISOString(),
        testRun: process.env.TEST_RUN_ID || 'local',
        environment: process.env.TEST_ENV || 'local'
      }
    };
    
    return {
      ...defaultUser,
      ...overrides,
      confirmPassword: overrides?.confirmPassword || overrides?.password || defaultUser.password
    };
  }
  
  /**
   * Generate multiple unique test users
   */
  static generateBatch(count: number, overrides?: Partial<TestUserData>): TestUserData[] {
    return Array.from({ length: count }, () => this.generate(overrides));
  }
  
  /**
   * Generate test user with specific persona
   */
  static generateWithPersona(persona: 'developer' | 'marketing' | 'student' | 'enterprise'): TestUserData {
    const personaData: Record<string, Partial<TestUserData>> = {
      developer: {
        firstName: 'Dev',
        lastName: 'User',
        username: `dev${this.counter}`,
        acceptMarketing: true,
        metadata: { role: 'developer', experience: 'senior' }
      },
      marketing: {
        firstName: 'Marketing',
        lastName: 'User',
        username: `marketing${this.counter}`,
        acceptMarketing: true,
        metadata: { role: 'marketing', department: 'growth' }
      },
      student: {
        firstName: 'Student',
        lastName: 'User',
        username: `student${this.counter}`,
        acceptMarketing: false,
        metadata: { role: 'student', institution: 'university' }
      },
      enterprise: {
        firstName: 'Enterprise',
        lastName: 'User', 
        username: `enterprise${this.counter}`,
        acceptMarketing: true,
        metadata: { role: 'enterprise', company: 'TechCorp' }
      }
    };
    
    return this.generate({
      ...personaData[persona],
      persona
    });
  }
  
  /**
   * Generate test user with invalid data for validation testing
   */
  static generateInvalid(invalidType: 'email' | 'password' | 'name'): TestUserData {
    const baseUser = this.generate();
    
    const invalidData: Record<string, Partial<TestUserData>> = {
      email: {
        email: 'invalid-email-format'
      },
      password: {
        password: '123', // Too weak
        confirmPassword: '123'
      },
      username: {
        username: '' // Empty username
      }
    };
    
    return {
      ...baseUser,
      ...invalidData[invalidType]
    };
  }
  
  /**
   * Generate test user with edge case data
   */
  static generateEdgeCase(edgeCase: 'long' | 'special' | 'unicode' | 'sql'): TestUserData {
    const edgeCaseData: Record<string, Partial<TestUserData>> = {
      long: {
        firstName: 'A'.repeat(128),
        lastName: 'B'.repeat(128),
        username: 'a'.repeat(64), // Very long username
        email: `${'a'.repeat(64)}@${'b'.repeat(63)}.com`
      },
      special: {
        firstName: "O'Brien-Smith",
        lastName: "& Co.",
        username: 'obrien_smith_co',
        email: 'test+special.chars-123@sub.domain.example.com'
      },
      unicode: {
        firstName: '测试用户',
        lastName: 'テストユーザー',
        username: 'unicode_test_user',
        email: 'unicode.test@example.com'
      },
      sql: {
        firstName: "Robert'); DROP TABLE users;--",
        lastName: "Smith",
        username: 'robert_smith',
        email: 'sql.injection@example.com'
      }
    };
    
    return this.generate(edgeCaseData[edgeCase]);
  }
  
  /**
   * Reset counter for test isolation
   */
  static reset(): void {
    this.counter = 0;
  }
}

/**
 * Helper function for quick user generation
 */
export function generateTestUser(overrides?: Partial<TestUserData>): TestUserData {
  return TestUserGenerator.generate(overrides);
}

/**
 * Generate a unique email address
 */
export function generateUniqueEmail(prefix: string = 'test'): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `${prefix}.${timestamp}.${random}@example.com`;
}

/**
 * Generate a secure password
 */
export function generateSecurePassword(length: number = 16): string {
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const numbers = '0123456789';
  const special = '!@#$%^&*()_+-=[]{}|;:,.<>?';
  const all = uppercase + lowercase + numbers + special;
  
  let password = '';
  // Ensure at least one of each type
  password += uppercase[Math.floor(Math.random() * uppercase.length)];
  password += lowercase[Math.floor(Math.random() * lowercase.length)];
  password += numbers[Math.floor(Math.random() * numbers.length)];
  password += special[Math.floor(Math.random() * special.length)];
  
  // Fill the rest randomly
  for (let i = password.length; i < length; i++) {
    password += all[Math.floor(Math.random() * all.length)];
  }
  
  // Shuffle the password
  return password.split('').sort(() => Math.random() - 0.5).join('');
}