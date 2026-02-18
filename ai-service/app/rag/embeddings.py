"""
Embedding Service Interfaces and Implementations

Following SOLID principles:
- Single Responsibility: Each class has one reason to change
- Open/Closed: Open for extension, closed for modification
- Dependency Inversion: Depend on abstractions, not concretions
"""
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Protocol
import google.generativeai as genai
from app.config import settings
from app.database import DatabaseConnection, get_db_connection
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type


class EmbeddingProvider(Protocol):
    """
    Protocol for embedding generation.
    
    This allows swapping between different providers (Gemini, OpenAI, etc.)
    without changing dependent code.
    """
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        ...
    
    @property
    def dimension(self) -> int:
        """Embedding vector dimension"""
        ...


class GeminiEmbeddingProvider:
    """
    Gemini API implementation of EmbeddingProvider.
    
    Generates embeddings using Google's Gemini API.
    """
    
    def __init__(
        self, 
        api_key: str = None,
        model_name: str = None,
        embedding_dim: int = None
    ):
        """
        Initialize Gemini embedding provider.
        
        Args:
            api_key: Gemini API key (uses settings if not provided)
            model_name: Model to use (uses settings if not provided)
            embedding_dim: Expected dimension (uses settings if not provided)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.embedding_model
        self._dimension = embedding_dim or settings.embedding_dimension
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        reraise=True
    )
    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Generate embedding using Gemini API.
        
        Args:
            text: Text to embed
            task_type: Type of task (retrieval_document, retrieval_query, etc.)
            
        Returns:
            Embedding vector
            
        Raises:
            Exception: If API call fails (after retries)
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            # Let tenacity handle the retry or re-raise if attempts exhausted
            raise e
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension"""
        return self._dimension


class EmbeddingRepository(ABC):
    """
    Abstract repository for embedding storage.
    
    Follows Repository pattern to separate data access logic.
    """
    
    @abstractmethod
    def save(self, content: str, embedding: List[float], metadata: Dict) -> int:
        """Save embedding to storage"""
        ...
    
    @abstractmethod
    def find_similar(
        self, 
        query_embedding: List[float], 
        limit: int, 
        threshold: float
    ) -> List[Dict]:
        """Find similar embeddings"""
        ...
    
    @abstractmethod
    def delete(self, embedding_id: int) -> None:
        """Delete embedding by ID"""
        ...


class PostgreSQLEmbeddingRepository(EmbeddingRepository):
    """
    PostgreSQL implementation of EmbeddingRepository.
    
    Stores embeddings in PostgreSQL with pgvector extension.
    """
    
    def __init__(self, db_connection: DatabaseConnection = None):
        """
        Initialize repository.
        
        Args:
            db_connection: Database connection (uses default if not provided)
        """
        self.db = db_connection or get_db_connection()
    
    def save(self, content: str, embedding: List[float], metadata: Dict) -> int:
        """
        Save embedding to PostgreSQL.
        
        Args:
            content: Original text content
            embedding: Embedding vector
            metadata: Additional metadata
            
        Returns:
            ID of saved embedding
        """
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        metadata_json = json.dumps(metadata)

        result = self.db.execute_one(
            """
            INSERT INTO embeddings (content, embedding, metadata)
            VALUES (%s, %s::vector, %s)
            RETURNING id
            """,
            (content, embedding_str, metadata_json)
        )
        
        self.db.commit()
        return result['id']
    
    def find_similar(
        self, 
        query_embedding: List[float], 
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Find similar embeddings using cosine similarity.
        
        Args:
            query_embedding: Query vector
            limit: Maximum results
            threshold: Minimum similarity score
            
        Returns:
            List of similar documents with scores
        """
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        results = self.db.execute(
            """
            SELECT 
                id,
                content,
                metadata,
                1 - (embedding <=> %s::vector(768)) as similarity
            FROM embeddings
            WHERE 1 - (embedding <=> %s::vector(768)) > %s
            ORDER BY embedding <=> %s::vector(768)
            LIMIT %s
            """,
            (embedding_str, embedding_str, threshold, embedding_str, limit)
        )
        
        return results
    
    def delete(self, embedding_id: int) -> None:
        """
        Delete embedding by ID.
        
        Args:
            embedding_id: ID to delete
        """
        self.db.execute("DELETE FROM embeddings WHERE id = %s", (embedding_id,))
        self.db.commit()


class EmbeddingService:
    """
    High-level embedding service.
    
    Orchestrates embedding generation and storage.
    Depends on abstractions (protocols), not concrete implementations.
    """
    
    def __init__(
        self,
        provider: EmbeddingProvider = None,
        repository: EmbeddingRepository = None
    ):
        """
        Initialize service with dependency injection.
        
        Args:
            provider: Embedding provider (uses Gemini if not provided)
            repository: Storage repository (uses PostgreSQL if not provided)
        """
        self.provider = provider or GeminiEmbeddingProvider()
        self.repository = repository or PostgreSQLEmbeddingRepository()
    
    async def ingest(
        self, 
        content: str, 
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Ingest content: generate embedding and store.
        
        Args:
            content: Text to ingest
            metadata: Optional metadata
            
        Returns:
            ID of stored embedding
        """
        # Generate embedding
        embedding = self.provider.generate_embedding(content)
        
        # Save to repository
        embedding_id = self.repository.save(
            content=content,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        return embedding_id
    
    async def search_similar(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search for similar content.
        
        Args:
            query: Search query
            limit: Maximum results
            threshold: Minimum similarity
            
        Returns:
            List of similar documents
        """
        # Generate query embedding
        query_embedding = self.provider.generate_embedding(query, task_type="retrieval_query")
        
        # Search in repository
        results = self.repository.find_similar(
            query_embedding=query_embedding,
            limit=limit,
            threshold=threshold
        )
        
        return results
    
    async def delete_embedding(self, embedding_id: int) -> None:
        """
        Delete embedding.
        
        Args:
            embedding_id: ID to delete
        """
        self.repository.delete(embedding_id)
