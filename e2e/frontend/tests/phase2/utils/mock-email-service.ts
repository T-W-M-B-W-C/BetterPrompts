import { Page, BrowserContext } from '@playwright/test';

/**
 * Mock Email Service Helper
 * Simulates email verification for testing
 */

export interface EmailMessage {
  id: string;
  to: string;
  from: string;
  subject: string;
  body: string;
  htmlBody?: string;
  timestamp: Date;
  verificationLink?: string;
  verificationCode?: string;
}

export class MockEmailService {
  private static emails: Map<string, EmailMessage[]> = new Map();
  private static verificationCodes: Map<string, string> = new Map();
  
  /**
   * Clear all stored emails
   */
  static reset(): void {
    this.emails.clear();
    this.verificationCodes.clear();
  }
  
  /**
   * Mock sending an email
   */
  static sendEmail(email: Omit<EmailMessage, 'id' | 'timestamp'>): EmailMessage {
    const message: EmailMessage = {
      ...email,
      id: `email-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };
    
    // Extract verification link or code from the email body
    const linkMatch = message.body.match(/https?:\/\/[^\s]+verify[^\s]+/);
    const codeMatch = message.body.match(/verification code[:\s]+([A-Z0-9]{6})/i);
    
    if (linkMatch) {
      message.verificationLink = linkMatch[0];
    }
    
    if (codeMatch) {
      message.verificationCode = codeMatch[1];
      this.verificationCodes.set(message.to, codeMatch[1]);
    }
    
    // Store email in inbox
    const inbox = this.emails.get(message.to) || [];
    inbox.push(message);
    this.emails.set(message.to, inbox);
    
    return message;
  }
  
  /**
   * Get all emails for a specific address
   */
  static getInbox(emailAddress: string): EmailMessage[] {
    return this.emails.get(emailAddress) || [];
  }
  
  /**
   * Get the latest email for a specific address
   */
  static getLatestEmail(emailAddress: string): EmailMessage | null {
    const inbox = this.getInbox(emailAddress);
    return inbox.length > 0 ? inbox[inbox.length - 1] : null;
  }
  
  /**
   * Get verification email for a specific address
   */
  static getVerificationEmail(emailAddress: string): EmailMessage | null {
    const inbox = this.getInbox(emailAddress);
    return inbox.find(email => 
      email.subject.toLowerCase().includes('verify') || 
      email.subject.toLowerCase().includes('confirm')
    ) || null;
  }
  
  /**
   * Get verification code for a specific email
   */
  static getVerificationCode(emailAddress: string): string | null {
    return this.verificationCodes.get(emailAddress) || null;
  }
  
  /**
   * Mock the email verification API endpoint
   */
  static async mockEmailEndpoint(page: Page | BrowserContext): Promise<void> {
    const context = 'newPage' in page ? page : page.context();
    
    // Mock the registration endpoint to capture email sends
    await context.route('**/api/v1/auth/register', async (route, request) => {
      const body = request.postDataJSON();
      
      // Simulate sending verification email
      const verificationCode = Math.random().toString(36).substr(2, 6).toUpperCase();
      const verificationLink = `http://localhost:3000/verify-email?token=${verificationCode}&email=${encodeURIComponent(body.email)}`;
      
      this.sendEmail({
        to: body.email,
        from: 'noreply@betterprompts.ai',
        subject: 'Verify your BetterPrompts account',
        body: `Welcome to BetterPrompts!\n\nPlease verify your email address by clicking the link below:\n${verificationLink}\n\nOr enter this verification code: ${verificationCode}\n\nThis link will expire in 24 hours.`,
        htmlBody: `
          <h2>Welcome to BetterPrompts!</h2>
          <p>Please verify your email address by clicking the button below:</p>
          <a href="${verificationLink}" style="display: inline-block; padding: 10px 20px; background: #4F46E5; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a>
          <p>Or enter this verification code: <strong>${verificationCode}</strong></p>
          <p>This link will expire in 24 hours.</p>
        `
      });
      
      // Return successful registration response
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Registration successful. Please check your email for verification.',
          userId: `user-${Date.now()}`,
          requiresVerification: true
        })
      });
    });
    
    // Mock the email verification endpoint
    await context.route('**/api/v1/auth/verify-email', async (route, request) => {
      const body = request.postDataJSON();
      const storedCode = this.getVerificationCode(body.email);
      
      if (body.code === storedCode || body.token === storedCode) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Email verified successfully',
            token: `jwt-token-${Date.now()}`,
            user: {
              id: `user-${Date.now()}`,
              email: body.email,
              emailVerified: true
            }
          })
        });
      } else {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            error: 'Invalid verification code'
          })
        });
      }
    });
    
    // Mock resend verification email endpoint
    await context.route('**/api/v1/auth/resend-verification', async (route, request) => {
      const body = request.postDataJSON();
      
      // Generate new verification code
      const verificationCode = Math.random().toString(36).substr(2, 6).toUpperCase();
      const verificationLink = `http://localhost:3000/verify-email?token=${verificationCode}&email=${encodeURIComponent(body.email)}`;
      
      this.sendEmail({
        to: body.email,
        from: 'noreply@betterprompts.ai',
        subject: 'Verify your BetterPrompts account (Resent)',
        body: `We've resent your verification email.\n\nPlease verify your email address by clicking the link below:\n${verificationLink}\n\nOr enter this verification code: ${verificationCode}`,
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Verification email resent successfully'
        })
      });
    });
  }
  
  /**
   * Extract verification link from email content
   */
  static extractVerificationLink(emailContent: string): string | null {
    const match = emailContent.match(/https?:\/\/[^\s]+verify[^\s]+/);
    return match ? match[0] : null;
  }
  
  /**
   * Extract verification code from email content
   */
  static extractVerificationCode(emailContent: string): string | null {
    const match = emailContent.match(/verification code[:\s]+([A-Z0-9]{6})/i);
    return match ? match[1] : null;
  }
  
  /**
   * Simulate clicking verification link
   */
  static async clickVerificationLink(page: Page, email: string): Promise<void> {
    const verificationEmail = this.getVerificationEmail(email);
    if (!verificationEmail || !verificationEmail.verificationLink) {
      throw new Error(`No verification link found for ${email}`);
    }
    
    await page.goto(verificationEmail.verificationLink);
  }
  
  /**
   * Wait for email to arrive (with timeout)
   */
  static async waitForEmail(
    email: string, 
    predicate?: (message: EmailMessage) => boolean,
    timeout: number = 10000
  ): Promise<EmailMessage> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const inbox = this.getInbox(email);
      const message = predicate 
        ? inbox.find(predicate)
        : inbox[inbox.length - 1];
        
      if (message) {
        return message;
      }
      
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    throw new Error(`Timeout waiting for email to ${email}`);
  }
}

/**
 * Helper to setup email mocking for a test
 */
export async function setupEmailMocking(page: Page | BrowserContext): Promise<void> {
  MockEmailService.reset();
  await MockEmailService.mockEmailEndpoint(page);
}

/**
 * Helper to get verification code from latest email
 */
export async function getVerificationCodeFromEmail(email: string): Promise<string> {
  const message = MockEmailService.getVerificationEmail(email);
  if (!message || !message.verificationCode) {
    throw new Error(`No verification code found for ${email}`);
  }
  return message.verificationCode;
}

/**
 * Helper to simulate email verification flow
 */
export async function completeEmailVerification(page: Page, email: string): Promise<void> {
  // Wait for the email to arrive
  await MockEmailService.waitForEmail(email, msg => 
    msg.subject.toLowerCase().includes('verify')
  );
  
  // Click the verification link
  await MockEmailService.clickVerificationLink(page, email);
}