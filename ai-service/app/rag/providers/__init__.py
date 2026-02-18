"""
Provider Module - Shared HTTP Client and Base Classes

Provides:
- Shared httpx.AsyncClient (resolves dependency conflicts)
- Base provider interface
- Common utilities
"""
import httpx
from typing import Optional

# Singleton async HTTP client
_http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """
    Get or create shared HTTP client.
    
    This prevents the httpx version conflict between groq and google-generativeai
    by using a single, properly configured client.
    """
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    return _http_client


async def close_http_client():
    """Close the shared HTTP client (call on shutdown)"""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
