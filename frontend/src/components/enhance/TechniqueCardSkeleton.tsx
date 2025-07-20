import { cn } from '@/lib/utils'

export default function TechniqueCardSkeleton() {
  return (
    <div className={cn(
      "relative overflow-hidden rounded-lg border p-4",
      "bg-gray-50 animate-pulse"
    )}>
      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div className="h-5 w-32 bg-gray-200 rounded" />
        <div className="h-4 w-12 bg-gray-200 rounded" />
      </div>
      
      {/* Description */}
      <div className="space-y-2">
        <div className="h-3 w-full bg-gray-200 rounded" />
        <div className="h-3 w-4/5 bg-gray-200 rounded" />
      </div>
      
      {/* Bottom indicator */}
      <div className="mt-3 flex items-center justify-between">
        <div className="h-3 w-20 bg-gray-200 rounded" />
        <div className="h-5 w-5 bg-gray-200 rounded-full" />
      </div>
    </div>
  )
}