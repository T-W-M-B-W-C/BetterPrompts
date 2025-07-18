import { useState } from 'react'
import { enhanceService, EnhanceRequest, EnhanceResponse } from '@/lib/api/enhance'
import { useEnhanceStore } from '@/store/useEnhanceStore'
import { ApiError } from '@/lib/api/client'

export function useEnhance() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const {
    setCurrentOutput,
    setIsEnhancing,
    addToHistory,
    preferences,
  } = useEnhanceStore()

  const enhance = async (request: EnhanceRequest): Promise<EnhanceResponse | null> => {
    setIsLoading(true)
    setIsEnhancing(true)
    setError(null)

    try {
      const response = await enhanceService.enhance(request)
      
      // Update store
      setCurrentOutput(response.enhanced.prompt)
      
      // Add to history if enabled
      if (preferences.saveHistory) {
        addToHistory({
          originalInput: request.input,
          enhancedOutput: response.enhanced.prompt,
          techniqueUsed: response.enhanced.technique,
        })
      }
      
      return response
    } catch (err) {
      const apiError = err as ApiError
      setError(apiError.message || 'Failed to enhance prompt')
      return null
    } finally {
      setIsLoading(false)
      setIsEnhancing(false)
    }
  }

  return {
    enhance,
    isLoading,
    error,
  }
}

export function useAnalyze() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const analyze = async (input: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await enhanceService.analyze({ input })
      return response
    } catch (err) {
      const apiError = err as ApiError
      setError(apiError.message || 'Failed to analyze input')
      return null
    } finally {
      setIsLoading(false)
    }
  }

  return {
    analyze,
    isLoading,
    error,
  }
}

export function useTechniques() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { setAvailableTechniques } = useEnhanceStore()

  const fetchTechniques = async (params?: { category?: string; intent?: string }) => {
    setIsLoading(true)
    setError(null)

    try {
      const techniques = await enhanceService.getTechniques(params)
      setAvailableTechniques(techniques)
      return techniques
    } catch (err) {
      const apiError = err as ApiError
      setError(apiError.message || 'Failed to fetch techniques')
      return []
    } finally {
      setIsLoading(false)
    }
  }

  return {
    fetchTechniques,
    isLoading,
    error,
  }
}