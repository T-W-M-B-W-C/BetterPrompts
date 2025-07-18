'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Copy, RefreshCw, Info, Sparkles, ChevronDown } from 'lucide-react'
import Container from '@/components/layout/Container'
import TechniqueCard from '@/components/enhance/TechniqueCard'
import { cn } from '@/lib/utils'

// Mock techniques for now - will be replaced with API data
const mockTechniques = [
  {
    id: 'cot',
    name: 'Chain of Thought',
    description: 'Break down complex reasoning into step-by-step analysis',
    confidence: 0.95,
  },
  {
    id: 'few-shot',
    name: 'Few-shot Learning',
    description: 'Provide examples to guide the model response',
    confidence: 0.87,
  },
  {
    id: 'tot',
    name: 'Tree of Thoughts',
    description: 'Explore multiple reasoning paths systematically',
    confidence: 0.82,
  },
]

export default function EnhancePage() {
  const [userInput, setUserInput] = useState('')
  const [enhancedPrompt, setEnhancedPrompt] = useState('')
  const [selectedTechnique, setSelectedTechnique] = useState<string | null>(null)
  const [isEnhancing, setIsEnhancing] = useState(false)
  const [showTechniques, setShowTechniques] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleEnhance = async () => {
    if (!userInput.trim()) return

    setIsEnhancing(true)
    setShowTechniques(true)
    
    // Simulate API call - replace with actual API integration
    setTimeout(() => {
      setEnhancedPrompt(`Let's approach this step-by-step:\n\n${userInput}\n\nFirst, I'll analyze the key components...\n[Enhanced with Chain of Thought technique]`)
      setSelectedTechnique('cot')
      setIsEnhancing(false)
    }, 1500)
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
                disabled={!userInput.trim() || isEnhancing}
                className={cn(
                  "btn-primary",
                  isEnhancing && "cursor-not-allowed opacity-50"
                )}
              >
                {isEnhancing ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Enhancing...
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
                className="mb-8 overflow-hidden"
              >
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {mockTechniques.map((technique) => (
                    <TechniqueCard
                      key={technique.id}
                      technique={technique}
                      isSelected={selectedTechnique === technique.id}
                      onClick={() => setSelectedTechnique(technique.id)}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Output Section */}
          <AnimatePresence>
            {enhancedPrompt && (
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