# Performance Guidelines

## Overview

This document defines the performance standards, optimization techniques, and monitoring practices that all muppets must implement to ensure optimal performance across the platform. These guidelines cover response times, resource utilization, scalability, and performance testing.

## Performance Targets

### Response Time Requirements

**API Response Times (95th percentile)**
- Health checks: < 50ms
- Simple queries (single record): < 200ms
- Complex queries (multiple joins): < 500ms
- Data mutations (create/update): < 300ms
- Bulk operations: < 2000ms
- File uploads: < 5000ms (excluding transfer time)

**Database Query Performance**
- Simple SELECT queries: < 10ms
- Complex queries with joins: < 100ms
- Write operations: < 50ms
- Bulk operations: < 1000ms

**External Service Calls**
- Internal service calls: < 100ms
- Third-party API calls: < 2000ms
- Implement timeouts for all external calls
- Use circuit breakers for unreliable services

### Resource Utilization Targets

**CPU Utilization**
- Normal operation: < 70%
- Peak load: < 85%
- Sustained high load: < 80%
- Alert threshold: > 90% for 5 minutes

**Memory Utilization**
- Normal operation: < 70%
- Peak load: < 85%
- Memory leak detection: > 90% for 10 minutes
- Garbage collection impact: < 5% of CPU time

**Network Utilization**
- Bandwidth utilization: < 80% of available
- Connection pool utilization: < 80%
- Keep-alive connections preferred
- Implement connection pooling for databases

## Application Performance Optimization

### Database Optimization

**Query Optimization**
```sql
-- GOOD: Use indexes effectively
SELECT user_id, email FROM users 
WHERE status = 'active' AND created_at > '2024-01-01'
ORDER BY created_at DESC LIMIT 100;

-- BAD: Avoid SELECT *
SELECT * FROM users WHERE email LIKE '%@example.com';

-- GOOD: Use specific columns and proper indexing
SELECT user_id, email FROM users 
WHERE email_domain = 'example.com';
```

**Index Strategy**
- Create indexes on frequently queried columns
- Use composite indexes for multi-column queries
- Monitor index usage and remove unused indexes
- Consider partial indexes for filtered queries

**Connection Management**
```python
# Database connection pool configuration
DATABASE_CONFIG = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

# Use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    **DATABASE_CONFIG
)
```

### Caching Strategies

**Multi-Level Caching**
```python
import redis
from functools import wraps
import json

# Redis connection pool
redis_pool = redis.ConnectionPool(
    host='redis-cluster',
    port=6379,
    max_connections=50,
    decode_responses=True
)
redis_client = redis.Redis(connection_pool=redis_pool)

def cache_result(ttl=300, key_prefix=""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

@cache_result(ttl=600, key_prefix="user")
async def get_user_profile(user_id: str):
    """Get user profile with caching"""
    return await user_repository.get_by_id(user_id)
```

**Cache Invalidation Strategy**
```python
class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all user-related cache entries"""
        pattern = f"user:*:{user_id}*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
```

### Asynchronous Processing

**Background Job Processing**
```python
import asyncio
from celery import Celery

# Celery configuration for background tasks
celery_app = Celery(
    'muppet-tasks',
    broker='redis://redis-cluster:6379/0',
    backend='redis://redis-cluster:6379/0'
)

@celery_app.task
def process_large_dataset(dataset_id: str):
    """Process large dataset asynchronously"""
    # Heavy processing logic here
    pass

# In your API endpoint
async def trigger_processing(dataset_id: str):
    """Trigger asynchronous processing"""
    task = process_large_dataset.delay(dataset_id)
    return {"task_id": task.id, "status": "processing"}
```

**Async/Await Patterns**
```python
import asyncio
import aiohttp

async def fetch_multiple_services(service_calls):
    """Fetch data from multiple services concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_service_data(session, call['url'], call['params'])
            for call in service_calls
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def fetch_service_data(session, url, params):
    """Fetch data from a single service"""
    try:
        async with session.get(url, params=params, timeout=2.0) as response:
            return await response.json()
    except asyncio.TimeoutError:
        return {"error": "Service timeout"}
```

## Framework-Specific Optimizations

**Java Micronaut Performance**

**JVM Optimization**
```bash
# JVM flags for production
JAVA_OPTS="-Xms2g -Xmx4g \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \
  -XX:+UseStringDeduplication \
  -XX:+OptimizeStringConcat \
  -server"
```

**Micronaut Configuration**
```yaml
# application.yml
micronaut:
  server:
    thread-selection: AUTO
    netty:
      worker:
        threads: 16
      event-loops:
        default:
          num-threads: 8
  http:
    client:
      pool:
        enabled: true
        max-connections: 50
      read-timeout: 30s
      connect-timeout: 5s
```

**Connection Pooling**
```java
@ConfigurationProperties("datasource.default")
public class DatabaseConfig {
    
    @Bean
    public HikariConfig hikariConfig() {
        HikariConfig config = new HikariConfig();
        config.setMaximumPoolSize(20);
        config.setMinimumIdle(5);
        config.setConnectionTimeout(30000);
        config.setIdleTimeout(600000);
        config.setMaxLifetime(1800000);
        config.setLeakDetectionThreshold(60000);
        return config;
    }
}
```

## Monitoring and Metrics

### Application Metrics

**Key Performance Indicators**
```python
import time
from prometheus_client import Counter, Histogram, Gauge

# Metrics collection
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_database_connections', 'Active database connections')

def track_performance(func):
    """Decorator to track function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(method='GET', endpoint='/users', status='200').inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(method='GET', endpoint='/users', status='500').inc()
            raise
        finally:
            REQUEST_DURATION.observe(time.time() - start_time)
    return wrapper
```

**Custom Business Metrics**
```python
# Business-specific metrics
USER_REGISTRATIONS = Counter('user_registrations_total', 'Total user registrations')
ORDER_VALUE = Histogram('order_value_dollars', 'Order value in dollars')
ACTIVE_USERS = Gauge('active_users_current', 'Currently active users')

def track_user_registration(user_type: str):
    """Track user registration metrics"""
    USER_REGISTRATIONS.labels(type=user_type).inc()

def track_order_value(value: float):
    """Track order value metrics"""
    ORDER_VALUE.observe(value)
```

### Performance Monitoring

**Health Check Implementation**
```python
from fastapi import FastAPI, HTTPException
import asyncio
import time

app = FastAPI()

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    checks = {
        "database": await check_database_health(),
        "redis": await check_redis_health(),
        "external_services": await check_external_services(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }
    
    # Overall health status
    healthy = all(check["status"] == "healthy" for check in checks.values())
    
    return {
        "status": "healthy" if healthy else "unhealthy",
        "timestamp": time.time(),
        "checks": checks
    }

async def check_database_health():
    """Check database connectivity and performance"""
    try:
        start_time = time.time()
        await database.fetch_one("SELECT 1")
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy" if response_time < 100 else "degraded",
            "response_time_ms": response_time
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

**Performance Alerting**
```python
import logging
from datadog import DogStatsdClient

statsd = DogStatsdClient(host='localhost', port=8125)

class PerformanceMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def track_response_time(self, endpoint: str, duration: float):
        """Track and alert on response times"""
        statsd.histogram('api.response_time', duration, tags=[f'endpoint:{endpoint}'])
        
        # Alert on slow responses
        if duration > 1.0:  # 1 second threshold
            self.logger.warning(
                f"Slow response detected",
                extra={
                    "endpoint": endpoint,
                    "duration_ms": duration * 1000,
                    "alert_type": "performance"
                }
            )
    
    def track_error_rate(self, endpoint: str, status_code: int):
        """Track error rates"""
        statsd.increment('api.requests', tags=[
            f'endpoint:{endpoint}',
            f'status:{status_code}'
        ])
        
        # Alert on high error rates
        if status_code >= 500:
            self.logger.error(
                f"Server error detected",
                extra={
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "alert_type": "error"
                }
            )
```

## Load Testing and Capacity Planning

### Load Testing Strategy

**Test Types**
- **Load Testing**: Normal expected load
- **Stress Testing**: Beyond normal capacity
- **Spike Testing**: Sudden load increases
- **Volume Testing**: Large amounts of data
- **Endurance Testing**: Extended periods

**Load Testing Tools**
```python
# Example using locust for load testing
from locust import HttpUser, task, between

class MuppetUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login user"""
        response = self.client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(3)
    def get_user_profile(self):
        """Get user profile - most common operation"""
        self.client.get("/users/me")
    
    @task(1)
    def update_user_profile(self):
        """Update user profile - less common operation"""
        self.client.put("/users/me", json={
            "name": "Updated Name"
        })
    
    @task(2)
    def list_items(self):
        """List items with pagination"""
        self.client.get("/items?page=1&limit=20")
```

**Performance Benchmarks**
```bash
# Run load test
locust -f load_test.py --host=https://api.muppet.com --users=100 --spawn-rate=10 --run-time=300s

# Expected results:
# - 95th percentile response time < 500ms
# - Error rate < 1%
# - Throughput > 1000 requests/second
# - CPU utilization < 80%
# - Memory utilization < 70%
```

### Capacity Planning

**Resource Scaling Guidelines**
```yaml
# Kubernetes HPA configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: muppet-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: muppet-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Database Scaling Strategy**
```python
# Read replica configuration
DATABASE_URLS = {
    'write': 'postgresql://user:pass@primary-db:5432/db',
    'read': [
        'postgresql://user:pass@replica1-db:5432/db',
        'postgresql://user:pass@replica2-db:5432/db'
    ]
}

class DatabaseRouter:
    def __init__(self):
        self.write_db = Database(DATABASE_URLS['write'])
        self.read_dbs = [Database(url) for url in DATABASE_URLS['read']]
        self.read_index = 0
    
    def get_read_db(self):
        """Round-robin read replica selection"""
        db = self.read_dbs[self.read_index]
        self.read_index = (self.read_index + 1) % len(self.read_dbs)
        return db
    
    def get_write_db(self):
        """Get write database"""
        return self.write_db
```

## Performance Testing

### Automated Performance Testing

**CI/CD Integration**
```yaml
# GitHub Actions performance test
name: Performance Tests
on:
  pull_request:
    branches: [main]

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Start test environment
      run: docker-compose -f docker-compose.test.yml up -d
    
    - name: Run performance tests
      run: |
        pip install locust
        locust -f tests/performance/load_test.py \
          --host=http://localhost:8000 \
          --users=50 \
          --spawn-rate=5 \
          --run-time=60s \
          --headless \
          --csv=results
    
    - name: Validate performance metrics
      run: |
        python tests/performance/validate_results.py results_stats.csv
```

**Performance Regression Detection**
```python
import pandas as pd
import sys

def validate_performance_results(results_file: str):
    """Validate performance test results against benchmarks"""
    df = pd.read_csv(results_file)
    
    # Performance thresholds
    thresholds = {
        'average_response_time': 500,  # ms
        '95th_percentile': 1000,       # ms
        'failure_rate': 1.0,           # %
        'requests_per_second': 100     # minimum RPS
    }
    
    failures = []
    
    # Check average response time
    avg_response = df['Average Response Time'].mean()
    if avg_response > thresholds['average_response_time']:
        failures.append(f"Average response time {avg_response}ms exceeds {thresholds['average_response_time']}ms")
    
    # Check 95th percentile
    p95_response = df['95%'].mean()
    if p95_response > thresholds['95th_percentile']:
        failures.append(f"95th percentile {p95_response}ms exceeds {thresholds['95th_percentile']}ms")
    
    # Check failure rate
    failure_rate = df['Failure Rate'].mean()
    if failure_rate > thresholds['failure_rate']:
        failures.append(f"Failure rate {failure_rate}% exceeds {thresholds['failure_rate']}%")
    
    if failures:
        print("Performance test failures:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("All performance tests passed!")

if __name__ == "__main__":
    validate_performance_results(sys.argv[1])
```

## Optimization Techniques

### Code-Level Optimizations

**Algorithm Optimization**
```python
# SLOW: O(n²) nested loops
def find_common_elements_slow(list1, list2):
    common = []
    for item1 in list1:
        for item2 in list2:
            if item1 == item2:
                common.append(item1)
    return common

# FAST: O(n) using sets
def find_common_elements_fast(list1, list2):
    return list(set(list1) & set(list2))

# MEMORY EFFICIENT: Generator for large datasets
def find_common_elements_generator(list1, list2):
    set2 = set(list2)
    for item in list1:
        if item in set2:
            yield item
```

**Memory Optimization**
```python
import sys
from typing import Iterator

def process_large_file_memory_efficient(filename: str) -> Iterator[dict]:
    """Process large files without loading everything into memory"""
    with open(filename, 'r') as file:
        for line in file:
            # Process one line at a time
            data = json.loads(line)
            yield process_record(data)

# Use __slots__ to reduce memory usage
class OptimizedUser:
    __slots__ = ['id', 'email', 'name', 'created_at']
    
    def __init__(self, id: str, email: str, name: str, created_at: datetime):
        self.id = id
        self.email = email
        self.name = name
        self.created_at = created_at
```

### Infrastructure Optimizations

**CDN Configuration**
```yaml
# CloudFront distribution for static assets
Resources:
  CDNDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Enabled: true
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # Managed-CachingOptimized
          Compress: true
        CacheBehaviors:
          - PathPattern: "/api/*"
            TargetOriginId: APIOrigin
            ViewerProtocolPolicy: https-only
            CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad
            TTL: 300  # 5 minutes for API responses
```

**Database Optimization**
```sql
-- Create appropriate indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_orders_user_created ON orders(user_id, created_at);
CREATE INDEX CONCURRENTLY idx_products_category_price ON products(category_id, price) WHERE active = true;

-- Optimize queries with EXPLAIN ANALYZE
EXPLAIN ANALYZE SELECT u.id, u.email, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.email
ORDER BY order_count DESC
LIMIT 100;
```

## Troubleshooting Performance Issues

### Performance Debugging

**Profiling Tools**
```python
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """Decorator to profile function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(10)  # Top 10 functions
    
    return wrapper

@profile_function
def slow_function():
    """Function to profile"""
    # Your code here
    pass
```

**Memory Profiling**
```python
import tracemalloc
import psutil
import os

def monitor_memory_usage():
    """Monitor memory usage of the current process"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'percent': process.memory_percent()
    }

# Enable memory tracing
tracemalloc.start()

# Your application code here

# Get memory statistics
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

### Common Performance Issues

**Database N+1 Problem**
```python
# BAD: N+1 queries
async def get_users_with_orders_bad():
    users = await User.all()
    for user in users:
        user.orders = await Order.filter(user_id=user.id)  # N additional queries
    return users

# GOOD: Single query with join
async def get_users_with_orders_good():
    return await User.all().prefetch_related('orders')
```

**Memory Leaks**
```python
# BAD: Circular references
class Parent:
    def __init__(self):
        self.children = []
    
    def add_child(self, child):
        child.parent = self  # Circular reference
        self.children.append(child)

# GOOD: Use weak references
import weakref

class Parent:
    def __init__(self):
        self.children = []
    
    def add_child(self, child):
        child.parent = weakref.ref(self)  # Weak reference
        self.children.append(child)
```

## Compliance and Standards

### Performance SLAs

**Service Level Agreements**
- API availability: 99.9% uptime
- Response time: 95th percentile < 500ms
- Error rate: < 0.1% for 4xx/5xx errors
- Recovery time: < 5 minutes for service restoration

### Performance Reporting

**Monthly Performance Reports**
- Response time trends and percentiles
- Error rate analysis and root causes
- Resource utilization patterns
- Capacity planning recommendations
- Performance optimization achievements

## Resources and Tools

### Performance Monitoring Tools

**Application Performance Monitoring (APM)**
- New Relic: Full-stack performance monitoring
- Datadog: Infrastructure and application monitoring
- AWS X-Ray: Distributed tracing for AWS services

**Database Monitoring**
- pganalyze: PostgreSQL performance insights
- MongoDB Compass: MongoDB performance monitoring
- AWS RDS Performance Insights: Database performance tuning

**Load Testing Tools**
- Locust: Python-based load testing
- JMeter: Java-based performance testing
- k6: Modern load testing tool

### Performance Libraries

**Java**
- Micrometer: Application metrics collection
- JProfiler: Java application profiling
- VisualVM: JVM monitoring and profiling

## Updates and Maintenance

This document is maintained by the platform team and updated based on:
- Performance monitoring insights
- New optimization techniques
- Framework performance improvements
- Infrastructure scaling experiences
- Industry performance best practices

Updates are automatically distributed to all muppets through the steering management system.