import { APIRequestContext, Page } from '@playwright/test';

/**
 * Helper class for making API requests in tests
 * Handles proper routing through nginx proxy
 */
export class ApiHelper {
  private readonly apiBaseUrl: string;
  
  constructor(private page: Page) {
    // Use the nginx proxy URL for API calls
    this.apiBaseUrl = 'http://localhost/api/v1';
  }
  
  /**
   * Get headers with auth token if available
   */
  async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await this.page.evaluate(() => localStorage.getItem('access_token'));
    
    return token ? {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    } : {
      'Content-Type': 'application/json'
    };
  }
  
  /**
   * Make an authenticated GET request
   */
  async get(endpoint: string) {
    const headers = await this.getAuthHeaders();
    return this.page.request.get(`${this.apiBaseUrl}${endpoint}`, { headers });
  }
  
  /**
   * Make an authenticated POST request
   */
  async post(endpoint: string, data?: any) {
    const headers = await this.getAuthHeaders();
    return this.page.request.post(`${this.apiBaseUrl}${endpoint}`, { 
      headers,
      data 
    });
  }
  
  /**
   * Make an authenticated PUT request
   */
  async put(endpoint: string, data?: any) {
    const headers = await this.getAuthHeaders();
    return this.page.request.put(`${this.apiBaseUrl}${endpoint}`, { 
      headers,
      data 
    });
  }
  
  /**
   * Make an authenticated DELETE request
   */
  async delete(endpoint: string) {
    const headers = await this.getAuthHeaders();
    return this.page.request.delete(`${this.apiBaseUrl}${endpoint}`, { headers });
  }
  
  /**
   * Test if API is accessible
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.page.request.get(`${this.apiBaseUrl}/health`);
      return response.ok();
    } catch (error) {
      console.error('API connection test failed:', error);
      return false;
    }
  }
  
  /**
   * Login via API and store tokens
   */
  async login(email: string, password: string): Promise<boolean> {
    try {
      const response = await this.page.request.post(`${this.apiBaseUrl}/auth/login`, {
        data: { email_or_username: email, password }
      });
      
      if (response.ok()) {
        const data = await response.json();
        
        // Navigate to home page first to avoid security error
        await this.page.goto('/');
        
        // Store tokens in localStorage
        await this.page.evaluate(({ accessToken, refreshToken, user }) => {
          localStorage.setItem('access_token', accessToken);
          localStorage.setItem('refresh_token', refreshToken);
          localStorage.setItem('user', JSON.stringify(user));
        }, {
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user
        });
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('API login failed:', error);
      return false;
    }
  }
  
  /**
   * Enhance a prompt via API
   */
  async enhance(prompt: string) {
    return this.post('/enhance', { text: prompt });
  }
  
  /**
   * Get enhancement history
   */
  async getHistory(params?: { page?: number; limit?: number; search?: string }) {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    
    const url = `/history${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.get(url);
  }
  
  /**
   * Get enhancement details
   */
  async getEnhancementDetails(id: string) {
    return this.get(`/history/${id}`);
  }
}