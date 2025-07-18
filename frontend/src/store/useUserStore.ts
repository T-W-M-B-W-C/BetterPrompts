import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  subscriptionTier: 'free' | 'pro' | 'enterprise'
  createdAt: string
}

interface UserState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  setUser: (user: User | null) => void
  login: (user: User) => void
  logout: () => void
  updateUser: (updates: Partial<User>) => void
  setLoading: (isLoading: boolean) => void
}

export const useUserStore = create<UserState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        
        setUser: (user) => 
          set({ 
            user, 
            isAuthenticated: !!user 
          }),
          
        login: (user) => 
          set({ 
            user, 
            isAuthenticated: true,
            isLoading: false
          }),
          
        logout: () => 
          set({ 
            user: null, 
            isAuthenticated: false 
          }),
          
        updateUser: (updates) =>
          set((state) => ({
            user: state.user ? { ...state.user, ...updates } : null,
          })),
          
        setLoading: (isLoading) => set({ isLoading }),
      }),
      {
        name: 'user-store',
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    )
  )
)