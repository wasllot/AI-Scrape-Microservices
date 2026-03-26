from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import timedelta
import os
import logging
import secrets

logger = logging.getLogger(__name__)

try:
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    # Fallback if specific exception not available
    resourceExhausted = None

from app.config import settings
from app.security import sanitize_input, create_access_token, get_current_user, verify_password, get_password_hash
from app.monitoring import metrics, HealthChecker, get_correlation_id
from app.data_management import DataValidator, DataHasher

health_checker = HealthChecker("ai-service")

# ... imports ...

from app.writing.service import ScriptWriterService

# Dependency injection for ScriptWriterService
def get_writing_service() -> ScriptWriterService:
    """Dependency injection for ScriptWriterService."""
    return ScriptWriterService()

app = FastAPI(
    # ... attributes ...
)

# Global Exception Handler for Rate Limits
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client_host": request.client.host if request.client else None,
        "headers": {k: v for k, v in request.headers.items() if k.lower() not in ['authorization', 'cookie']}
    }
    
    # Check for ResourceExhausted or 429 in message
    if (ResourceExhausted and isinstance(exc, ResourceExhausted)) or "429" in error_msg or "Resource has been exhausted" in error_msg:
        logging.warning(f"Rate limit exceeded | Request: {request_info} | Error: {error_msg}")
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Please wait before making more requests.",
                "error_type": "rate_limit",
                "retry_after": 60
            }
        )
    
    # Default behavior for other exceptions
    logging.error(f"Unhandled exception | Request: {request_info} | Error: {error_msg}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_type": "internal_error"}
    )
    
    # Default behavior for other exceptions
    logging.error(f"Global error: {error_msg}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": error_msg}
    )

# CORS middleware
# ...
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
    allow_origins=settings.allowed_origins_list,
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
    
    try:
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
    print(f"📊 Database: {settings.postgres_host}:{settings.postgres_port}")
    print(f"🤖 Model: {settings.chat_model}")
    
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


class Token(BaseModel):
    """Response model for JWT token"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Request model for login"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


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
    db_healthy = False
    try:
        db_healthy = test_connection()
    except Exception:
        pass
    
    gemini_status = "configured" if settings.gemini_api_key else "missing_key"
    
    overall_status = "healthy"
    if not db_healthy:
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "service": "ai-service",
        "database": "connected" if db_healthy else "error",
        "gemini_api": gemini_status,
        "version": "2.0.0",
        "dependencies": {
            "database": {"status": "healthy" if db_healthy else "unhealthy"},
            "gemini": {"status": "healthy" if gemini_status == "configured" else "unhealthy"}
        }
    }


@app.get(
    "/metrics",
    summary="Service Metrics",
    description="Returns service metrics including request counts, timings, and errors",
    tags=["Monitoring"]
)
async def get_metrics():
    """Get service metrics"""
    return metrics.get_metrics()


@app.post(
    "/token",
    response_model=Token,
    summary="Obtener Token JWT",
    description="Endpoint para obtener token de acceso JWT",
    tags=["Authentication"]
)
async def login(request: LoginRequest):
    """
    Login endpoint to get JWT token.
    
    For demo purposes, accepts any username with password "admin".
    In production, validate against a user database.
    """
    if not (secrets.compare_digest(request.username, settings.admin_username) and 
            secrets.compare_digest(request.password, settings.admin_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get(
    "/health/ready",
    summary="Readiness Check",
    description="Kubernetes-style readiness probe",
    tags=["Monitoring"]
)
async def readiness_check():
    """ readiness probe for Kubernetes"""
    db_ready = False
    try:
        db_ready = test_connection()
    except Exception:
        pass
    
    if not db_ready:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database unavailable"}
        )
    
    return {"status": "ready"}


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
    service: EmbeddingService = Depends(get_embedding_service),
    current_user: dict = Depends(get_current_user)
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
        # Input validation and sanitization
        sanitized_content = sanitize_input(request.content, max_length=10000)
        
        # Data validation if enabled
        if settings.data_validation_enabled:
            validation = DataValidator.validate_content(sanitized_content)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=validation["error"])
            
            # PII sanitization if enabled
            if settings.pii_sanitization_enabled and validation.get("contains_pii"):
                sanitized_content = DataValidator.sanitize_pii(sanitized_content)
                logger.warning(f"PII detected and sanitized in content")
        
        # Metadata validation
        if request.metadata:
            metadata_validation = DataValidator.validate_metadata(request.metadata)
            if not metadata_validation["valid"]:
                raise HTTPException(status_code=400, detail=metadata_validation["error"])
        
        sanitized_source = sanitize_input(request.source, max_length=100) if request.source else "unknown"
        
        metadata = request.metadata or {}
        metadata['source'] = sanitized_source
        
        embedding_id = await service.ingest(
            content=sanitized_content,
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
    service: RAGChatService = Depends(get_chat_service),
    current_user: dict = Depends(get_current_user)
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
    sanitized_question = sanitize_input(request.question, max_length=1000)
    sanitized_conversation_id = sanitize_input(request.conversation_id, max_length=100) if request.conversation_id else None
    
    response = await service.generate_response(
        question=sanitized_question,
        conversation_id=sanitized_conversation_id,
        max_context_items=request.max_context_items
    )
    
    return response


class WelcomeRequest(BaseModel):
    """Request model for welcome message"""
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID de conversación opcional para recuperar contexto"
    )

class WelcomeResponse(BaseModel):
    """Response model for welcome message"""
    message: str = Field(..., description="Mensaje de bienvenida generado")
    conversation_id: str = Field(..., description="ID de la conversación")


@app.post(
    "/chat/welcome",
    response_model=WelcomeResponse,
    summary="Mensaje de Bienvenida",
    description="Genera un saludo inteligente, nuevo o de retorno",
    tags=["RAG Chat"]
)
async def welcome_message(
    request: WelcomeRequest,
    service: RAGChatService = Depends(get_chat_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para obtener mensaje de bienvenida.
    """
    try:
        response = await service.generate_welcome(
            conversation_id=request.conversation_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/embeddings/{embedding_id}",
    summary="Eliminar Embedding",
    description="Elimina un embedding específico de la base de datos",
    tags=["Data Management"]
)
async def delete_embedding(
    embedding_id: int,
    service: EmbeddingService = Depends(get_embedding_service),
    current_user: dict = Depends(get_current_user)
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
# Writing/Script Improvement Endpoints
# ============================================

class WritingImproveRequest(BaseModel):
    """Request model for script improvement"""
    content: str = Field(..., description="Contenido del guión a mejorar", min_length=1)
    tone: Optional[str] = Field(default="professional", description="Tono deseado: formal, professional, casual, dynamic, friendly, authoritative")
    target_audience: Optional[str] = Field(default="general", description="Audiencia objetivo")
    purpose: Optional[str] = Field(default=None, description="Propósito del guión")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Mi nombre es Juan y soy desarrollador...",
                "tone": "professional",
                "target_audience": "reclutadores",
                "purpose": "presentacion personal"
            }
        }


class WritingStructureRequest(BaseModel):
    """Request model for structure improvement"""
    content: str = Field(..., description="Contenido del guión a reestructurar", min_length=1)
    technique: Optional[str] = Field(default="storytelling", description="Técnica: storytelling, aida, pas, hero_journey, three_act, inverted_pyramid, rule_of_three")
    tone: Optional[str] = Field(default="professional", description="Tono deseado")
    target_audience: Optional[str] = Field(default="general", description="Audiencia objetivo")


class WritingToneRequest(BaseModel):
    """Request model for tone change"""
    content: str = Field(..., description="Contenido del guión", min_length=1)
    tone: str = Field(..., description="Nuevo tono: formal, professional, casual, dynamic, friendly, authoritative")


class WritingExpandRequest(BaseModel):
    """Request model for script expansion"""
    content: str = Field(..., description="Contenido a expandir", min_length=1)
    factor: Optional[str] = Field(default="medium", description="Factor: short (30%), medium (50%), long (100%)")


class WritingSummarizeRequest(BaseModel):
    """Request model for summarization"""
    content: str = Field(..., description="Contenido a resumir", min_length=1)
    length: Optional[str] = Field(default="medium", description="Longitud: short (20%), medium (35%), long (50%)")


class WritingAdaptRequest(BaseModel):
    """Request model for format adaptation"""
    content: str = Field(..., description="Contenido a adaptar", min_length=1)
    format_type: str = Field(..., description="Formato destino: video, podcast, linkedin, presentation")
    target_audience: Optional[str] = Field(default="general", description="Audiencia objetivo")


class WritingAnalyzeRequest(BaseModel):
    """Request model for quality analysis"""
    content: str = Field(..., description="Contenido a analizar", min_length=1)
    keywords: Optional[List[str]] = Field(default=None, description="Palabras clave para análisis SEO")


@app.post(
    "/writing/improve",
    summary="Mejorar Guión",
    description="Mejora un guión existente con mejor fluidez, gramática y engagement",
    tags=["Script Writing"]
)
async def improve_script(
    request: WritingImproveRequest,
    service: ScriptWriterService = Depends(get_writing_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Mejora un guión existente.
    
    - **content**: El guión original
    - **tone**: Tono deseado (formal, professional, casual, dynamic, friendly, authoritative)
    - **target_audience**: Audiencia objetivo
    - **purpose**: Propósito opcional del guión
    """
    try:
        result = await service.improve(
            content=request.content,
            tone=request.tone,
            target_audience=request.target_audience,
            purpose=request.purpose
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/writing/structure",
    summary="Reestructurar con Técnica",
    description="Reestructura el guión usando una técnica específica de escritura",
    tags=["Script Writing"]
)
async def improve_structure(
    request: WritingStructureRequest,
    service: ScriptWriterService = Depends(get_writing_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Reestructura el guión usando técnicas narrativas avanzadas.
    
    Técnicas disponibles:
    - **storytelling**: Narrativa con personajes y arco dramático
    - **aida**: Atención → Interés → Deseo → Acción
    - **pas**: Problema → Agitación → Solución
    - **hero_journey**: Viaje del héroe (12 pasos)
    - **three_act**: Setup → Confrontation → Resolution
    - **inverted_pyramid**: Conclusión primero
    - **rule_of_three**: Tres puntos clave por sección
    """
    try:
        result = await service.improve_structure(
            content=request.content,
            technique=request.technique,
            tone=request.tone,
            target_audience=request.target_audience
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/writing/tone",
    summary="Cambiar Tono",
    description="Cambia el tono del guión sin modificar el contenido",
    tags=["Script Writing"]
)
async def change_tone(
    request: WritingToneRequest,
    service: ScriptWriterService = Depends(get_writing_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Cambia el tono del guión.
    
    Tonos disponibles: formal, professional, casual, dynamic, friendly, authoritative
    """
    try:
        result = await service.change_tone(
            content=request.content,
            tone=request.tone
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/writing/expand",
    summary="Expandir Guión",
    description="Expande el guión añadiendo más detalles y contexto",
    tags=["Script Writing"]
)
async def expand_script(
    request: WritingExpandRequest,
    service: ScriptWriterService = Depends(get_writing_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Expande el guión manteniendo su esencia.
    
    Factores: short (30%), medium (50%), long (100%)
    """
    try:
        result = await service.expand(
            content=request.content,
            factor=request.factor
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/writing/summarize",
    summary="Resumir Guión",
    description="Resume el guión manteniendo los puntos esenciales",
    tags=["Script Writing"]
)
async def summarize_script(
    request: WritingSummarizeRequest,
    service: ScriptWriterService = Depends(get_writing_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Resume el guión.
    
    Longitudes: short (20%), medium (35%), long (50%)
    """
    try:
        result = await service.summarize(
            content=request.content,
            length=request.length
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/writing/adapt",
    summary="Adaptar Formato",
    description="Adapta el guión a un formato específico",
    tags=["Script Writing"]
)
async def adapt_format(
    request: WritingAdaptRequest,
    service: ScriptWriterService = Depends(get_writing_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Adapta el guión a diferentes formatos.
    
    Formatos:
    - **video**: Script con hooks, transiciones y CTAs
    - **podcast**: Formato conversacional con notas de audio
    - **linkedin**: Post optimizado para LinkedIn
    - **presentation**: Slides con notas del speaker
    """
    try:
        result = await service.adapt_format(
            content=request.content,
            format_type=request.format_type,
            target_audience=request.target_audience
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/writing/analyze",
    summary="Analizar Calidad",
    description="Analiza la calidad del guión (legibilidad, SEO, estructura, duración)",
    tags=["Script Writing"]
)
async def analyze_script(
    request: WritingAnalyzeRequest,
    service: ScriptWriterService = Depends(get_writing_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Analiza la calidad del guión.
    
    Incluye:
    - Legibilidad (Flesch-Kincaid, Flesch Reading Ease)
    - Estructura (intro, desarrollo, conclusión)
    - SEO (densidad de keywords, estructura de encabezados)
    - Duración estimada (lectura y speaking)
    - Flags de calidad (clichés, redundancia, voz pasiva)
    """
    try:
        result = await service.analyze(
            content=request.content,
            keywords=request.keywords
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Startup/Shutdown Events
# ============================================



@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print(f"👋 Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
