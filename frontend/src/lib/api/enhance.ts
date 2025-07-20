import { apiClient } from './client'

// Backend-aligned interfaces
export interface EnhanceRequest {
  text: string
  context?: Record<string, any>
  prefer_techniques?: string[]
  exclude_techniques?: string[]
  target_complexity?: string
}

export interface EnhanceResponse {
  id: string
  original_text: string
  enhanced_text: string
  intent: string
  complexity: string
  techniques_used: string[]
  confidence: number
  processing_time_ms: number
  metadata?: Record<string, any>
}

// Frontend-friendly adapter interfaces
export interface FrontendEnhanceRequest {
  input: string
  technique?: string
  options?: {
    variations?: number
    explanation?: boolean
  }
}

export interface FrontendEnhanceResponse {
  enhanced: {
    id: string
    prompt: string
    technique: string
    metadata?: Record<string, any>
  }
  alternatives?: Array<{
    id: string
    prompt: string
    technique: string
  }>
  explanation?: string
}

export interface AnalyzeRequest {
  input: string
}

export interface AnalyzeResponse {
  intent: {
    primaryIntent: string
    confidence: number
    subIntents: string[]
    complexity: 'simple' | 'moderate' | 'complex'
    domain: string
    taskType: string
    estimatedTokens: number
    language: string
  }
  suggestedTechniques: Array<{
    id: string
    name: string
    description: string
    confidence: number
    reasoning: string
  }>
}

export interface Technique {
  id: string
  name: string
  category: string
  description: string
  complexity: number
  examples: string[]
  parameters?: Record<string, any>
  effectiveness: {
    overall: number
    byIntent: Record<string, number>
  }
}

class EnhanceService {
  // Main enhance method with adapter
  async enhance(request: FrontendEnhanceRequest): Promise<FrontendEnhanceResponse> {
    // Transform frontend request to backend format
    const backendRequest: EnhanceRequest = {
      text: request.input,
      prefer_techniques: request.technique ? [request.technique] : undefined,
      context: request.options ? { options: request.options } : undefined
    }

    // Call backend API
    const backendResponse = await apiClient.post<EnhanceResponse>('/enhance', backendRequest)

    // Transform backend response to frontend format
    return this.transformToFrontendResponse(backendResponse, request)
  }

  // Direct backend-aligned enhance method
  async enhanceRaw(request: EnhanceRequest): Promise<EnhanceResponse> {
    return apiClient.post<EnhanceResponse>('/enhance', request)
  }

  async analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    // Backend expects 'text' not 'input'
    const backendRequest = { text: request.input }
    const response = await apiClient.post<any>('/analyze', backendRequest)
    
    // Transform backend response to match frontend expectations
    return {
      intent: {
        primaryIntent: response.intent,
        confidence: response.confidence,
        subIntents: response.sub_intents || [],
        complexity: response.complexity,
        domain: response.domain || 'general',
        taskType: response.task_type || 'unknown',
        estimatedTokens: response.estimated_tokens || 0,
        language: response.language || 'en'
      },
      suggestedTechniques: response.suggested_techniques || []
    }
  }

  async getTechniques(params?: {
    category?: string
    intent?: string
  }): Promise<Technique[]> {
    return apiClient.get<Technique[]>('/techniques', { params })
  }

  async getTechnique(id: string): Promise<Technique> {
    return apiClient.get<Technique>(`/techniques/${id}`)
  }

  async provideFeedback(promptId: string, feedback: {
    rating: number
    comment?: string
  }): Promise<void> {
    return apiClient.post(`/feedback`, {
      prompt_id: promptId,
      rating: feedback.rating,
      comment: feedback.comment
    })
  }

  // Helper method to transform backend response to frontend format
  private transformToFrontendResponse(
    backend: EnhanceResponse, 
    request: FrontendEnhanceRequest
  ): FrontendEnhanceResponse {
    return {
      enhanced: {
        id: backend.id,
        prompt: backend.enhanced_text,
        technique: backend.techniques_used[0] || request.technique || 'auto',
        metadata: {
          ...backend.metadata,
          intent: backend.intent,
          complexity: backend.complexity,
          confidence: backend.confidence,
          processing_time_ms: backend.processing_time_ms,
          all_techniques: backend.techniques_used
        }
      },
      // TODO: Implement alternatives when backend supports variations
      alternatives: undefined,
      // TODO: Extract explanation from metadata when available
      explanation: backend.metadata?.explanation as string | undefined
    }
  }
}

export const enhanceService = new EnhanceService()