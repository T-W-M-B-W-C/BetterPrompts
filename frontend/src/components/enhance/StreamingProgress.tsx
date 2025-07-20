import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain, 
  Sparkles, 
  Zap, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  ArrowRight,
  Timer
} from 'lucide-react'
import { cn } from '@/lib/utils'

export type StreamingStep = 
  | 'analyzing'
  | 'classifying_intent'
  | 'selecting_techniques'
  | 'generating_prompt'
  | 'optimizing'
  | 'complete'
  | 'error'

interface StepConfig {
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  duration: number // Expected duration in ms
}

const stepConfigs: Record<StreamingStep, StepConfig> = {
  analyzing: {
    label: 'Analyzing Input',
    description: 'Understanding your prompt structure and requirements',
    icon: Brain,
    duration: 1500
  },
  classifying_intent: {
    label: 'Classifying Intent',
    description: 'Identifying the purpose and goals of your prompt',
    icon: Zap,
    duration: 2000
  },
  selecting_techniques: {
    label: 'Selecting Techniques',
    description: 'Choosing optimal enhancement strategies',
    icon: Sparkles,
    duration: 1800
  },
  generating_prompt: {
    label: 'Generating Enhancement',
    description: 'Applying selected techniques to improve your prompt',
    icon: Loader2,
    duration: 3000
  },
  optimizing: {
    label: 'Final Optimization',
    description: 'Fine-tuning for maximum effectiveness',
    icon: Sparkles,
    duration: 1200
  },
  complete: {
    label: 'Enhancement Complete',
    description: 'Your prompt has been successfully enhanced',
    icon: CheckCircle2,
    duration: 0
  },
  error: {
    label: 'Enhancement Failed',
    description: 'An error occurred during the enhancement process',
    icon: AlertCircle,
    duration: 0
  }
}

interface StreamingProgressProps {
  currentStep: StreamingStep
  progress?: number // 0-100 for current step
  error?: string
  className?: string
  showDetails?: boolean
  completedSteps?: StreamingStep[]
  estimatedTimeRemaining?: number
}

export default function StreamingProgress({
  currentStep,
  progress = 0,
  error,
  className,
  showDetails = true,
  completedSteps = [],
  estimatedTimeRemaining
}: StreamingProgressProps) {
  const config = stepConfigs[currentStep]
  const Icon = config.icon
  const isError = currentStep === 'error'
  const isComplete = currentStep === 'complete'

  // Calculate overall progress based on completed steps
  const totalSteps = Object.keys(stepConfigs).filter(
    step => step !== 'error' && step !== 'complete'
  ).length
  const overallProgress = ((completedSteps.length / totalSteps) * 100)

  return (
    <div className={cn("space-y-4", className)}>
      {/* Main Progress Indicator */}
      <div className="relative">
        {/* Overall Progress Bar */}
        <div className="absolute -top-2 left-0 right-0 h-1 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${overallProgress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            style={{ height: '100%' }}
          >
            <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500" />
          </motion.div>
        </div>

        {/* Current Step Display */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            <div className={cn(
              "bg-white rounded-lg border-2 p-6 shadow-sm",
              isError && "border-red-200 bg-red-50",
              isComplete && "border-green-200 bg-green-50",
              !isError && !isComplete && "border-blue-200"
            )}>
            <div className="flex items-center space-x-4">
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
                      "h-8 w-8",
                      isError && "text-red-500",
                      isComplete && "text-green-500",
                      !isError && !isComplete && "text-blue-500"
                    )}
                  />
                </motion.div>
                
                {/* Pulse animation for active steps */}
                {!isError && !isComplete && (
                  <motion.div
                    initial={{ scale: 0.8, opacity: 0.5 }}
                    animate={{ scale: 1.5, opacity: 0 }}
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

              {/* Step Info */}
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-gray-900">
                  {config.label}
                </h3>
                {showDetails && (
                  <p className="text-sm text-gray-600 mt-1">
                    {error || config.description}
                  </p>
                )}
              </div>

              {/* Time Remaining */}
              {estimatedTimeRemaining && !isError && !isComplete && (
                <div className="flex items-center text-sm text-gray-500">
                  <Timer className="h-4 w-4 mr-1" />
                  <span>{Math.ceil(estimatedTimeRemaining / 1000)}s</span>
                </div>
              )}
            </div>

            {/* Step Progress Bar */}
            {!isError && !isComplete && progress > 0 && (
              <div className="mt-4">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                    style={{ height: '100%' }}
                  >
                    <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600" />
                  </motion.div>
                </div>
              </div>
            )}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Step Timeline (optional detailed view) */}
      {showDetails && completedSteps.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Progress Timeline</h4>
          <div className="space-y-1">
            {completedSteps.map((step, index) => {
              const stepConfig = stepConfigs[step]
              const StepIcon = stepConfig.icon
              
              return (
                <motion.div
                  key={step}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="flex items-center space-x-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span className="text-gray-600">{stepConfig.label}</span>
                  <ArrowRight className="h-3 w-3 text-gray-400" />
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// Export step sequence for external use
export const ENHANCEMENT_STEPS: StreamingStep[] = [
  'analyzing',
  'classifying_intent',
  'selecting_techniques',
  'generating_prompt',
  'optimizing'
]

// Utility to calculate estimated total time
export function calculateEstimatedTime(fromStep: StreamingStep): number {
  const remainingSteps = ENHANCEMENT_STEPS.slice(
    ENHANCEMENT_STEPS.indexOf(fromStep)
  )
  
  return remainingSteps.reduce((total, step) => {
    return total + stepConfigs[step].duration
  }, 0)
}