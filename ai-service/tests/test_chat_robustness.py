import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.rag.chat import RAGChatService, GeminiLLMProvider, GroqLLMProvider
from app.config import settings

@pytest.mark.asyncio
async def test_generate_welcome_static():
    """Test that welcome message is generated statically without LLM call"""
    # Setup
    service = RAGChatService(
        embedding_service=MagicMock(),
        llm_provider=MagicMock(), # Should not be used
        conversation_store=MagicMock(),
        prompt_builder=MagicMock()
    )
    service.conversation_store.get_history.return_value = [] # New user
    
    # Act
    response = await service.generate_welcome()
    
    # Assert
    assert "message" in response
    assert isinstance(response["message"], str)
    assert len(response["message"]) > 10
    # Ensure no LLM call was made
    service.primary_llm.generate_response.assert_not_called()

@pytest.mark.asyncio
async def test_fallback_to_groq_on_error():
    """Test fallback to Groq when Gemini fails"""
    # Setup
    mock_gemini = MagicMock(spec=GeminiLLMProvider)
    mock_gemini.generate_response.side_effect = Exception("429 Resource Exhausted")
    
    mock_groq = MagicMock(spec=GroqLLMProvider)
    mock_groq.generate_response.return_value = "Groq Response"
    
    service = RAGChatService(
        embedding_service=AsyncMock(),
        llm_provider=mock_gemini,
        conversation_store=MagicMock(),
        prompt_builder=MagicMock()
    )
    # Inject mock secondary provider manually since __init__ checks settings
    service.secondary_llm = mock_groq
    
    # Mock embedding search to return something
    service.embedding_service.search_similar.return_value = [
        {"id": 1, "content": "Context", "similarity": 0.9}
    ]
    
    # Act
    response = await service.generate_response("Test Question")
    
    # Assert
    assert "Groq Response" in response["answer"]
    assert "(Respuesta generada por el sistema de respaldo)" in response["answer"]
    mock_gemini.generate_response.assert_called_once()
    mock_groq.generate_response.assert_called_once()
