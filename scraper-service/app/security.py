"""
Security utilities for input sanitization.
"""
import re
import html
from typing import Optional


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Optional maximum length limit
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    sanitized = text.strip()
    
    sanitized = html.escape(sanitized)
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def sanitize_css_selector(selector: str) -> str:
    """
    Sanitize CSS selector to prevent injection.
    
    Args:
        selector: CSS selector to sanitize
        
    Returns:
        Sanitized selector
    """
    if not selector:
        return ""
    
    dangerous_patterns = [
        r'javascript:',
        r'on\w+\s*=',
        r'<script',
        r'</script>',
    ]
    
    for pattern in dangerous_patterns:
        selector = re.sub(pattern, '', selector, flags=re.IGNORECASE)
    
    return selector.strip()


def sanitize_url(url: str) -> str:
    """
    Validate and sanitize URL for scraping.
    
    Args:
        url: URL to sanitize
        
    Returns:
        Sanitized URL
        
    Raises:
        ValueError: If URL is invalid or potentially dangerous
    """
    url = url.strip().lower()
    
    if not url.startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https://")
    
    dangerous_schemes = ['javascript:', 'data:', 'file:']
    if any(url.startswith(scheme) for scheme in dangerous_schemes):
        raise ValueError("Potentially dangerous URL scheme")
    
    return url
