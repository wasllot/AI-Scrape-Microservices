"""
Script Writer Service - Main orchestration for writing operations

Provides high-level API for:
- Script improvement
- Structure enhancement with specific techniques
- Tone modification
- Summarization and expansion
- Format adaptation
- Quality analysis
"""
from typing import Dict, Optional, List
import json
import logging

from app.config import settings
from app.rag.router import LLMRouter
from app.providers_factory import (
    create_primary_provider,
    create_secondary_provider,
)
from app.writing.prompts import WritingPrompts, WritingTechnique, ToneType, FormatType
from app.writing.analyzers import QualityAnalyzer
from app.writing.formatters import FormatAdapter
import redis

logger = logging.getLogger(__name__)


class ScriptWriterService:
    """
    Main service for script writing and improvement operations.
    
    Orchestrates LLM calls with fallback mechanism and provides
    structured responses for all writing operations.
    """
    
    MAX_CONTENT_LENGTH = 20000
    
    def __init__(self, llm_router: Optional[LLMRouter] = None):
        """
        Initialize ScriptWriterService.
        
        Args:
            llm_router: Optional LLMRouter instance (creates one if not provided)
        """
        self.llm_router = llm_router or self._create_router()
    
    def _create_router(self) -> LLMRouter:
        """Create default LLM router with fallback"""
        primary = create_primary_provider()
        secondary = create_secondary_provider() if settings.groq_api_key else None
        
        redis_client = None
        try:
            redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis unavailable for circuit breaker: {e}")
        
        return LLMRouter(
            primary=primary,
            secondary=secondary,
            redis_client=redis_client
        )
    
    def _call_llm(self, prompt: str) -> Dict[str, any]:
        """
        Call LLM with prompt and return response with metadata.
        """
        result = self.llm_router.generate(prompt)
        return result
    
    def _validate_content(self, content: str) -> None:
        """Validate content length"""
        word_count = len(content.split())
        if word_count > self.MAX_CONTENT_LENGTH:
            raise ValueError(
                f"Content too long. Maximum {self.MAX_CONTENT_LENGTH} words allowed, "
                f"got {word_count} words."
            )
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
    
    async def improve(
        self,
        content: str,
        tone: str = "professional",
        target_audience: str = "general",
        purpose: Optional[str] = None
    ) -> Dict:
        """
        Improve existing script.
        
        Args:
            content: Original script content
            tone: Desired tone (formal, professional, casual, dynamic, friendly, authoritative)
            target_audience: Target audience description
            purpose: Optional purpose of the script
            
        Returns:
            Dict with improved content and metadata
        """
        self._validate_content(content)
        
        prompt = WritingPrompts.get_improve_prompt(
            content=content,
            tone=tone,
            target_audience=target_audience,
            purpose=purpose
        )
        
        result = await self._call_llm(prompt)
        
        return {
            "result": result["text"],
            "original_length": len(content),
            "result_length": len(result["text"]),
            "provider": result["provider"],
            "fallback_used": result.get("fallback_used", False)
        }
    
    async def improve_structure(
        self,
        content: str,
        technique: str = "storytelling",
        tone: str = "professional",
        target_audience: str = "general"
    ) -> Dict:
        """
        Improve script structure using specific technique.
        
        Args:
            content: Original script content
            technique: Writing technique (storytelling, aida, pas, hero_journey, three_act, inverted_pyramid, rule_of_three)
            tone: Desired tone
            target_audience: Target audience
            
        Returns:
            Dict with restructured content
        """
        self._validate_content(content)
        
        valid_techniques = [t.value for t in WritingTechnique]
        if technique not in valid_techniques:
            technique = WritingTechnique.STORYTELLING.value
        
        prompt = WritingPrompts.get_structure_prompt(
            content=content,
            technique=technique,
            tone=tone,
            target_audience=target_audience
        )
        
        result = await self._call_llm(prompt)
        
        return {
            "result": result["text"],
            "technique_used": technique,
            "original_length": len(content),
            "result_length": len(result["text"]),
            "provider": result["provider"],
            "fallback_used": result.get("fallback_used", False)
        }
    
    async def change_tone(
        self,
        content: str,
        tone: str
    ) -> Dict:
        """
        Change tone of existing script.
        
        Args:
            content: Original script
            tone: New tone (formal, professional, casual, dynamic, friendly, authoritative)
            
        Returns:
            Dict with content in new tone
        """
        self._validate_content(content)
        
        valid_tones = [t.value for t in ToneType]
        if tone not in valid_tones:
            tone = ToneType.PROFESSIONAL.value
        
        prompt = WritingPrompts.get_tone_prompt(content=content, tone=tone)
        
        result = await self._call_llm(prompt)
        
        return {
            "result": result["text"],
            "tone_applied": tone,
            "original_length": len(content),
            "result_length": len(result["text"]),
            "provider": result["provider"],
            "fallback_used": result.get("fallback_used", False)
        }
    
    async def expand(
        self,
        content: str,
        factor: str = "medium"
    ) -> Dict:
        """
        Expand script content.
        
        Args:
            content: Original script
            factor: Expansion factor (short=30%, medium=50%, long=100%)
            
        Returns:
            Dict with expanded content
        """
        self._validate_content(content)
        
        prompt = WritingPrompts.get_expand_prompt(content=content, factor=factor)
        
        result = await self._call_llm(prompt)
        
        return {
            "result": result["text"],
            "expansion_factor": factor,
            "original_length": len(content),
            "result_length": len(result["text"]),
            "provider": result["provider"],
            "fallback_used": result.get("fallback_used", False)
        }
    
    async def summarize(
        self,
        content: str,
        length: str = "medium"
    ) -> Dict:
        """
        Summarize script content.
        
        Args:
            content: Original script
            length: Summary length (short=20%, medium=35%, long=50%)
            
        Returns:
            Dict with summarized content
        """
        self._validate_content(content)
        
        prompt = WritingPrompts.get_summarize_prompt(content=content, length=length)
        
        result = await self._call_llm(prompt)
        
        return {
            "result": result["text"],
            "summary_length": length,
            "original_length": len(content),
            "result_length": len(result["text"]),
            "provider": result["provider"],
            "fallback_used": result.get("fallback_used", False)
        }
    
    async def adapt_format(
        self,
        content: str,
        format_type: str,
        target_audience: str = "general"
    ) -> Dict:
        """
        Adapt script to different format.
        
        Args:
            content: Original script
            format_type: Target format (video, podcast, linkedin, presentation)
            target_audience: Target audience
            
        Returns:
            Dict with formatted content and notes
        """
        self._validate_content(content)
        
        valid_formats = [f.value for f in FormatType]
        if format_type not in valid_formats:
            format_type = FormatType.GENERAL.value
        
        prompt = WritingPrompts.get_adapt_format_prompt(
            content=content,
            format_type=format_type,
            target_audience=target_audience
        )
        
        result = await self._call_llm(prompt)
        
        format_result = FormatAdapter.format(content, format_type)
        
        return {
            "result": result["text"],
            "format_type": format_type,
            "format_notes": format_result.notes,
            "original_length": len(content),
            "result_length": len(result["text"]),
            "provider": result["provider"],
            "fallback_used": result.get("fallback_used", False)
        }
    
    async def analyze(
        self,
        content: str,
        keywords: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze script quality.
        
        Args:
            content: Script to analyze
            keywords: Optional keywords for SEO analysis
            
        Returns:
            Dict with comprehensive analysis
        """
        self._validate_content(content)
        
        prompt = WritingPrompts.get_analysis_prompt(content)
        
        llm_result = await self._call_llm(prompt)
        
        try:
            ai_analysis = json.loads(llm_result["text"])
        except json.JSONDecodeError:
            ai_analysis = None
        
        analyzer = QualityAnalyzer(content, keywords)
        local_analysis = analyzer.analyze()
        
        return {
            "ai_analysis": ai_analysis,
            "local_analysis": local_analysis,
            "word_count": len(content.split()),
            "character_count": len(content),
            "provider": llm_result["provider"]
        }
