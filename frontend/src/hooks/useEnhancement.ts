import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api, EnhanceRequest, EnhanceResponse, AnalyzeRequest, AnalyzeResponse, Technique } from '@/lib/api/services'
import { useToast } from '@/components/ui/use-toast'

export function useEnhancement() {
  const { toast } = useToast()
  const [selectedTechniques, setSelectedTechniques] = useState<string[]>([])

  // Analyze prompt mutation
  const analyzeMutation = useMutation<AnalyzeResponse, Error, AnalyzeRequest>({
    mutationFn: api.prompts.analyze,
    onSuccess: (data) => {
      // Auto-select suggested techniques
      if (data.suggested_techniques?.length > 0) {
        setSelectedTechniques(data.suggested_techniques)
      }
    },
    onError: (error) => {
      toast({
        title: 'Analysis failed',
        description: error.message || 'Failed to analyze prompt',
        variant: 'destructive',
      })
    },
  })

  // Enhance prompt mutation
  const enhanceMutation = useMutation<EnhanceResponse, Error, EnhanceRequest>({
    mutationFn: api.prompts.enhance,
    onError: (error) => {
      toast({
        title: 'Enhancement failed',
        description: error.message || 'Failed to enhance prompt',
        variant: 'destructive',
      })
    },
  })

  // Get available techniques
  const techniquesQuery = useQuery<Technique[], Error>({
    queryKey: ['techniques'],
    queryFn: api.prompts.getTechniques,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  })

  // Combined function to analyze and enhance
  const analyzeAndEnhance = async (text: string, options?: {
    intent?: string
    complexity?: 'simple' | 'moderate' | 'complex'
    target_model?: string
    techniques?: string[]
    autoEnhance?: boolean
  }) => {
    try {
      // First analyze the prompt
      const analyzeResult = await analyzeMutation.mutateAsync({
        text,
        context: options,
      })

      // If autoEnhance is true, automatically enhance with suggested techniques
      if (options?.autoEnhance !== false) {
        const enhanceResult = await enhanceMutation.mutateAsync({
          text,
          intent: options?.intent || analyzeResult.intent,
          complexity: options?.complexity || analyzeResult.complexity as any,
          target_model: options?.target_model || 'gpt-4',
          techniques: options?.techniques || analyzeResult.suggested_techniques,
          context: {
            ...options,
            analysis_metadata: analyzeResult.metadata,
          },
        })

        return {
          analysis: analyzeResult,
          enhancement: enhanceResult,
        }
      }

      return {
        analysis: analyzeResult,
        enhancement: null,
      }
    } catch (error) {
      // Error is already handled by the mutations
      throw error
    }
  }

  // Function to enhance with custom techniques
  const enhanceWithTechniques = async (text: string, techniques: string[], options?: {
    intent?: string
    complexity?: 'simple' | 'moderate' | 'complex'
    target_model?: string
  }) => {
    return enhanceMutation.mutateAsync({
      text,
      techniques,
      intent: options?.intent,
      complexity: options?.complexity,
      target_model: options?.target_model || 'gpt-4',
    })
  }

  // Function to toggle technique selection
  const toggleTechnique = (techniqueId: string) => {
    setSelectedTechniques(prev => 
      prev.includes(techniqueId)
        ? prev.filter(id => id !== techniqueId)
        : [...prev, techniqueId]
    )
  }

  // Function to clear all selections
  const clearTechniques = () => {
    setSelectedTechniques([])
  }

  return {
    // State
    selectedTechniques,
    setSelectedTechniques,
    
    // Queries
    techniques: techniquesQuery.data || [],
    techniquesLoading: techniquesQuery.isLoading,
    techniquesError: techniquesQuery.error,
    
    // Mutations
    analyzeMutation,
    enhanceMutation,
    
    // Combined functions
    analyzeAndEnhance,
    enhanceWithTechniques,
    
    // UI helpers
    toggleTechnique,
    clearTechniques,
    
    // Loading states
    isAnalyzing: analyzeMutation.isPending,
    isEnhancing: enhanceMutation.isPending,
    isProcessing: analyzeMutation.isPending || enhanceMutation.isPending,
  }
}