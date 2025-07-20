import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api/client'

export function useApiStatus() {
  const [isConnected, setIsConnected] = useState(true)
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    const checkConnection = async () => {
      setIsChecking(true)
      try {
        // Try to hit the health endpoint
        await apiClient.get('/health')
        setIsConnected(true)
      } catch (error) {
        setIsConnected(false)
      } finally {
        setIsChecking(false)
      }
    }

    // Check immediately
    checkConnection()

    // Check periodically
    const interval = setInterval(checkConnection, 30000) // Every 30 seconds

    return () => clearInterval(interval)
  }, [])

  return { isConnected, isChecking }
}