"""
Provider Factory - Centralized provider creation for dependency injection

This module provides a factory for creating LLM providers with:
- Easy mocking for tests
- Centralized configuration
- Runtime provider selection
"""
from typing import Optional
from app.rag.router import LLMProvider
from app.rag.providers.gemini import GeminiLLMProvider
from app.rag.providers.groq import GroqLLMProvider
from app.rag.providers.static import StaticFallbackProvider


class ProviderFactory:
    """
    Factory for creating LLM providers.
    
    Usage:
        # Production
        factory = ProviderFactory()
        primary = factory.create("gemini")
        secondary = factory.create("groq")
        fallback = factory.create("static")
        
        # Testing with mocks
        factory = ProviderFactory()
        factory.register("mock", MockProvider())
        provider = factory.create("mock")
    """
    
    DEFAULT_PROVIDERS = {
        "gemini": GeminiLLMProvider,
        "groq": GroqLLMProvider,
        "static": StaticFallbackProvider,
    }
    
    def __init__(self):
        self._providers: dict = {}
        self._custom_providers: dict = {}
    
    def create(self, provider_name: str, **kwargs) -> LLMProvider:
        """
        Create a provider instance.
        
        Args:
            provider_name: Name of provider ("gemini", "groq", "static", or custom)
            **kwargs: Additional arguments passed to provider constructor
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider not found
        """
        # Check custom providers first (for testing/mocks)
        if provider_name in self._custom_providers:
            return self._custom_providers[provider_name]
        
        # Look up in default providers
        provider_class = self.DEFAULT_PROVIDERS.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return provider_class(**kwargs)
    
    def register(self, name: str, provider: LLMProvider):
        """
        Register a custom provider (useful for testing).
        
        Args:
            name: Provider identifier
            provider: Provider instance
        """
        self._custom_providers[name.lower()] = provider
    
    def get_available_providers(self) -> list:
        """Get list of available provider names"""
        return list(self.DEFAULT_PROVIDERS.keys()) + list(self._custom_providers.keys())


# Singleton factory instance
_factory: Optional[ProviderFactory] = None


def get_provider_factory() -> ProviderFactory:
    """Get singleton provider factory"""
    global _factory
    if _factory is None:
        _factory = ProviderFactory()
    return _factory


def create_primary_provider(**kwargs) -> LLMProvider:
    """Create primary (Gemini) provider"""
    return get_provider_factory().create("gemini", **kwargs)


def create_secondary_provider(**kwargs) -> LLMProvider:
    """Create secondary (Groq) provider"""
    return get_provider_factory().create("groq", **kwargs)


def create_fallback_provider(**kwargs) -> LLMProvider:
    """Create fallback (static) provider"""
    return get_provider_factory().create("static", **kwargs)
