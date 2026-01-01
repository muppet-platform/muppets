import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { ValidationError, NotFoundError } from '@/middleware/errorHandler';
import { logger } from '@/utils/logger';

const router = Router();

// Validation schemas
const createItemSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
  category: z.string().optional(),
});

const updateItemSchema = z.object({
  name: z.string().min(1).max(100).optional(),
  description: z.string().optional(),
  category: z.string().optional(),
});

// Types
interface Item {
  id: string;
  name: string;
  description?: string;
  category?: string;
  createdAt: string;
  updatedAt: string;
}

// In-memory storage (replace with actual database in production)
const items: Map<string, Item> = new Map();

// Helper function to generate ID
const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};

// Validation middleware
const validateCreateItem = (req: Request, res: Response, next: NextFunction): void => {
  try {
    req.body = createItemSchema.parse(req.body);
    next();
  } catch (error) {
    if (error instanceof z.ZodError) {
      const firstError = error.errors[0];
      if (firstError) {
        next(new ValidationError(
          `${firstError.path.join('.')}: ${firstError.message}`,
          firstError.path.join('.')
        ));
      } else {
        next(new ValidationError('Validation failed'));
      }
    } else {
      next(error);
    }
  }
};

const validateUpdateItem = (req: Request, res: Response, next: NextFunction): void => {
  try {
    req.body = updateItemSchema.parse(req.body);
    next();
  } catch (error) {
    if (error instanceof z.ZodError) {
      const firstError = error.errors[0];
      if (firstError) {
        next(new ValidationError(
          `${firstError.path.join('.')}: ${firstError.message}`,
          firstError.path.join('.')
        ));
      } else {
        next(new ValidationError('Validation failed'));
      }
    } else {
      next(error);
    }
  }
};

// Routes

// GET /api/v1/items - List all items
router.get('/', (req: Request, res: Response) => {
  const itemList = Array.from(items.values());
  
  logger.info('Items retrieved', { count: itemList.length });
  
  res.json({
    success: true,
    data: itemList,
    count: itemList.length,
    timestamp: new Date().toISOString(),
  });
});

// GET /api/v1/items/:id - Get item by ID
router.get('/:id', (req: Request, res: Response, next: NextFunction) => {
  const { id } = req.params;
  
  if (!id) {
    return next(new ValidationError('Item ID is required'));
  }
  
  const item = items.get(id);
  
  if (!item) {
    return next(new NotFoundError('Item', id));
  }
  
  logger.info('Item retrieved', { itemId: id });
  
  res.json({
    success: true,
    data: item,
    timestamp: new Date().toISOString(),
  });
});

// POST /api/v1/items - Create new item
router.post('/', validateCreateItem, (req: Request, res: Response) => {
  const id = generateId();
  const now = new Date().toISOString();
  
  const item: Item = {
    id,
    name: req.body.name,
    description: req.body.description,
    category: req.body.category,
    createdAt: now,
    updatedAt: now,
  };
  
  items.set(id, item);
  
  logger.info('Item created', { itemId: id, name: item.name });
  
  res.status(201).json({
    success: true,
    data: item,
    timestamp: new Date().toISOString(),
  });
});

// PUT /api/v1/items/:id - Update item
router.put('/:id', validateUpdateItem, (req: Request, res: Response, next: NextFunction) => {
  const { id } = req.params;
  
  if (!id) {
    return next(new ValidationError('Item ID is required'));
  }
  
  const existingItem = items.get(id);
  
  if (!existingItem) {
    return next(new NotFoundError('Item', id));
  }
  
  const updatedItem: Item = {
    ...existingItem,
    ...req.body,
    updatedAt: new Date().toISOString(),
  };
  
  items.set(id, updatedItem);
  
  logger.info('Item updated', { itemId: id });
  
  res.json({
    success: true,
    data: updatedItem,
    timestamp: new Date().toISOString(),
  });
});

// DELETE /api/v1/items/:id - Delete item
router.delete('/:id', (req: Request, res: Response, next: NextFunction) => {
  const { id } = req.params;
  
  if (!id) {
    return next(new ValidationError('Item ID is required'));
  }
  
  const item = items.get(id);
  
  if (!item) {
    return next(new NotFoundError('Item', id));
  }
  
  items.delete(id);
  
  logger.info('Item deleted', { itemId: id });
  
  res.json({
    success: true,
    message: 'Item deleted successfully',
    timestamp: new Date().toISOString(),
  });
});

export { router as itemsRouter };