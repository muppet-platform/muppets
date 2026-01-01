import { z } from 'zod';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'staging', 'production', 'test']).default('development'),
  PORT: z.string().transform(Number).default('3000'),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  
  // CORS configuration
  CORS_ALLOWED_ORIGINS: z.string().default('*'),
  
  // Database configuration (if needed)
  DATABASE_URL: z.string().optional(),
  
  // External service configuration
  API_BASE_URL: z.string().url().optional(),
  API_TIMEOUT: z.string().transform(Number).default('30000'),
  
  // Security
  JWT_SECRET: z.string().optional(),
  
  // AWS configuration (for production)
  AWS_REGION: z.string().default('us-east-1'),
  AWS_ACCESS_KEY_ID: z.string().optional(),
  AWS_SECRET_ACCESS_KEY: z.string().optional(),
});

export type Environment = z.infer<typeof envSchema>;

const env = envSchema.parse(process.env);

export const config = {
  environment: env.NODE_ENV,
  server: {
    port: env.PORT,
  },
  logging: {
    level: env.LOG_LEVEL,
  },
  cors: {
    allowedOrigins: env.CORS_ALLOWED_ORIGINS === '*' 
      ? true 
      : env.CORS_ALLOWED_ORIGINS.split(',').map(origin => origin.trim()),
  },
  database: {
    url: env.DATABASE_URL,
  },
  api: {
    baseUrl: env.API_BASE_URL,
    timeout: env.API_TIMEOUT,
  },
  security: {
    jwtSecret: env.JWT_SECRET,
  },
  aws: {
    region: env.AWS_REGION,
    accessKeyId: env.AWS_ACCESS_KEY_ID,
    secretAccessKey: env.AWS_SECRET_ACCESS_KEY,
  },
} as const;

export type Config = typeof config;