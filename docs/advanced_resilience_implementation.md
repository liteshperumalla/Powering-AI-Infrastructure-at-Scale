# Advanced Resilience System Implementation

## Overview

The advanced resilience system provides comprehensive error handling, circuit breakers, fallback mechanisms, and sophisticated rate limiting for the Infra Mind platform. This system ensures reliable operation even when external cloud APIs fail or become unavailable.

## Architecture Components

### 1. Circuit Breaker Pattern

**File**: `src/infra_mind/core/resilience.py`

The circuit breaker prevents cascading failures by temporarily blocking requests to failing services.

#### States
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service is failing, requests are blocked
- **HALF_OPEN**: Testing if service has recovered

#### Configuration
```python
CircuitBreakerConfig(
    failure_threshold=5,      # Failures before opening
    recovery_timeout=60,      # Seconds before trying half-open
    success_threshold=3,      # Successes to close from half-open
    timeout=30.0,            # Request timeout in seconds
    expected_exceptions=(Exception,)  # Exceptions that count as failures
)
```

#### Usage
```python
from src.infra_mind.core.resilience import resilience_manager

async with resilience_manager.resilient_call("aws_pricing") as execute:
    result = await execute(lambda: aws_client.get_pricing())
```

### 2. Retry Mechanism

**File**: `src/infra_mind/core/resilience.py`

Implements intelligent retry strategies with exponential backoff and jitter.

#### Features
- Exponential backoff with configurable base and maximum delays
- Jitter to prevent thundering herd problems
- Configurable retry attempts and retryable exceptions
- Detailed logging of retry attempts

#### Configuration
```python
RetryConfig(
    max_attempts=3,
    base_delay=1.0,           # Base delay in seconds
    max_delay=60.0,           # Maximum delay in seconds
    exponential_base=2.0,     # Exponential backoff base
    jitter=True,              # Add random jitter
    retryable_exceptions=(Exception,)
)
```

### 3. Fallback Manager

**File**: `src/infra_mind/core/resilience.py`

Provides multiple fallback strategies when primary services fail.

#### Fallback Strategies (in order of preference)
1. **Recent Fallback Cache**: Recently cached successful responses
2. **Stale Cache Data**: Older cached data with staleness warnings
3. **Default Data**: Predefined fallback data
4. **Degraded Mode**: Minimal functionality with clear limitations

#### Configuration
```python
FallbackConfig(
    enable_cache_fallback=True,
    cache_staleness_threshold=3600,  # 1 hour
    enable_default_fallback=True,
    fallback_data_ttl=300,          # 5 minutes
    enable_degraded_mode=True
)
```

### 4. Advanced Rate Limiting

**File**: `src/infra_mind/core/advanced_rate_limiter.py`

Sophisticated rate limiting with multiple algorithms and adaptive behavior.

#### Algorithms

##### Sliding Window
- Maintains a sliding window of requests
- Precise rate limiting with Redis sorted sets
- Good for consistent rate enforcement

##### Token Bucket
- Allows burst traffic up to bucket capacity
- Refills tokens at configured rate
- Good for handling traffic spikes

##### Adaptive Rate Limiting
- Adjusts limits based on success rates
- Reduces limits when success rate drops
- Increases limits when performance improves

#### Configuration
```python
# Sliding Window
RateLimitConfig(
    algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
    requests_per_minute=100,
    window_size=60
)

# Token Bucket
RateLimitConfig(
    algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
    requests_per_minute=100,
    burst_capacity=20,
    refill_rate=1.67  # tokens per second
)

# Adaptive
RateLimitConfig(
    algorithm=RateLimitAlgorithm.ADAPTIVE,
    requests_per_minute=100,
    adaptive_threshold=0.8,
    backoff_factor=0.7,
    recovery_factor=1.2
)
```

## Integration with Cloud Services

### Enhanced Cache Manager

**File**: `src/infra_mind/core/cache.py`

The cache manager has been enhanced to support:
- Stale data retrieval for fallback purposes
- Cache invalidation for specific entries
- Better staleness detection and metadata

### Base Cloud Client Integration

**File**: `src/infra_mind/cloud/base.py`

The base cloud client now uses the resilience system:
- Automatic circuit breaker protection
- Retry mechanisms for transient failures
- Fallback to cached data when APIs fail
- Advanced rate limiting integration

## Usage Examples

### Basic Resilient Call

```python
from src.infra_mind.core.resilience import resilience_manager

async with resilience_manager.resilient_call(
    service_name="aws_pricing",
    fallback_key="aws_pricing_us_east_1",
    default_data={"services": [], "degraded": True}
) as execute:
    result = await execute(lambda: aws_client.get_pricing())
    
    print(f"Data source: {result['source']}")
    print(f"Fallback used: {result['fallback_used']}")
    print(f"Degraded mode: {result['degraded_mode']}")
```

### Rate Limiting

```python
from src.infra_mind.core.advanced_rate_limiter import advanced_rate_limiter

try:
    await advanced_rate_limiter.check_rate_limit("aws_pricing")
    # Proceed with API call
    result = await aws_client.get_pricing()
except RateLimitExceeded as e:
    print(f"Rate limited, retry after {e.retry_after} seconds")
```

### Service Configuration

```python
from src.infra_mind.core.resilience import configure_service_resilience

configure_service_resilience(
    "custom_service",
    failure_threshold=3,
    recovery_timeout=30,
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0
)
```

## Monitoring and Health Checks

### Circuit Breaker Health

```python
from src.infra_mind.core.resilience import resilience_manager

# Get health of specific service
health = resilience_manager.get_service_health("aws_pricing")
print(f"State: {health['state']}")
print(f"Failures: {health['failure_count']}")

# Get health of all services
all_health = resilience_manager.get_all_services_health()
```

### Rate Limiting Status

```python
from src.infra_mind.core.advanced_rate_limiter import advanced_rate_limiter

status = await advanced_rate_limiter.get_rate_limit_status("aws_pricing")
print(f"Algorithm: {status['algorithm']}")
print(f"Current limit: {status['requests_per_minute']}")
print(f"Success rate: {status['success_rate']}")
```

## Error Handling Patterns

### Exception Hierarchy

```python
# Base resilience exceptions
CircuitBreakerError      # Circuit breaker is open
RetryExhaustedError     # All retry attempts failed
FallbackError           # All fallback strategies failed
RateLimitExceeded       # Rate limit exceeded

# Cloud service exceptions (from base.py)
CloudServiceError       # Base cloud service error
RateLimitError         # Rate limiting error
AuthenticationError    # Authentication failure
ServiceUnavailableError # Service unavailable
```

### Error Response Format

```python
{
    "data": None,
    "source": "error",
    "fallback_used": False,
    "degraded_mode": False,
    "warnings": ["Service call failed: Connection timeout"],
    "error": "Connection timeout after 30 seconds"
}
```

## Configuration

### Environment Variables

```bash
# Redis configuration for caching and rate limiting
REDIS_URL=redis://localhost:6379

# Rate limiting defaults
AWS_RATE_LIMIT=20
AZURE_RATE_LIMIT=100
GCP_RATE_LIMIT=60

# Circuit breaker defaults
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

### Initialization

```python
from src.infra_mind.core.cache import init_cache
from src.infra_mind.core.advanced_rate_limiter import init_advanced_rate_limiter
from src.infra_mind.core.resilience import init_cloud_service_resilience

# Initialize all resilience systems
await init_cache()
await init_advanced_rate_limiter()
init_cloud_service_resilience()
```

## Testing

### Unit Tests

**File**: `tests/test_advanced_resilience.py`

Comprehensive tests covering:
- Circuit breaker state transitions
- Retry mechanism with various failure patterns
- Fallback strategy execution
- Rate limiting algorithms
- Integration between components

### Running Tests

```bash
# Run all resilience tests
python -m pytest tests/test_advanced_resilience.py -v

# Run specific test class
python -m pytest tests/test_advanced_resilience.py::TestCircuitBreaker -v

# Run with coverage
python -m pytest tests/test_advanced_resilience.py --cov=src.infra_mind.core
```

### Demo Script

**File**: `demo_advanced_resilience.py`

Interactive demonstration of all resilience features:

```bash
python demo_advanced_resilience.py
```

## Performance Considerations

### Memory Usage
- Circuit breakers maintain minimal state (counters, timestamps)
- Rate limiters use Redis for distributed state
- Fallback cache has configurable TTL and cleanup

### Latency Impact
- Circuit breaker checks: ~0.1ms
- Rate limit checks: ~1-5ms (Redis roundtrip)
- Retry delays: Configurable exponential backoff
- Fallback retrieval: ~1-10ms depending on source

### Scalability
- Circuit breakers scale with number of services
- Rate limiting scales horizontally with Redis
- Fallback mechanisms are stateless

## Best Practices

### Service Configuration
1. Set failure thresholds based on service reliability
2. Configure recovery timeouts based on typical outage duration
3. Use appropriate retry delays for service characteristics
4. Enable fallback mechanisms for critical paths

### Rate Limiting
1. Use sliding window for precise rate control
2. Use token bucket for bursty traffic patterns
3. Use adaptive limiting for variable load services
4. Monitor success rates for adaptive tuning

### Monitoring
1. Track circuit breaker state changes
2. Monitor rate limiting effectiveness
3. Alert on excessive fallback usage
4. Track service success rates

### Error Handling
1. Always handle CircuitBreakerError gracefully
2. Provide meaningful error messages to users
3. Log detailed error information for debugging
4. Use appropriate HTTP status codes in APIs

## Future Enhancements

### Planned Features
1. **Bulkhead Pattern**: Isolate resources for different service types
2. **Health Check Integration**: Automatic service health monitoring
3. **Metrics Dashboard**: Real-time resilience metrics visualization
4. **Configuration Hot-Reload**: Dynamic configuration updates
5. **Multi-Region Failover**: Automatic failover to different regions

### Extensibility
The resilience system is designed for easy extension:
- New rate limiting algorithms can be added
- Custom fallback strategies can be implemented
- Additional circuit breaker configurations supported
- Integration with external monitoring systems

## Troubleshooting

### Common Issues

#### Circuit Breaker Stuck Open
- Check service health manually
- Verify recovery timeout configuration
- Reset circuit breaker if needed: `resilience_manager.reset_service("service_name")`

#### Rate Limiting Too Aggressive
- Check success rates: `advanced_rate_limiter.get_rate_limit_status("service")`
- Adjust adaptive thresholds
- Consider using token bucket for burst tolerance

#### Fallback Data Stale
- Check cache TTL configuration
- Verify cache invalidation on data updates
- Monitor cache hit/miss ratios

#### High Latency
- Review retry configurations (reduce max_delay)
- Check Redis connection performance
- Consider disabling jitter in low-latency scenarios

### Debug Logging

Enable debug logging for detailed resilience information:

```python
import logging
logging.getLogger('src.infra_mind.core.resilience').setLevel(logging.DEBUG)
logging.getLogger('src.infra_mind.core.advanced_rate_limiter').setLevel(logging.DEBUG)
```

This comprehensive resilience system ensures the Infra Mind platform remains reliable and performant even when external dependencies fail or become unavailable.