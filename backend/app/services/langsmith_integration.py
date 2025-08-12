"""
LangSmith integration for observability and tracing.

This module handles LangSmith initialization, custom tracing,
and metadata collection for contract analysis workflows.
"""

import logging
import os
import random
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from langsmith import Client, traceable
    from langsmith.run_helpers import tracing_context, get_current_run_tree
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    # Create dummy decorators if LangSmith is not available
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def tracing_context(*args, **kwargs):
        from contextlib import nullcontext
        return nullcontext()
    
    def get_current_run_tree():
        return None

from ..settings import settings

logger = logging.getLogger(__name__)


class LangSmithTracer:
    """
    LangSmith integration for Lawyerless contract analysis.
    
    Provides tracing, metadata collection, and observability
    for the contract analysis workflow.
    """
    
    def __init__(self):
        """Initialize LangSmith client if enabled and available."""
        self.enabled = False
        self.client = None
        
        if not LANGSMITH_AVAILABLE:
            logger.warning("LangSmith not installed. Tracing disabled.")
            return
        
        if not settings.langsmith_enabled:
            logger.info("LangSmith tracing disabled in settings")
            return
            
        if not settings.langsmith_api_key:
            logger.warning("LangSmith API key not configured. Tracing disabled.")
            return
        
        try:
            # Set environment variables for LangSmith
            os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
            os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
            os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
            # Ensure LangChain v2 tracing variables are also set for decorators/helpers
            os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
            os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
            os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
            
            # Initialize client
            self.client = Client(
                api_key=settings.langsmith_api_key,
                api_url=settings.langsmith_endpoint
            )
            
            self.enabled = True
            logger.info(f"LangSmith tracing enabled for project: {settings.langsmith_project}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith: {e}")
            self.enabled = False
    
    def should_trace(self) -> bool:
        """Determine if this request should be traced based on sample rate."""
        if not self.enabled:
            return False
        
        return random.random() <= settings.langsmith_sample_rate
    
    def create_contract_metadata(
        self,
        document_id: str,
        filename: str,
        perspectiva: str,
        llm_provider: str,
        total_clauses: int,
        total_pages: int,
        file_size: int
    ) -> Dict[str, Any]:
        """
        Create metadata for contract analysis traces.
        
        Args:
            document_id: Document identifier
            filename: Original filename
            perspectiva: Analysis perspective
            llm_provider: LLM provider used
            total_clauses: Number of clauses
            total_pages: Number of pages
            file_size: File size in bytes
        
        Returns:
            Metadata dictionary for tracing
        """
        return {
            "document_id": document_id,
            "filename": filename,
            "perspectiva": perspectiva,
            "llm_provider": llm_provider,
            "total_clauses": total_clauses,
            "total_pages": total_pages,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "service": "lawyerless-contract-analyzer"
        }
    
    def create_clause_metadata(
        self,
        clause_id: str,
        clause_number: Optional[str],
        clause_level: int,
        clause_length: int,
        pattern_type: str
    ) -> Dict[str, Any]:
        """
        Create metadata for individual clause analysis.
        
        Args:
            clause_id: Clause identifier
            clause_number: Clause number (e.g., "1.2.1")
            clause_level: Hierarchical level
            clause_length: Length of clause text
            pattern_type: Pattern used to detect clause
        
        Returns:
            Metadata dictionary for clause tracing
        """
        return {
            "clause_id": clause_id,
            "clause_number": clause_number,
            "clause_level": clause_level,
            "clause_length": clause_length,
            "pattern_type": pattern_type,
            "timestamp": datetime.now().isoformat()
        }
    
    @contextmanager
    def trace_contract_analysis(
        self,
        document_id: str,
        filename: str,
        perspectiva: str,
        llm_provider: str,
        total_clauses: int,
        total_pages: int,
        file_size: int
    ):
        """
        Context manager for tracing full contract analysis.
        
        Args:
            document_id: Document identifier
            filename: Original filename
            perspectiva: Analysis perspective
            llm_provider: LLM provider used
            total_clauses: Number of clauses
            total_pages: Number of pages
            file_size: File size in bytes
        """
        if not self.should_trace():
            yield None
            return
        
        metadata = self.create_contract_metadata(
            document_id, filename, perspectiva, llm_provider,
            total_clauses, total_pages, file_size
        )
        
        try:
            with tracing_context(
                name="contract_analysis",
                metadata=metadata,
                tags=["contract", "analysis", perspectiva, llm_provider],
                project_name=settings.langsmith_project,
                enabled=True,
                client=self.client
            ) as trace:
                yield trace
                
                if trace:
                    try:
                        trace.update(
                            outputs={"status": "completed"},
                            metadata={**metadata, "success": True}
                        )
                    except Exception:
                        # Avoid crashing on tracing update failures
                        pass
        except Exception as e:
            if LANGSMITH_AVAILABLE:
                try:
                    if 'trace' in locals() and trace:
                        trace.update(
                            outputs={"status": "failed", "error": str(e)},
                            metadata={**metadata, "success": False, "error": str(e)}
                        )
                except Exception:
                    pass
                logger.error(f"Contract analysis trace failed: {e}")
            raise
    
    @contextmanager
    def trace_clause_analysis(
        self,
        clause_id: str,
        clause_number: Optional[str],
        clause_level: int,
        clause_length: int,
        pattern_type: str
    ):
        """
        Context manager for tracing individual clause analysis.
        
        Args:
            clause_id: Clause identifier
            clause_number: Clause number
            clause_level: Hierarchical level
            clause_length: Length of clause text
            pattern_type: Pattern used to detect clause
        """
        if not self.should_trace():
            yield None
            return
        
        metadata = self.create_clause_metadata(
            clause_id, clause_number, clause_level, clause_length, pattern_type
        )
        
        try:
            with tracing_context(
                name="clause_analysis",
                metadata=metadata,
                tags=["clause", "analysis", pattern_type, f"level_{clause_level}"],
                project_name=settings.langsmith_project,
                enabled=True,
                client=self.client
            ) as trace:
                yield trace
                
                if trace:
                    try:
                        trace.update(
                            outputs={"status": "completed"},
                            metadata={**metadata, "success": True}
                        )
                    except Exception:
                        pass
        except Exception as e:
            if LANGSMITH_AVAILABLE:
                try:
                    if 'trace' in locals() and trace:
                        trace.update(
                            outputs={"status": "failed", "error": str(e)},
                            metadata={**metadata, "success": False, "error": str(e)}
                        )
                except Exception:
                    pass
                logger.error(f"Clause analysis trace failed: {e}")
            raise


# Global tracer instance
tracer = LangSmithTracer()


# Convenience decorators and functions
def trace_contract_analysis_func(
    document_id: str,
    filename: str,
    perspectiva: str = "fundador",
    llm_provider: str = "openai",
    total_clauses: int = 0,
    total_pages: int = 0,
    file_size: int = 0
):
    """
    Decorator for tracing contract analysis functions.
    
    Usage:
        @trace_contract_analysis_func(
            document_id="doc123",
            filename="contract.pdf",
            perspectiva="fundador"
        )
        async def analyze_contract(...):
            ...
    """
    def decorator(func):
        if not tracer.enabled:
            return func
        
        @traceable(
            name=f"contract_analysis_{func.__name__}",
            metadata={
                "document_id": document_id,
                "filename": filename,
                "perspectiva": perspectiva,
                "llm_provider": llm_provider
            }
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_analysis_metrics(
    document_id: str,
    processing_time: float,
    clause_count: int,
    risk_summary: Dict[str, int],
    confidence_score: float
):
    """
    Log analysis metrics to LangSmith.
    
    Args:
        document_id: Document identifier
        processing_time: Total processing time in seconds
        clause_count: Number of clauses analyzed
        risk_summary: Risk flag counts
        confidence_score: Analysis confidence score
    """
    if not tracer.enabled:
        return
    
    try:
        metrics = {
            "document_id": document_id,
            "processing_time_seconds": processing_time,
            "clause_count": clause_count,
            "risk_summary": risk_summary,
            "confidence_score": confidence_score,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"LangSmith metrics logged for {document_id}: {metrics}")
        
    except Exception as e:
        logger.error(f"Failed to log metrics to LangSmith: {e}")


def get_tracing_status() -> Dict[str, Any]:
    """
    Get current LangSmith tracing status.
    
    Returns:
        Status information dictionary
    """
    return {
        "langsmith_available": LANGSMITH_AVAILABLE,
        "tracing_enabled": tracer.enabled,
        "project": settings.langsmith_project,
        "sample_rate": settings.langsmith_sample_rate,
        "api_key_configured": bool(settings.langsmith_api_key)
    }