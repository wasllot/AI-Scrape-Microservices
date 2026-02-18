"""
Static Fallback Provider

Last-resort provider that returns search results without LLM generation.
Ensures 100% uptime even when all AI services are down.
"""
from typing import List, Dict, Optional
import logging

from app.rag.router import LLMProvider

logger = logging.getLogger(__name__)


class StaticFallbackProvider(LLMProvider):
    """
    Static response provider for when all LLMs fail.
    
    Returns formatted search results without AI generation.
    This ensures we NEVER return a 500 error to the user.
    """
    
    def __init__(self, search_results: Optional[List[Dict]] = None):
        self.search_results = search_results or []
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate static response from search results.
        
        If search results available, format them nicely.
        Otherwise, return helpful error message.
        """
        if not self.search_results:
            return self._get_no_results_message()
        
        # Format search results as a readable response
        response_parts = [
            "📚 **Información Relevante Encontrada:**\n",
            "_(Nota: Respuesta generada sin IA debido a problemas técnicos)_\n"
        ]
        
        for idx, result in enumerate(self.search_results[:3], 1):
            content = result.get('content', '').strip()
            similarity = result.get('similarity', 0)
            
            # Truncate long content
            if len(content) > 200:
                content = content[:200] + "..."
            
            response_parts.append(f"\n**{idx}. Fragmento Relevante** (Similitud: {similarity:.0%})")
            response_parts.append(f"{content}\n")
        
        response_parts.append(
            "\n💡 _Para una respuesta más elaborada, por favor intenta de nuevo en unos minutos._"
        )
        
        return "\n".join(response_parts)
    
    def _get_no_results_message(self) -> str:
        """Message when no search results available"""
        return (
            "⚠️ **Sistema en Modo de Emergencia**\n\n"
            "Actualmente no puedo procesar tu consulta debido a problemas técnicos temporales. "
            "Por favor:\n\n"
            "1. Intenta reformular tu pregunta\n"
            "2. Vuelve a intentarlo en unos minutos\n"
            "3. Contacta directamente si es urgente\n\n"
            "_Disculpa las molestias. Estamos trabajando para restaurar el servicio._"
        )
    
    @property
    def name(self) -> str:
        return "static_fallback"
