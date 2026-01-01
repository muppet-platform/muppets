import winston from 'winston';
import { config } from '@/config/environment';

const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss',
  }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    const logEntry = {
      timestamp,
      level,
      message,
      service: '{{muppet_name}}',
      environment: config.environment,
      ...meta,
    };
    return JSON.stringify(logEntry);
  })
);

export const logger = winston.createLogger({
  level: config.logging.level,
  format: logFormat,
  defaultMeta: {
    service: '{{muppet_name}}',
    environment: config.environment,
  },
  transports: [
    new winston.transports.Console({
      format: config.environment === 'development'
        ? winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        : logFormat,
    }),
  ],
});

// Add file transport for production
if (config.environment === 'production') {
  logger.add(new winston.transports.File({
    filename: 'logs/error.log',
    level: 'error',
    format: logFormat,
  }));
  
  logger.add(new winston.transports.File({
    filename: 'logs/combined.log',
    format: logFormat,
  }));
}

export default logger;