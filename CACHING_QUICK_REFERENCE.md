# Multi-Layer Caching - Quick Reference Guide

**Phase 2 Week 7-8 - November 12, 2025**

---

## 🚀 Quick Start

### Using Caching in Your Endpoints

```python
from ...core.dependencies import CacheManagerDep

@router.get("/your-endpoint")
async def your_endpoint(
    cache: CacheManagerDep = None  # Optional dependency
):
    # 1. Try cache first
    cache_key = "your:cache:key"
    if cache:
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data

    # 2. Cache miss - query database
    data = await database.query()

    # 3. Store in cache
    if cache:
        await cache.set(cache_key, data, ttl=300)  # 5 minutes

    return data
```

---

## 📋 Cache Key Patterns

| Endpoint | Cache Key Pattern | TTL | Example |
|----------|------------------|-----|---------|
| Assessment Detail | `assessment:{id}:details` | 60s or 300s | `assessment:123:details` |
| Recommendations | `recommendations:{id}:list` | 300s | `recommendations:456:list` |
| Dashboard | `dashboard:overview:{user_id}` | 60s | `dashboard:overview:789` |
| User Profile | `user:{id}:profile` | 300s | `user:abc:profile` |

---

## ⚡ Performance Expectations

| Cache Layer | Hit Rate | Response Time | When It Happens |
|------------|----------|---------------|-----------------|
| **L1 (Memory)** | 80% | <1ms | Data recently accessed on same instance |
| **L2 (Redis)** | 15% | <5ms | Data accessed on different instance |
| **Database** | 5% | 50-200ms | First access or expired cache |

---

## 🔄 Cache Invalidation

### Automatic Invalidation

```python
@router.put("/{resource_id}")
async def update_resource(
    resource_id: str,
    cache: CacheManagerDep = None
):
    # Update database
    await resource.save()

    # Invalidate cache
    if cache:
        await cache.delete(f"resource:{resource_id}:details")
```

### Pattern-Based Invalidation

```python
# Delete all user-related caches
await cache.delete_pattern("user:123:*")

# Delete all assessment caches
await cache.delete_pattern("assessment:*")
```

### Manual Cache Clearing

```bash
# Clear all caches (requires authentication)
curl -X POST http://localhost:8000/api/v2/cache-demo/clear \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 Best Practices

### ✅ DO

1. **Use cache for read-heavy endpoints**
   ```python
   # Good: Frequently read, rarely updated
   cache_key = f"report:{report_id}:pdf"
   ```

2. **Set appropriate TTLs**
   ```python
   # Changing data: 30-60s
   await cache.set(key, data, ttl=60)

   # Stable data: 5-15 minutes
   await cache.set(key, data, ttl=300)
   ```

3. **Invalidate on updates**
   ```python
   await resource.save()
   await cache.delete(cache_key)
   ```

4. **Use smart caching**
   ```python
   # Only cache unfiltered requests
   if cache and not any([filter1, filter2]):
       await cache.set(key, data)
   ```

### ❌ DON'T

1. **Don't cache filtered results**
   ```python
   # Bad: Too many unique cache keys
   cache_key = f"users:{status}:{role}:{page}:{limit}"
   ```

2. **Don't cache sensitive data without encryption**
   ```python
   # Bad: Caching passwords
   await cache.set(f"user:{id}:password", password)
   ```

3. **Don't forget to handle cache misses**
   ```python
   # Bad: No fallback
   return await cache.get(key)

   # Good: Always have fallback
   cached = await cache.get(key)
   return cached if cached else await db.query()
   ```

4. **Don't use very long TTLs for changing data**
   ```python
   # Bad: 1 hour TTL for frequently updated data
   await cache.set(key, user_status, ttl=3600)
   ```

---

## 🧪 Testing Cache Performance

### Test 1: Performance Comparison

```bash
# Test with 10 iterations
curl "http://localhost:8000/api/v2/cache-demo/test/performance?iterations=10"
```

**Expected Output:**
```json
{
    "performance_improvement": {
        "speedup_factor": "3.0x faster",
        "time_saved_percentage": "66.4%"
    }
}
```

### Test 2: Hit Rate Simulation

```bash
# Simulate 100 requests with 80/20 pattern
curl "http://localhost:8000/api/v2/cache-demo/test/hit-rate?requests=100"
```

**Expected Output:**
```json
{
    "cache_statistics": {
        "hit_rate": 60.0
    },
    "conclusions": {
        "effectiveness": "good"
    }
}
```

### Test 3: Cache Statistics

```bash
# View current cache stats (requires auth)
curl "http://localhost:8000/api/v2/cache-demo/stats" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔧 Troubleshooting

### Cache Not Working?

**Check 1: Is cache manager initialized?**
```python
if cache is None:
    logger.warning("Cache manager not available")
```

**Check 2: Is Redis running?**
```bash
docker-compose ps redis
# Should show "Up"
```

**Check 3: Check cache stats**
```bash
curl "http://localhost:8000/api/v2/cache-demo/stats"
# Look for "cache_enabled": true
```

### Cache Hit Rate Too Low?

**Possible Causes:**
1. **Too many filters** - Only cache unfiltered requests
2. **TTL too short** - Increase TTL for stable data
3. **High write rate** - Cache invalidation happening too often
4. **Cold cache** - Normal after restart, will improve

**Solutions:**
```python
# 1. Only cache unfiltered requests
if not any([filter1, filter2, filter3]):
    await cache.set(key, data)

# 2. Increase TTL for stable data
await cache.set(key, data, ttl=600)  # 10 minutes

# 3. Use smart invalidation
# Only invalidate specific keys, not patterns
await cache.delete(f"resource:{id}")
```

### Cache Stale Data?

**Solution: Decrease TTL or improve invalidation**
```python
# Shorter TTL
await cache.set(key, data, ttl=30)  # 30 seconds

# Better invalidation
@router.put("/{id}")
async def update(id: str, cache: CacheManagerDep = None):
    await resource.save()

    # Invalidate all related caches
    if cache:
        await cache.delete(f"resource:{id}:details")
        await cache.delete(f"resource:{id}:summary")
```

---

## 📊 Monitoring

### Key Metrics to Watch

1. **Cache Hit Rate** - Target: 70%+
   ```
   hit_rate = (l1_hits + l2_hits) / total_requests * 100
   ```

2. **Response Time** - Target: <5ms
   ```
   avg_response_time = sum(response_times) / total_requests
   ```

3. **Database Load** - Target: <20% of pre-cache load
   ```
   db_load_reduction = (1 - db_queries / total_requests) * 100
   ```

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Cache Hit Rate | <50% | <30% |
| L1 Response Time | >5ms | >10ms |
| L2 Response Time | >10ms | >20ms |
| Cache Errors | >1% | >5% |

---

## 🔐 Security Considerations

### Sensitive Data

**DO:**
- Encrypt sensitive data before caching
- Use short TTLs for sensitive data (30-60s)
- Implement cache access controls
- Log cache access for audit trails

**DON'T:**
- Cache passwords or credentials
- Cache PII without encryption
- Use predictable cache keys
- Cache data beyond authorization scope

### Example: Secure Caching

```python
@router.get("/sensitive-data/{id}")
async def get_sensitive_data(
    id: str,
    current_user: User = Depends(get_current_user),
    cache: CacheManagerDep = None
):
    # Include user in cache key for isolation
    cache_key = f"sensitive:{id}:user:{current_user.id}"

    if cache:
        cached = await cache.get(cache_key)
        if cached:
            # Verify user still has access
            if can_access(current_user, id):
                return cached

    # Query and cache with short TTL
    data = await fetch_sensitive_data(id)

    if cache:
        await cache.set(cache_key, data, ttl=60)  # 1 minute only

    return data
```

---

## 📈 Optimization Tips

### 1. Batch Cache Operations

```python
# Instead of this:
for item in items:
    await cache.get(f"item:{item.id}")

# Do this:
keys = [f"item:{item.id}" for item in items]
cached_items = await cache.get_many(keys)
```

### 2. Cache Warming

```python
# Pre-populate cache on startup
async def warm_cache(cache: CacheManager):
    popular_items = await db.popular_items.find().limit(100)

    for item in popular_items:
        cache_key = f"item:{item.id}"
        await cache.set(cache_key, item, ttl=3600)
```

### 3. Conditional Caching

```python
# Only cache successful responses
if response.status == 200:
    await cache.set(key, response, ttl=300)
```

### 4. Cache Compression

```python
# For large data, compress before caching
import gzip, json

data_json = json.dumps(data)
compressed = gzip.compress(data_json.encode())
await cache.set(key, compressed, ttl=300)

# Decompress on retrieval
compressed = await cache.get(key)
data_json = gzip.decompress(compressed).decode()
data = json.loads(data_json)
```

---

## 🎓 Advanced Patterns

### Pattern 1: Cache-Aside

```python
async def get_with_cache_aside(cache_key: str, fetch_fn):
    """Standard cache-aside pattern"""
    # Try cache
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Fetch from source
    data = await fetch_fn()

    # Store in cache
    await cache.set(cache_key, data)
    return data
```

### Pattern 2: Write-Through

```python
async def save_with_write_through(resource, cache_key):
    """Update database and cache together"""
    # Save to database
    await resource.save()

    # Update cache immediately
    await cache.set(cache_key, resource, ttl=300)
```

### Pattern 3: Cache Stampede Prevention

```python
import asyncio

_locks = {}

async def get_with_lock(cache_key: str, fetch_fn):
    """Prevent multiple requests from fetching same data"""
    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Get or create lock
    if cache_key not in _locks:
        _locks[cache_key] = asyncio.Lock()

    # Only one request fetches, others wait
    async with _locks[cache_key]:
        # Double-check cache
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # Fetch and cache
        data = await fetch_fn()
        await cache.set(cache_key, data)
        return data
```

---

## 📚 Additional Resources

- **Full Documentation:** `PHASE_2_WEEK_7_8_CACHING_COMPLETE.md`
- **Final Report:** `PHASE_2_WEEK_7_8_FINAL_REPORT.md`
- **API Docs:** http://localhost:8000/docs

---

## 🆘 Getting Help

**Cache Not Working?**
1. Check this guide's troubleshooting section
2. Review logs: `docker-compose logs api`
3. Test cache stats endpoint
4. Check Redis status

**Need to Modify Caching Behavior?**
1. Adjust TTL values in endpoint code
2. Change cache key patterns for better hit rates
3. Implement custom invalidation logic
4. Add compression for large data

---

**Last Updated:** November 12, 2025
**Phase:** Phase 2 Week 7-8 Complete
**Status:** ✅ Production Ready
