"""
Extraction Report Generator for contract clause analysis.

This module generates detailed reports about the clause extraction process,
including which method was used and formatted output of all extracted clauses.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..models import ProcessedClause, PDFExtractionResult, BoundingBox
from ..settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractionMetrics:
    """Metrics about the extraction process."""
    total_clauses: int
    method_used: str  # "advanced", "docling", "paragraph_fallback"
    processing_time: float
    success_rate: float
    advanced_clauses: int = 0
    docling_clauses: int = 0
    fallback_clauses: int = 0


class ExtractionReporter:
    """
    Generate extraction reports and markdown documentation.
    
    Creates detailed reports about clause extraction process including
    method used, success metrics, and formatted clause output.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize extraction reporter with output directory."""
        self.output_dir = Path(output_dir) if output_dir else Path("extraction_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_extraction_report(
        self,
        extraction_result: PDFExtractionResult,
        clauses: List[ProcessedClause],
        extraction_method: str,
        metrics: ExtractionMetrics
    ) -> str:
        """
        Generate comprehensive extraction report.
        
        Args:
            extraction_result: PDF extraction result
            clauses: List of extracted clauses
            extraction_method: Primary method used ("advanced" or "docling")
            metrics: Extraction metrics
            
        Returns:
            Path to generated report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extraction_report_{extraction_result.document_id}_{timestamp}.md"
        report_path = self.output_dir / filename
        
        logger.info(f"Generating extraction report: {report_path}")
        
        # Generate report content
        report_content = self._create_report_content(
            extraction_result, clauses, extraction_method, metrics
        )
        
        # Write report to file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Extraction report generated: {report_path}")
        return str(report_path)
    
    def generate_clauses_markdown(
        self,
        extraction_result: PDFExtractionResult,
        clauses: List[ProcessedClause],
        extraction_method: str
    ) -> str:
        """
        Generate markdown file with all clauses separated and formatted.
        
        Args:
            extraction_result: PDF extraction result
            clauses: List of extracted clauses
            extraction_method: Extraction method used
            
        Returns:
            Path to generated markdown file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"clauses_{extraction_result.document_id}_{timestamp}.md"
        clauses_path = self.output_dir / filename
        
        logger.info(f"Generating clauses markdown: {clauses_path}")
        
        # Generate clauses content
        clauses_content = self._create_clauses_markdown_content(
            extraction_result, clauses, extraction_method
        )
        
        # Write clauses to file
        with open(clauses_path, 'w', encoding='utf-8') as f:
            f.write(clauses_content)
        
        logger.info(f"Clauses markdown generated: {clauses_path}")
        return str(clauses_path)
    
    def _create_report_content(
        self,
        extraction_result: PDFExtractionResult,
        clauses: List[ProcessedClause],
        extraction_method: str,
        metrics: ExtractionMetrics
    ) -> str:
        """Create the main extraction report content."""
        
        # Header
        content = [
            "# Relatório de Extração de Cláusulas",
            "",
            f"**Data/Hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"**Documento:** {extraction_result.metadata.filename}",
            f"**Document ID:** {extraction_result.document_id}",
            "",
            "## 📊 Resumo da Extração",
            "",
            f"- **Método Principal Utilizado:** `{extraction_method.upper()}`",
            f"- **Total de Cláusulas Extraídas:** {metrics.total_clauses}",
            f"- **Tempo de Processamento:** {metrics.processing_time:.2f} segundos",
            f"- **Taxa de Sucesso:** {metrics.success_rate:.1%}",
            "",
        ]
        
        # Method breakdown
        if metrics.advanced_clauses > 0 or metrics.docling_clauses > 0 or metrics.fallback_clauses > 0:
            content.extend([
                "### Detalhamento por Método:",
                "",
                f"- **Método Avançado (IMPROVEMENTS.md):** {metrics.advanced_clauses} cláusulas",
                f"- **Método Docling:** {metrics.docling_clauses} cláusulas", 
                f"- **Fallback (Parágrafos):** {metrics.fallback_clauses} cláusulas",
                "",
            ])
        
        # Document metadata
        content.extend([
            "## 📄 Metadados do Documento",
            "",
            f"- **Nome do Arquivo:** {extraction_result.metadata.filename}",
            f"- **Tamanho do Arquivo:** {extraction_result.metadata.file_size:,} bytes",
            f"- **Número de Páginas:** {extraction_result.metadata.page_count}",
            f"- **Método de Extração:** {extraction_result.extraction_method}",
            "",
        ])
        
        # Clauses summary
        content.extend([
            "## 🔍 Resumo das Cláusulas Extraídas",
            "",
            f"Total de {len(clauses)} cláusulas identificadas:",
            "",
        ])
        
        # Clauses table
        content.append("| # | Número | Título | Tamanho | Página | Nível |")
        content.append("|---|--------|--------|---------|--------|-------|")
        
        for i, clause in enumerate(clauses, 1):
            clause_num = clause.clause_number or "N/A"
            title = clause.title[:50] + "..." if len(clause.title) > 50 else clause.title
            size = len(clause.text)
            page = clause.coordinates.page_number + 1 if clause.coordinates else "N/A"
            level = clause.level or 1
            
            content.append(f"| {i} | {clause_num} | {title} | {size} chars | {page} | {level} |")
        
        content.extend([
            "",
            "## 🏷️ Distribuição por Nível",
            "",
        ])
        
        # Level distribution
        level_counts = {}
        for clause in clauses:
            level = clause.level or 1
            level_counts[level] = level_counts.get(level, 0) + 1
        
        for level in sorted(level_counts.keys()):
            count = level_counts[level]
            content.append(f"- **Nível {level}:** {count} cláusula(s)")
        
        content.extend([
            "",
            "## ⚙️ Configurações Utilizadas",
            "",
            f"- **Máximo de Páginas:** {settings.max_pdf_pages}",
            f"- **Timeout de Processamento:** {settings.pdf_processing_timeout}s",
            f"- **Provider LLM:** {settings.llm_provider}",
            "",
            "---",
            "",
            f"*Relatório gerado automaticamente pelo sistema Lawyerless em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*"
        ])
        
        return "\n".join(content)
    
    def _create_clauses_markdown_content(
        self,
        extraction_result: PDFExtractionResult,
        clauses: List[ProcessedClause],
        extraction_method: str
    ) -> str:
        """Create formatted markdown content with all clauses."""
        
        # Header
        content = [
            "# Cláusulas Extraídas - Documento Completo",
            "",
            f"**Arquivo:** {extraction_result.metadata.filename}",
            f"**Data de Extração:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"**Método de Extração:** {extraction_method.upper()}",
            f"**Total de Cláusulas:** {len(clauses)}",
            "",
            "---",
            "",
        ]
        
        # Table of contents
        content.extend([
            "## 📋 Índice de Cláusulas",
            "",
        ])
        
        for i, clause in enumerate(clauses, 1):
            clause_num = clause.clause_number or f"Seção {i}"
            title = clause.title
            anchor = self._create_anchor(clause_num, title)
            content.append(f"{i}. [{clause_num} - {title}](#{anchor})")
        
        content.extend([
            "",
            "---",
            "",
            "## 📄 Cláusulas Completas",
            "",
        ])
        
        # Individual clauses
        for i, clause in enumerate(clauses, 1):
            clause_num = clause.clause_number or f"Seção {i}"
            title = clause.title
            anchor = self._create_anchor(clause_num, title)
            
            # Clause header
            content.extend([
                f"### {clause_num} - {title} {{#{anchor}}}",
                "",
            ])
            
            # Clause metadata
            metadata_items = []
            metadata_items.append(f"**Número da Cláusula:** {clause_num}")
            metadata_items.append(f"**Nível:** {clause.level or 1}")
            metadata_items.append(f"**Tamanho:** {len(clause.text)} caracteres")
            
            if clause.coordinates:
                page_num = clause.coordinates.page_number + 1
                metadata_items.append(f"**Página:** {page_num}")
                metadata_items.append(f"**Posição:** Top: {clause.coordinates.top:.1f}, Bottom: {clause.coordinates.bottom:.1f}")
            
            content.extend(metadata_items)
            content.extend([
                "",
                "**Texto da Cláusula:**",
                "",
                "```",
                clause.text,
                "```",
                "",
                "---",
                "",
            ])
        
        # Footer
        content.extend([
            "",
            "## 📊 Estatísticas do Documento",
            "",
            f"- **Total de Cláusulas:** {len(clauses)}",
            f"- **Arquivo Original:** {extraction_result.metadata.filename}",
            f"- **Tamanho do Arquivo:** {extraction_result.metadata.file_size:,} bytes",
            f"- **Páginas:** {extraction_result.metadata.page_count}",
            f"- **Tempo de Extração:** {extraction_result.extraction_time:.2f} segundos",
            "",
            "### Distribuição por Nível:",
            "",
        ])
        
        # Level distribution for footer
        level_counts = {}
        for clause in clauses:
            level = clause.level or 1
            level_counts[level] = level_counts.get(level, 0) + 1
        
        for level in sorted(level_counts.keys()):
            count = level_counts[level]
            content.append(f"- **Nível {level}:** {count} cláusula(s)")
        
        content.extend([
            "",
            "---",
            "",
            f"*Documento gerado automaticamente pelo sistema Lawyerless*  ",
            f"*Método de extração: {extraction_method.upper()}*  ",
            f"*Data: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*"
        ])
        
        return "\n".join(content)
    
    def _create_anchor(self, clause_num: str, title: str) -> str:
        """Create URL-safe anchor for markdown headers."""
        import re
        
        # Combine clause number and title
        anchor_text = f"{clause_num}-{title}"
        
        # Convert to lowercase and replace spaces/special chars with hyphens
        anchor = re.sub(r'[^\w\s-]', '', anchor_text.lower())
        anchor = re.sub(r'[\s_-]+', '-', anchor)
        anchor = anchor.strip('-')
        
        return anchor
    
    def create_extraction_metrics(
        self,
        total_clauses: int,
        method_used: str,
        processing_time: float,
        advanced_count: int = 0,
        docling_count: int = 0,
        fallback_count: int = 0
    ) -> ExtractionMetrics:
        """
        Create extraction metrics object.
        
        Args:
            total_clauses: Total number of clauses extracted
            method_used: Primary method used
            processing_time: Time taken for extraction
            advanced_count: Number of clauses from advanced method
            docling_count: Number of clauses from docling method
            fallback_count: Number of clauses from fallback method
            
        Returns:
            ExtractionMetrics object
        """
        success_rate = 1.0 if total_clauses > 0 else 0.0
        
        # Adjust success rate based on fallback usage
        if fallback_count > 0:
            success_rate = (total_clauses - fallback_count) / total_clauses
        
        return ExtractionMetrics(
            total_clauses=total_clauses,
            method_used=method_used,
            processing_time=processing_time,
            success_rate=success_rate,
            advanced_clauses=advanced_count,
            docling_clauses=docling_count,
            fallback_clauses=fallback_count
        )


# Convenience function for external use
def generate_extraction_reports(
    extraction_result: PDFExtractionResult,
    clauses: List[ProcessedClause],
    extraction_method: str,
    output_dir: Optional[str] = None,
    advanced_count: int = 0,
    docling_count: int = 0,
    fallback_count: int = 0
) -> Dict[str, str]:
    """
    Generate both extraction report and clauses markdown.
    
    Args:
        extraction_result: PDF extraction result
        clauses: List of extracted clauses
        extraction_method: Primary extraction method used
        output_dir: Output directory for reports
        advanced_count: Number of clauses from advanced method
        docling_count: Number of clauses from docling method  
        fallback_count: Number of clauses from fallback method
        
    Returns:
        Dictionary with paths to generated files
    """
    reporter = ExtractionReporter(output_dir)
    
    # Create metrics
    metrics = reporter.create_extraction_metrics(
        total_clauses=len(clauses),
        method_used=extraction_method,
        processing_time=extraction_result.extraction_time,
        advanced_count=advanced_count,
        docling_count=docling_count,
        fallback_count=fallback_count
    )
    
    # Generate reports
    report_path = reporter.generate_extraction_report(
        extraction_result, clauses, extraction_method, metrics
    )
    
    clauses_path = reporter.generate_clauses_markdown(
        extraction_result, clauses, extraction_method
    )
    
    return {
        "extraction_report": report_path,
        "clauses_markdown": clauses_path,
        "metrics": metrics
    }