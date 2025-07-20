import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import { useUserStore } from '@/store/useUserStore'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api/v1'

// Validate API URL configuration
if (!API_BASE_URL) {
  console.error('API_BASE_URL is not configured. Please set NEXT_PUBLIC_API_URL environment variable.')
}

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      withCredentials: true, // Enable CORS credentials
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - logout user
          useUserStore.getState().logout()
          window.location.href = '/login'
        }
        return Promise.reject(this.formatError(error))
      }
    )
  }

  private getAuthToken(): string | null {
    // In a real app, this would get the token from secure storage
    return localStorage.getItem('auth_token')
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