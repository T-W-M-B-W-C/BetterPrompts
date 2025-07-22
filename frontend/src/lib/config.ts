// Application configuration with type safety
export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api/v1',
    timeout: 30000, // 30 seconds
  },
  
  features: {
    auth: process.env.NEXT_PUBLIC_ENABLE_AUTH === 'true',
    analytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
    feedback: process.env.NEXT_PUBLIC_ENABLE_FEEDBACK === 'true',
  },
  
  development: {
    isDevMode: process.env.NEXT_PUBLIC_DEV_MODE === 'true' || process.env.NODE_ENV === 'development',
  },
  
  limits: {
    maxPromptLength: parseInt(process.env.NEXT_PUBLIC_MAX_PROMPT_LENGTH || '5000', 10),
    maxTechniques: 5,
    maxHistoryItems: 100,
  },
  
  defaults: {
    targetModel: process.env.NEXT_PUBLIC_DEFAULT_MODEL || 'gpt-4',
    complexity: 'moderate' as const,
  },
  
  // API endpoints configuration
  endpoints: {
    auth: {
      register: '/auth/register',
      login: '/auth/login',
      refresh: '/auth/refresh',
      logout: '/auth/logout',
      profile: '/auth/profile',
      changePassword: '/auth/change-password',
      verifyEmail: '/auth/verify-email',
    },
    prompts: {
      analyze: '/analyze',
      enhance: '/enhance',
      techniques: '/techniques',
      selectTechniques: '/techniques/select',
    },
    history: {
      list: '/history',
      get: (id: string) => `/history/${id}`,
      delete: (id: string) => `/history/${id}`,
    },
    feedback: '/feedback',
    admin: {
      users: '/admin/users',
      metrics: '/admin/metrics',
      cache: '/admin/cache',
    },
    developer: {
      apiKeys: '/dev/api-keys',
      analytics: '/dev/analytics',
    },
  },
  
  // Third-party services
  external: {
    posthog: {
      enabled: !!process.env.NEXT_PUBLIC_POSTHOG_KEY,
      apiKey: process.env.NEXT_PUBLIC_POSTHOG_KEY || '',
    },
    sentry: {
      enabled: !!process.env.NEXT_PUBLIC_SENTRY_DSN,
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN || '',
    },
  },
}

// Type-safe config getter
export function getConfig<K extends keyof typeof config>(key: K): typeof config[K] {
  return config[key]
}

// Environment checker
export const isProduction = process.env.NODE_ENV === 'production'
export const isDevelopment = process.env.NODE_ENV === 'development'
export const isTest = process.env.NODE_ENV === 'test'

// API URL helper
export function getApiUrl(endpoint: string): string {
  const baseUrl = config.api.baseUrl
  // Ensure no double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${baseUrl}${cleanEndpoint}`
}

// Port configuration for different services
export const servicePorts = {
  frontend: 3000,
  apiGateway: {
    internal: 8090,  // Internal Docker port
    external: 8000,  // External exposed port
    nginx: 80,       // Through nginx proxy
  },
  intentClassifier: 8001,
  techniqueSelector: 8002,
  promptGenerator: 8003,
  torchServe: {
    inference: 8080,
    management: 8081,
    metrics: 8082,
  },
  postgres: 5432,
  redis: 6379,
  grafana: 3001,
  prometheus: 9090,
}

// Helper to get the correct API URL based on environment
export function getEnvironmentApiUrl(): string {
  if (isProduction) {
    // In production, use the configured URL
    return config.api.baseUrl
  }
  
  if (config.development.isDevMode) {
    // In dev mode, allow direct API Gateway access
    console.log('Dev mode: Direct API Gateway access available at port', servicePorts.apiGateway.external)
  }
  
  // Default to nginx proxy
  return config.api.baseUrl
}