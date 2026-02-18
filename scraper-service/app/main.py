"""
Universal Scraper Service - Main Application

FastAPI application with dependency injection and comprehensive documentation.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Optional, List
import asyncio

from app.config import settings
from app.security import sanitize_css_selector, sanitize_url
from app.monitoring import metrics
from app.scrapers.base import (
    ScraperService,
    JobPostingScraper,
    ExtractionRule,
    ScrapedData
)

# ============================================
# Application Setup
# ============================================

app = FastAPI(
    title="Universal Scraper Service",
    description="""
    Servicio universal de web scraping con soporte para JavaScript rendering.
    
    ## Características
    
    * **Scraping Universal**: Extrae datos de cualquier sitio web
    * **JavaScript Rendering**: Usa Playwright para contenido dinámico
    * **Reglas Personalizables**: Define tus propias reglas de extracción
    * **Caché Inteligente**: Reduce llamadas redundantes
    * **Scrapers Especializados**: Scrapers pre-configurados para casos comunes
    
    ## Tecnologías
    
    * FastAPI para la API REST
    * Playwright para navegación y JavaScript
    * BeautifulSoup4 para parsing HTML
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
# Global Scraper Instance
# ============================================

_scraper_service: Optional[ScraperService] = None
_job_scraper: Optional[JobPostingScraper] = None


def get_scraper_service() -> ScraperService:
    """
    Dependency injection for ScraperService.
    
    Returns:
        Singleton ScraperService instance
    """
    global _scraper_service
    if _scraper_service is None:
        _scraper_service = ScraperService()
    return _scraper_service


def get_job_scraper() -> JobPostingScraper:
    """
    Dependency injection for JobPostingScraper.
    
    Returns:
        Singleton JobPostingScraper instance
    """
    global _job_scraper
    if _job_scraper is None:
        scraper = get_scraper_service()
        _job_scraper = JobPostingScraper(scraper_service=scraper)
    return _job_scraper


# ============================================
# Request/Response Models
# ============================================

class ExtractionRuleModel(BaseModel):
    """Model for extraction rules"""
    selector: str = Field(
        ...,
        description="CSS selector para el elemento",
        examples=["h1.title", ".price", "a[href]"]
    )
    attribute: Optional[str] = Field(
        default=None,
        description="Atributo HTML a extraer (None para texto)",
        examples=["href", "src", "data-id"]
    )
    multiple: bool = Field(
        default=False,
        description="Extraer todos los elementos que coincidan"
    )


class ScrapeRequest(BaseModel):
    """Request model for generic scraping"""
    url: HttpUrl = Field(
        ...,
        description="URL a scrapear",
        examples=["https://example.com/page"]
    )
    extraction_rules: Dict[str, ExtractionRuleModel] = Field(
        ...,
        description="Reglas de extracción (nombre_campo -> regla)"
    )
    use_cache: bool = Field(
        default=True,
        description="Usar caché si está disponible"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/product",
                "extraction_rules": {
                    "title": {"selector": "h1.product-title"},
                    "price": {"selector": ".price"},
                    "images": {"selector": "img.product-image", "attribute": "src", "multiple": True}
                },
                "use_cache": True
            }
        }


class JobScrapeRequest(BaseModel):
    """Request model for job posting scraping"""
    url: HttpUrl = Field(
        ...,
        description="URL de la oferta de trabajo",
        examples=["https://example.com/jobs/123"]
    )


class ScrapeResponse(BaseModel):
    """Response model for scraping"""
    success: bool = Field(..., description="Indica si el scraping fue exitoso")
    url: str = Field(..., description="URL scrapeada")
    title: Optional[str] = Field(None, description="Título de la página")
    data: Dict = Field(..., description="Datos extraídos")
    metadata: Optional[Dict] = Field(None, description="Metadatos adicionales")
    error: Optional[str] = Field(None, description="Mensaje de error si falló")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Estado del servicio")
    playwright: str = Field(..., description="Estado de Playwright")
    cache: str = Field(..., description="Estado del caché")
    version: str = Field(..., description="Versión del servicio")


# ============================================
# Endpoints
# ============================================

@app.get(
    "/",
    summary="Información del servicio",
    description="Retorna información básica sobre el servicio"
)
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.app_name,
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "extract": "/extract",
            "scrape_job": "/scrape/job-posting"
        },
        "documentation": "/docs"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verifica el estado del servicio",
    tags=["Monitoring"]
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Estado del servicio y sus componentes
    """
    return {
        "status": "ok",
        "service": "scraper-service",
        "playwright": "ready",
        "cache": "enabled" if settings.cache_enabled else "disabled",
        "version": "2.0.0",
        "dependencies": {
            "cache": {"status": "healthy" if settings.cache_enabled else "disabled"},
            "playwright": {"status": "healthy"}
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


@app.get(
    "/health/ready",
    summary="Readiness Check",
    description="Kubernetes-style readiness probe",
    tags=["Monitoring"]
)
async def readiness_check():
    """Readiness probe for Kubernetes"""
    return {"status": "ready"}


@app.post(
    "/extract",
    response_model=ScrapeResponse,
    summary="Scraping Universal",
    description="Extrae datos de cualquier URL usando reglas personalizadas",
    tags=["Scraping"],
    status_code=200
)
async def extract_data(
    request: ScrapeRequest,
    scraper: ScraperService = Depends(get_scraper_service)
):
    """
    Endpoint para scraping genérico con reglas personalizadas.
    
    **Proceso:**
    1. Navega a la URL con Playwright
    2. Renderiza JavaScript
    3. Extrae datos según reglas CSS
    4. Cachea resultados
    
    **Casos de uso:**
    - Extraer precios de productos
    - Obtener datos de perfiles
    - Scrapear listados
    
    Args:
        request: URL y reglas de extracción
        scraper: Servicio de scraping (inyectado)
        
    Returns:
        Datos extraídos
        
    Raises:
        HTTPException: Si falla el scraping
    """
    try:
        sanitized_url = sanitize_url(str(request.url))
        
        rules = {
            field_name: ExtractionRule(
                selector=sanitize_css_selector(rule.selector),
                attribute=rule.attribute,
                multiple=rule.multiple
            )
            for field_name, rule in request.extraction_rules.items()
        }
        
        result: ScrapedData = await scraper.scrape(
            url=sanitized_url,
            extraction_rules=rules,
            use_cache=request.use_cache
        )
        
        return ScrapeResponse(
            success=result.success,
            url=result.url,
            title=result.title,
            data=result.data or {},
            metadata=result.metadata,
            error=result.error
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@app.post(
    "/scrape/job-posting",
    response_model=ScrapeResponse,
    summary="Scrapear Oferta de Trabajo",
    description="Scraper especializado para ofertas de trabajo",
    tags=["Specialized Scrapers"]
)
async def scrape_job_posting(
    request: JobScrapeRequest,
    job_scraper: JobPostingScraper = Depends(get_job_scraper)
):
    """
    Endpoint especializado para scrapear ofertas de trabajo.
    
    **Extrae automáticamente:**
    - Título del puesto
    - Empresa
    - Ubicación
    - Descripción
    - Requisitos
    - Salario
    
    Args:
        request: URL de la oferta
        job_scraper: Scraper especializado (inyectado)
        
    Returns:
        Datos de la oferta de trabajo
        
    Raises:
        HTTPException: Si falla el scraping
    """
    try:
        sanitized_url = sanitize_url(str(request.url))
        result: ScrapedData = await job_scraper.scrape_job(sanitized_url)
        
        return ScrapeResponse(
            success=result.success,
            url=result.url,
            title=result.title,
            data=result.data or {},
            metadata=result.metadata,
            error=result.error
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Job scraping failed: {str(e)}"
        )


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print(f"🚀 Starting {settings.app_name}")
    print(f"🎭 Playwright headless: {settings.headless}")
    print(f"💾 Cache enabled: {settings.cache_enabled}")
    print(f"⏱️  Timeout: {settings.timeout}ms")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print(f"👋 Shutting down {settings.app_name}")
    
    # Cleanup scrapers
    global _scraper_service, _job_scraper
    if _scraper_service:
        await _scraper_service.cleanup()
    if _job_scraper:
        await _job_scraper.cleanup()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
