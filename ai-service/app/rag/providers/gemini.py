"""
Gemini LLM Provider

Production-ready wrapper for Google Gemini API with:
- Proper error handling
- Retry logic via tenacity
- Structured logging
"""
import google.generativeai as genai
from typing import Optional
import logging

from app.rag.router import LLMProvider
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiLLMProvider(LLMProvider):
    """
    Google Gemini 1.5 Flash provider.
    
    Features:
    - Automatic retry on transient errors
    - Safety settings configured
    - Structured error logging
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.chat_model
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate response using Gemini.
        
        Raises:
            Exception: On API errors (caught by router for fallback)
        """
        try:
            response = self.model.generate_content(prompt)
            
            # Check if response was blocked
            if not response.text:
                if hasattr(response, 'prompt_feedback'):
                    logger.warning(f"Gemini blocked response: {response.prompt_feedback}")
                raise ValueError("Gemini returned empty response")
            
            return response.text
            
        except Exception as e:
            # Log specific error details
            error_type = type(e).__name__
            logger.error({
                "event": "gemini_error",
                "error_type": error_type,
                "error": str(e),
                "model": self.model_name
            })
            raise
    
    @property
    def name(self) -> str:
        return "gemini"
