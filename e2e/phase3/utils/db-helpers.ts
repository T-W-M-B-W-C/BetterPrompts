import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export class DbHelpers {
  /**
   * Reset test user account to clean state
   */
  static async resetTestUser() {
    try {
      const command = `docker compose exec -T postgres psql -U betterprompts -d betterprompts_e2e -c "UPDATE auth.users SET failed_login_attempts = 0, locked_until = NULL WHERE email = 'test@example.com';"`;
      await execAsync(command);
      console.log('Test user account reset successfully');
    } catch (error) {
      console.error('Failed to reset test user:', error);
    }
  }
}