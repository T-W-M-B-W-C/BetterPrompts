import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import { useUserStore } from '@/store/useUserStore'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
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
      return {
        message: (error.response.data as any)?.message || error.message,
        status: error.response.status,
        data: error.response.data,
      }
    } else if (error.request) {
      return {
        message: 'Network error - please check your connection',
        status: 0,
      }
    } else {
      return {
        message: error.message,
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