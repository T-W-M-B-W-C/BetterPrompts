import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { StreamingStep, calculateEstimatedTime } from '@/components/enhance/StreamingProgress'

// Helper function to calculate remaining time
function calculateRemainingTime(currentStep: StreamingStep): number {
  return calculateEstimatedTime(currentStep)
}

export interface Technique {
  id: string
  name: string
  description: string
  category: string
  complexity: number
  effectiveness: number
}

export interface EnhancedPrompt {
  id: string
  originalInput: string
  enhancedOutput: string
  techniqueUsed: string
  timestamp: number
  rating?: number
}

export interface UserPreferences {
  preferredTechniques: string[]
  autoSuggest: boolean
  saveHistory: boolean
  theme: 'light' | 'dark' | 'system'
}

interface StreamingState {
  currentStep: StreamingStep | null
  stepProgress: number
  completedSteps: StreamingStep[]
  error: string | null
  estimatedTimeRemaining: number
  streamingData: {
    intent?: string
    techniques?: string[]
    partialOutput?: string
  }
}

interface EnhanceState {
  // Current enhancement session
  currentInput: string
  currentOutput: string
  selectedTechnique: string | null
  isEnhancing: boolean
  
  // Streaming progress state
  streaming: StreamingState
  
  // History
  history: EnhancedPrompt[]
  
  // Techniques
  availableTechniques: Technique[]
  
  // User preferences
  preferences: UserPreferences
  
  // Actions
  setCurrentInput: (input: string) => void
  setCurrentOutput: (output: string) => void
  setSelectedTechnique: (techniqueId: string | null) => void
  setIsEnhancing: (isEnhancing: boolean) => void
  
  // Streaming actions
  updateStreamingStep: (step: StreamingStep | null, progress?: number) => void
  completeStreamingStep: (step: StreamingStep) => void
  setStreamingError: (error: string | null) => void
  updateStreamingData: (data: Partial<StreamingState['streamingData']>) => void
  resetStreaming: () => void
  
  // History actions
  addToHistory: (prompt: Omit<EnhancedPrompt, 'id' | 'timestamp'>) => void
  clearHistory: () => void
  removeFromHistory: (id: string) => void
  ratePrompt: (id: string, rating: number) => void
  
  // Preference actions
  updatePreferences: (preferences: Partial<UserPreferences>) => void
  togglePreferredTechnique: (techniqueId: string) => void
  
  // Technique actions
  setAvailableTechniques: (techniques: Technique[]) => void
}

const defaultPreferences: UserPreferences = {
  preferredTechniques: [],
  autoSuggest: true,
  saveHistory: true,
  theme: 'system',
}

const defaultStreamingState: StreamingState = {
  currentStep: null,
  stepProgress: 0,
  completedSteps: [],
  error: null,
  estimatedTimeRemaining: 0,
  streamingData: {}
}

export const useEnhanceStore = create<EnhanceState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        currentInput: '',
        currentOutput: '',
        selectedTechnique: null,
        isEnhancing: false,
        streaming: defaultStreamingState,
        history: [],
        availableTechniques: [],
        preferences: defaultPreferences,
        
        // Actions
        setCurrentInput: (input) => set({ currentInput: input }),
        setCurrentOutput: (output) => set({ currentOutput: output }),
        setSelectedTechnique: (techniqueId) => set({ selectedTechnique: techniqueId }),
        setIsEnhancing: (isEnhancing) => set({ isEnhancing }),
        
        // Streaming actions
        updateStreamingStep: (step, progress = 0) =>
          set((state) => ({
            streaming: {
              ...state.streaming,
              currentStep: step,
              stepProgress: progress,
              error: null,
              estimatedTimeRemaining: step ? calculateRemainingTime(step) : 0
            }
          })),
          
        completeStreamingStep: (step) =>
          set((state) => ({
            streaming: {
              ...state.streaming,
              completedSteps: [...state.streaming.completedSteps, step],
              stepProgress: 100
            }
          })),
          
        setStreamingError: (error) =>
          set((state) => ({
            streaming: {
              ...state.streaming,
              currentStep: error ? 'error' : state.streaming.currentStep,
              error
            }
          })),
          
        updateStreamingData: (data) =>
          set((state) => ({
            streaming: {
              ...state.streaming,
              streamingData: {
                ...state.streaming.streamingData,
                ...data
              }
            }
          })),
          
        resetStreaming: () =>
          set({ streaming: defaultStreamingState }),
        
        // History actions
        addToHistory: (prompt) =>
          set((state) => ({
            history: [
              {
                ...prompt,
                id: crypto.randomUUID(),
                timestamp: Date.now(),
              },
              ...state.history,
            ].slice(0, 50), // Keep only last 50 entries
          })),
          
        clearHistory: () => set({ history: [] }),
        
        removeFromHistory: (id) =>
          set((state) => ({
            history: state.history.filter((item) => item.id !== id),
          })),
          
        ratePrompt: (id, rating) =>
          set((state) => ({
            history: state.history.map((item) =>
              item.id === id ? { ...item, rating } : item
            ),
          })),
        
        // Preference actions
        updatePreferences: (newPreferences) =>
          set((state) => ({
            preferences: { ...state.preferences, ...newPreferences },
          })),
          
        togglePreferredTechnique: (techniqueId) =>
          set((state) => {
            const preferred = state.preferences.preferredTechniques
            const isPreferred = preferred.includes(techniqueId)
            
            return {
              preferences: {
                ...state.preferences,
                preferredTechniques: isPreferred
                  ? preferred.filter((id) => id !== techniqueId)
                  : [...preferred, techniqueId],
              },
            }
          }),
        
        // Technique actions
        setAvailableTechniques: (techniques) =>
          set({ availableTechniques: techniques }),
      }),
      {
        name: 'enhance-store',
        partialize: (state) => ({
          history: state.history,
          preferences: state.preferences,
        }),
      }
    )
  )
)