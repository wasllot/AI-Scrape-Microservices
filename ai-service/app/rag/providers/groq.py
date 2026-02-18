"""
Groq LLM Provider

Production-ready wrapper for Groq API (Llama 3) with:
- Proper error handling
- Structured logging
- Fallback-optimized configuration
"""
from groq import Groq
from typing import Optional
import logging

from app.rag.router import LLMProvider
from app.config import settings

logger = logging.getLogger(__name__)


class GroqLLMProvider(LLMProvider):
    """
    Groq/Llama3 provider for fast, reliable fallback.
    
    Features:
    - Lower latency than Gemini
    - Higher rate limits on paid tier
    - Good for backup scenarios
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.api_key = api_key or settings.groq_api_key
        self.model_name = model_name or settings.groq_model
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not configured")
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate response using Groq.
        
        Raises:
            Exception: On API errors (caught by router)
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente profesional y servicial. Responde en español de forma clara y concisa."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model_name,
                temperature=0.7,
                max_tokens=1024
            )
            
            response_text = chat_completion.choices[0].message.content
            
            if not response_text:
                raise ValueError("Groq returned empty response")
            
            return response_text
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error({
                "event": "groq_error",
                "error_type": error_type,
                "error": str(e),
                "model": self.model_name
            })
            raise
    
    @property
    def name(self) -> str:
        return "groq"
