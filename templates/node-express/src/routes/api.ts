import { Router } from 'express';
import { itemsRouter } from './items';

const router = Router();

// Mount sub-routers
router.use('/items', itemsRouter);

// API info endpoint
router.get('/', (req, res) => {
  res.json({
    success: true,
    message: '{{muppet_name}} API v1',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      items: '/api/v1/items',
    },
    timestamp: new Date().toISOString(),
  });
});

export { router as apiRouter };