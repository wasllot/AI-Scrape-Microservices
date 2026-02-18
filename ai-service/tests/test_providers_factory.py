"""
Unit Tests for Provider Factory

Tests provider creation and mocking for testing.
"""
import pytest
from unittest.mock import Mock
from app.providers_factory import (
    ProviderFactory,
    create_primary_provider,
    create_secondary_provider,
    create_fallback_provider,
    get_provider_factory
)


class MockProvider:
    """Mock provider for testing"""
    def __init__(self, name="mock"):
        self._name = name
    
    def generate_response(self, prompt):
        return f"Mock response for: {prompt}"
    
    @property
    def name(self):
        return self._name


class TestProviderFactory:
    """Tests for ProviderFactory class"""
    
    def test_create_gemini_provider(self):
        """Should create Gemini provider"""
        factory = ProviderFactory()
        provider = factory.create("gemini")
        assert provider is not None
        assert provider.name == "gemini"
    
    def test_create_groq_provider(self):
        """Should create Groq provider"""
        factory = ProviderFactory()
        provider = factory.create("groq")
        assert provider is not None
        assert provider.name == "groq"
    
    def test_create_static_provider(self):
        """Should create static provider"""
        factory = ProviderFactory()
        provider = factory.create("static")
        assert provider is not None
        assert provider.name == "static"
    
    def test_create_unknown_provider_raises(self):
        """Should raise ValueError for unknown provider"""
        factory = ProviderFactory()
        with pytest.raises(ValueError, match="Unknown provider"):
            factory.create("unknown_provider")
    
    def test_register_custom_provider(self):
        """Should register custom provider"""
        factory = ProviderFactory()
        mock_provider = MockProvider("custom")
        factory.register("custom", mock_provider)
        
        provider = factory.create("custom")
        assert provider.name == "custom"
    
    def test_custom_provider_overrides_default(self):
        """Custom provider should override default"""
        factory = ProviderFactory()
        custom = MockProvider("custom-gemini")
        factory.register("gemini", custom)
        
        provider = factory.create("gemini")
        assert provider.name == "custom-gemini"
    
    def test_get_available_providers(self):
        """Should list available providers"""
        factory = ProviderFactory()
        providers = factory.get_available_providers()
        
        assert "gemini" in providers
        assert "groq" in providers
        assert "static" in providers
    
    def test_get_available_includes_custom(self):
        """Should include custom providers"""
        factory = ProviderFactory()
        factory.register("custom", MockProvider())
        
        providers = factory.get_available_providers()
        assert "custom" in providers


class TestProviderFactoryFunctions:
    """Tests for factory convenience functions"""
    
    def test_create_primary_provider(self):
        """Should create primary (Gemini) provider"""
        provider = create_primary_provider()
        assert provider.name == "gemini"
    
    def test_create_secondary_provider(self):
        """Should create secondary (Groq) provider"""
        provider = create_secondary_provider()
        assert provider.name == "groq"
    
    def test_create_fallback_provider(self):
        """Should create fallback (static) provider"""
        provider = create_fallback_provider()
        assert provider.name == "static"
    
    def test_get_provider_factory_singleton(self):
        """Should return singleton instance"""
        factory1 = get_provider_factory()
        factory2 = get_provider_factory()
        assert factory1 is factory2
