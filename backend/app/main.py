"""
Lawyerless FastAPI application main entry point.

This module sets up the FastAPI application with CORS, middleware, 
error handling, and routes for Brazilian contract analysis.
"""

import logging
import traceback
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
from starlette.exceptions import HTTPException as StarletteHTTPException

from .settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Max file size: {settings.max_file_size / (1024*1024):.1f}MB")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Lawyerless API")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para análise de contratos de investimento em português brasileiro",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add trusted host middleware for security
if settings.app_env == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual domains in production
    )


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with Portuguese error messages."""
    
    error_messages = {
        400: "Requisição inválida",
        401: "Não autorizado", 
        403: "Acesso negado",
        404: "Recurso não encontrado",
        413: "Arquivo muito grande",
        415: "Tipo de arquivo não suportado",
        422: "Dados inválidos",
        429: "Muitas requisições",
        500: "Erro interno do servidor",
        503: "Serviço indisponível"
    }
    
    message = error_messages.get(exc.status_code, exc.detail)
    
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": message,
            "detail": exc.detail if settings.debug else None,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with Portuguese messages."""
    
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Dados de entrada inválidos",
            "detail": exc.errors() if settings.debug else None,
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    
    error_id = f"err_{hash(str(exc))}"
    
    logger.error(f"Unexpected error {error_id} on {request.url.path}: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Erro interno do servidor",
            "error_id": error_id,
            "detail": str(exc) if settings.debug else None,
            "status_code": 500
        }
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    
    logger.info(f"{request.method} {request.url.path} - Client: {request.client.host}")
    
    response = await call_next(request)
    
    logger.info(f"Response: {response.status_code} - Path: {request.url.path}")
    
    return response


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Check API health status.
    
    Returns basic health information including version and configuration.
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "llm_provider": settings.llm_provider,
        "max_file_size_mb": round(settings.max_file_size / (1024*1024), 1),
        "supported_formats": settings.allowed_file_types,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


# API Info endpoint
@app.get("/", tags=["Info"])
async def root() -> Dict[str, Any]:
    """
    API root endpoint with basic information.
    
    Returns API information and available endpoints.
    """
    return {
        "message": "Lawyerless - Análise de Contratos de Investimento",
        "description": "API para análise automatizada de documentos legais brasileiros",
        "version": settings.app_version,
        "docs_url": "/docs" if settings.debug else None,
        "health_check": "/health",
        "supported_documents": [
            "SAFE (Simple Agreement for Future Equity)",
            "Mútuo Conversível",
            "Term Sheet",
            "Acordo de Acionistas/Quotistas",
            "Side Letters"
        ],
        "features": [
            "Análise cláusula por cláusula",
            "Bandeiras de risco (Verde/Amarelo/Vermelho)", 
            "Perguntas para negociação",
            "Extração de dados estruturados",
            "Explicações em português brasileiro"
        ]
    }


# Include API routes
from .api.routes import router as api_router  # noqa: E402
app.include_router(api_router, prefix="/api/v1", tags=["Analysis"])


if __name__ == "__main__":
    """Run the application directly."""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )