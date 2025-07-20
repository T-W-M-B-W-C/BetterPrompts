import { motion } from 'framer-motion'
import { Brain, Sparkles, Zap, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { StreamingStep } from './StreamingProgress'

const stepIcons: Record<StreamingStep, React.ComponentType<{ className?: string }>> = {
  analyzing: Brain,
  classifying_intent: Zap,
  selecting_techniques: Sparkles,
  generating_prompt: Loader2,
  optimizing: Sparkles,
  complete: CheckCircle2,
  error: AlertCircle
}

const stepLabels: Record<StreamingStep, string> = {
  analyzing: 'Analyzing',
  classifying_intent: 'Classifying',
  selecting_techniques: 'Selecting',
  generating_prompt: 'Generating',
  optimizing: 'Optimizing',
  complete: 'Complete',
  error: 'Error'
}

interface StreamingProgressCompactProps {
  currentStep: StreamingStep
  progress?: number
  error?: string
  className?: string
}

export default function StreamingProgressCompact({
  currentStep,
  progress = 0,
  error,
  className
}: StreamingProgressCompactProps) {
  const Icon = stepIcons[currentStep]
  const label = stepLabels[currentStep]
  const isError = currentStep === 'error'
  const isComplete = currentStep === 'complete'

  return (
    <div className={cn("flex items-center space-x-3", className)}>
      {/* Icon with animation */}
      <div className="relative">
        <motion.div
          animate={
            currentStep === 'generating_prompt' || currentStep === 'analyzing'
              ? { rotate: 360 }
              : {}
          }
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Icon
            className={cn(
              "h-5 w-5",
              isError && "text-red-500",
              isComplete && "text-green-500",
              !isError && !isComplete && "text-blue-500"
            )}
          />
        </motion.div>
        
        {/* Pulse for active steps */}
        {!isError && !isComplete && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0.5 }}
            animate={{ scale: 1.8, opacity: 0 }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '9999px',
              backgroundColor: 'rgb(96 165 250)'
            }}
          />
        )}
      </div>

      {/* Label and progress */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className={cn(
            "text-sm font-medium",
            isError && "text-red-700",
            isComplete && "text-green-700",
            !isError && !isComplete && "text-gray-700"
          )}>
            {error || label}
          </span>
          {!isError && !isComplete && progress > 0 && (
            <span className="text-xs text-gray-500">{Math.round(progress)}%</span>
          )}
        </div>
        
        {/* Progress bar */}
        {!isError && !isComplete && (
          <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
              style={{ height: '100%' }}
            >
              <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600" />
            </motion.div>
          </div>
        )}
      </div>
    </div>
  )
}

// Mini version for very compact spaces
export function StreamingProgressMini({
  currentStep,
  className
}: {
  currentStep: StreamingStep
  className?: string
}) {
  const Icon = stepIcons[currentStep]
  const isError = currentStep === 'error'
  const isComplete = currentStep === 'complete'
  const isActive = !isError && !isComplete

  return (
    <div className={cn("inline-flex items-center space-x-2", className)}>
      <motion.div
        animate={isActive ? { rotate: 360 } : {}}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      >
        <Icon
          className={cn(
            "h-4 w-4",
            isError && "text-red-500",
            isComplete && "text-green-500",
            isActive && "text-blue-500"
          )}
        />
      </motion.div>
      <span className={cn(
        "text-xs",
        isError && "text-red-600",
        isComplete && "text-green-600",
        isActive && "text-gray-600"
      )}>
        {stepLabels[currentStep]}
      </span>
    </div>
  )
}

// Progress dots indicator
export function StreamingProgressDots({
  currentStep,
  completedSteps = [],
  className
}: {
  currentStep: StreamingStep | null
  completedSteps?: StreamingStep[]
  className?: string
}) {
  const steps: StreamingStep[] = [
    'analyzing',
    'classifying_intent',
    'selecting_techniques',
    'generating_prompt',
    'optimizing'
  ]

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      {steps.map((step, index) => {
        const isCompleted = completedSteps.includes(step)
        const isCurrent = currentStep === step
        const isPending = !isCompleted && !isCurrent

        return (
          <motion.div
            key={step}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className={cn(
              "h-2 w-2 rounded-full",
              isCompleted && "bg-green-500",
              isCurrent && "bg-blue-500",
              isPending && "bg-gray-300"
            )}>
            {isCurrent && (
              <motion.div
                animate={{ scale: [1, 1.5, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                style={{
                  height: '100%',
                  width: '100%',
                  borderRadius: '9999px',
                  backgroundColor: 'rgb(96 165 250)'
                }}
              />
            )}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}