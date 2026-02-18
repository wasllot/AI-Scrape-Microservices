"""
Unit Tests for Monitoring Module

Tests metrics collection, correlation IDs, and health checking.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from app.monitoring import (
    MetricsCollector,
    HealthChecker,
    get_correlation_id,
    set_correlation_id
)


class TestMetricsCollector:
    """Tests for MetricsCollector class"""
    
    def setup_method(self):
        """Reset metrics before each test"""
        self.metrics = MetricsCollector()
        self.metrics.reset()
    
    def test_increment_counter(self):
        """Should increment counter"""
        self.metrics.increment("test_counter")
        self.metrics.increment("test_counter")
        result = self.metrics.get_metrics()
        assert result["counters"]["test_counter"] == 2
    
    def test_increment_with_value(self):
        """Should increment by custom value"""
        self.metrics.increment("test_counter", 5)
        result = self.metrics.get_metrics()
        assert result["counters"]["test_counter"] == 5
    
    def test_timing_records_duration(self):
        """Should record timing metrics"""
        self.metrics.timing("test_operation", 150.5)
        self.metrics.timing("test_operation", 200.0)
        result = self.metrics.get_metrics()
        assert "test_operation" in result["timings_avg_ms"]
    
    def test_timing_calculation(self):
        """Should calculate average timing"""
        self.metrics.timing("test_op", 100.0)
        self.metrics.timing("test_op", 200.0)
        result = self.metrics.get_metrics()
        assert result["timings_avg_ms"]["test_op"] == 150.0
    
    def test_error_counter(self):
        """Should track errors"""
        self.metrics.error("test_error")
        self.metrics.error("test_error")
        self.metrics.error("test_error")
        result = self.metrics.get_metrics()
        assert result["errors"]["test_error"] == 3
    
    def test_get_metrics_returns_all(self):
        """Should return all metric types"""
        self.metrics.increment("counter1")
        self.metrics.timing("timing1", 100)
        self.metrics.error("error1")
        
        result = self.metrics.get_metrics()
        
        assert "counters" in result
        assert "timings_avg_ms" in result
        assert "errors" in result
    
    def test_reset_clears_all(self):
        """Should clear all metrics"""
        self.metrics.increment("test", 10)
        self.metrics.timing("test", 100)
        self.metrics.error("test")
        
        self.metrics.reset()
        
        result = self.metrics.get_metrics()
        assert result["counters"] == {}
        assert result["timings_avg_ms"] == {}
        assert result["errors"] == {}


class TestCorrelationId:
    """Tests for correlation ID management"""
    
    def test_get_correlation_id_creates_new(self):
        """Should create new correlation ID if none exists"""
        # Clear any existing
        set_correlation_id(None)
        cid = get_correlation_id()
        assert cid is not None
        assert len(cid) > 0
    
    def test_set_and_get_correlation_id(self):
        """Should set and retrieve correlation ID"""
        test_id = "test-correlation-id-123"
        set_correlation_id(test_id)
        cid = get_correlation_id()
        assert cid == test_id


class TestHealthChecker:
    """Tests for HealthChecker class"""
    
    @pytest.mark.asyncio
    async def test_healthy_status(self):
        """Should return healthy when all checks pass"""
        checker = HealthChecker("test-service")
        checker.register_dependency("db", AsyncMock(return_value=True), critical=True)
        
        result = await checker.check_all()
        
        assert result["status"] == "healthy"
        assert result["dependencies"]["db"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_unhealthy_critical_failure(self):
        """Should return unhealthy on critical dependency failure"""
        checker = HealthChecker("test-service")
        checker.register_dependency("db", AsyncMock(return_value=False), critical=True)
        
        result = await checker.check_all()
        
        assert result["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_degraded_non_critical_failure(self):
        """Should return degraded on non-critical failure"""
        checker = HealthChecker("test-service")
        checker.register_dependency("cache", AsyncMock(return_value=False), critical=False)
        
        result = await checker.check_all()
        
        assert result["status"] == "degraded"
    
    @pytest.mark.asyncio
    async def test_handles_exception(self):
        """Should handle check exceptions gracefully"""
        checker = HealthChecker("test-service")
        
        async def failing_check():
            raise Exception("Connection failed")
        
        checker.register_dependency("db", failing_check, critical=True)
        
        result = await checker.check_all()
        
        assert result["status"] == "unhealthy"
        assert "error" in result["dependencies"]["db"]
    
    @pytest.mark.asyncio
    async def test_multiple_dependencies_mixed(self):
        """Should handle mix of healthy and unhealthy"""
        checker = HealthChecker("test-service")
        checker.register_dependency("db", AsyncMock(return_value=True), critical=True)
        checker.register_dependency("cache", AsyncMock(return_value=False), critical=False)
        checker.register_dependency("api", AsyncMock(return_value=True), critical=True)
        
        result = await checker.check_all()
        
        assert result["status"] == "degraded"
        assert result["dependencies"]["db"]["status"] == "healthy"
        assert result["dependencies"]["cache"]["status"] == "unhealthy"
        assert result["dependencies"]["api"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_returns_service_name(self):
        """Should include service name in response"""
        checker = HealthChecker("my-service")
        checker.register_dependency("dep", AsyncMock(return_value=True), critical=True)
        
        result = await checker.check_all()
        
        assert result["service"] == "my-service"
    
    @pytest.mark.asyncio
    async def test_includes_timestamp(self):
        """Should include timestamp in response"""
        checker = HealthChecker("test-service")
        checker.register_dependency("dep", AsyncMock(return_value=True), critical=True)
        
        result = await checker.check_all()
        
        assert "timestamp" in result
