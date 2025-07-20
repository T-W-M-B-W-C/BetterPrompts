import { useEffect, useRef, useCallback } from 'react'
import { useEnhanceStore } from '@/store/useEnhanceStore'
import { StreamingStep, ENHANCEMENT_STEPS } from '@/components/enhance/StreamingProgress'

interface StreamingMessage {
  type: 'step' | 'progress' | 'data' | 'complete' | 'error'
  step?: StreamingStep
  progress?: number
  data?: {
    intent?: string
    techniques?: string[]
    partialOutput?: string
  }
  error?: string
  result?: {
    prompt: string
    technique: string
  }
}

interface UseStreamingEnhancementOptions {
  onComplete?: (result: { prompt: string; technique: string }) => void
  onError?: (error: string) => void
}

export function useStreamingEnhancement(options: UseStreamingEnhancementOptions = {}) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const {
    updateStreamingStep,
    completeStreamingStep,
    setStreamingError,
    updateStreamingData,
    resetStreaming,
    setCurrentOutput,
    setIsEnhancing
  } = useEnhanceStore()

  const connect = useCallback((url: string) => {
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected for streaming enhancement')
      }

      ws.onmessage = (event) => {
        try {
          const message: StreamingMessage = JSON.parse(event.data)
          
          switch (message.type) {
            case 'step':
              if (message.step) {
                updateStreamingStep(message.step, 0)
              }
              break
              
            case 'progress':
              if (message.step && message.progress !== undefined) {
                updateStreamingStep(message.step, message.progress)
                
                // Complete step when progress reaches 100
                if (message.progress >= 100) {
                  completeStreamingStep(message.step)
                }
              }
              break
              
            case 'data':
              if (message.data) {
                updateStreamingData(message.data)
              }
              break
              
            case 'complete':
              updateStreamingStep('complete', 100)
              setIsEnhancing(false)
              
              if (message.result) {
                setCurrentOutput(message.result.prompt)
                options.onComplete?.(message.result)
              }
              
              // Close connection after completion
              ws.close()
              break
              
            case 'error':
              setStreamingError(message.error || 'Unknown error occurred')
              setIsEnhancing(false)
              options.onError?.(message.error || 'Unknown error')
              ws.close()
              break
          }
        } catch (error) {
          console.error('Error parsing streaming message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setStreamingError('Connection error occurred')
        setIsEnhancing(false)
      }

      ws.onclose = () => {
        console.log('WebSocket connection closed')
        wsRef.current = null
        
        // Attempt to reconnect after 3 seconds if not intentionally closed
        if (!wsRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...')
            // Reconnect logic would go here
          }, 3000)
        }
      }

    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
      setStreamingError('Failed to establish connection')
      setIsEnhancing(false)
    }
  }, [updateStreamingStep, completeStreamingStep, setStreamingError, updateStreamingData, setCurrentOutput, setIsEnhancing, options])

  const startStreaming = useCallback(async (input: string, technique?: string) => {
    resetStreaming()
    setIsEnhancing(true)
    
    // In a real implementation, this would be your WebSocket endpoint
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost/api/v1/enhance/stream'
    const params = new URLSearchParams({
      input: encodeURIComponent(input),
      ...(technique && { technique })
    })
    
    connect(`${wsUrl}?${params}`)
  }, [connect, resetStreaming, setIsEnhancing])

  const cancelStreaming = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    resetStreaming()
    setIsEnhancing(false)
  }, [resetStreaming, setIsEnhancing])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    startStreaming,
    cancelStreaming,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN
  }
}

// Server-Sent Events (SSE) alternative implementation
export function useStreamingEnhancementSSE(options: UseStreamingEnhancementOptions = {}) {
  const eventSourceRef = useRef<EventSource | null>(null)
  const {
    updateStreamingStep,
    completeStreamingStep,
    setStreamingError,
    updateStreamingData,
    resetStreaming,
    setCurrentOutput,
    setIsEnhancing
  } = useEnhanceStore()

  const startStreaming = useCallback(async (input: string, technique?: string) => {
    resetStreaming()
    setIsEnhancing(true)
    
    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }
    
    const params = new URLSearchParams({
      input: encodeURIComponent(input),
      ...(technique && { technique })
    })
    
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api/v1'}/enhance/stream?${params}`
    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const message: StreamingMessage = JSON.parse(event.data)
        
        // Handle message same as WebSocket implementation
        switch (message.type) {
          case 'step':
            if (message.step) {
              updateStreamingStep(message.step, 0)
            }
            break
            
          case 'progress':
            if (message.step && message.progress !== undefined) {
              updateStreamingStep(message.step, message.progress)
              
              if (message.progress >= 100) {
                completeStreamingStep(message.step)
              }
            }
            break
            
          case 'data':
            if (message.data) {
              updateStreamingData(message.data)
            }
            break
            
          case 'complete':
            updateStreamingStep('complete', 100)
            setIsEnhancing(false)
            
            if (message.result) {
              setCurrentOutput(message.result.prompt)
              options.onComplete?.(message.result)
            }
            
            eventSource.close()
            break
            
          case 'error':
            setStreamingError(message.error || 'Unknown error occurred')
            setIsEnhancing(false)
            options.onError?.(message.error || 'Unknown error')
            eventSource.close()
            break
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      setStreamingError('Connection error occurred')
      setIsEnhancing(false)
      eventSource.close()
    }
  }, [updateStreamingStep, completeStreamingStep, setStreamingError, updateStreamingData, resetStreaming, setCurrentOutput, setIsEnhancing, options])

  const cancelStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    
    resetStreaming()
    setIsEnhancing(false)
  }, [resetStreaming, setIsEnhancing])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return {
    startStreaming,
    cancelStreaming
  }
}