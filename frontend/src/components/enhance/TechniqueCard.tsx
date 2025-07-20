import { motion } from 'framer-motion'
import { Check } from 'lucide-react'
import * as Tooltip from '@radix-ui/react-tooltip'
import { cn } from '@/lib/utils'

interface TechniqueCardProps {
  technique: {
    id: string
    name: string
    description: string
    confidence: number
  }
  isSelected: boolean
  onClick: () => void
}

export default function TechniqueCard({ technique, isSelected, onClick }: TechniqueCardProps) {
  return (
    <Tooltip.Provider>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <button
              onClick={onClick}
              className={cn(
                "relative w-full rounded-lg border p-4 text-left transition-all",
                isSelected
                  ? "border-blue-500 bg-blue-50 shadow-md"
                  : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
              )}
            >
            {/* Selection indicator */}
            {isSelected && (
              <div className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-white">
                <Check className="h-4 w-4" />
              </div>
            )}

            {/* Content */}
            <h3 className="mb-1 font-semibold text-gray-900">
              {technique.name}
            </h3>
            <p className="mb-3 text-sm text-gray-600 line-clamp-2">
              {technique.description}
            </p>

            {/* Confidence indicator */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Confidence:</span>
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${technique.confidence * 100}%` }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  style={{ height: '100%' }}
                >
                  <div className={cn(
                    "h-full rounded-full",
                    technique.confidence > 0.8
                      ? "bg-green-500"
                      : technique.confidence > 0.6
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  )} />
                </motion.div>
              </div>
              <span className="text-xs font-medium text-gray-700">
                {Math.round(technique.confidence * 100)}%
              </span>
            </div>
            </button>
          </motion.div>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className="max-w-xs rounded-lg bg-gray-900 px-4 py-3 text-sm text-white shadow-lg"
            sideOffset={5}
          >
            <p className="mb-2 font-medium">{technique.name}</p>
            <p className="text-gray-300">{technique.description}</p>
            <p className="mt-2 text-xs text-gray-400">
              Click to select this technique for your prompt enhancement
            </p>
            <Tooltip.Arrow className="fill-gray-900" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  )
}