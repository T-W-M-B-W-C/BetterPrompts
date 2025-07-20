'use client'

import { useState } from 'react'
import { enhanceService } from '@/lib/api/enhance'

export default function ApiTestPage() {
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const testAnalyze = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await enhanceService.analyze({ input: 'Help me write a blog post' })
      setResult(response)
    } catch (err: any) {
      setError(err.message || 'Failed to analyze')
    } finally {
      setLoading(false)
    }
  }

  const testEnhance = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await enhanceService.enhance({
        input: 'Help me write a blog post',
        technique: 'chain_of_thought'
      })
      setResult(response)
    } catch (err: any) {
      setError(err.message || 'Failed to enhance')
    } finally {
      setLoading(false)
    }
  }

  const testTechniques = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await enhanceService.getTechniques()
      setResult(response)
    } catch (err: any) {
      setError(err.message || 'Failed to get techniques')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">API Integration Test</h1>
      
      <div className="space-y-4 mb-6">
        <button 
          onClick={testAnalyze} 
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded mr-2"
        >
          Test Analyze
        </button>
        <button 
          onClick={testEnhance} 
          disabled={loading}
          className="bg-green-500 text-white px-4 py-2 rounded mr-2"
        >
          Test Enhance
        </button>
        <button 
          onClick={testTechniques} 
          disabled={loading}
          className="bg-purple-500 text-white px-4 py-2 rounded"
        >
          Test Get Techniques
        </button>
      </div>

      {loading && <p>Loading...</p>}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          Error: {error}
        </div>
      )}

      {result && (
        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-bold mb-2">Result:</h2>
          <pre className="whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}