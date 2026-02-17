"""
Tests for RAG Chat Service and Conversation Persistence

Tests the conversation storage implementations and RAG chat functionality.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import uuid

from app.rag.chat import (
    InMemoryConversationStore,
    PostgresConversationStore,
    RAGChatService,
    PromptBuilder,
    GeminiLLMProvider
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_db():
    """Mock database connection"""
    db = Mock()
    db.execute = Mock(return_value=[])
    db.execute_one = Mock(return_value=None)
    db.commit = Mock()
    return db


@pytest.fixture
def conversation_id():
    """Generate a test conversation ID"""
    return str(uuid.uuid4())


# ============================================
# InMemoryConversationStore Tests
# ============================================

def test_in_memory_store_save_turn(conversation_id):
    """Test saving a conversation turn to memory"""
    # Arrange
    store = InMemoryConversationStore()
    question = "What is RAG?"
    answer = "RAG stands for Retrieval-Augmented Generation"
    
    # Act
    store.save_turn(conversation_id, question, answer)
    
    # Assert
    history = store.get_history(conversation_id)
    assert len(history) == 1
    assert history[0]["question"] == question
    assert history[0]["answer"] == answer
    assert "timestamp" in history[0]


def test_in_memory_store_get_history_limit(conversation_id):
    """Test history retrieval with limit"""
    # Arrange
    store = InMemoryConversationStore()
    
    # Add 15 turns
    for i in range(15):
        store.save_turn(conversation_id, f"Question {i}", f"Answer {i}")
    
    # Act
    history = store.get_history(conversation_id, limit=5)
    
    # Assert
    assert len(history) == 5
    assert history[0]["question"] == "Question 10"  # Last 5 turns


def test_in_memory_store_max_turns(conversation_id):
    """Test that store keeps only last 10 turns"""
    # Arrange
    store = InMemoryConversationStore()
    
    # Add 15 turns
    for i in range(15):
        store.save_turn(conversation_id, f"Question {i}", f"Answer {i}")
    
    # Act
    all_history = store.get_history(conversation_id, limit=20)
    
    # Assert
    assert len(all_history) == 10  # Should keep only last 10


# ============================================
# PostgresConversationStore Tests
# ============================================

def test_postgres_store_save_turn(mock_db, conversation_id):
    """Test saving a conversation turn to PostgreSQL"""
    # Arrange
    store = PostgresConversationStore(db_connection=mock_db)
    question = "What is RAG?"
    answer = "RAG stands for Retrieval-Augmented Generation"
    
    # Act
    store.save_turn(conversation_id, question, answer)
    
    # Assert
    assert mock_db.execute.call_count == 3  # 1 conversation + 2 messages
    assert mock_db.commit.called


def test_postgres_store_get_history(mock_db, conversation_id):
    """Test retrieving conversation history from PostgreSQL"""
    # Arrange
    mock_db.execute.return_value = [
        {
            'role': 'user',
            'content': 'What is RAG?',
            'created_at': datetime.now()
        },
        {
            'role': 'assistant',
            'content': 'RAG stands for Retrieval-Augmented Generation',
            'created_at': datetime.now()
        }
    ]
    
    store = PostgresConversationStore(db_connection=mock_db)
    
    # Act
    history = store.get_history(conversation_id)
    
    # Assert
    assert len(history) == 1
    assert history[0]["question"] == "What is RAG?"
    assert history[0]["answer"] == "RAG stands for Retrieval-Augmented Generation"


def test_postgres_store_get_history_with_limit(mock_db, conversation_id):
    """Test history retrieval with limit"""
    # Arrange
    messages = []
    for i in range(10):
        messages.extend([
            {'role': 'user', 'content': f'Question {i}', 'created_at': datetime.now()},
            {'role': 'assistant', 'content': f'Answer {i}', 'created_at': datetime.now()}
        ])
    
    mock_db.execute.return_value = messages
    store = PostgresConversationStore(db_connection=mock_db)
    
    # Act
    history = store.get_history(conversation_id, limit=3)
    
    # Assert
    assert len(history) == 3
    assert history[0]["question"] == "Question 7"  # Last 3 turns


# ============================================
# PromptBuilder Tests
# ============================================

def test_prompt_builder_build_context():
    """Test context building from documents"""
    # Arrange
    builder = PromptBuilder()
    documents = [
        {
            'content': 'RAG is a technique',
            'similarity': 0.95,
            'metadata': {'source': 'doc1.txt'}
        },
        {
            'content': 'It combines retrieval and generation',
            'similarity': 0.88,
            'metadata': {'source': 'doc2.txt'}
        }
    ]
    
    # Act
    context = builder.build_context(documents)
    
    # Assert
    assert 'RAG is a technique' in context
    assert 'doc1.txt' in context
    assert '0.95' in context


def test_prompt_builder_build_history():
    """Test history building"""
    # Arrange
    builder = PromptBuilder()
    history = [
        {'question': 'Q1', 'answer': 'A1', 'timestamp': '2024-01-01T00:00:00'},
        {'question': 'Q2', 'answer': 'A2', 'timestamp': '2024-01-01T00:01:00'},
        {'question': 'Q3', 'answer': 'A3', 'timestamp': '2024-01-01T00:02:00'},
        {'question': 'Q4', 'answer': 'A4', 'timestamp': '2024-01-01T00:03:00'}
    ]
    
    # Act
    history_text = builder.build_history(history)
    
    # Assert
    assert 'Q2' in history_text  # Should include last 3
    assert 'Q3' in history_text
    assert 'Q4' in history_text
    assert 'Q1' not in history_text  # Should exclude first


def test_prompt_builder_build_prompt():
    """Test complete prompt building"""
    # Arrange
    builder = PromptBuilder()
    question = "What is RAG?"
    context = "RAG is Retrieval-Augmented Generation"
    history = "Previous conversation..."
    
    # Act
    prompt = builder.build_prompt(question, context, history)
    
    # Assert
    assert question in prompt
    assert context in prompt
    assert history in prompt
    assert "CONTEXTO DISPONIBLE" in prompt


# ============================================
# RAGChatService Integration Tests
# ============================================

@pytest.mark.asyncio
async def test_rag_chat_service_generate_response():
    """Test RAG chat service response generation"""
    # Arrange
    mock_embedding_service = Mock()
    mock_embedding_service.search_similar = Mock(return_value=[
        {
            'id': 1,
            'content': 'RAG is a technique',
            'similarity': 0.95,
            'metadata': {'source': 'test.txt'}
        }
    ])
    
    mock_llm = Mock()
    mock_llm.generate_response = Mock(return_value="RAG stands for Retrieval-Augmented Generation")
    
    mock_store = InMemoryConversationStore()
    
    service = RAGChatService(
        embedding_service=mock_embedding_service,
        llm_provider=mock_llm,
        conversation_store=mock_store
    )
    
    # Act
    response = await service.generate_response("What is RAG?")
    
    # Assert
    assert "answer" in response
    assert "sources" in response
    assert "conversation_id" in response
    assert response["answer"] == "RAG stands for Retrieval-Augmented Generation"
    assert len(response["sources"]) == 1


@pytest.mark.asyncio
async def test_rag_chat_service_with_conversation_id():
    """Test RAG chat service with existing conversation"""
    # Arrange
    mock_embedding_service = Mock()
    mock_embedding_service.search_similar = Mock(return_value=[])
    
    mock_llm = Mock()
    mock_llm.generate_response = Mock(return_value="Follow-up answer")
    
    mock_store = InMemoryConversationStore()
    
    service = RAGChatService(
        embedding_service=mock_embedding_service,
        llm_provider=mock_llm,
        conversation_store=mock_store
    )
    
    # First message
    response1 = await service.generate_response("First question")
    conversation_id = response1["conversation_id"]
    
    # Act - Second message with same conversation ID
    response2 = await service.generate_response(
        "Follow-up question",
        conversation_id=conversation_id
    )
    
    # Assert
    assert response2["conversation_id"] == conversation_id
    history = mock_store.get_history(conversation_id)
    assert len(history) == 2  # Should have 2 turns
