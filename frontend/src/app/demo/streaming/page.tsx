'use client'

import Container from '@/components/layout/Container'
import StreamingDemo from '@/components/enhance/StreamingDemo'
import StreamingProgress from '@/components/enhance/StreamingProgress'
import StreamingProgressCompact, { 
  StreamingProgressMini, 
  StreamingProgressDots 
} from '@/components/enhance/StreamingProgressCompact'
import EnhancementFlow from '@/components/enhance/EnhancementFlow'
import { useState } from 'react'
import { motion } from 'framer-motion'

export default function StreamingDemoPage() {
  const [showEnhancementFlow, setShowEnhancementFlow] = useState(false)
  const [enhancementResult, setEnhancementResult] = useState<{ prompt: string; technique: string } | null>(null)

  return (
    <section className="py-8 sm:py-16">
      <Container size="xl">
        <div className="space-y-12">
          {/* Page Header */}
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">Streaming Progress Indicators</h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Real-time feedback during the prompt enhancement process with multiple visualization options
            </p>
          </div>

          {/* Interactive Demo */}
          <div className="bg-gray-50 rounded-xl p-8">
            <StreamingDemo />
          </div>

          {/* Component Showcase */}
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-center">Component Variants</h2>
            
            {/* Full Progress */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Full Progress Indicator</h3>
              <div className="bg-white rounded-lg border p-6">
                <StreamingProgress
                  currentStep="generating_prompt"
                  progress={65}
                  completedSteps={['analyzing', 'classifying_intent', 'selecting_techniques']}
                  estimatedTimeRemaining={4500}
                  showDetails={true}
                />
              </div>
            </div>

            {/* Compact Progress */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Compact Progress</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-white rounded-lg border p-4">
                  <StreamingProgressCompact
                    currentStep="analyzing"
                    progress={30}
                  />
                </div>
                <div className="bg-white rounded-lg border p-4">
                  <StreamingProgressCompact
                    currentStep="complete"
                  />
                </div>
              </div>
            </div>

            {/* Mini & Dots */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Mini Indicators</h3>
              <div className="flex flex-wrap gap-4">
                <div className="bg-white rounded-lg border px-4 py-2">
                  <StreamingProgressMini currentStep="analyzing" />
                </div>
                <div className="bg-white rounded-lg border px-4 py-2">
                  <StreamingProgressMini currentStep="generating_prompt" />
                </div>
                <div className="bg-white rounded-lg border px-4 py-2">
                  <StreamingProgressMini currentStep="complete" />
                </div>
                <div className="bg-white rounded-lg border px-4 py-2">
                  <StreamingProgressMini currentStep="error" />
                </div>
              </div>

              <div className="bg-white rounded-lg border p-4">
                <p className="text-sm text-gray-600 mb-2">Progress Dots:</p>
                <StreamingProgressDots
                  currentStep="selecting_techniques"
                  completedSteps={['analyzing', 'classifying_intent']}
                />
              </div>
            </div>
          </div>

          {/* Full Enhancement Flow Demo */}
          <div className="space-y-4">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">Full Enhancement Flow</h2>
              <p className="text-gray-600 mb-4">
                Try the complete enhancement experience with streaming feedback
              </p>
              <button
                onClick={() => setShowEnhancementFlow(!showEnhancementFlow)}
                className="btn-primary"
              >
                {showEnhancementFlow ? 'Hide' : 'Show'} Enhancement Flow
              </button>
            </div>

            {showEnhancementFlow && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="max-w-4xl mx-auto">
                  <EnhancementFlow
                    onComplete={(result) => {
                      setEnhancementResult(result)
                    }}
                  />
                  
                  {enhancementResult && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <div className="mt-6 p-6 bg-green-50 rounded-lg border border-green-200">
                        <h3 className="font-semibold text-green-900 mb-2">Enhancement Result:</h3>
                        <p className="text-sm text-green-800">{enhancementResult.prompt}</p>
                        <p className="text-xs text-green-600 mt-2">
                          Technique used: {enhancementResult.technique}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            )}
          </div>

          {/* Implementation Guide */}
          <div className="bg-blue-50 rounded-xl p-8">
            <h2 className="text-2xl font-bold mb-4">Implementation Guide</h2>
            <div className="space-y-4 text-sm">
              <div>
                <h3 className="font-semibold mb-2">1. Basic Usage</h3>
                <pre className="bg-white rounded p-3 overflow-x-auto">
{`import StreamingProgress from '@/components/enhance/StreamingProgress'

<StreamingProgress
  currentStep="analyzing"
  progress={45}
  completedSteps={[]}
  showDetails={true}
/>`}
                </pre>
              </div>

              <div>
                <h3 className="font-semibold mb-2">2. With WebSocket Integration</h3>
                <pre className="bg-white rounded p-3 overflow-x-auto">
{`import { useStreamingEnhancement } from '@/hooks/useStreamingEnhancement'

const { startStreaming, cancelStreaming } = useStreamingEnhancement({
  onComplete: (result) => console.log('Done!', result),
  onError: (error) => console.error('Failed:', error)
})

// Start streaming
startStreaming(userInput, selectedTechnique)`}
                </pre>
              </div>

              <div>
                <h3 className="font-semibold mb-2">3. State Management</h3>
                <pre className="bg-white rounded p-3 overflow-x-auto">
{`import { useEnhanceStore } from '@/store/useEnhanceStore'

const { streaming, updateStreamingStep } = useEnhanceStore()

// Update progress
updateStreamingStep('analyzing', 75)`}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </section>
  )
}