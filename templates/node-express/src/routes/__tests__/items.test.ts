import request from 'supertest';
import { app } from '../../app';

describe('Items API', () => {
  describe('GET /api/v1/items', () => {
    it('should return empty list initially', async () => {
      const response = await request(app)
        .get('/api/v1/items')
        .expect(200);

      expect(response.body).toBeValidApiResponse();
      expect(response.body.data).toEqual([]);
      expect(response.body.count).toBe(0);
    });
  });

  describe('POST /api/v1/items', () => {
    it('should create a new item', async () => {
      const itemData = {
        name: 'Test Item',
        description: 'A test item',
        category: 'test',
      };

      const response = await request(app)
        .post('/api/v1/items')
        .send(itemData)
        .expect(201);

      expect(response.body).toBeValidApiResponse();
      expect(response.body.data).toMatchObject({
        id: expect.any(String),
        name: itemData.name,
        description: itemData.description,
        category: itemData.category,
        createdAt: expect.any(String),
        updatedAt: expect.any(String),
      });
    });

    it('should validate required fields', async () => {
      const response = await request(app)
        .post('/api/v1/items')
        .send({})
        .expect(400);

      expect(response.body).toBeValidErrorResponse();
      expect(response.body.code).toBe('VALIDATION_ERROR');
    });

    it('should validate name length', async () => {
      const response = await request(app)
        .post('/api/v1/items')
        .send({ name: '' })
        .expect(400);

      expect(response.body).toBeValidErrorResponse();
      expect(response.body.code).toBe('VALIDATION_ERROR');
    });
  });

  describe('GET /api/v1/items/:id', () => {
    let itemId: string;

    beforeEach(async () => {
      const createResponse = await request(app)
        .post('/api/v1/items')
        .send({
          name: 'Test Item',
          description: 'A test item',
        });
      itemId = createResponse.body.data.id;
    });

    it('should get item by id', async () => {
      const response = await request(app)
        .get(`/api/v1/items/${itemId}`)
        .expect(200);

      expect(response.body).toBeValidApiResponse();
      expect(response.body.data.id).toBe(itemId);
      expect(response.body.data.name).toBe('Test Item');
    });

    it('should return 404 for non-existent item', async () => {
      const response = await request(app)
        .get('/api/v1/items/nonexistent')
        .expect(404);

      expect(response.body).toBeValidErrorResponse();
      expect(response.body.code).toBe('NOT_FOUND');
    });
  });

  describe('PUT /api/v1/items/:id', () => {
    let itemId: string;

    beforeEach(async () => {
      const createResponse = await request(app)
        .post('/api/v1/items')
        .send({
          name: 'Test Item',
          description: 'A test item',
        });
      itemId = createResponse.body.data.id;
    });

    it('should update item', async () => {
      const updateData = {
        name: 'Updated Item',
        description: 'Updated description',
      };

      const response = await request(app)
        .put(`/api/v1/items/${itemId}`)
        .send(updateData)
        .expect(200);

      expect(response.body).toBeValidApiResponse();
      expect(response.body.data.name).toBe(updateData.name);
      expect(response.body.data.description).toBe(updateData.description);
      expect(response.body.data.updatedAt).not.toBe(response.body.data.createdAt);
    });

    it('should return 404 for non-existent item', async () => {
      const response = await request(app)
        .put('/api/v1/items/nonexistent')
        .send({ name: 'Updated' })
        .expect(404);

      expect(response.body).toBeValidErrorResponse();
      expect(response.body.code).toBe('NOT_FOUND');
    });
  });

  describe('DELETE /api/v1/items/:id', () => {
    let itemId: string;

    beforeEach(async () => {
      const createResponse = await request(app)
        .post('/api/v1/items')
        .send({
          name: 'Test Item',
          description: 'A test item',
        });
      itemId = createResponse.body.data.id;
    });

    it('should delete item', async () => {
      const response = await request(app)
        .delete(`/api/v1/items/${itemId}`)
        .expect(200);

      expect(response.body).toBeValidApiResponse();
      expect(response.body.message).toContain('deleted successfully');

      // Verify item is deleted
      await request(app)
        .get(`/api/v1/items/${itemId}`)
        .expect(404);
    });

    it('should return 404 for non-existent item', async () => {
      const response = await request(app)
        .delete('/api/v1/items/nonexistent')
        .expect(404);

      expect(response.body).toBeValidErrorResponse();
      expect(response.body.code).toBe('NOT_FOUND');
    });
  });
});