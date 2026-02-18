"""
LLM Router - Production-Grade Orchestration Layer

Implements Chain of Responsibility pattern for resilient LLM routing with:
- Multi-layer fallback (Gemini → Groq → Static)
- Circuit Breaker pattern (Redis-backed)
- Exponential backoff retries
- Structured logging for observability

Architecture:
    Layer 1: Gemini 1.5 Flash (Fast, Smart)
    Layer 2: Groq/Llama3 (Reliable Backup)
    Layer 3: Static Response (Always Available)
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
import time
import logging
import json
from datetime import datetime, timedelta

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import redis

# Configure structured logging
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Provider is down, skip it
    HALF_OPEN = "HALF_OPEN"  # Testing if provider recovered


class LLMProvider(ABC):
    """
    Protocol for LLM providers.
    All providers must implement this interface.
    """
    
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate text response from prompt"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier for logging"""
        pass


class CircuitBreaker:
    """
    Redis-backed circuit breaker for LLM providers.
    
    Prevents cascading failures by tracking provider health:
    - CLOSED: Normal operation
    - OPEN: Provider failing, route to backup (2min cooldown)
    - HALF_OPEN: Testing recovery (1 request)
    
    Redis Keys:
        llm:{provider}:failures - Failure counter (TTL 5min)
        llm:{provider}:circuit_state - Current state
        llm:{provider}:opened_at - Timestamp when circuit opened
    """
    
    FAILURE_THRESHOLD = 5  # Failures to trip circuit
    FAILURE_WINDOW = 300   # 5 minutes
    OPEN_DURATION = 120    # 2 minutes before retry
    
    def __init__(self, redis_client: redis.Redis, provider_name: str):
        self.redis = redis_client
        self.provider = provider_name
        self.failure_key = f"llm:{provider_name}:failures"
        self.state_key = f"llm:{provider_name}:circuit_state"
        self.opened_key = f"llm:{provider_name}:opened_at"
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        try:
            state_str = self.redis.get(self.state_key)
            if not state_str:
                return CircuitState.CLOSED
            
            state = CircuitState(state_str.decode())
            
            # Check if OPEN circuit should transition to HALF_OPEN
            if state == CircuitState.OPEN:
                opened_at = self.redis.get(self.opened_key)
                if opened_at:
                    opened_time = float(opened_at.decode())
                    if time.time() - opened_time >= self.OPEN_DURATION:
                        self._set_state(CircuitState.HALF_OPEN)
                        return CircuitState.HALF_OPEN
            
            return state
        except redis.RedisError as e:
            logger.warning(f"Redis error in circuit breaker, defaulting to CLOSED: {e}")
            return CircuitState.CLOSED
    
    def _set_state(self, state: CircuitState):
        """Set circuit state in Redis"""
        try:
            self.redis.set(self.state_key, state.value, ex=600)  # 10min TTL
            if state == CircuitState.OPEN:
                self.redis.set(self.opened_key, str(time.time()), ex=600)
        except redis.RedisError as e:
            logger.error(f"Failed to set circuit state: {e}")
    
    def record_success(self):
        """Record successful call, reset circuit if needed"""
        try:
            current_state = self.get_state()
            
            # Reset failures
            self.redis.delete(self.failure_key)
            
            # Close circuit if it was HALF_OPEN
            if current_state == CircuitState.HALF_OPEN:
                self._set_state(CircuitState.CLOSED)
                logger.info({
                    "event": "circuit_closed",
                    "provider": self.provider,
                    "message": "Provider recovered"
                })
        except redis.RedisError as e:
            logger.warning(f"Failed to record success: {e}")
    
    def record_failure(self):
        """Record failed call, potentially trip circuit"""
        try:
            # Increment failure counter
            failures = self.redis.incr(self.failure_key)
            self.redis.expire(self.failure_key, self.FAILURE_WINDOW)
            
            # Trip circuit if threshold exceeded
            if failures >= self.FAILURE_THRESHOLD:
                self._set_state(CircuitState.OPEN)
                logger.warning({
                    "event": "circuit_opened",
                    "provider": self.provider,
                    "failures": failures,
                    "message": f"Circuit opened after {failures} failures"
                })
        except redis.RedisError as e:
            logger.error(f"Failed to record failure: {e}")
    
    def can_attempt(self) -> bool:
        """Check if provider can be attempted"""
        state = self.get_state()
        return state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)


class LLMRouter:
    """
    Production-grade LLM orchestrator with resilient routing.
    
    Features:
    - Chain of Responsibility: Try providers in order
    - Circuit Breaker: Skip failing providers
    - Exponential Backoff: Retry with increasing delays
    - Graceful Degradation: Always return a response
    
    Usage:
        router = LLMRouter(
            primary=gemini_provider,
            secondary=groq_provider,
            redis_client=redis_conn
        )
        response = await router.generate(prompt)
    """
    
    def __init__(
        self,
        primary: LLMProvider,
        secondary: Optional[LLMProvider] = None,
        redis_client: Optional[redis.Redis] = None
    ):
        self.primary = primary
        self.secondary = secondary
        self.redis = redis_client
        
        # Initialize circuit breakers if Redis available
        self.primary_breaker = None
        self.secondary_breaker = None
        
        if redis_client:
            self.primary_breaker = CircuitBreaker(redis_client, primary.name)
            if secondary:
                self.secondary_breaker = CircuitBreaker(redis_client, secondary.name)
    
    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _call_provider(self, provider: LLMProvider, prompt: str) -> str:
        """
        Call provider with exponential backoff retry.
        Only retries on network errors, not API errors.
        """
        start_time = time.time()
        try:
            response = provider.generate_response(prompt)
            latency = int((time.time() - start_time) * 1000)
            
            # Log success
            logger.info({
                "event": "llm_success",
                "provider": provider.name,
                "latency_ms": latency
            })
            
            # Track metrics in Redis
            if self.redis:
                try:
                    self.redis.incr(f"llm:{provider.name}:requests")
                    self.redis.lpush(f"llm:{provider.name}:latency_ms", latency)
                    self.redis.ltrim(f"llm:{provider.name}:latency_ms", 0, 99)  # Keep last 100
                except redis.RedisError:
                    pass  # Don't fail on metrics
            
            return response
            
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.error({
                "event": "llm_error",
                "provider": provider.name,
                "error": str(e),
                "error_type": type(e).__name__,
                "latency_ms": latency
            })
            raise
    
    async def generate(
        self,
        prompt: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response with automatic fallback.
        
        Returns:
            {
                "text": str,
                "provider": str,
                "fallback_used": bool,
                "metadata": {...}
            }
        """
        providers_to_try = []
        
        # Layer 1: Primary (Gemini)
        if not self.primary_breaker or self.primary_breaker.can_attempt():
            providers_to_try.append(("primary", self.primary, self.primary_breaker))
        else:
            logger.info({
                "event": "circuit_open_skip",
                "provider": self.primary.name,
                "message": "Skipping primary due to open circuit"
            })
        
        # Layer 2: Secondary (Groq)
        if self.secondary:
            if not self.secondary_breaker or self.secondary_breaker.can_attempt():
                providers_to_try.append(("secondary", self.secondary, self.secondary_breaker))
        
        # Try each provider in order
        last_error = None
        for layer, provider, breaker in providers_to_try:
            try:
                response_text = self._call_provider(provider, prompt)
                
                # Record success in circuit breaker
                if breaker:
                    breaker.record_success()
                
                return {
                    "text": response_text,
                    "provider": provider.name,
                    "fallback_used": layer != "primary",
                    "metadata": {
                        "layer": layer,
                        "conversation_id": conversation_id
                    }
                }
                
            except Exception as e:
                last_error = e
                
                # Record failure in circuit breaker
                if breaker:
                    breaker.record_failure()
                
                # Log fallback attempt
                logger.warning({
                    "event": "llm_fallback",
                    "from_provider": provider.name,
                    "error": str(e),
                    "trying_next": len(providers_to_try) > providers_to_try.index((layer, provider, breaker)) + 1
                })
                
                continue  # Try next provider
        
        # Layer 3: All providers failed, return static fallback
        logger.error({
            "event": "all_llm_failed",
            "last_error": str(last_error),
            "conversation_id": conversation_id
        })
        
        return {
            "text": self._get_static_fallback(),
            "provider": "static_fallback",
            "fallback_used": True,
            "metadata": {
                "layer": "static",
                "error": str(last_error),
                "conversation_id": conversation_id
            }
        }
    
    def _get_static_fallback(self) -> str:
        """
        Static response when all LLMs fail.
        This ensures we NEVER return a 500 error.
        """
        return (
            "⚠️ **Disculpa las molestias técnicas**\n\n"
            "Estoy experimentando dificultades temporales con mis sistemas de IA. "
            "Por favor, intenta reformular tu pregunta o vuelve en unos minutos. "
            "Si necesitas asistencia urgente, contacta directamente con el equipo.\n\n"
            "_Sistema de respaldo activado_"
        )
