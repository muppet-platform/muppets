import { Request, Response, NextFunction } from 'express';
import { logger } from '@/utils/logger';
import { config } from '@/config/environment';

export interface ApiError extends Error {
  statusCode?: number;
  code?: string;
  field?: string;
}

export class ValidationError extends Error implements ApiError {
  statusCode = 400;
  code = 'VALIDATION_ERROR';
  field?: string;
  
  constructor(message: string, field?: string) {
    super(message);
    this.name = 'ValidationError';
    if (field !== undefined) {
      this.field = field;
    }
  }
}

export class NotFoundError extends Error implements ApiError {
  statusCode = 404;
  code = 'NOT_FOUND';
  
  constructor(resource: string, id?: string) {
    super(id ? `${resource} with id ${id} not found` : `${resource} not found`);
    this.name = 'NotFoundError';
  }
}

export class UnauthorizedError extends Error implements ApiError {
  statusCode = 401;
  code = 'UNAUTHORIZED';
  
  constructor(message = 'Unauthorized') {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

export class ForbiddenError extends Error implements ApiError {
  statusCode = 403;
  code = 'FORBIDDEN';
  
  constructor(message = 'Forbidden') {
    super(message);
    this.name = 'ForbiddenError';
  }
}

export const errorHandler = (
  err: ApiError,
  req: Request,
  res: Response,
  _next: NextFunction
): void => {
  // Log error details
  logger.error('Request error', {
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    statusCode: err.statusCode || 500,
    code: err.code,
    field: err.field,
    userAgent: req.get('User-Agent'),
    ip: req.ip,
  });

  // Handle specific error types
  if (err instanceof ValidationError) {
    res.status(400).json({
      success: false,
      error: err.message,
      code: err.code,
      field: err.field,
    });
    return;
  }

  if (err instanceof NotFoundError) {
    res.status(404).json({
      success: false,
      error: err.message,
      code: err.code,
    });
    return;
  }

  if (err instanceof UnauthorizedError) {
    res.status(401).json({
      success: false,
      error: err.message,
      code: err.code,
    });
    return;
  }

  if (err instanceof ForbiddenError) {
    res.status(403).json({
      success: false,
      error: err.message,
      code: err.code,
    });
    return;
  }

  // Handle known HTTP errors
  if (err.statusCode && err.statusCode >= 400 && err.statusCode < 500) {
    res.status(err.statusCode).json({
      success: false,
      error: err.message,
      code: err.code || 'CLIENT_ERROR',
    });
    return;
  }

  // Generic server error
  const statusCode = err.statusCode || 500;
  const message = config.environment === 'production' 
    ? 'Internal server error' 
    : err.message;

  res.status(statusCode).json({
    success: false,
    error: message,
    code: err.code || 'INTERNAL_ERROR',
    ...(config.environment !== 'production' && { stack: err.stack }),
  });
};