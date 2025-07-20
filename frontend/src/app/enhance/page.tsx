'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Copy, RefreshCw, Info, Sparkles, ChevronDown, AlertCircle, WifiOff } from 'lucide-react'
import Container from '@/components/layout/Container'
import TechniqueCard from '@/components/enhance/TechniqueCard'
import TechniqueCardSkeleton from '@/components/enhance/TechniqueCardSkeleton'
import { cn } from '@/lib/utils'
import { useEnhance, useTechniques } from '@/hooks/useEnhance'
import { useApiStatus } from '@/hooks/useApiStatus'
import { Technique } from '@/lib/api/enhance'

export default function EnhancePage() {
  const [userInput, setUserInput] = useState('')
  const [enhancedPrompt, setEnhancedPrompt] = useState('')
  const [selectedTechnique, setSelectedTechnique] = useState<string | null>(null)
  const [showTechniques, setShowTechniques] = useState(false)
  const [copied, setCopied] = useState(false)
  const [techniques, setTechniques] = useState<Technique[]>([])
  
  // API hooks
  const { enhance, isLoading: isEnhancing, error: enhanceError } = useEnhance()
  const { fetchTechniques, isLoading: loadingTechniques, error: techniquesError } = useTechniques()
  const { isConnected, isChecking } = useApiStatus()

  // Load techniques on mount
  useEffect(() => {
    fetchTechniques().then(techs => {
      setTechniques(techs)
    })
  }, [fetchTechniques])

  const handleEnhance = async () => {
    if (!userInput.trim()) return

    setShowTechniques(true)
    
    const response = await enhance({
      input: userInput,
      technique: selectedTechnique || undefined,
      options: {
        explanation: true
      }
    })

    if (response) {
      setEnhancedPrompt(response.enhanced.prompt)
      setSelectedTechnique(response.enhanced.technique)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(enhancedPrompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleEnhance()
    }
  }

  return (
    <section className="py-8 sm:py-16">
      <Container size="xl">
        {/* Connection Status Banner */}
        <AnimatePresence>
          {!isConnected && !isChecking && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="mb-6">
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-center">
                  <WifiOff className="h-5 w-5 text-orange-500 mr-3 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-orange-800 font-medium">Connection Issue</p>
                    <p className="text-xs text-orange-600 mt-1">
                      Unable to connect to the server. Please check your internet connection and try again.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Enhance Your Prompts
            </h1>
            <p className="text-lg text-gray-600">
              Enter your prompt below and let AI optimize it for better results
            </p>
          </div>

          {/* Input Section */}
          <div className="mb-8">
            <div className="relative">
              <label htmlFor="user-input" className="sr-only">
                Enter your prompt
              </label>
              <textarea
                id="user-input"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter your prompt here... (e.g., 'Help me write a blog post about sustainable living')"
                className="w-full min-h-[150px] p-4 pr-12 text-base border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isEnhancing}
              />
              <div className="absolute bottom-4 right-4 flex items-center gap-2">
                <span className="text-xs text-gray-400">
                  Ctrl + Enter
                </span>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <button
                onClick={handleEnhance}
                disabled={!userInput.trim() || isEnhancing || !isConnected}
                className={cn(
                  "btn-primary",
                  (isEnhancing || !isConnected) && "cursor-not-allowed opacity-50"
                )}
              >
                {isEnhancing ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Enhancing...
                  </>
                ) : !isConnected ? (
                  <>
                    <WifiOff className="mr-2 h-4 w-4" />
                    Offline
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Enhance Prompt
                  </>
                )}
              </button>
              <button
                onClick={() => setShowTechniques(!showTechniques)}
                className="btn-ghost text-sm"
              >
                <Info className="mr-2 h-4 w-4" />
                Techniques
                <ChevronDown className={cn(
                  "ml-1 h-4 w-4 transition-transform",
                  showTechniques && "rotate-180"
                )} />
              </button>
            </div>
          </div>

          {/* Techniques Section */}
          <AnimatePresence>
            {showTechniques && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="mb-8 overflow-hidden">
                  <div className="space-y-4">
                  {/* Loading state */}
                  {loadingTechniques && (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {[...Array(6)].map((_, i) => (
                        <TechniqueCardSkeleton key={i} />
                      ))}
                    </div>
                  )}
                  
                  {/* Error state */}
                  {techniquesError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                      <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                      <div>
                        <p className="text-sm text-red-800">Failed to load techniques</p>
                        <p className="text-xs text-red-600 mt-1">{techniquesError}</p>
                      </div>
                    </div>
                  )}
                  
                  {/* Techniques grid */}
                  {!loadingTechniques && !techniquesError && (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
                          onClick={() => setSelectedTechnique(technique.id)}
                        />
                      ))}
                    </div>
                  )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error Section */}
          <AnimatePresence>
            {enhanceError && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="mb-6">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-red-800 font-medium">Enhancement failed</p>
                    <p className="text-xs text-red-600 mt-1">{enhanceError}</p>
                  </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Output Section */}
          <AnimatePresence>
            {enhancedPrompt && !enhanceError && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="relative">
                  <div className="absolute -top-3 left-4 bg-white px-2">
                    <span className="text-sm font-medium text-gray-600">
                      Enhanced Prompt
                    </span>
                  </div>
                  <div className="rounded-xl border bg-gray-50 p-4">
                    <pre className="whitespace-pre-wrap font-sans text-base text-gray-800">
                      {enhancedPrompt}
                    </pre>
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <button
                      onClick={handleCopy}
                      className="btn-secondary"
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      {copied ? 'Copied!' : 'Copy to Clipboard'}
                    </button>
                    <button
                      onClick={handleEnhance}
                      className="btn-ghost"
                    >
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Try Another Technique
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </Container>
    </section>
  )
}