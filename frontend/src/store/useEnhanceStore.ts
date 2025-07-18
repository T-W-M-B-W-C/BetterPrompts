import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

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

interface EnhanceState {
  // Current enhancement session
  currentInput: string
  currentOutput: string
  selectedTechnique: string | null
  isEnhancing: boolean
  
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

export const useEnhanceStore = create<EnhanceState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        currentInput: '',
        currentOutput: '',
        selectedTechnique: null,
        isEnhancing: false,
        history: [],
        availableTechniques: [],
        preferences: defaultPreferences,
        
        // Actions
        setCurrentInput: (input) => set({ currentInput: input }),
        setCurrentOutput: (output) => set({ currentOutput: output }),
        setSelectedTechnique: (techniqueId) => set({ selectedTechnique: techniqueId }),
        setIsEnhancing: (isEnhancing) => set({ isEnhancing }),
        
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