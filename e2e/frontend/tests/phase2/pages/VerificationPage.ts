import { Page } from '@playwright/test';

export class VerificationPage {
  constructor(private page: Page) {}

  async verifyWithCode(code: string) {
    // Split code into individual characters
    const chars = code.split('');
    
    // Find all code input fields
    const inputs = await this.page.locator('input[type="text"][maxlength="1"]').all();
    
    // Fill each input
    for (let i = 0; i < chars.length && i < inputs.length; i++) {
      await inputs[i].fill(chars[i]);
    }
    
    // Submit the form
    await this.page.click('button:has-text("Verify Email")');
  }

  async verifyAutoVerificationWithToken() {
    // Wait for auto-verification to complete
    await this.page.waitForSelector('text=/Email Verified|Your email has been successfully verified/i', { timeout: 10000 });
  }

  async isVerificationSuccessful(): Promise<boolean> {
    try {
      await this.page.waitForSelector('text=/Email Verified|successfully verified/i', { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async continueToApp() {
    await this.page.click('button:has-text("Continue to Dashboard")');
  }

  async resendVerificationEmail() {
    await this.page.click('button:has-text("Resend verification email")');
  }

  async getErrorMessage(): Promise<string> {
    const errorAlert = await this.page.locator('[role="alert"], .text-red-500').first();
    const isVisible = await errorAlert.isVisible().catch(() => false);
    if (!isVisible) return '';
    return await errorAlert.textContent() || '';
  }

  async getResendTimerText(): Promise<string> {
    const timerButton = await this.page.locator('button:has-text("Resend in")');
    const isVisible = await timerButton.isVisible().catch(() => false);
    if (!isVisible) return '';
    return await timerButton.textContent() || '';
  }
}