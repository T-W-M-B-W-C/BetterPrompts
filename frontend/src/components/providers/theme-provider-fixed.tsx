'use client'

import * as React from 'react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import { type ThemeProviderProps } from 'next-themes/dist/types'
import { useEnhanceStore } from '@/store/useEnhanceStore'

/**
 * Fixed ThemeProvider that handles hydration correctly
 * 
 * Changes made:
 * 1. Removed manual DOM manipulation that was causing hydration mismatch
 * 2. Let next-themes handle all theme switching internally
 * 3. Sync with store preferences after mount to avoid SSR issues
 */
export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  const { preferences } = useEnhanceStore()
  const [mounted, setMounted] = React.useState(false)
  
  // Track when component is mounted to avoid hydration issues
  React.useEffect(() => {
    setMounted(true)
  }, [])
  
  // Use a stable default theme for SSR
  const defaultTheme = mounted && preferences.theme ? preferences.theme : 'light'
  
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme={defaultTheme}
      enableSystem
      disableTransitionOnChange
      storageKey="betterprompts-theme"
      // Disable color-scheme to prevent style attribute hydration mismatch
      enableColorScheme={false}
      {...props}
    >
      {children}
    </NextThemesProvider>
  )
}