import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Check if the application is ready to serve requests
    // Use internal Docker network URL when in container, external URL otherwise
    const apiUrl = process.env.NODE_ENV === 'production' 
      ? 'http://infra-mind-api-service:8000' 
      : process.env.NEXT_PUBLIC_API_URL || 'http://api:8000';
    
    // Simple connectivity check to API
    try {
      const response = await fetch(`${apiUrl}/health`, { 
        method: 'HEAD',
        signal: AbortSignal.timeout(5000)
      });
      
      const apiHealthy = response.ok;
      
      return NextResponse.json({
        status: 'ready',
        timestamp: new Date().toISOString(),
        service: 'frontend',
        dependencies: {
          api: apiHealthy ? 'healthy' : 'unhealthy'
        }
      });
    } catch (apiError) {
      return NextResponse.json({
        status: 'ready',
        timestamp: new Date().toISOString(),
        service: 'frontend',
        dependencies: {
          api: 'unreachable'
        },
        warning: 'API dependency check failed but frontend is ready'
      });
    }
  } catch (error) {
    return NextResponse.json(
      {
        status: 'not ready',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      },
      { status: 503 }
    );
  }
}