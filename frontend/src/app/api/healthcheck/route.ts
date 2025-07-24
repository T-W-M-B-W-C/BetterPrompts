import { NextResponse } from 'next/server';

export async function GET() {
  // Basic health check
  const health: any = {
    status: 'ok',
    service: 'frontend',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV,
    version: process.env.npm_package_version || '1.0.0',
  };

  // Check if we can reach the API gateway
  try {
    // Use nginx service name for server-side requests in Docker
    const apiUrl = process.env.NODE_ENV === 'development' && process.env.DOCKERIZED 
      ? 'http://nginx/api/v1'
      : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api/v1');
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    const response = await fetch(`${apiUrl}/health`, {
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    health.apiGateway = {
      reachable: response.ok,
      status: response.status,
    };
  } catch (error) {
    health.apiGateway = {
      reachable: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }

  return NextResponse.json(health);
}