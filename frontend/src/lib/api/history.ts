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
    
    // The backend returns an array, we need to wrap it
    const items = await apiClient.get<PromptHistoryItem[]>('/history', { params })
    
    // Calculate pagination metadata
    const total = items.length // This will be updated when backend provides total count
    const hasMore = items.length === params.limit
    
    return {
      items,
      total,
      page: params.page,
      limit: params.limit,
      has_more: hasMore
    }
  }

  /**
   * Get a specific history item by ID
   */
  async getHistoryItem(id: string): Promise<PromptHistoryItem> {
    return apiClient.get<PromptHistoryItem>(`/history/${id}`)
  }

  /**
   * Delete a history item
   */
  async deleteHistoryItem(id: string): Promise<void> {
    return apiClient.delete(`/history/${id}`)
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