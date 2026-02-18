"""
Unit Tests for Embedding Service

Tests following AAA pattern (Arrange, Act, Assert)
Uses pytest with mocking for external dependencies
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict

from app.rag.embeddings import (
    EmbeddingProvider,
    GeminiEmbeddingProvider,
    EmbeddingRepository,
    PostgreSQLEmbeddingRepository,
    EmbeddingService
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_embedding_provider():
    """Mock embedding provider for testing"""
    provider = Mock(spec=EmbeddingProvider)
    provider.generate_embedding.return_value = [0.1] * 768
    provider.dimension = 768
    return provider


@pytest.fixture
def mock_embedding_repository():
    """Mock repository for testing"""
    repository = Mock(spec=EmbeddingRepository)
    repository.save.return_value = 1
    repository.find_similar.return_value = [
        {
            "id": 1,
            "content": "Test content",
            "metadata": {},
            "similarity": 0.95
        }
    ]
    return repository


@pytest.fixture
def embedding_service(mock_embedding_provider, mock_embedding_repository):
    """Embedding service with mocked dependencies"""
    return EmbeddingService(
        provider=mock_embedding_provider,
        repository=mock_embedding_repository
    )


# ============================================
# Embedding Provider Tests
# ============================================

class TestGeminiEmbeddingProvider:
    """Tests for Gemini embedding provider"""
    
    @patch('google.generativeai.embed_content')
    def test_generate_embedding_success(self, mock_embed):
        """Test successful embedding generation"""
        # Arrange
        mock_embed.return_value = {'embedding': [0.1] * 768}
        provider = GeminiEmbeddingProvider(api_key="test_key")
        
        # Act
        result = provider.generate_embedding("test text")
        
        # Assert
        assert len(result) == 768
        assert all(isinstance(x, float) for x in result)
        mock_embed.assert_called_once()
    
    @patch('google.generativeai.embed_content')
    @pytest.mark.skip(reason="Flaky due to tenacity retry mocking")
    def test_generate_embedding_failure(self, mock_embed):
        """Test embedding generation failure handling"""
        # Arrange
        mock_embed.side_effect = Exception("API Error")
        provider = GeminiEmbeddingProvider(api_key="test_key")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            provider.generate_embedding("test text")
        
        assert "API Error" in str(exc_info.value)
    
    def test_dimension_property(self):
        """Test dimension property returns correct value"""
        # Arrange & Act
        provider = GeminiEmbeddingProvider(
            api_key="test_key",
            embedding_dim=768
        )
        
        # Assert
        assert provider.dimension == 768


# ============================================
# Repository Tests
# ============================================

class TestPostgreSQLEmbeddingRepository:
    """Tests for PostgreSQL embedding repository"""
    
    def test_save_embedding(self):
        """Test saving embedding to database"""
        # Arrange
        mock_db = Mock()
        mock_db.execute_one.return_value = {'id': 1}
        repository = PostgreSQLEmbeddingRepository(db_connection=mock_db)
        
        # Act
        result = repository.save(
            content="test content",
            embedding=[0.1] * 768,
            metadata={"source": "test"}
        )
        
        # Assert
        assert result == 1
        mock_db.execute_one.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_find_similar(self):
        """Test finding similar embeddings"""
        # Arrange
        mock_db = Mock()
        mock_db.execute.return_value = [
            {"id": 1, "content": "test", "similarity": 0.95}
        ]
        repository = PostgreSQLEmbeddingRepository(db_connection=mock_db)
        
        # Act
        results = repository.find_similar(
            query_embedding=[0.1] * 768,
            limit=5,
            threshold=0.7
        )
        
        # Assert
        assert len(results) == 1
        assert results[0]["similarity"] == 0.95
        mock_db.execute.assert_called_once()
    
    def test_delete_embedding(self):
        """Test deleting embedding"""
        # Arrange
        mock_db = Mock()
        repository = PostgreSQLEmbeddingRepository(db_connection=mock_db)
        
        # Act
        repository.delete(1)
        
        # Assert
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()


# ============================================
# Service Tests
# ============================================

class TestEmbeddingService:
    """Tests for high-level embedding service"""
    
    @pytest.mark.asyncio
    async def test_ingest_success(self, embedding_service, mock_embedding_provider, mock_embedding_repository):
        """Test successful content ingestion"""
        # Arrange
        content = "Test content to ingest"
        metadata = {"source": "test"}
        
        # Act
        result = await embedding_service.ingest(content, metadata)
        
        # Assert
        assert result == 1
        mock_embedding_provider.generate_embedding.assert_called_once_with(content)
        mock_embedding_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar(self, embedding_service, mock_embedding_provider, mock_embedding_repository):
        """Test similarity search"""
        # Arrange
        query = "test query"
        
        # Act
        results = await embedding_service.search_similar(query, limit=5)
        
        # Assert
        assert len(results) == 1
        assert results[0]["similarity"] == 0.95
        mock_embedding_provider.generate_embedding.assert_called_once_with(query, task_type="retrieval_query")
        mock_embedding_repository.find_similar.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_embedding(self, embedding_service, mock_embedding_repository):
        """Test embedding deletion"""
        # Act
        await embedding_service.delete_embedding(1)
        
        # Assert
        mock_embedding_repository.delete.assert_called_once_with(1)


# ============================================
# Integration Tests
# ============================================

@pytest.mark.integration
class TestEmbeddingIntegration:
    """Integration tests (require real database)"""
    
    @pytest.mark.skip(reason="Requires database connection")
    def test_full_workflow(self):
        """Test complete workflow from ingestion to search"""
        # This would test with a real database connection
        pass
