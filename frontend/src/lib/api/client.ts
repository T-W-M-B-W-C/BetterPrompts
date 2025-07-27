import redaxios from 'redaxios'
import type { AxiosError, AxiosInstance, AxiosRequestConfig } from 'redaxios'
import { useUserStore } from '@/store/useUserStore'

// Determine API URL based on environment
// In development, you can use direct API Gateway port or nginx proxy
const getApiUrl = () => {
  // Check for explicit environment variable first
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  
  // Use nginx proxy by default (recommended for CORS and consistency)
  // This routes through nginx which proxies to API Gateway on port 8090
  return 'http://localhost/api/v1'
  
  // Alternative: Direct API Gateway connection (may have CORS issues)
  // return 'http://localhost:8000/api/v1'
}

const API_BASE_URL = getApiUrl()

// Validate API URL configuration
if (!API_BASE_URL) {
  console.error('API_BASE_URL is not configured. Please set NEXT_PUBLIC_API_URL environment variable.')
}

console.log('API Client initialized with base URL:', API_BASE_URL)

class ApiClient {
  private client: typeof redaxios
  private baseConfig: AxiosRequestConfig

  constructor() {
    this.baseConfig = {
      baseURL: API_BASE_URL,
      timeout: 30000,
      withCredentials: true, // Enable CORS credentials
      headers: {
        'Content-Type': 'application/json',
      },
    }

    // Create a wrapper around redaxios to add interceptor-like functionality
    this.client = this.createClient()
  }

  private createClient() {
    // Create a custom wrapper that adds auth headers and handles errors
    const wrappedClient = (config: AxiosRequestConfig) => {
      // Add auth token to headers
      const token = this.getAuthToken()
      const finalConfig = {
        ...this.baseConfig,
        ...config,
        headers: {
          ...this.baseConfig.headers,
          ...config.headers,
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      }

      // Make the request
      return redaxios(finalConfig).catch(async (error: AxiosError) => {
        // Handle 401 errors
        if (error.response?.status === 401) {
          useUserStore.getState().logout()
          window.location.href = '/login'
        }
        throw this.formatError(error)
      })
    }

    // Add convenience methods
    wrappedClient.get = (url: string, config?: AxiosRequestConfig) => 
      wrappedClient({ ...config, method: 'GET', url })
    wrappedClient.post = (url: string, data?: any, config?: AxiosRequestConfig) => 
      wrappedClient({ ...config, method: 'POST', url, data })
    wrappedClient.put = (url: string, data?: any, config?: AxiosRequestConfig) => 
      wrappedClient({ ...config, method: 'PUT', url, data })
    wrappedClient.delete = (url: string, config?: AxiosRequestConfig) => 
      wrappedClient({ ...config, method: 'DELETE', url })

    return wrappedClient as any
  }

  private getAuthToken(): string | null {
    // Try to get token from Zustand store first
    const storeToken = useUserStore.getState().accessToken
    if (storeToken) return storeToken
    
    // Fallback to localStorage
    return localStorage.getItem('access_token')
  }

  private formatError(error: AxiosError): ApiError {
    if (error.response) {
      // Server responded with error
      const data = error.response.data as any
      let message = data?.message || data?.error || 'An error occurred'
      
      // Add more context based on status code
      if (error.response.status === 429) {
        message = 'Too many requests. Please try again later.'
      } else if (error.response.status === 503) {
        message = 'Service temporarily unavailable. Please try again in a few moments.'
      } else if (error.response.status >= 500) {
        message = 'Server error. Our team has been notified.'
      }
      
      return {
        message,
        status: error.response.status,
        data: error.response.data,
      }
    } else if (error.request) {
      // Request made but no response
      return {
        message: 'Unable to connect to the server. Please check your internet connection.',
        status: 0,
      }
    } else {
      // Request setup error
      return {
        message: error.message || 'An unexpected error occurred',
        status: 0,
      }
    }
  }

  // Generic request methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config)
    return response.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config)
    return response.data
  }
}

export interface ApiError {
  message: string
  status: number
  data?: any
}

export const apiClient = new ApiClient()