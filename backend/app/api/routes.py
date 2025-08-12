"""
FastAPI routes for contract analysis API.

This module implements all API endpoints for PDF upload, processing,
and contract analysis with real-time updates via WebSockets.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import (
    APIRouter, 
    HTTPException, 
    UploadFile, 
    File, 
    WebSocket,
    WebSocketDisconnect,
    status,
    BackgroundTasks
)

from ..models import (
    ContractAnalysisResponse,
    AnalysisStatus
)
from ..services import PDFProcessor, ClauseSegmenter, ContractExtractor
from ..services.llm_providers import list_available_providers, get_provider_info
from ..services.langsmith_integration import get_tracing_status
from ..agents import analyze_contract_clauses
from ..settings import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# In-memory storage for analysis status (in production, use Redis or database)
analysis_status_store: Dict[str, Dict[str, Any]] = {}
analysis_results_store: Dict[str, ContractAnalysisResponse] = {}

# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, document_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        self.active_connections[document_id].append(websocket)
        logger.info(f"WebSocket connected for document {document_id}")
    
    def disconnect(self, websocket: WebSocket, document_id: str):
        """Remove WebSocket connection."""
        if document_id in self.active_connections:
            if websocket in self.active_connections[document_id]:
                self.active_connections[document_id].remove(websocket)
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
        logger.info(f"WebSocket disconnected for document {document_id}")
    
    async def send_status_update(self, document_id: str, status: Dict[str, Any]):
        """Send status update to all connected clients for a document."""
        if document_id in self.active_connections:
            connections = self.active_connections[document_id].copy()
            for connection in connections:
                try:
                    await connection.send_json(status)
                except Exception as e:
                    logger.error(f"Failed to send WebSocket update: {e}")
                    self.disconnect(connection, document_id)


# Global connection manager
manager = ConnectionManager()


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded PDF file.
    
    Args:
        file: Uploaded file
    
    Raises:
        HTTPException: If file is invalid
    """
    # Check file type
    if file.content_type not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Tipo de arquivo não suportado. Apenas PDF é permitido."
        )
    
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Arquivo deve ter extensão .pdf"
        )
    
    # File size will be checked during processing
    logger.info(f"PDF file validated: {file.filename}")


async def update_analysis_status(
    document_id: str, 
    status: str, 
    progress: int = 0, 
    message: str = "", 
    error_details: Optional[str] = None
):
    """Update analysis status and notify WebSocket clients."""
    status_update = {
        "document_id": document_id,
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "error_details": error_details
    }
    
    analysis_status_store[document_id] = status_update
    await manager.send_status_update(document_id, status_update)
    logger.info(f"Status updated for {document_id}: {status} ({progress}%)")


async def process_contract_analysis(
    file_content: bytes,
    filename: str,
    document_id: str,
    perspectiva: str = "fundador",
    llm_provider: Optional[str] = None
):
    """
    Background task to process contract analysis.
    
    Args:
        file_content: PDF file content
        filename: Original filename
        document_id: Document identifier
        perspectiva: Analysis perspective
    """
    try:
        await update_analysis_status(
            document_id, 
            "processing", 
            10, 
            "Iniciando processamento do PDF..."
        )
        
        # Step 1: PDF Processing
        logger.info(f"Starting PDF processing for {document_id}")
        pdf_processor = PDFProcessor()
        extraction_result = await pdf_processor.extract_text_with_coordinates(
            file_content, filename
        )
        
        await update_analysis_status(
            document_id, 
            "processing", 
            30, 
            "PDF processado. Segmentando cláusulas..."
        )
        
        # Step 2: Clause Segmentation
        logger.info(f"Starting clause segmentation for {document_id}")
        segmenter = ClauseSegmenter()
        clauses = await segmenter.segment_clauses(extraction_result)
        
        await update_analysis_status(
            document_id, 
            "processing", 
            50, 
            f"Identificadas {len(clauses)} cláusulas. Extraindo dados do contrato..."
        )
        
        # Step 3: Contract Summary Extraction
        logger.info(f"Starting contract extraction for {document_id}")
        extractor = ContractExtractor()
        contract_summary = await extractor.extract_contract_summary(
            extraction_result, clauses
        )
        
        await update_analysis_status(
            document_id, 
            "processing", 
            70, 
            "Dados extraídos. Analisando cláusulas com IA..."
        )
        
        # Step 4: LLM Analysis
        logger.info(f"Starting LLM analysis for {document_id} with provider: {llm_provider or settings.llm_provider}")
        analysis_result = await analyze_contract_clauses(
            extraction_result,
            clauses,
            contract_summary,
            perspectiva,
            llm_provider
        )
        
        # Store result
        analysis_results_store[document_id] = analysis_result
        
        await update_analysis_status(
            document_id, 
            "completed", 
            100, 
            f"Análise completa! {len(analysis_result.clauses)} cláusulas analisadas."
        )
        
        logger.info(f"Contract analysis completed successfully for {document_id}")
        
    except Exception as e:
        logger.error(f"Contract analysis failed for {document_id}: {str(e)}")
        await update_analysis_status(
            document_id,
            "failed",
            0,
            f"Falha na análise: {str(e)}",
            str(e)
        )


@router.post("/analyze", response_model=AnalysisStatus, status_code=status.HTTP_202_ACCEPTED)
async def upload_and_analyze_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    perspectiva: str = "fundador",
    llm_provider: Optional[str] = None
):
    """
    Upload PDF contract and start analysis.
    
    Args:
        file: PDF file to analyze
        perspectiva: Analysis perspective ("fundador" or "investidor")
    
    Returns:
        Analysis status with document ID
    """
    logger.info(f"Received file upload: {file.filename}, perspective: {perspectiva}")
    
    # Validate file
    validate_pdf_file(file)
    
    # Validate perspective
    if perspectiva not in ["fundador", "investidor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Perspectiva deve ser 'fundador' ou 'investidor'"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Check file size
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande. Máximo permitido: {settings.max_file_size / (1024*1024):.1f}MB"
            )
        
        # Generate document ID
        import hashlib
        content_hash = hashlib.md5(file_content).hexdigest()[:16]
        timestamp = int(datetime.now().timestamp())
        document_id = f"doc_{timestamp}_{content_hash}"
        
        # Initialize status
        await update_analysis_status(
            document_id,
            "pending", 
            0, 
            "Documento recebido. Aguardando processamento..."
        )
        
        # Validate LLM provider if specified
        if llm_provider and llm_provider not in ["openai", "lm_studio"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provedor LLM deve ser 'openai' ou 'lm_studio'"
            )
        
        # Start background processing
        background_tasks.add_task(
            process_contract_analysis,
            file_content,
            file.filename,
            document_id,
            perspectiva,
            llm_provider
        )
        
        return AnalysisStatus(
            document_id=document_id,
            status="pending",
            progress=0,
            message="Análise iniciada. Use WebSocket ou polling para acompanhar o progresso.",
            estimated_completion=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no upload: {str(e)}"
        )


@router.get("/analysis/{document_id}/status", response_model=AnalysisStatus)
async def get_analysis_status(document_id: str):
    """
    Get analysis status for a document.
    
    Args:
        document_id: Document identifier
    
    Returns:
        Current analysis status
    """
    if document_id not in analysis_status_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado"
        )
    
    status_info = analysis_status_store[document_id]
    
    return AnalysisStatus(
        document_id=document_id,
        status=status_info["status"],
        progress=status_info["progress"],
        message=status_info["message"],
        error_details=status_info.get("error_details")
    )


@router.get("/analysis/{document_id}", response_model=ContractAnalysisResponse)
async def get_analysis_result(document_id: str):
    """
    Get complete analysis result for a document.
    
    Args:
        document_id: Document identifier
    
    Returns:
        Complete contract analysis
    """
    # Check if analysis exists
    if document_id not in analysis_status_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado"
        )
    
    # Check if analysis is completed
    status_info = analysis_status_store[document_id]
    if status_info["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Análise ainda em andamento. Status: {status_info['status']}"
        )
    
    # Get result
    if document_id not in analysis_results_store:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resultado da análise não encontrado"
        )
    
    result = analysis_results_store[document_id]
    logger.info(f"Returning analysis result for {document_id}")
    
    return result


@router.delete("/analysis/{document_id}")
async def delete_analysis(document_id: str):
    """
    Delete analysis data for a document.
    
    Args:
        document_id: Document identifier
    
    Returns:
        Success message
    """
    # Remove from stores
    if document_id in analysis_status_store:
        del analysis_status_store[document_id]
    
    if document_id in analysis_results_store:
        del analysis_results_store[document_id]
    
    # Disconnect any WebSocket connections
    if document_id in manager.active_connections:
        connections = manager.active_connections[document_id].copy()
        for connection in connections:
            try:
                await connection.close()
            except Exception:
                pass
        del manager.active_connections[document_id]
    
    logger.info(f"Analysis data deleted for {document_id}")
    
    return {"message": "Análise removida com sucesso"}


@router.get("/analysis")
async def list_analyses():
    """
    List all analyses with their current status.
    
    Returns:
        List of analysis statuses
    """
    analyses = []
    
    for document_id, status_info in analysis_status_store.items():
        analyses.append({
            "document_id": document_id,
            "status": status_info["status"],
            "progress": status_info["progress"],
            "message": status_info["message"],
            "timestamp": status_info["timestamp"]
        })
    
    # Sort by timestamp (most recent first)
    analyses.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"analyses": analyses, "total": len(analyses)}


@router.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for real-time analysis updates.
    
    Args:
        websocket: WebSocket connection
        document_id: Document identifier to monitor
    """
    await manager.connect(websocket, document_id)
    
    try:
        # Send current status if available
        if document_id in analysis_status_store:
            await websocket.send_json(analysis_status_store[document_id])
        
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_text(f"pong: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(f"WebSocket error for {document_id}: {e}")
        manager.disconnect(websocket, document_id)


@router.post("/analyze/batch")
async def batch_analyze_contracts(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    perspectiva: str = "fundador",
    llm_provider: Optional[str] = None
):
    """
    Batch upload and analyze multiple contracts.
    
    Args:
        files: List of PDF files to analyze
        perspectiva: Analysis perspective
    
    Returns:
        List of document IDs and initial status
    """
    if len(files) > 10:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 10 arquivos por lote"
        )
    
    results = []
    
    for file in files:
        # Validate each file
        validate_pdf_file(file)
        
        # Process similar to single upload
        file_content = await file.read()
        
        if len(file_content) > settings.max_file_size:
            results.append({
                "filename": file.filename,
                "error": f"Arquivo muito grande (máx. {settings.max_file_size / (1024*1024):.1f}MB)"
            })
            continue
        
        # Generate document ID
        import hashlib
        content_hash = hashlib.md5(file_content).hexdigest()[:16]
        timestamp = int(datetime.now().timestamp())
        document_id = f"doc_{timestamp}_{content_hash}"
        
        # Initialize status
        await update_analysis_status(
            document_id,
            "pending",
            0,
            f"Arquivo {file.filename} na fila de processamento..."
        )
        
        # Start background processing
        background_tasks.add_task(
            process_contract_analysis,
            file_content,
            file.filename,
            document_id,
            perspectiva,
            llm_provider
        )
        
        results.append({
            "filename": file.filename,
            "document_id": document_id,
            "status": "pending"
        })
    
    logger.info(f"Batch upload completed: {len(results)} files")
    
    return {"results": results, "total": len(results)}


# LLM Provider Management Endpoints
@router.get("/llm/providers")
async def get_llm_providers():
    """
    Get list of available LLM providers with their configuration status.
    
    Returns:
        List of providers with their availability and configuration status
    """
    try:
        providers = list_available_providers()
        return {
            "providers": providers,
            "current_provider": settings.llm_provider,
            "total": len(providers)
        }
    except Exception as e:
        logger.error(f"Failed to get LLM providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao obter provedores LLM: {str(e)}"
        )


@router.get("/llm/provider/{provider_name}")
async def get_llm_provider_info(provider_name: str):
    """
    Get detailed information about a specific LLM provider.
    
    Args:
        provider_name: Name of the provider (openai, lm_studio)
    
    Returns:
        Provider configuration and status information
    """
    if provider_name not in ["openai", "lm_studio"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provedor deve ser 'openai' ou 'lm_studio'"
        )
    
    try:
        provider_info = get_provider_info(provider_name)
        return {
            "provider": provider_info,
            "is_current": provider_name == settings.llm_provider
        }
    except Exception as e:
        logger.error(f"Failed to get provider info for {provider_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao obter informações do provedor: {str(e)}"
        )


@router.post("/llm/provider/test/{provider_name}")
async def test_llm_provider(provider_name: str):
    """
    Test connection to a specific LLM provider.
    
    Args:
        provider_name: Name of the provider to test
    
    Returns:
        Test result with success/failure status
    """
    if provider_name not in ["openai", "lm_studio"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provedor deve ser 'openai' ou 'lm_studio'"
        )
    
    try:
        # Try to create a simple test analysis
        from ..services.llm_providers import LLMProviderFactory
        
        provider = LLMProviderFactory.get_provider(provider_name)
        provider_info = provider.get_provider_info()
        
        # Validate configuration
        is_valid = provider.validate_configuration()
        
        return {
            "provider": provider_name,
            "status": "success" if is_valid else "configuration_error",
            "message": "Provedor configurado corretamente" if is_valid else "Configuração inválida",
            "provider_info": provider_info,
            "test_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"LLM provider test failed for {provider_name}: {e}")
        return {
            "provider": provider_name,
            "status": "error",
            "message": f"Falha no teste: {str(e)}",
            "test_timestamp": datetime.now().isoformat()
        }


# Health check endpoint for the API routes
@router.get("/health")
async def api_health():
    """API-specific health check."""
    return {
        "status": "healthy",
        "active_analyses": len(analysis_status_store),
        "websocket_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "current_llm_provider": settings.llm_provider,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/observability/status")
async def get_observability_status():
    """
    Get observability and tracing status information.
    
    Returns:
        LangSmith tracing configuration and status
    """
    try:
        tracing_status = get_tracing_status()
        return {
            "observability": {
                "langsmith": tracing_status
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get observability status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao obter status de observabilidade: {str(e)}"
        )