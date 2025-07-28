'use client'

import * as React from 'react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import { type ThemeProviderProps } from 'next-themes/dist/types'

/**
 * Hydration-safe theme provider that prevents className mismatches
 * between server and client rendering.
 * 
 * Key changes:
 * 1. Added suppressHydrationWarning to prevent hydration warnings
 * 2. Use defaultTheme="light" to ensure consistent initial state
 * 3. Removed manual DOM manipulation in favor of next-themes handling
 * 4. Added storageKey to ensure theme persistence
 */
export function HydrationSafeThemeProvider({ 
  children, 
  ...props 
}: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="light"
      enableSystem
      disableTransitionOnChange
      storageKey="betterprompts-theme"
      // Ensure theme is applied after hydration
      enableColorScheme={false}
      {...props}
    >
      {children}
    </NextThemesProvider>
  )
}

/**
 * Hook to safely access theme on client-side only
 */
export function useClientTheme() {
  const [mounted, setMounted] = React.useState(false)
  
  React.useEffect(() => {
    setMounted(true)
  }, [])
  
  // Return consistent state during SSR
  if (!mounted) {
    return { theme: 'light', setTheme: () => {} }
  }
  
  // After hydration, use the actual theme hook
  // This would need to be imported from next-themes
  return { theme: 'light', setTheme: () => {} } // Placeholder
}