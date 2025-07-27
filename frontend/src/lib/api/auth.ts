import { apiClient } from './client'
import { User } from '@/store/useUserStore'

export interface LoginRequest {
  email_or_username: string
  password: string
  remember_me?: boolean
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
}

export interface RefreshTokenRequest {
  refreshToken: string
}

export interface RefreshTokenResponse {
  token: string
  refreshToken: string
}

class AuthService {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials)
    this.setTokens(response.access_token, response.refresh_token)
    return response
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', data)
    this.setTokens(response.access_token, response.refresh_token)
    return response
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      this.clearTokens()
    }
  }

  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const response = await apiClient.post<RefreshTokenResponse>('/auth/refresh', {
      refreshToken,
    })
    this.setTokens(response.token, response.refreshToken)
    return response
  }

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/auth/me')
  }

  async updateProfile(updates: Partial<User>): Promise<User> {
    return apiClient.put<User>('/auth/profile', updates)
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    return apiClient.post('/auth/change-password', {
      currentPassword,
      newPassword,
    })
  }

  async requestPasswordReset(email: string): Promise<void> {
    return apiClient.post('/auth/reset-password', { email })
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    return apiClient.post('/auth/reset-password/confirm', {
      token,
      newPassword,
    })
  }

  // Token management
  private setTokens(token: string, refreshToken: string): void {
    localStorage.setItem('auth_token', token)
    localStorage.setItem('refresh_token', refreshToken)
  }

  private clearTokens(): void {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
  }

  getStoredToken(): string | null {
    return localStorage.getItem('auth_token')
  }

  getStoredRefreshToken(): string | null {
    return localStorage.getItem('refresh_token')
  }
}

export const authService = new AuthService()