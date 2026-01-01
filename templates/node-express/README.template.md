# {{muppet_name}}

A Node.js Express microservice built with the Muppet Platform.

## Overview

{{muppet_name}} is a production-ready Node.js Express application with TypeScript support, comprehensive testing, and modern development tooling. It follows the Muppet Platform's "Simple by Default, Extensible by Choice" philosophy.

## Features

- **Node.js 20 LTS** with TypeScript support
- **Express.js** web framework with security middleware
- **Jest** testing framework with coverage reporting
- **ESLint & Prettier** for code quality and formatting
- **Health check endpoints** for monitoring
- **Structured logging** with Winston
- **ARM64 optimized** Docker containers
- **Production-ready** configuration

## Quick Start

### Prerequisites

- Node.js 20 LTS or higher
- npm 10 or higher

### Installation

```bash
# Initialize development environment
./scripts/init.sh

# Or manually:
npm ci
```

### Development

```bash
# Start development server with hot reload
npm run dev
# or
./scripts/run.sh --dev

# The server will be available at:
# http://localhost:3000
```

### Building

```bash
# Build for production
npm run build
# or
./scripts/build.sh
```

### Testing

```bash
# Run all tests with coverage
npm test
# or
./scripts/test.sh

# Run tests in watch mode
npm run test:watch
```

## API Endpoints

### Health Checks

- `GET /health` - Basic health status
- `GET /health/ready` - Readiness probe (includes dependency checks)
- `GET /health/live` - Liveness probe

### API

- `GET /api/v1` - API information
- `GET /api/v1/items` - List all items
- `POST /api/v1/items` - Create new item
- `GET /api/v1/items/:id` - Get item by ID
- `PUT /api/v1/items/:id` - Update item
- `DELETE /api/v1/items/:id` - Delete item

## Development Scripts

| Script | Description |
|--------|-------------|
| `./scripts/init.sh` | Initialize development environment |
| `./scripts/build.sh` | Build the application |
| `./scripts/run.sh` | Run with various options |
| `./scripts/test.sh` | Run tests with coverage |

### Run Script Options

```bash
./scripts/run.sh --dev      # Development mode (default)
./scripts/run.sh --prod     # Production mode
./scripts/run.sh --docker   # Docker mode
./scripts/run.sh --compose  # Docker Compose with LocalStack
```

## Docker

### Build and Run

```bash
# Build Docker image
docker build -t {{muppet_name}} .

# Run container
docker run -p 3000:3000 {{muppet_name}}
```

### Docker Compose (with LocalStack)

```bash
# Start all services
docker-compose -f docker-compose.local.yml up

# Stop services
docker-compose -f docker-compose.local.yml down
```

## Configuration

Configuration is managed through environment variables. Copy `.env.local` to `.env` and customize:

```bash
cp .env.local .env
```

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment (development/staging/production) | `development` |
| `PORT` | Server port | `3000` |
| `LOG_LEVEL` | Logging level (error/warn/info/debug) | `info` |
| `CORS_ALLOWED_ORIGINS` | CORS allowed origins | `*` |

## Testing

The application includes comprehensive testing:

- **Unit tests** for individual components
- **Integration tests** for API endpoints
- **Coverage reporting** with 70% minimum threshold
- **Custom Jest matchers** for API responses

### Running Tests

```bash
# All tests with coverage
npm test

# Watch mode
npm run test:watch

# Coverage only
npm run test:coverage
```

## Code Quality

### Linting and Formatting

```bash
# Check linting
npm run lint

# Fix linting issues
npm run lint:fix

# Check formatting
npm run format:check

# Format code
npm run format
```

### Pre-commit Checks

The build script runs:
1. ESLint for code quality
2. TypeScript compiler for type checking
3. Jest for testing
4. Build verification

## Deployment

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### AWS Deployment

Deployment is handled automatically through GitHub Actions:

- **Staging**: Push to `develop` branch
- **Production**: Push to `main` branch

The application will be available at:
- **Staging**: `https://{{muppet_name}}-staging.s3u.dev`
- **Production**: `https://{{muppet_name}}.s3u.dev`

## Monitoring

### Health Checks

- **Liveness**: `GET /health/live` - Basic application health
- **Readiness**: `GET /health/ready` - Includes dependency checks

### Logging

Structured JSON logging with Winston:

```typescript
import { logger } from '@/utils/logger';

logger.info('Operation completed', { 
  operation: 'create_item', 
  itemId: '123' 
});
```

### Metrics

Application metrics are automatically exported to CloudWatch in production:

- HTTP request metrics
- Response times
- Error rates
- Custom business metrics

## Architecture

```
src/
├── app.ts                 # Application entry point
├── config/
│   └── environment.ts     # Environment configuration
├── middleware/
│   ├── errorHandler.ts    # Error handling middleware
│   └── requestLogger.ts   # Request logging middleware
├── routes/
│   ├── health.ts          # Health check endpoints
│   ├── api.ts             # API router
│   └── items.ts           # Items CRUD endpoints
├── utils/
│   └── logger.ts          # Logging configuration
└── test/
    └── setup.ts           # Test configuration
```

## Security

- **Helmet.js** for security headers
- **CORS** configuration
- **Rate limiting** (100 requests per 15 minutes per IP)
- **Input validation** with Zod
- **Non-root Docker user**
- **Security scanning** in CI/CD

## Performance

- **ARM64 optimized** containers for cost efficiency
- **Multi-stage Docker builds** for smaller images
- **Compression middleware** for response optimization
- **Request logging** with performance metrics
- **Health check optimization** (excluded from logs)

## Troubleshooting

### Common Issues

1. **Port 3000 already in use**
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

2. **Node.js version issues**
   ```bash
   node -v  # Should be 20.x.x
   npm -v   # Should be 10.x.x
   ```

3. **Build failures**
   ```bash
   npm run clean
   npm ci
   npm run build
   ```

### Useful Commands

```bash
# Check application health
curl http://localhost:3000/health

# View logs (Docker)
docker logs {{muppet_name}}-dev

# Connect to container
docker exec -it {{muppet_name}}-dev /bin/sh

# Check dependencies
npm ls
```

## Contributing

1. Create feature branch from `main`
2. Make changes with tests
3. Run `./scripts/test.sh` to verify
4. Submit pull request
5. Deploy via CI/CD pipeline

## Resources

- [Express.js Documentation](https://expressjs.com/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Jest Testing Framework](https://jestjs.io/)
- [Node.js 20 LTS](https://nodejs.org/)
- [Muppet Platform Documentation](../../../docs/)

## License

MIT License - see LICENSE file for details.