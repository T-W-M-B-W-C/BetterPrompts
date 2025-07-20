'use client'

import * as React from 'react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import { type ThemeProviderProps } from 'next-themes/dist/types'
import { useEnhanceStore } from '@/store/useEnhanceStore'

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  const { preferences } = useEnhanceStore()
  
  React.useEffect(() => {
    // Apply theme from user preferences
    if (preferences.theme && typeof window !== 'undefined') {
      const root = window.document.documentElement
      root.classList.remove('light', 'dark')
      
      if (preferences.theme === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        root.classList.add(systemTheme)
      } else {
        root.classList.add(preferences.theme)
      }
    }
  }, [preferences.theme])
  
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme={preferences.theme || 'system'}
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemesProvider>
  )
}