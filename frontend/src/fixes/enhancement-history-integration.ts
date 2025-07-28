/**
 * Enhancement-to-History Integration Fix
 * 
 * This module provides fixes for ensuring that enhancements are properly
 * saved to history for authenticated users.
 * 
 * Issues addressed:
 * 1. Backend response includes prompt ID but frontend doesn't use it
 * 2. Frontend expects history_id but backend returns id
 * 3. Need to verify user is authenticated before expecting history save
 */

import { FrontendEnhanceResponse, EnhanceResponse } from '@/lib/api/enhance'

/**
 * Enhanced response type that includes history information
 */
export interface EnhancedFrontendResponse extends FrontendEnhanceResponse {
  history_id?: string
  techniques_used?: string[]
}

/**
 * Transform backend response to include history information
 */
export function transformEnhanceResponseWithHistory(
  backend: EnhanceResponse,
  request: { input: string; technique?: string }
): EnhancedFrontendResponse {
  return {
    enhanced: {
      id: backend.id, // This is the history ID!
      prompt: backend.enhanced_text,
      technique: backend.techniques_used[0] || request.technique || 'auto',
      metadata: {
        intent: backend.intent,
        complexity: backend.complexity,
        confidence: backend.confidence,
        processing_time_ms: backend.processing_time_ms,
        all_techniques: backend.techniques_used
      }
    },
    // Include the ID as history_id for the component
    history_id: backend.id,
    techniques_used: backend.techniques_used,
    alternatives: undefined,
    explanation: backend.metadata?.explanation as string | undefined
  }
}

/**
 * Verify if a user is authenticated by checking for auth token
 */
export function isUserAuthenticated(): boolean {
  // Check for auth token in localStorage or cookies
  if (typeof window === 'undefined') return false
  
  // Check localStorage
  const token = localStorage.getItem('auth_token')
  if (token) return true
  
  // Check cookies
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split('=')
    if (key === 'auth_token' && value) return true
  }
  
  return false
}

/**
 * Enhanced enhance method that properly handles history
 */
export async function enhanceWithHistory(
  enhanceFunction: (request: any) => Promise<EnhanceResponse>,
  request: { input: string; technique?: string }
): Promise<EnhancedFrontendResponse> {
  // Call the original enhance function
  const response = await enhanceFunction({
    text: request.input,
    prefer_techniques: request.technique ? [request.technique] : undefined
  })
  
  // Transform with history information
  const enhancedResponse = transformEnhanceResponseWithHistory(response, request)
  
  // Log for debugging
  if (isUserAuthenticated()) {
    console.log('Enhancement saved to history with ID:', enhancedResponse.history_id)
  } else {
    console.log('User not authenticated, enhancement not saved to history')
  }
  
  return enhancedResponse
}