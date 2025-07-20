'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import StreamingProgress, { StreamingStep, ENHANCEMENT_STEPS } from './StreamingProgress'
import { Play, Pause, RotateCcw, FastForward } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function StreamingDemo() {
  const [currentStep, setCurrentStep] = useState<StreamingStep | null>(null)
  const [progress, setProgress] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<StreamingStep[]>([])
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [speed, setSpeed] = useState(1)

  const startDemo = () => {
    setIsPlaying(true)
    setError(null)
    runDemo()
  }

  const runDemo = async () => {
    for (let i = 0; i < ENHANCEMENT_STEPS.length; i++) {
      const step = ENHANCEMENT_STEPS[i]
      setCurrentStep(step)
      setProgress(0)

      // Simulate progress
      for (let p = 0; p <= 100; p += 5) {
        if (!isPlaying) return
        setProgress(p)
        await new Promise(resolve => setTimeout(resolve, 50 / speed))
      }

      setCompletedSteps(prev => [...prev, step])
      await new Promise(resolve => setTimeout(resolve, 200 / speed))
    }

    // Complete
    setCurrentStep('complete')
    setIsPlaying(false)
  }

  const pauseDemo = () => {
    setIsPlaying(false)
  }

  const resetDemo = () => {
    setCurrentStep(null)
    setProgress(0)
    setCompletedSteps([])
    setIsPlaying(false)
    setError(null)
  }

  const simulateError = () => {
    setCurrentStep('error')
    setError('Connection lost during enhancement process')
    setIsPlaying(false)
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Streaming Progress Demo</h2>
        <p className="text-gray-600">
          Experience how the enhancement process provides real-time feedback
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        <button
          onClick={isPlaying ? pauseDemo : startDemo}
          disabled={currentStep === 'complete' || currentStep === 'error'}
          className={cn(
            "btn-primary",
            (currentStep === 'complete' || currentStep === 'error') && "opacity-50 cursor-not-allowed"
          )}
        >
          {isPlaying ? (
            <>
              <Pause className="mr-2 h-4 w-4" />
              Pause
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Start Demo
            </>
          )}
        </button>

        <button
          onClick={resetDemo}
          className="btn-ghost"
        >
          <RotateCcw className="mr-2 h-4 w-4" />
          Reset
        </button>

        <button
          onClick={simulateError}
          className="btn-ghost text-red-600"
          disabled={isPlaying}
        >
          Simulate Error
        </button>

        <div className="flex items-center gap-2">
          <FastForward className="h-4 w-4 text-gray-500" />
          <select
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="0.5">0.5x</option>
            <option value="1">1x</option>
            <option value="2">2x</option>
            <option value="4">4x</option>
          </select>
        </div>
      </div>

      {/* Progress Display */}
      <div className="max-w-2xl mx-auto">
        {currentStep && (
          <StreamingProgress
            currentStep={currentStep}
            progress={progress}
            error={error || undefined}
            completedSteps={completedSteps}
            estimatedTimeRemaining={
              currentStep && currentStep !== 'complete' && currentStep !== 'error'
                ? (ENHANCEMENT_STEPS.length - completedSteps.length) * 2000
                : undefined
            }
            showDetails={true}
          />
        )}
      </div>

      {/* Demo States */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="p-4 border rounded-lg cursor-pointer"
          onClick={() => {
            resetDemo()
            setCurrentStep('analyzing')
            setProgress(45)
          }}
        >
          <h3 className="font-medium mb-1">Analyzing State</h3>
          <p className="text-sm text-gray-600">Shows initial analysis phase</p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="p-4 border rounded-lg cursor-pointer"
          onClick={() => {
            resetDemo()
            setCurrentStep('selecting_techniques')
            setProgress(75)
            setCompletedSteps(['analyzing', 'classifying_intent'])
          }}
        >
          <h3 className="font-medium mb-1">Mid-Process</h3>
          <p className="text-sm text-gray-600">Multiple steps completed</p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="p-4 border rounded-lg cursor-pointer"
          onClick={() => {
            resetDemo()
            setCurrentStep('complete')
            setCompletedSteps([...ENHANCEMENT_STEPS])
          }}
        >
          <h3 className="font-medium mb-1">Complete State</h3>
          <p className="text-sm text-gray-600">Shows success state</p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="p-4 border rounded-lg cursor-pointer"
          onClick={() => {
            resetDemo()
            setCurrentStep('error')
            setError('Failed to connect to enhancement service')
          }}
        >
          <h3 className="font-medium mb-1">Error State</h3>
          <p className="text-sm text-gray-600">Shows error handling</p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="p-4 border rounded-lg cursor-pointer"
          onClick={() => {
            resetDemo()
            setCurrentStep('generating_prompt')
            setProgress(30)
            setCompletedSteps(['analyzing', 'classifying_intent', 'selecting_techniques'])
          }}
        >
          <h3 className="font-medium mb-1">Generating</h3>
          <p className="text-sm text-gray-600">Main generation phase</p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="p-4 border rounded-lg cursor-pointer"
          onClick={() => {
            resetDemo()
            setCurrentStep('optimizing')
            setProgress(60)
            setCompletedSteps(['analyzing', 'classifying_intent', 'selecting_techniques', 'generating_prompt'])
          }}
        >
          <h3 className="font-medium mb-1">Final Phase</h3>
          <p className="text-sm text-gray-600">Optimization in progress</p>
        </motion.div>
      </div>
    </div>
  )
}