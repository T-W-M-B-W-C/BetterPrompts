import { Client } from 'pg';

/**
 * Database utilities for E2E tests
 * Provides cleanup and data access for test isolation
 */

// Database configuration for E2E tests
const DB_CONFIG = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5433'),
  user: process.env.DB_USER || 'betterprompts',
  password: process.env.DB_PASSWORD || 'betterprompts',
  database: process.env.DB_NAME || 'betterprompts_e2e',
};

/**
 * Create a new database client
 */
export function createDbClient(): Client {
  return new Client(DB_CONFIG);
}

/**
 * Clean up all test data from the database
 */
export async function cleanupDatabase(): Promise<void> {
  const client = createDbClient();
  
  try {
    await client.connect();
    
    // Delete in reverse order of foreign key dependencies
    const tables = [
      { schema: 'prompts', name: 'history' },
      { schema: 'auth', name: 'sessions' },
      { schema: 'public', name: 'email_verifications' },
      { schema: 'auth', name: 'api_keys' },
      { schema: 'auth', name: 'user_preferences' },
      { schema: 'auth', name: 'users' }
    ];
    
    for (const table of tables) {
      try {
        await client.query(`DELETE FROM ${table.schema}.${table.name}`);
        console.log(`Cleaned table: ${table.schema}.${table.name}`);
      } catch (error) {
        console.warn(`Failed to clean table ${table.schema}.${table.name}:`, error);
      }
    }
    
    // Reset sequences
    await client.query(`
      SELECT setval(pg_get_serial_sequence('auth.users', 'id'), 1, false);
    `);
    
  } finally {
    await client.end();
  }
}

/**
 * Get verification code for a user by email
 */
export async function getVerificationCode(email: string): Promise<string | null> {
  const client = createDbClient();
  
  try {
    await client.connect();
    
    // For E2E tests, we'll create a simple verification table if needed
    await client.query(`
      CREATE TABLE IF NOT EXISTS email_verifications (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        verification_token VARCHAR(255) NOT NULL,
        expires_at TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
      );
    `);
    
    const result = await client.query(
      `SELECT verification_token 
       FROM email_verifications 
       WHERE email = $1 
       ORDER BY created_at DESC 
       LIMIT 1`,
      [email]
    );
    
    return result.rows[0]?.verification_token || null;
    
  } finally {
    await client.end();
  }
}

/**
 * Check if a user exists in the database
 */
export async function userExists(email: string): Promise<boolean> {
  const client = createDbClient();
  
  try {
    await client.connect();
    
    const result = await client.query(
      'SELECT 1 FROM auth.users WHERE email = $1',
      [email]
    );
    
    return result.rows.length > 0;
    
  } finally {
    await client.end();
  }
}

/**
 * Get user details by email
 */
export async function getUser(email: string): Promise<any | null> {
  const client = createDbClient();
  
  try {
    await client.connect();
    
    const result = await client.query(
      `SELECT id, email, username, first_name, last_name, is_verified as email_verified, created_at 
       FROM auth.users 
       WHERE email = $1`,
      [email]
    );
    
    return result.rows[0] || null;
    
  } finally {
    await client.end();
  }
}

/**
 * Seed test data into the database
 */
export async function seedTestData(data: {
  users?: Array<{
    email: string;
    name: string;
    password: string;
    emailVerified?: boolean;
  }>;
}): Promise<void> {
  const client = createDbClient();
  
  try {
    await client.connect();
    
    // Insert test users
    if (data.users) {
      for (const user of data.users) {
        await client.query(
          `INSERT INTO auth.users (email, name, password_hash, is_verified) 
           VALUES ($1, $2, $3, $4) 
           ON CONFLICT (email) DO NOTHING`,
          [
            user.email,
            user.name,
            // This is a placeholder - real app would hash the password
            `hashed_${user.password}`,
            user.emailVerified || false
          ]
        );
      }
    }
    
  } finally {
    await client.end();
  }
}

/**
 * Wait for database to be ready
 */
export async function waitForDatabase(maxAttempts: number = 30): Promise<void> {
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    const client = createDbClient();
    
    try {
      await client.connect();
      await client.query('SELECT 1');
      await client.end();
      console.log('Database is ready');
      return;
    } catch (error) {
      attempts++;
      console.log(`Waiting for database... (attempt ${attempts}/${maxAttempts})`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  throw new Error('Database not ready after maximum attempts');
}

/**
 * Create test-only database tables if needed
 */
export async function ensureTestTables(): Promise<void> {
  const client = createDbClient();
  
  try {
    await client.connect();
    
    // Create email_verifications table if it doesn't exist
    await client.query(`
      CREATE TABLE IF NOT EXISTS email_verifications (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        verification_token VARCHAR(255) NOT NULL,
        expires_at TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
      );
      
      CREATE INDEX IF NOT EXISTS idx_email_verifications_email 
      ON email_verifications(email);
      
      CREATE INDEX IF NOT EXISTS idx_email_verifications_token 
      ON email_verifications(verification_token);
    `);
    
  } finally {
    await client.end();
  }
}