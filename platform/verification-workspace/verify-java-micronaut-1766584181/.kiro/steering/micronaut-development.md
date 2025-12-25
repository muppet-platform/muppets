# Micronaut Development Guide for verify-java-micronaut-1766584181

This guide provides Micronaut-specific development patterns and best practices for your verify-java-micronaut-1766584181 muppet.

## Project Structure

Your muppet follows the standard Micronaut project structure:

```
src/
├── main/
│   ├── java/com/muppetplatform/verify-java-micronaut-1766584181/
│   │   ├── Application.java              # Main application class
│   │   └── controller/                   # REST controllers
│   └── resources/
│       ├── application.yml               # Configuration
│       └── logback.xml                   # Logging configuration
└── test/
    └── java/com/muppetplatform/verify-java-micronaut-1766584181/
        └── controller/                   # Controller tests
```

## Development Workflow

### 1. Local Development
```bash
# Set up environment (first time only)
./scripts/init.sh

# Build the application
./scripts/build.sh

# Run tests
./scripts/test.sh

# Start locally (choose one)
./scripts/run.sh           # Run JAR directly
./scripts/run.sh --gradle  # Run with Gradle (hot reload)
./scripts/run.sh --docker  # Run with Docker
```

### 2. Adding New Endpoints

Create controllers in `src/main/java/com/muppetplatform/verify-java-micronaut-1766584181/controller/`:

```java
@Controller("/api/v1/items")
public class ItemController {
    
    @Get
    public HttpResponse<List<Item>> list() {
        // Implementation
    }
    
    @Post
    public HttpResponse<Item> create(@Body Item item) {
        // Implementation
    }
}
```

### 3. Configuration Management

Add configuration in `src/main/resources/application.yml`:

```yaml
verify-java-micronaut-1766584181:
  feature:
    enabled: true
    timeout: 30s
```

Access in code:
```java
@ConfigurationProperties("verify-java-micronaut-1766584181.feature")
public class FeatureConfig {
    private boolean enabled;
    private Duration timeout;
    // getters and setters
}
```

### 4. Testing Patterns

#### Controller Tests
```java
@MicronautTest
class ItemControllerTest {
    
    @Inject
    @Client("/")
    HttpClient client;
    
    @Test
    void testCreateItem() {
        // Test implementation
    }
}
```

#### Integration Tests
```java
@MicronautTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class ItemIntegrationTest {
    // Integration test implementation
}
```

## Micronaut Best Practices

### 1. Dependency Injection
- Use constructor injection when possible
- Use `@Singleton` for stateless services
- Use `@Prototype` for stateful beans

### 2. HTTP Clients
```java
@Client("https://api.external-service.com")
public interface ExternalServiceClient {
    
    @Get("/data/{id}")
    HttpResponse<Data> getData(@PathVariable String id);
}
```

### 3. Error Handling
```java
@Error(global = true)
public class GlobalErrorHandler {
    
    @Error
    public HttpResponse<JsonError> error(HttpRequest request, Throwable ex) {
        return HttpResponse.serverError(new JsonError("Internal error"));
    }
}
```

### 4. Validation
```java
@Controller("/api/items")
public class ItemController {
    
    @Post
    public HttpResponse<Item> create(@Body @Valid Item item) {
        // Validation happens automatically
    }
}
```

## Monitoring and Observability

### Health Checks
The template includes health check endpoints:
- `/health` - Overall health status
- `/health/ready` - Readiness probe
- `/health/live` - Liveness probe

### Metrics
Metrics are automatically exported to CloudWatch in production:
- HTTP request metrics
- JVM metrics
- Custom business metrics

Add custom metrics:
```java
@Inject
MeterRegistry meterRegistry;

public void recordBusinessMetric() {
    meterRegistry.counter("business.operation.count").increment();
}
```

### Logging
Use structured logging with SLF4J:
```java
private static final Logger log = LoggerFactory.getLogger(ItemController.class);

public void processItem(Item item) {
    log.info("Processing item: {}", item.getId());
}
```

## Deployment

### Local Testing
```bash
# Test with Docker
./scripts/run.sh --docker

# Test with Docker Compose (includes LocalStack)
./scripts/run.sh --compose
```

### AWS Deployment
Deployment is handled automatically through GitHub Actions:
- Push to `develop` → deploys to staging
- Push to `main` → deploys to production

Manual deployment:
```bash
cd terraform
terraform plan -var="muppet_name=verify-java-micronaut-1766584181" -var="environment=production"
terraform apply -var="muppet_name=verify-java-micronaut-1766584181" -var="environment=production"
```

## Troubleshooting

### Common Issues

1. **Port 3000 already in use**
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

2. **Gradle build fails**
   ```bash
   ./gradlew clean build --refresh-dependencies
   ```

3. **Docker build issues**
   ```bash
   docker system prune -f
   ./scripts/build.sh
   ```

### Useful Commands

```bash
# View application logs
docker logs verify-java-micronaut-1766584181-dev

# Connect to running container
docker exec -it verify-java-micronaut-1766584181-dev /bin/sh

# Check health endpoint
curl http://localhost:3000/health

# View Gradle dependencies
./gradlew dependencies
```

## Resources

- [Micronaut Documentation](https://docs.micronaut.io/)
- [Micronaut Guides](https://guides.micronaut.io/)
- [Java 21 Release Notes](https://openjdk.org/projects/jdk/21/)
- [Amazon Corretto 21](https://aws.amazon.com/corretto/)
- [Muppet Platform Documentation](https://github.com/muppet-platform/platform/docs)