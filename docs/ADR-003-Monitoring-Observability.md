# ADR-003: Monitoring and Observability

## Status
Implemented

## Context
The system needed comprehensive monitoring to:
- Track request metrics and performance
- Enable distributed tracing across services
- Provide health checks for orchestration (Kubernetes)
- Debug production issues effectively

## Decision

### 1. Metrics Collection
Created `app/monitoring.py` with `MetricsCollector`:

```python
class MetricsCollector:
    - Thread-safe singleton
    - Counters: increment(name, value)
    - Timings: timing(name, duration_ms)
    - Errors: error(name), increment(name + ".errors")
```

### 2. Distributed Tracing
Added correlation ID support via `contextvars`:

```python
correlation_id = get_correlation_id()  # Creates or retrieves
logger.info("Request processed", extra={"correlation_id": correlation_id})
```

### 3. Enhanced Health Checks
- `/health`: Liveness probe with dependency status
- `/health/ready`: Readiness probe for Kubernetes
- `/metrics`: Service metrics endpoint

### 4. HealthChecker Class
```python
checker = HealthChecker("service-name")
checker.register_dependency("db", check_fn, critical=True)
result = await checker.check_all()
# Returns: {status: "healthy|degraded|unhealthy", dependencies: {...}}
```

## Consequences

### Positive
- Prometheus-compatible metrics format
- Request tracing across microservices
- Kubernetes probe support
- Production debugging capabilities

### Negative
- Additional storage for metrics (in-memory for now)
- Need to add Prometheus export for production

## API Endpoints Added
| Endpoint | Purpose |
|----------|---------|
| GET /health | Basic health + dependencies |
| GET /health/ready | Kubernetes readiness |
| GET /metrics | Request counts, timings, errors |

## Configuration
```bash
# No new config - using defaults
```

## References
- [Prometheus Metrics](https://prometheus.io/docs/concepts/metric_types/)
- [Kubernetes Liveness/Readiness](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
