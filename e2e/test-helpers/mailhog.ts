import axios from 'axios';

/**
 * MailHog email testing utilities
 * Provides helpers to retrieve and parse emails from MailHog during E2E tests
 */

const MAILHOG_API_URL = process.env.MAILHOG_API_URL || 'http://localhost:8025/api/v1';

export interface MailHogMessage {
  ID: string;
  From: {
    Mailbox: string;
    Domain: string;
  };
  To: Array<{
    Mailbox: string;
    Domain: string;
  }>;
  Content: {
    Headers: Record<string, string[]>;
    Body: string;
  };
  Created: string;
  Raw: {
    From: string;
    To: string[];
    Data: string;
  };
}

export interface MailHogSearchResult {
  total: number;
  count: number;
  start: number;
  items: MailHogMessage[];
}

/**
 * Get all emails from MailHog
 */
export async function getAllEmails(): Promise<MailHogMessage[]> {
  try {
    const response = await axios.get<MailHogMessage[]>(`${MAILHOG_API_URL}/messages`);
    return response.data || [];
  } catch (error) {
    console.error('Failed to fetch emails from MailHog:', error);
    return [];
  }
}

/**
 * Get emails for a specific recipient
 */
export async function getEmailsForRecipient(email: string): Promise<MailHogMessage[]> {
  const allEmails = await getAllEmails();
  
  return allEmails.filter(message => 
    message.To.some(recipient => 
      `${recipient.Mailbox}@${recipient.Domain}`.toLowerCase() === email.toLowerCase()
    )
  );
}

/**
 * Get the latest email for a specific recipient
 */
export async function getLatestEmail(email: string): Promise<MailHogMessage | null> {
  const emails = await getEmailsForRecipient(email);
  
  if (emails.length === 0) {
    return null;
  }
  
  // Sort by creation date and return the latest
  return emails.sort((a, b) => 
    new Date(b.Created).getTime() - new Date(a.Created).getTime()
  )[0];
}

/**
 * Extract verification code from email body
 */
export function extractVerificationCode(emailBody: string): string | null {
  // Look for common verification code patterns
  const patterns = [
    /verification code[:\s]+([A-Z0-9]{6})/i,
    /code[:\s]+([A-Z0-9]{6})/i,
    /\b([A-Z0-9]{6})\b/  // Any 6-character alphanumeric code
  ];
  
  for (const pattern of patterns) {
    const match = emailBody.match(pattern);
    if (match) {
      return match[1];
    }
  }
  
  return null;
}

/**
 * Extract verification link from email body
 */
export function extractVerificationLink(emailBody: string): string | null {
  // Look for verification links
  const patterns = [
    /https?:\/\/[^\s]+verify[^\s]+/i,
    /https?:\/\/[^\s]+confirmation[^\s]+/i,
    /https?:\/\/[^\s]+activate[^\s]+/i
  ];
  
  for (const pattern of patterns) {
    const match = emailBody.match(pattern);
    if (match) {
      return match[0];
    }
  }
  
  return null;
}

/**
 * Wait for an email to arrive with retry logic
 */
export async function waitForEmail(
  recipientEmail: string,
  options: {
    timeout?: number;
    interval?: number;
    subject?: string;
  } = {}
): Promise<MailHogMessage> {
  const { 
    timeout = 30000,  // 30 seconds default
    interval = 1000,  // Check every second
    subject 
  } = options;
  
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const emails = await getEmailsForRecipient(recipientEmail);
    
    // Filter by subject if provided
    const matchingEmails = subject 
      ? emails.filter(email => 
          email.Content.Headers['Subject']?.[0]?.toLowerCase().includes(subject.toLowerCase())
        )
      : emails;
    
    if (matchingEmails.length > 0) {
      // Return the latest matching email
      return matchingEmails.sort((a, b) => 
        new Date(b.Created).getTime() - new Date(a.Created).getTime()
      )[0];
    }
    
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  throw new Error(`No email found for ${recipientEmail} within ${timeout}ms`);
}

/**
 * Get verification code from the latest email
 */
export async function getVerificationCodeFromEmail(email: string): Promise<string> {
  const message = await waitForEmail(email, { 
    subject: 'verify',
    timeout: 10000 
  });
  
  const code = extractVerificationCode(message.Content.Body);
  
  if (!code) {
    throw new Error(`No verification code found in email for ${email}`);
  }
  
  return code;
}

/**
 * Get verification link from the latest email
 */
export async function getVerificationLinkFromEmail(email: string): Promise<string> {
  const message = await waitForEmail(email, { 
    subject: 'verify',
    timeout: 10000 
  });
  
  const link = extractVerificationLink(message.Content.Body);
  
  if (!link) {
    throw new Error(`No verification link found in email for ${email}`);
  }
  
  return link;
}

/**
 * Clear all emails in MailHog
 */
export async function clearAllEmails(): Promise<void> {
  try {
    await axios.delete(`${MAILHOG_API_URL}/messages`);
    console.log('Cleared all emails from MailHog');
  } catch (error) {
    console.error('Failed to clear emails from MailHog:', error);
  }
}

/**
 * Delete a specific email
 */
export async function deleteEmail(messageId: string): Promise<void> {
  try {
    await axios.delete(`${MAILHOG_API_URL}/messages/${messageId}`);
  } catch (error) {
    console.error(`Failed to delete email ${messageId}:`, error);
  }
}

/**
 * Get email content as plain text
 */
export function getPlainTextContent(message: MailHogMessage): string {
  // MailHog stores the raw email content
  // We need to decode it and extract the plain text part
  const body = message.Content.Body;
  
  // Simple extraction - in production you might use a proper email parser
  if (body.includes('Content-Type: text/plain')) {
    const plainTextMatch = body.match(/Content-Type: text\/plain[\s\S]*?\n\n([\s\S]*?)(?=--|\z)/);
    return plainTextMatch ? plainTextMatch[1].trim() : body;
  }
  
  return body;
}

/**
 * Get email content as HTML
 */
export function getHtmlContent(message: MailHogMessage): string | null {
  const body = message.Content.Body;
  
  if (body.includes('Content-Type: text/html')) {
    const htmlMatch = body.match(/Content-Type: text\/html[\s\S]*?\n\n([\s\S]*?)(?=--|\z)/);
    return htmlMatch ? htmlMatch[1].trim() : null;
  }
  
  return null;
}