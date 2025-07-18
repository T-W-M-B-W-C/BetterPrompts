'use client'

import { ReactNode } from 'react'
import { 
  useRouteAnnouncer, 
  useSkipToContent, 
  useReducedMotion, 
  useKeyboardNavigation 
} from '@/hooks/useAccessibility'

interface AccessibilityProviderProps {
  children: ReactNode
}

export default function AccessibilityProvider({ children }: AccessibilityProviderProps) {
  // Initialize all accessibility features
  useRouteAnnouncer()
  useSkipToContent()
  useReducedMotion()
  useKeyboardNavigation()

  return (
    <>
      {/* Skip to content link */}
      <a
        id="skip-to-content"
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded-lg focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        Skip to main content
      </a>
      {children}
    </>
  )
}