"""
AI & RAG Engine - Main Application

FastAPI application with dependency injection and comprehensive documentation.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os

from app.config import settings
from app.rag.embeddings import EmbeddingService
from app.rag.chat import RAGChatService
from app.database import get_db_connection, test_connection
import glob
from pathlib import Path

# ============================================
# Application Setup
# ============================================

app = FastAPI(
    title="AI & RAG Engine",
    description="""
    Servicio de Inteligencia Artificial con capacidades RAG (Retrieval-Augmented Generation).
    
    ## Características
    
    * **Ingesta de Datos**: Convierte texto en embeddings vectoriales
    * **Búsqueda Semántica**: Encuentra contenido similar usando vectores
    * **Chat RAG**: Genera respuestas contextuales basadas en datos almacenados
    * **Memoria de Conversación**: Mantiene contexto entre mensajes
    
    ## Tecnologías
    
    * FastAPI para la API REST
    * Gemini API para embeddings y generación de texto
    * PostgreSQL con pgvector para almacenamiento vectorial
    * Arquitectura basada en principios SOLID
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Database Migrations
# ============================================

def run_migrations():
    """
    Run SQL migrations from migrations directory.
    
    Executes all .sql files in migrations/ directory in alphabetical order.
    This is idempotent - migrations use IF NOT EXISTS clauses.
    """
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    if not migrations_dir.exists():
        print("⚠ No migrations directory found")
        return
    
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("⚠ No migration files found")
        return
    
    print(f"\n🔄 Running {len(migration_files)} migration(s)...")
    
    db = get_db_connection()
    db._ensure_connection()
    
    for migration_file in migration_files:
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # Execute migration using raw cursor (DDL doesn't return results)
            db._cursor.execute(sql)
            db.commit()
            print(f"✓ Applied: {migration_file.name}")
            
        except Exception as e:
            print(f"✗ Failed to apply {migration_file.name}: {e}")
            raise
        finally:
            db.close()
    
    print("✓ All migrations completed\n")


@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks.
    
    - Test database connection
    - Run migrations
    """
    print("\n" + "="*50)
    print("🚀 AI Service Starting Up")
    print("="*50)
    
    # Test database connection
    if not test_connection():
        raise Exception("Database connection failed")
    
    # Run migrations
    run_migrations()
    
    print("✓ Startup complete\n")

# ============================================
# Dependency Injection
# ============================================

def get_embedding_service() -> EmbeddingService:
    """
    Dependency injection for EmbeddingService.
    
    Returns:
        Configured EmbeddingService instance
    """
    return EmbeddingService()


def get_chat_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> RAGChatService:
    """
    Dependency injection for RAGChatService.
    
    Args:
        embedding_service: Injected embedding service
        
    Returns:
        Configured RAGChatService instance
    """
    return RAGChatService(embedding_service=embedding_service)


# ============================================
# Request/Response Models
# ============================================

class IngestRequest(BaseModel):
    """Request model for data ingestion"""
    content: str = Field(
        ..., 
        description="Texto a procesar y convertir en embeddings",
        min_length=1,
        max_length=10000,
        examples=["Juan Pérez - Desarrollador Full Stack con 5 años de experiencia"]
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Metadatos adicionales (tipo, fuente, fecha, etc.)",
        examples=[{"type": "cv", "candidate": "Juan Pérez"}]
    )
    source: Optional[str] = Field(
        default="unknown",
        description="Fuente del contenido",
        examples=["upload", "scraper", "api"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "María González - Ingeniera de Software con experiencia en Python y FastAPI",
                "metadata": {"type": "cv", "candidate": "María González"},
                "source": "upload"
            }
        }


class IngestResponse(BaseModel):
    """Response model for ingestion"""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    embedding_id: int = Field(..., description="ID del embedding almacenado")
    message: str = Field(..., description="Mensaje descriptivo")


class ChatRequest(BaseModel):
    """Request model for RAG chat"""
    question: str = Field(
        ...,
        description="Pregunta del usuario",
        min_length=1,
        max_length=1000,
        examples=["¿Qué candidatos tienen experiencia en Python?"]
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID de conversación para mantener contexto"
    )
    max_context_items: Optional[int] = Field(
        default=5,
        description="Número de documentos a recuperar",
        ge=1,
        le=20
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "¿Qué experiencia tiene en desarrollo web?",
                "max_context_items": 5
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat"""
    answer: str = Field(..., description="Respuesta generada por el asistente")
    sources: List[dict] = Field(..., description="Fuentes utilizadas para la respuesta")
    conversation_id: str = Field(..., description="ID de la conversación")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Estado general del servicio")
    database: str = Field(..., description="Estado de la base de datos")
    gemini_api: str = Field(..., description="Estado de Gemini API")
    version: str = Field(..., description="Versión del servicio")


# ============================================
# Endpoints
# ============================================

@app.get(
    "/",
    summary="Información del servicio",
    description="Retorna información básica sobre el servicio y sus endpoints disponibles"
)
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.app_name,
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "ingest": "/ingest",
            "chat": "/chat"
        },
        "documentation": "/docs"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verifica el estado del servicio y sus dependencias",
    tags=["Monitoring"]
)
async def health_check():
    """
    Health check endpoint.
    
    Verifica:
    - Conexión a base de datos
    - Configuración de Gemini API
    - Estado general del servicio
    
    Returns:
        Estado del servicio y sus dependencias
    """
    try:
        db_status = "connected" if test_connection() else "error"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    gemini_status = "configured" if settings.gemini_api_key else "missing_key"
    
    return {
        "status": "ok",
        "service": "ai-service",
        "database": db_status,
        "gemini_api": gemini_status,
        "version": "2.0.0"
    }


@app.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingestar Datos",
    description="Convierte texto en embeddings y los almacena en la base vectorial",
    tags=["Data Ingestion"],
    status_code=201
)
async def ingest_data(
    request: IngestRequest,
    service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Endpoint para ingerir datos y crear embeddings.
    
    **Proceso:**
    1. Recibe el texto
    2. Genera embeddings con Gemini API
    3. Almacena en PostgreSQL con pgvector
    
    **Casos de uso:**
    - Ingestar CVs de candidatos
    - Almacenar ofertas de trabajo scrapeadas
    - Indexar documentación
    
    Args:
        request: Datos a ingestar
        service: Servicio de embeddings (inyectado)
        
    Returns:
        Confirmación con ID del embedding
        
    Raises:
        HTTPException: Si falla la ingesta
    """
    try:
        # Merge metadata
        metadata = request.metadata or {}
        metadata['source'] = request.source
        
        # Generate and store embedding
        embedding_id = await service.ingest(
            content=request.content,
            metadata=metadata
        )
        
        return {
            "success": True,
            "embedding_id": embedding_id,
            "message": f"Successfully ingested {len(request.content)} characters"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat RAG",
    description="Genera respuestas contextuales usando Retrieval-Augmented Generation",
    tags=["RAG Chat"]
)
async def chat(
    request: ChatRequest,
    service: RAGChatService = Depends(get_chat_service)
):
    """
    Endpoint para consultas RAG.
    
    **Proceso:**
    1. Busca contexto relevante en la base vectorial
    2. Construye prompt con contexto + historial
    3. Genera respuesta con Gemini
    4. Guarda en historial de conversación
    
    **Características:**
    - Búsqueda semántica de contexto
    - Memoria de conversación
    - Citas de fuentes
    
    Args:
        request: Pregunta y parámetros
        service: Servicio RAG (inyectado)
        
    Returns:
        Respuesta con fuentes y conversation_id
        
    Raises:
        HTTPException: Si falla la generación
    """
    try:
        response = await service.generate_response(
            question=request.question,
            conversation_id=request.conversation_id,
            max_context_items=request.max_context_items
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@app.delete(
    "/embeddings/{embedding_id}",
    summary="Eliminar Embedding",
    description="Elimina un embedding específico de la base de datos",
    tags=["Data Management"]
)
async def delete_embedding(
    embedding_id: int,
    service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Delete a specific embedding.
    
    Args:
        embedding_id: ID del embedding a eliminar
        service: Servicio de embeddings (inyectado)
        
    Returns:
        Confirmación de eliminación
        
    Raises:
        HTTPException: Si falla la eliminación
    """
    try:
        await service.delete_embedding(embedding_id)
        return {
            "success": True,
            "message": f"Embedding {embedding_id} deleted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print(f"🚀 Starting {settings.app_name}")
    print(f"📊 Database: {settings.postgres_host}:{settings.postgres_port}")
    print(f"🤖 Model: {settings.chat_model}")
    print(f"📐 Embedding dimension: {settings.embedding_dimension}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print(f"👋 Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
