"""
Monitoring utilities for metrics, tracing, and health checks.

Provides:
- Request metrics (count, timing, errors)
- Distributed tracing with correlation IDs
- Enhanced health check dependencies
"""
import time
import uuid
import logging
from typing import Dict, Optional, Callable
from functools import wraps
from contextvars import ContextVar
from dataclasses import dataclass, field
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def get_correlation_id() -> str:
    """Get or create correlation ID for request tracing"""
    cid = correlation_id_var.get()
    if cid is None:
        cid = str(uuid.uuid4())
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(cid: str):
    """Set correlation ID for current context"""
    correlation_id_var.set(cid)


class MetricsCollector:
    """
    Thread-safe in-memory metrics collector.
    
    For production, consider exporting to Prometheus or StatsD.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._counters: Dict[str, int] = defaultdict(int)
        self._timings: Dict[str, list] = defaultdict(list)
        self._errors: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def increment(self, metric: str, value: int = 1):
        """Increment a counter metric"""
        with self._lock:
            self._counters[metric] += value
    
    def timing(self, metric: str, duration_ms: float):
        """Record a timing metric"""
        with self._lock:
            self._timings[metric].append(duration_ms)
            if len(self._timings[metric]) > 1000:
                self._timings[metric] = self._timings[metric][-1000:]
    
    def error(self, metric: str):
        """Record an error"""
        with self._lock:
            self._errors[metric] += 1
    
    def get_metrics(self) -> Dict:
        """Get all metrics"""
        with self._lock:
            timings_avg = {
                k: sum(v) / len(v) if v else 0 
                for k, v in self._timings.items()
            }
            return {
                "counters": dict(self._counters),
                "timings_avg_ms": timings_avg,
                "errors": dict(self._errors)
            }
    
    def reset(self):
        """Reset all metrics (for testing)"""
        with self._lock:
            self._counters.clear()
            self._timings.clear()
            self._errors.clear()


def track_request(metric_name: str):
    """
    Decorator to track request metrics.
    
    Usage:
        @track_request("scraper_service.extract")
        async def extract(request):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cid = get_correlation_id()
            start = time.time()
            m = MetricsCollector()
            try:
                result = await func(*args, **kwargs)
                m.increment(f"{metric_name}.requests")
                return result
            except Exception as e:
                m.increment(f"{metric_name}.errors")
                m.error(metric_name)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                m.timing(f"{metric_name}.duration_ms", duration_ms)
                logger.info(
                    f"{metric_name} completed",
                    extra={
                        "correlation_id": cid,
                        "duration_ms": duration_ms,
                        "metric": metric_name
                    }
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cid = get_correlation_id()
            start = time.time()
            m = MetricsCollector()
            try:
                result = func(*args, **kwargs)
                m.increment(f"{metric_name}.requests")
                return result
            except Exception as e:
                m.increment(f"{metric_name}.errors")
                m.error(metric_name)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                m.timing(f"{metric_name}.duration_ms", duration_ms)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class HealthChecker:
    """
    Enhanced health checker with dependency status.
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._dependencies: Dict[str, dict] = {}
    
    def register_dependency(self, name: str, check_fn: Callable, critical: bool = True):
        """Register a dependency health check"""
        self._dependencies[name] = {
            "check": check_fn,
            "critical": critical,
            "status": "unknown"
        }
    
    async def check_all(self) -> Dict:
        """Run all health checks"""
        results = {
            "service": self.service_name,
            "status": "healthy",
            "dependencies": {},
            "timestamp": time.time()
        }
        
        critical_failures = 0
        
        for name, dep in self._dependencies.items():
            try:
                is_healthy = await dep["check"]()
                dep["status"] = "healthy" if is_healthy else "unhealthy"
                results["dependencies"][name] = {"status": dep["status"]}
                
                if not is_healthy and dep["critical"]:
                    critical_failures += 1
                    
            except Exception as e:
                dep["status"] = "unhealthy"
                results["dependencies"][name] = {"status": "unhealthy", "error": str(e)}
                logger.error(f"Health check failed for {name}: {e}")
                
                if dep["critical"]:
                    critical_failures += 1
        
        if critical_failures > 0:
            results["status"] = "unhealthy"
        elif len([d for d in self._dependencies.values() if d["status"] == "unhealthy"]) > 0:
            results["status"] = "degraded"
        
        return results


metrics = MetricsCollector()
