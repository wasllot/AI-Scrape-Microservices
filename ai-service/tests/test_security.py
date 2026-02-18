"""
Unit Tests for Security Module

Tests input sanitization, CSS selector validation, and URL validation.
"""
import pytest
from app.security import sanitize_input, sanitize_css_selector, sanitize_url


class TestSanitizeInput:
    """Tests for sanitize_input function"""
    
    def test_sanitize_normal_text(self):
        """Normal text should pass through unchanged (but trimmed)"""
        result = sanitize_input("  Hello World  ")
        assert result == "Hello World"
    
    def test_sanitize_html_tags(self):
        """HTML tags should be escaped"""
        result = sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_with_max_length(self):
        """Content should be truncated if exceeds max_length"""
        long_text = "a" * 2000
        result = sanitize_input(long_text, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_empty_string(self):
        """Empty string should return empty"""
        result = sanitize_input("")
        assert result == ""
    
    def test_sanitize_none(self):
        """None should return empty string"""
        result = sanitize_input(None)
        assert result == ""


class TestSanitizeCssSelector:
    """Tests for sanitize_css_selector function"""
    
    def test_valid_selector(self):
        """Valid CSS selectors should pass"""
        result = sanitize_css_selector(".product-title")
        assert result == ".product-title"
    
    def test_removes_javascript_protocol(self):
        """javascript: protocol should be removed"""
        result = sanitize_css_selector("javascript:alert(1)")
        assert "javascript" not in result.lower()
    
    def test_removes_onclick(self):
        """onclick handlers should be removed"""
        result = sanitize_css_selector('div onclick="alert(1)"')
        assert "onclick" not in result.lower()
    
    def test_removes_script_tags(self):
        """script tags should be removed"""
        result = sanitize_css_selector("<script>evil()</script>")
        assert "script" not in result.lower()
    
    def test_empty_selector(self):
        """Empty selector should return empty string"""
        result = sanitize_css_selector("")
        assert result == ""


class TestSanitizeUrl:
    """Tests for sanitize_url function"""
    
    def test_valid_http_url(self):
        """Valid HTTP URL should pass"""
        result = sanitize_url("http://example.com")
        assert result == "http://example.com"
    
    def test_valid_https_url(self):
        """Valid HTTPS URL should pass"""
        result = sanitize_url("https://example.com")
        assert result == "https://example.com"
    
    def test_url_normalized_to_lowercase(self):
        """URL should be normalized to lowercase"""
        result = sanitize_url("HTTPS://EXAMPLE.COM/PAGE")
        assert result == "https://example.com/page"
    
    def test_rejects_non_http_urls(self):
        """Non-HTTP URLs should raise ValueError"""
        with pytest.raises(ValueError):
            sanitize_url("javascript:alert(1)")
    
    def test_rejects_data_urls(self):
        """data: URLs should raise ValueError"""
        with pytest.raises(ValueError):
            sanitize_url("data:text/html,<script>alert(1)</script>")
    
    def test_rejects_file_urls(self):
        """file: URLs should raise ValueError"""
        with pytest.raises(ValueError):
            sanitize_url("file:///etc/passwd")
    
    def test_strips_whitespace(self):
        """Whitespace should be stripped"""
        result = sanitize_url("  https://example.com  ")
        assert result == "https://example.com"
