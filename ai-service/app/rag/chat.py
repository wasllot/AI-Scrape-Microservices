"""
RAG Chat Service with SOLID Principles

Implements conversation management and response generation
following Single Responsibility and Dependency Inversion principles.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Protocol
import uuid
from datetime import datetime
import google.generativeai as genai

from app.config import settings
from app.rag.embeddings import EmbeddingService


class LLMProvider(Protocol):
    """
    Protocol for Language Model providers.
    
    Allows swapping between different LLM providers (Gemini, OpenAI, etc.)
    """
    
    def generate_response(self, prompt: str) -> str:
        """Generate text response from prompt"""
        ...


class GeminiLLMProvider:
    """
    Gemini implementation of LLM provider.
    """
    
    def __init__(self, api_key: str = None, model_name: str = None):
        """
        Initialize Gemini LLM provider.
        
        Args:
            api_key: Gemini API key
            model_name: Model to use for generation
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.chat_model
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate response using Gemini.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated text
        """
        response = self.model.generate_content(prompt)
        return response.text


class ConversationStore(ABC):
    """
    Abstract storage for conversation history.
    
    Follows Repository pattern for conversation persistence.
    """
    
    @abstractmethod
    def save_turn(
        self, 
        conversation_id: str, 
        question: str, 
        answer: str
    ) -> None:
        """Save a conversation turn"""
        ...
    
    @abstractmethod
    def get_history(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Retrieve conversation history"""
        ...


class InMemoryConversationStore(ConversationStore):
    """
    In-memory implementation of conversation storage.
    
    For production, replace with Redis or database implementation.
    """
    
    def __init__(self):
        self._conversations: Dict[str, List[Dict]] = {}
    
    def save_turn(
        self, 
        conversation_id: str, 
        question: str, 
        answer: str
    ) -> None:
        """
        Save conversation turn to memory.
        
        Args:
            conversation_id: Conversation identifier
            question: User question
            answer: Assistant answer
        """
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        
        self._conversations[conversation_id].append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 turns
        if len(self._conversations[conversation_id]) > 10:
            self._conversations[conversation_id] = self._conversations[conversation_id][-10:]
    
    def get_history(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum turns to return
            
        Returns:
            List of conversation turns
        """
        history = self._conversations.get(conversation_id, [])
        return history[-limit:]


class PostgresConversationStore(ConversationStore):
    """
    PostgreSQL implementation of conversation storage.
    
    Stores conversations and messages in PostgreSQL for persistence
    across service restarts.
    """
    
    def __init__(self, db_connection = None):
        """
        Initialize PostgreSQL conversation store.
        
        Args:
            db_connection: Database connection (uses default if not provided)
        """
        from app.database import get_db_connection
        self.db = db_connection or get_db_connection()
    
    def save_turn(
        self, 
        conversation_id: str, 
        question: str, 
        answer: str
    ) -> None:
        """
        Save conversation turn to PostgreSQL.
        
        Args:
            conversation_id: Conversation identifier (UUID)
            question: User question
            answer: Assistant answer
        """
        # Ensure conversation exists
        self.db.execute(
            """
            INSERT INTO conversations (id, created_at, updated_at)
            VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
            """,
            (conversation_id,),
            fetch_results=False
        )
        
        # Insert user message
        self.db.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (%s, 'user', %s, CURRENT_TIMESTAMP)
            """,
            (conversation_id, question),
            fetch_results=False
        )
        
        # Insert assistant message
        self.db.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (%s, 'assistant', %s, CURRENT_TIMESTAMP)
            """,
            (conversation_id, answer),
            fetch_results=False
        )
        
        self.db.commit()
    
    def get_history(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """
        Get conversation history from PostgreSQL.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum turns to return (each turn = 2 messages)
            
        Returns:
            List of conversation turns
        """
        # Get messages ordered by creation time
        messages = self.db.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            """,
            (conversation_id,)
        )
        
        # Group messages into turns (user + assistant pairs)
        turns = []
        i = 0
        while i < len(messages) - 1:
            if messages[i]['role'] == 'user' and messages[i + 1]['role'] == 'assistant':
                turns.append({
                    "question": messages[i]['content'],
                    "answer": messages[i + 1]['content'],
                    "timestamp": messages[i]['created_at'].isoformat()
                })
                i += 2
            else:
                i += 1
        
        # Return last N turns
        return turns[-limit:]



class PromptBuilder:
    """
    Builds prompts for RAG queries.
    
    Single Responsibility: Only handles prompt construction.
    """
    
    def __init__(self, system_instruction: str = None):
        """
        Initialize prompt builder.
        
        Args:
            system_instruction: Custom system instruction
        """
        self.system_instruction = system_instruction or self._default_instruction()
    
    def _default_instruction(self) -> str:
        """Default system instruction for RAG"""
        return """Eres un Asistente de IA profesional representando a Reinaldo Tineo. Tu objetivo es ayudar a reclutadores y técnicos a entender por qué Reinaldo es el candidato ideal.

Reglas de Comportamiento:
1. Responde siempre en primera persona del singular ("yo", "mi experiencia") como si fueras Reinaldo, o en tercera persona neutral ("el candidato") si te preguntan explícitamente sobre él. PREFERENCIA: Habla como un asistente profesional que conoce perfectamente a Reinaldo.
2. Usa SOLO la información del contexto proporcionado (CV, proyectos) para responder.
3. Si te preguntan por una tecnología o experiencia que NO está en el contexto, sé honesto: "No tengo información específica sobre esa herramienta en mi base de conocimientos actual, pero puedo contarte sobre mi experiencia en [tecnología similar]".
4. Destaca logros cuantificables y tecnologías clave (Laravel, PHP, Python, FastAPI, Docker, Microservicios).
5. Mantén un tono profesional, seguro y entusiasta, pero no arrogante.
6. Sé conciso pero ofrece detalles técnicos cuando la pregunta lo requiera.

Si el contexto está vacío y te saludan, preséntate brevemente como el asistente virtual de Reinaldo Tineo."""
    
    def build_context(self, documents: List[Dict]) -> str:
        """
        Build context string from retrieved documents.
        
        Args:
            documents: List of documents with content and metadata
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No se encontró contexto relevante en la base de datos."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'unknown')
            similarity = doc.get('similarity', 0)
            
            context_parts.append(
                f"[Documento {i} - Fuente: {source} - Similitud: {similarity:.2f}]\n{doc['content']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def build_history(self, history: List[Dict]) -> str:
        """
        Build history string from conversation turns.
        
        Args:
            history: List of conversation turns
            
        Returns:
            Formatted history string
        """
        if not history:
            return ""
        
        history_text = "\n\nHistorial de conversación:\n"
        for turn in history[-3:]:  # Last 3 turns only
            history_text += f"Usuario: {turn['question']}\nAsistente: {turn['answer']}\n\n"
        
        return history_text
    
    def build_prompt(
        self, 
        question: str, 
        context: str, 
        history: str = ""
    ) -> str:
        """
        Build complete prompt for LLM.
        
        Args:
            question: User question
            context: Retrieved context
            history: Conversation history
            
        Returns:
            Complete prompt
        """
        return f"""{self.system_instruction}

{history}

CONTEXTO DISPONIBLE:
{context}

PREGUNTA DEL USUARIO:
{question}

RESPUESTA:"""


class RAGChatService:
    """
    High-level RAG chat service.
    
    Orchestrates retrieval, prompt building, and response generation.
    Uses dependency injection for all dependencies.
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        llm_provider: LLMProvider = None,
        conversation_store: ConversationStore = None,
        prompt_builder: PromptBuilder = None
    ):
        """
        Initialize RAG chat service with dependencies.
        
        Args:
            embedding_service: Service for embedding operations
            llm_provider: LLM provider for generation
            conversation_store: Storage for conversations
            prompt_builder: Builder for prompts
        """
        self.embedding_service = embedding_service
        self.llm_provider = llm_provider or GeminiLLMProvider()
        self.conversation_store = conversation_store or PostgresConversationStore()
        self.prompt_builder = prompt_builder or PromptBuilder()
    
    async def generate_response(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        max_context_items: int = 5
    ) -> Dict:
        """
        Generate RAG response.
        
        Args:
            question: User question
            conversation_id: Optional conversation ID
            max_context_items: Number of documents to retrieve
            
        Returns:
            Response with answer, sources, and conversation ID
        """
        # Generate or use conversation ID
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Step 1: Retrieve relevant context
        context_documents = await self.embedding_service.search_similar(
            query=question,
            limit=max_context_items,
            threshold=0.5
        )
        
        # Step 2: Build context and history
        context_text = self.prompt_builder.build_context(context_documents)
        history = self.conversation_store.get_history(conversation_id)
        history_text = self.prompt_builder.build_history(history)
        
        # Step 3: Build prompt
        prompt = self.prompt_builder.build_prompt(
            question=question,
            context=context_text,
            history=history_text
        )
        
        # Step 4: Generate response
        answer = self.llm_provider.generate_response(prompt)
        
        # Step 5: Save conversation turn
        self.conversation_store.save_turn(
            conversation_id=conversation_id,
            question=question,
            answer=answer
        )
        
        # Step 6: Prepare response
        sources = [
            {
                "id": doc["id"],
                "content": doc["content"],  # Full content
                "text": doc["content"],     # Alias for compatibility
                "content_preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                "similarity": float(doc["similarity"]),
                "metadata": doc.get("metadata", {})
            }
            for doc in context_documents
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "conversation_id": conversation_id
        }

    async def generate_welcome(self, conversation_id: Optional[str] = None) -> Dict:
        """
        Generate a smart welcome message.
        
        Args:
            conversation_id: Optional existing conversation ID
            
        Returns:
            Dict with welcome message and conversation ID
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        # Check if conversation exists (has history)
        history = self.conversation_store.get_history(conversation_id)
        
        if history:
            prompt = """Eres el asistente virtual de Reinaldo Tineo.
            El usuario ha regresado a una conversación previa.
            Genera un saludo breve y cordial ("Bienvenido de nuevo...") invitándole a continuar la charla.
            Sé conciso (máximo 2 frases)."""
        else:
            prompt = """Eres el asistente virtual de Reinaldo Tineo.
            Un nuevo usuario acaba de iniciar el chat.
            Genera un saludo profesional, entusiasta y breve.
            Preséntate rápidamente indicando que puedes responder preguntas sobre la experiencia y habilidades de Reinaldo.
            (Máximo 2 frases)."""
            
        welcome_message = self.llm_provider.generate_response(prompt)
        
        return {
            "message": welcome_message,
            "conversation_id": conversation_id
        }
