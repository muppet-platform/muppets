import { logger } from '@/utils/logger';

// Suppress logs during testing
logger.silent = true;

// Global test setup
beforeAll((): void => {
  // Set test environment
  process.env.NODE_ENV = 'test';
});

afterAll((): void => {
  // Cleanup after all tests
});

// Global test utilities
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeValidApiResponse(): R;
      toBeValidErrorResponse(): R;
    }
  }
}

// Custom Jest matchers
expect.extend({
  toBeValidApiResponse(received): jest.CustomMatcherResult {
    const pass = 
      typeof received === 'object' &&
      received !== null &&
      typeof received.success === 'boolean' &&
      received.success === true &&
      typeof received.timestamp === 'string';

    if (pass) {
      return {
        message: (): string => `expected ${JSON.stringify(received)} not to be a valid API response`,
        pass: true,
      };
    } else {
      return {
        message: (): string => `expected ${JSON.stringify(received)} to be a valid API response with success: true and timestamp`,
        pass: false,
      };
    }
  },

  toBeValidErrorResponse(received): jest.CustomMatcherResult {
    const pass = 
      typeof received === 'object' &&
      received !== null &&
      typeof received.success === 'boolean' &&
      received.success === false &&
      typeof received.error === 'string';

    if (pass) {
      return {
        message: (): string => `expected ${JSON.stringify(received)} not to be a valid error response`,
        pass: true,
      };
    } else {
      return {
        message: (): string => `expected ${JSON.stringify(received)} to be a valid error response with success: false and error message`,
        pass: false,
      };
    }
  },
});