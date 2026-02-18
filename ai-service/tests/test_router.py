"""
Tests for LLM Router with Circuit Breaker

Verifies:
- Multi-layer fallback (Gemini → Groq → Static)
- Circuit breaker state transitions
- Exponential backoff retries
- Metrics tracking
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import redis
import time

from app.rag.router import LLMRouter, CircuitBreaker, CircuitState, LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock provider for testing"""
    
    def __init__(self, name: str, should_fail: bool = False):
        self._name = name
        self.should_fail = should_fail
        self.call_count = 0
    
    def generate_response(self, prompt: str) -> str:
        self.call_count += 1
        if self.should_fail:
            raise ConnectionError(f"{self._name} failed")
        return f"Response from {self._name}"
    
    @property
    def name(self) -> str:
        return self._name


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = MagicMock(spec=redis.Redis)
    redis_mock.get.return_value = None
    redis_mock.incr.return_value = 1
    return redis_mock


@pytest.fixture
def primary_provider():
    """Primary (Gemini) provider"""
    return MockLLMProvider("gemini")


@pytest.fixture
def secondary_provider():
    """Secondary (Groq) provider"""
    return MockLLMProvider("groq")


class TestCircuitBreaker:
    """Test Circuit Breaker logic"""
    
    def test_initial_state_is_closed(self, mock_redis):
        """Circuit should start in CLOSED state"""
        breaker = CircuitBreaker(mock_redis, "test_provider")
        assert breaker.get_state() == CircuitState.CLOSED
    
    def test_circuit_opens_after_threshold_failures(self, mock_redis):
        """Circuit should open after 5 failures"""
        breaker = CircuitBreaker(mock_redis, "test_provider")
        
        # Simulate failures
        for i in range(5):
            mock_redis.incr.return_value = i + 1
            breaker.record_failure()
        
        # Verify circuit opened
        mock_redis.set.assert_called()
        calls = [call for call in mock_redis.set.call_args_list if 'circuit_state' in str(call)]
        assert any(CircuitState.OPEN.value in str(call) for call in calls)
    
    def test_circuit_closes_on_success_from_half_open(self, mock_redis):
        """Circuit should close when request succeeds in HALF_OPEN state"""
        breaker = CircuitBreaker(mock_redis, "test_provider")
        
        # Set to HALF_OPEN
        mock_redis.get.return_value = CircuitState.HALF_OPEN.value.encode()
        
        # Record success
        breaker.record_success()
        
        # Verify circuit closed
        mock_redis.delete.assert_called_with(breaker.failure_key)
    
    def test_can_attempt_returns_false_when_open(self, mock_redis):
        """Should not attempt when circuit is OPEN"""
        breaker = CircuitBreaker(mock_redis, "test_provider")
        mock_redis.get.return_value = CircuitState.OPEN.value.encode()
        
        assert breaker.can_attempt() is False
    
    def test_can_attempt_returns_true_when_closed(self, mock_redis):
        """Should attempt when circuit is CLOSED"""
        breaker = CircuitBreaker(mock_redis, "test_provider")
        mock_redis.get.return_value = CircuitState.CLOSED.value.encode()
        
        assert breaker.can_attempt() is True


class TestLLMRouter:
    """Test LLM Router orchestration"""
    
    @pytest.mark.asyncio
    async def test_router_uses_primary_when_available(self, primary_provider, secondary_provider, mock_redis):
        """Router should use primary provider when it works"""
        router = LLMRouter(
            primary=primary_provider,
            secondary=secondary_provider,
            redis_client=mock_redis
        )
        
        response = await router.generate("test prompt")
        
        assert response["text"] == "Response from gemini"
        assert response["provider"] == "gemini"
        assert response["fallback_used"] is False
        assert primary_provider.call_count == 1
        assert secondary_provider.call_count == 0
    
    @pytest.mark.asyncio
    async def test_router_falls_back_to_secondary_on_primary_failure(self, mock_redis):
        """Router should fallback to Groq when Gemini fails"""
        primary = MockLLMProvider("gemini", should_fail=True)
        secondary = MockLLMProvider("groq", should_fail=False)
        
        router = LLMRouter(
            primary=primary,
            secondary=secondary,
            redis_client=mock_redis
        )
        
        response = await router.generate("test prompt")
        
        assert response["text"] == "Response from groq"
        assert response["provider"] == "groq"
        assert response["fallback_used"] is True
        assert primary.call_count >= 1  # May retry
        assert secondary.call_count == 1
    
    @pytest.mark.asyncio
    async def test_router_returns_static_when_all_fail(self, mock_redis):
        """Router should return static fallback when all providers fail"""
        primary = MockLLMProvider("gemini", should_fail=True)
        secondary = MockLLMProvider("groq", should_fail=True)
        
        router = LLMRouter(
            primary=primary,
            secondary=secondary,
            redis_client=mock_redis
        )
        
        response = await router.generate("test prompt")
        
        assert response["provider"] == "static_fallback"
        assert response["fallback_used"] is True
        assert "Disculpa las molestias" in response["text"]
    
    @pytest.mark.asyncio
    async def test_router_skips_primary_when_circuit_open(self, mock_redis):
        """Router should skip primary when circuit is OPEN"""
        primary = MockLLMProvider("gemini")
        secondary = MockLLMProvider("groq")
        
        # Mock circuit breaker to return OPEN state
        with patch.object(CircuitBreaker, 'can_attempt', return_value=False):
            router = LLMRouter(
                primary=primary,
                secondary=secondary,
                redis_client=mock_redis
            )
            
            response = await router.generate("test prompt")
            
            # Should skip to secondary
            assert response["provider"] == "groq"
            assert primary.call_count == 0  # Never called
            assert secondary.call_count == 1
    
    @pytest.mark.asyncio
    async def test_router_tracks_metrics_in_redis(self, primary_provider, mock_redis):
        """Router should track request metrics in Redis"""
        router = LLMRouter(
            primary=primary_provider,
            redis_client=mock_redis
        )
        
        await router.generate("test prompt")
        
        # Verify metrics were tracked
        mock_redis.incr.assert_any_call("llm:gemini:requests")
        mock_redis.lpush.assert_called()  # Latency tracking
    
    @pytest.mark.asyncio
    async def test_router_works_without_redis(self, primary_provider):
        """Router should work even if Redis is unavailable"""
        router = LLMRouter(
            primary=primary_provider,
            redis_client=None  # No Redis
        )
        
        response = await router.generate("test prompt")
        
        # Should still work, just without circuit breaker
        assert response["text"] == "Response from gemini"
        assert response["provider"] == "gemini"


class TestExponentialBackoff:
    """Test retry logic with exponential backoff"""
    
    @pytest.mark.asyncio
    async def test_router_retries_on_network_errors(self, mock_redis):
        """Router should retry on transient network errors"""
        call_count = 0
        
        class FlakyProvider(LLMProvider):
            def generate_response(self, prompt: str) -> str:
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ConnectionError("Network error")
                return "Success after retries"
            
            @property
            def name(self) -> str:
                return "flaky"
        
        router = LLMRouter(
            primary=FlakyProvider(),
            redis_client=mock_redis
        )
        
        response = await router.generate("test prompt")
        
        assert response["text"] == "Success after retries"
        assert call_count == 3  # Failed 2 times, succeeded on 3rd


@pytest.mark.asyncio
async def test_integration_full_fallback_chain(mock_redis):
    """Integration test: Full fallback chain Gemini → Groq → Static"""
    
    # Scenario: Gemini fails, Groq succeeds
    primary = MockLLMProvider("gemini", should_fail=True)
    secondary = MockLLMProvider("groq", should_fail=False)
    
    router = LLMRouter(
        primary=primary,
        secondary=secondary,
        redis_client=mock_redis
    )
    
    response = await router.generate("test prompt", conversation_id="test-123")
    
    # Assertions
    assert response["provider"] == "groq"
    assert response["fallback_used"] is True
    assert response["metadata"]["conversation_id"] == "test-123"
    assert "Response from groq" in response["text"]
