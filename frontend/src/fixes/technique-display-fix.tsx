/**
 * Technique Cards Display Fix
 * 
 * Fixes the issue where technique cards are not displaying despite
 * API returning data successfully.
 * 
 * Issues addressed:
 * 1. Techniques section hidden during streaming
 * 2. showTechniques state not persisting after enhancement
 * 3. Techniques visibility logic conflicts
 */

import React, { useState, useEffect } from 'react'
import { Technique } from '@/lib/api/enhance'

interface TechniquesSectionProps {
  techniques: Technique[]
  selectedTechnique: string | null
  onSelectTechnique: (id: string) => void
  isEnhancing: boolean
  isLoadingTechniques: boolean
  techniquesError: string | null
  onRetryLoadTechniques: () => void
}

/**
 * Fixed techniques section that properly handles visibility
 */
export function TechniquesSection({
  techniques,
  selectedTechnique,
  onSelectTechnique,
  isEnhancing,
  isLoadingTechniques,
  techniquesError,
  onRetryLoadTechniques
}: TechniquesSectionProps) {
  // Separate visibility state from enhancement state
  const [isExpanded, setIsExpanded] = useState(false)
  
  // Auto-expand when techniques are loaded
  useEffect(() => {
    if (techniques.length > 0 && !isExpanded) {
      setIsExpanded(true)
    }
  }, [techniques.length])
  
  return (
    <div className="space-y-4">
      {/* Toggle button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="btn-ghost text-sm w-full sm:w-auto justify-center"
        disabled={isEnhancing}
        aria-expanded={isExpanded}
        aria-controls="techniques-section"
      >
        <span className="mr-2">
          Techniques {techniques.length > 0 && `(${techniques.length})`}
        </span>
        <ChevronDown className={cn(
          "h-4 w-4 transition-transform duration-200",
          isExpanded && "rotate-180"
        )} />
      </button>
      
      {/* Techniques content - show even during enhancement */}
      {isExpanded && (
        <div id="techniques-section" className={cn(
          "transition-opacity duration-300",
          isEnhancing && "opacity-50 pointer-events-none"
        )}>
          {/* Loading state */}
          {isLoadingTechniques && (
            <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-100 animate-pulse rounded-lg" />
              ))}
            </div>
          )}
          
          {/* Error state */}
          {techniquesError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 mb-2">Failed to load techniques</p>
              <button onClick={onRetryLoadTechniques} className="btn-sm btn-secondary">
                Retry
              </button>
            </div>
          )}
          
          {/* Techniques grid */}
          {!isLoadingTechniques && !techniquesError && techniques.length > 0 && (
            <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {techniques.map((technique) => (
                <TechniqueCard
                  key={technique.id}
                  technique={{
                    id: technique.id,
                    name: technique.name,
                    description: technique.description,
                    confidence: technique.effectiveness.overall
                  }}
                  isSelected={selectedTechnique === technique.id}
                  onClick={() => onSelectTechnique(technique.id)}
                  disabled={isEnhancing}
                />
              ))}
            </div>
          )}
          
          {/* Empty state */}
          {!isLoadingTechniques && !techniquesError && techniques.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>No techniques available</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Enhanced technique card with disabled state
 */
function TechniqueCard({ 
  technique, 
  isSelected, 
  onClick,
  disabled = false 
}: {
  technique: { id: string; name: string; description: string; confidence: number }
  isSelected: boolean
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "p-4 rounded-lg border-2 transition-all text-left",
        isSelected
          ? "border-blue-500 bg-blue-50"
          : "border-gray-200 hover:border-gray-300",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <h3 className="font-semibold mb-1">{technique.name}</h3>
      <p className="text-sm text-gray-600 mb-2">{technique.description}</p>
      <div className="text-xs text-gray-500">
        Confidence: {Math.round(technique.confidence * 100)}%
      </div>
    </button>
  )
}

// Import necessary utilities (these would come from actual imports)
declare const cn: (...classes: string[]) => string
declare const ChevronDown: React.FC<{ className?: string }>

export default TechniquesSection