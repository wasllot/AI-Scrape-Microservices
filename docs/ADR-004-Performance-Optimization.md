# ADR-004: Performance Optimization

## Status
Implemented

## Context
Performance issues identified:
- N+1 queries in conversation storage (3 INSERT statements)
- Inefficient caching (only in-memory, simple keys)
- Browser context recreation on every request

## Decision

### 1. Database Query Optimization
Combined multiple INSERT statements into single batch insert:

```python
# Before: 3 queries
self.db.execute("INSERT INTO conversations ...", fetch_results=False)
self.db.execute("INSERT INTO messages (user) ...", fetch_results=False)
self.db.execute("INSERT INTO messages (assistant) ...", fetch_results=False)

# After: 1 query
self.db.execute("""
    INSERT INTO messages (conversation_id, role, content, created_at)
    VALUES 
        (%s, 'user', %s, CURRENT_TIMESTAMP),
        (%s, 'assistant', %s, CURRENT_TIMESTAMP)
""", (conversation_id, question, conversation_id, answer))
```

Added LIMIT to history queries to reduce data transfer.

### 2. Enhanced Caching
Created Redis-based cache for production:

```python
class RedisCache:
    async def get(self, key: str) -> Optional[str]:
        await self._ensure_client()
        return await self._client.get(key)
    
    async def set(self, key: str, value: str, ttl: int):
        await self._client.setex(key, ttl, value)
```

Cache keys now include extraction rules hash for better invalidation.

### 3. Browser Context Pooling
Reuse Playwright browser contexts instead of creating new ones:

```python
class PlaywrightBrowserProvider:
    def __init__(self, max_contexts=5):
        self._contexts: List[BrowserContext] = []
        self._available_contexts: asyncio.Queue = None
    
    async def _get_context(self) -> BrowserContext:
        return await self._available_contexts.get()
```

## Consequences

### Positive
- Reduced database round trips
- Multi-instance cache via Redis
- Lower browser resource usage

### Negative
- More complex context lifecycle management
- Redis dependency in production

## Configuration
```bash
PLAYWRIGHT_CONTEXTS=5
CACHE_ENABLED=true
CACHE_TTL=3600
REDIS_HOST=redis
```

## References
- [PostgreSQL Batch Inserts](https://www.postgresql.org/docs/current/sql-insert.html)
- [Playwright Context Reuse](https://playwright.dev/python/docs/api/class-browsercontext)
