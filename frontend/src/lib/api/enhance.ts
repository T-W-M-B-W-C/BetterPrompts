import { apiClient } from './client'

export interface EnhanceRequest {
  input: string
  technique?: string
  options?: {
    variations?: number
    explanation?: boolean
  }
}

export interface EnhanceResponse {
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
  async enhance(request: EnhanceRequest): Promise<EnhanceResponse> {
    return apiClient.post<EnhanceResponse>('/enhance', request)
  }

  async analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    return apiClient.post<AnalyzeResponse>('/analyze', request)
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
      promptId,
      ...feedback,
    })
  }
}

export const enhanceService = new EnhanceService()