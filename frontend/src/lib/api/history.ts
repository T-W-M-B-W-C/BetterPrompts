import { apiClient } from './client'

// Types aligned with backend PromptHistory model
export interface PromptHistoryItem {
  id: string
  user_id?: string
  session_id?: string
  original_input: string
  enhanced_output: string
  intent?: string
  complexity?: string
  techniques_used: string[]
  confidence?: number
  metadata?: Record<string, any>
  created_at: string
}

export interface PromptHistoryResponse {
  items: PromptHistoryItem[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

export interface HistoryFilters {
  page?: number
  limit?: number
  start_date?: string
  end_date?: string
  intent?: string
  technique?: string
  search?: string
}

class HistoryService {
  /**
   * Get user's prompt history with pagination and filters
   */
  async getHistory(filters?: HistoryFilters): Promise<PromptHistoryResponse> {
    const params = {
      page: filters?.page || 1,
      limit: filters?.limit || 20,
      ...filters
    }
    
    // Backend returns paginated response with data and pagination fields
    const response = await apiClient.get<{
      data: PromptHistoryItem[]
      pagination: {
        page: number
        limit: number
        total_records: number
        total_pages: number
        has_next: boolean
        has_previous: boolean
      }
    }>('/prompts/history', { params })
    
    return {
      items: response.data,
      total: response.pagination.total_records,
      page: response.pagination.page,
      limit: response.pagination.limit,
      has_more: response.pagination.has_next
    }
  }

  /**
   * Get a specific history item by ID
   */
  async getHistoryItem(id: string): Promise<PromptHistoryItem> {
    return apiClient.get<PromptHistoryItem>(`/prompts/${id}`)
  }

  /**
   * Delete a history item
   */
  async deleteHistoryItem(id: string): Promise<void> {
    return apiClient.delete(`/prompts/${id}`)
  }

  /**
   * Rerun a prompt with the same techniques
   */
  async rerunPrompt(id: string): Promise<{
    id: string
    enhanced: boolean
    enhanced_text: string
    techniques: string[]
    intent: string
    confidence: number
    metadata: Record<string, any>
  }> {
    return apiClient.post(`/prompts/${id}/rerun`)
  }

  /**
   * Export history data (future feature)
   */
  async exportHistory(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await apiClient.get('/history/export', {
      params: { format },
      responseType: 'blob'
    })
    return response as Blob
  }

  /**
   * Get usage statistics
   */
  async getUsageStats(): Promise<{
    total_prompts: number
    techniques_breakdown: Record<string, number>
    intents_breakdown: Record<string, number>
    daily_usage: Array<{ date: string; count: number }>
  }> {
    return apiClient.get('/history/stats')
  }
}

export const historyService = new HistoryService()