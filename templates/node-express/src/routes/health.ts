import { Router, Request, Response } from 'express';
import { logger } from '@/utils/logger';
import { config } from '@/config/environment';

const router = Router();

interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  uptime: number;
  version: string;
  environment: string;
  checks?: {
    [key: string]: {
      status: 'healthy' | 'unhealthy';
      message?: string;
      responseTime?: number;
    };
  };
}

// Basic health check
router.get('/', (req: Request, res: Response) => {
  const healthStatus: HealthStatus = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0',
    environment: config.environment,
  };

  res.json(healthStatus);
});

// Readiness probe - checks if the service is ready to receive traffic
router.get('/ready', async (req: Request, res: Response) => {
  const checks: HealthStatus['checks'] = {};
  let overallStatus: 'healthy' | 'unhealthy' = 'healthy';

  try {
    // Check database connection (if applicable)
    if (config.database.url) {
      const dbStart = Date.now();
      try {
        // Add actual database health check here
        // await checkDatabaseConnection();
        checks.database = {
          status: 'healthy',
          responseTime: Date.now() - dbStart,
        };
      } catch (error) {
        checks.database = {
          status: 'unhealthy',
          message: error instanceof Error ? error.message : 'Database connection failed',
          responseTime: Date.now() - dbStart,
        };
        overallStatus = 'unhealthy';
      }
    }

    // Check external API dependencies (if applicable)
    if (config.api.baseUrl) {
      const apiStart = Date.now();
      try {
        // Add actual external API health check here
        // await checkExternalAPI();
        checks.externalAPI = {
          status: 'healthy',
          responseTime: Date.now() - apiStart,
        };
      } catch (error) {
        checks.externalAPI = {
          status: 'unhealthy',
          message: error instanceof Error ? error.message : 'External API check failed',
          responseTime: Date.now() - apiStart,
        };
        overallStatus = 'unhealthy';
      }
    }

    const healthStatus: HealthStatus = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: '1.0.0',
      environment: config.environment,
      checks,
    };

    const statusCode = overallStatus === 'healthy' ? 200 : 503;
    res.status(statusCode).json(healthStatus);

  } catch (error) {
    logger.error('Health check failed', { error: error instanceof Error ? error.message : 'Unknown error' });
    
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: '1.0.0',
      environment: config.environment,
      error: error instanceof Error ? error.message : 'Health check failed',
    });
  }
});

// Liveness probe - checks if the service is alive
router.get('/live', (req: Request, res: Response) => {
  const healthStatus: HealthStatus = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0',
    environment: config.environment,
  };

  res.json(healthStatus);
});

export { router as healthRouter };