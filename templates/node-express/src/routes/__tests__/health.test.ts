import request from 'supertest';
import { app } from '../../app';

describe('Health Routes', () => {
  describe('GET /health', () => {
    it('should return healthy status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toMatchObject({
        status: 'healthy',
        version: '1.0.0',
        environment: expect.any(String),
        timestamp: expect.any(String),
        uptime: expect.any(Number),
      });
    });
  });

  describe('GET /health/ready', () => {
    it('should return readiness status', async () => {
      const response = await request(app)
        .get('/health/ready')
        .expect(200);

      expect(response.body).toMatchObject({
        status: 'healthy',
        version: '1.0.0',
        environment: expect.any(String),
        timestamp: expect.any(String),
        uptime: expect.any(Number),
      });
    });
  });

  describe('GET /health/live', () => {
    it('should return liveness status', async () => {
      const response = await request(app)
        .get('/health/live')
        .expect(200);

      expect(response.body).toMatchObject({
        status: 'healthy',
        version: '1.0.0',
        environment: expect.any(String),
        timestamp: expect.any(String),
        uptime: expect.any(Number),
      });
    });
  });
});