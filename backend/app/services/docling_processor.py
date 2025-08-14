"""
Docling-based PDF processing service with improved clause identification.

This module uses Docling for superior PDF text extraction and implements
the clause identification patterns proven successful in testing.
"""

import logging
import hashlib
import re
import tempfile
import os
from io import BytesIO
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

from docling.document_converter import DocumentConverter

from ..models import (
    PDFMetadata, 
    TextFragment, 
    BoundingBox, 
    PDFExtractionResult,
    ProcessedClause
)
from ..settings import settings
from .advanced_clause_extractor import extract_clauses_with_advanced_method
from .extraction_reporter import generate_extraction_reports

logger = logging.getLogger(__name__)


class DoclingProcessingError(Exception):
    """Custom exception for Docling PDF processing errors."""
    pass


class DoclingProcessor:
    """
    Enhanced PDF processing service using Docling.
    
    Provides superior text extraction and clause identification
    compared to traditional PDF libraries.
    """
    
    def __init__(self):
        """Initialize Docling processor with configuration."""
        self.max_pages = settings.max_pdf_pages
        self.processing_timeout = settings.pdf_processing_timeout
        self.converter = DocumentConverter()
        
    async def extract_text_with_coordinates(
        self, 
        file_content: bytes, 
        filename: str
    ) -> PDFExtractionResult:
        """
        Extract text with enhanced clause identification using Docling.
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
        
        Returns:
            PDFExtractionResult with improved text extraction and clause segmentation
        
        Raises:
            DoclingProcessingError: If extraction fails
        """
        start_time = datetime.now()
        
        try:
            # Generate document ID
            document_id = self._generate_document_id(file_content, filename)
            
            # Create temporary file for Docling (it requires a file path)
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Convert PDF using Docling
                logger.info(f"Starting Docling conversion for {filename}")
                result = self.converter.convert(temp_file_path)
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    logger.warning(f"Failed to delete temporary file: {temp_file_path}")
            
            # Extract text
            full_text = result.document.export_to_text()
            logger.info(f"Docling extracted {len(full_text)} characters from {filename}")
            
            # Generate metadata
            metadata = self._create_pdf_metadata(file_content, filename, full_text)
            
            # Validate page count
            estimated_pages = self._estimate_page_count(full_text)
            if estimated_pages > self.max_pages:
                raise DoclingProcessingError(
                    f"PDF estimated to have {estimated_pages} pages, maximum allowed is {self.max_pages}"
                )
            
            # Filter headers/footers and clean text
            cleaned_text = self._filter_headers_footers(full_text)
            
            # Identify and extract clauses using proven patterns with method tracking
            clauses, extraction_metrics = await self._extract_clauses_with_docling(
                cleaned_text, document_id, estimated_pages
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log extraction summary with method details
            method_used = extraction_metrics.get("method_used", "unknown")
            logger.info(f"📊 PDF processing completed in {processing_time:.2f}s")
            logger.info(f"📈 Primary method: {method_used.upper()}")
            logger.info(f"📋 Total clauses: {len(clauses)}")
            logger.info(f"🔍 Method breakdown: Advanced={extraction_metrics.get('advanced', 0)}, "
                       f"Docling={extraction_metrics.get('docling', 0)}, "
                       f"Fallback={extraction_metrics.get('fallback', 0)}")
            
            # Create extraction result with correct method
            actual_extraction_method = method_used if method_used != "unknown" else "docling"
            extraction_result = PDFExtractionResult(
                document_id=document_id,
                metadata=metadata,
                clauses=clauses,
                full_text=cleaned_text,
                extraction_time=processing_time,
                extraction_method=actual_extraction_method,
                warnings=[]
            )
            
            # Generate extraction reports
            try:
                reports = generate_extraction_reports(
                    extraction_result=extraction_result,
                    clauses=clauses,
                    extraction_method=method_used,
                    output_dir="extraction_reports",
                    advanced_count=extraction_metrics.get("advanced", 0),
                    docling_count=extraction_metrics.get("docling", 0),
                    fallback_count=extraction_metrics.get("fallback", 0)
                )
                
                logger.info(f"📄 Extraction report generated: {reports['extraction_report']}")
                logger.info(f"📝 Clauses markdown generated: {reports['clauses_markdown']}")
                
                # Add report paths to warnings for user visibility
                extraction_result.warnings.extend([
                    f"Relatório de extração: {reports['extraction_report']}",
                    f"Cláusulas em markdown: {reports['clauses_markdown']}"
                ])
                
            except Exception as e:
                logger.warning(f"Failed to generate extraction reports: {e}")
                extraction_result.warnings.append(f"Falha ao gerar relatórios: {e}")
            
            return extraction_result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Docling processing failed after {processing_time:.2f}s: {str(e)}")
            raise DoclingProcessingError(f"Docling processing failed: {str(e)}") from e
    
    def _filter_headers_footers(self, text: str) -> str:
        """
        Remove headers and footers from extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text without headers/footers
        """
        # Remove Clicksign footers (as identified in testing)
        text = re.sub(r'Clicksign\s+[a-f0-9-]+\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove common PDF metadata footers
        text = re.sub(r'^\s*Página\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\s*Page\s+\d+\s*of\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    async def _extract_clauses_with_docling(
        self, 
        text: str, 
        document_id: str, 
        estimated_pages: int
    ) -> Tuple[List[ProcessedClause], Dict[str, int]]:
        """
        Extract clauses using multi-tier approach: Advanced method first, then Docling patterns.
        
        Args:
            text: Cleaned text from Docling
            document_id: Document identifier
            estimated_pages: Estimated number of pages
            
        Returns:
            Tuple of (List of ProcessedClause objects, extraction method counts)
        """
        # Track extraction method usage
        method_counts = {"advanced": 0, "docling": 0, "fallback": 0}
        primary_method = "unknown"
        
        # TIER 1: Try Advanced Clause Extractor first (from IMPROVEMENTS.md)
        try:
            logger.info("🔍 TIER 1: Attempting advanced clause extraction (IMPROVEMENTS.md method)")
            advanced_clauses = await extract_clauses_with_advanced_method(
                text, document_id, estimated_pages
            )
            
            if advanced_clauses and len(advanced_clauses) >= 3:  # Reasonable threshold
                logger.info(f"✅ Advanced extraction successful: {len(advanced_clauses)} clauses found")
                
                # Log what we found
                advanced_numbers = [c.clause_number for c in advanced_clauses if c.clause_number]
                logger.info(f"Advanced method found clause numbers: {sorted(advanced_numbers)}")
                
                method_counts["advanced"] = len(advanced_clauses)
                primary_method = "advanced"
                return advanced_clauses, {"method_used": primary_method, **method_counts}
            else:
                logger.warning(f"⚠️ Advanced extraction returned {len(advanced_clauses)} clauses (<3), trying Docling method")
        
        except Exception as e:
            logger.warning(f"❌ Advanced extraction failed: {e}, falling back to Docling method")
        
        # TIER 2: Fallback to original Docling pattern matching
        logger.info("🔍 TIER 2: Using Docling pattern matching as fallback")
        clauses = []
        
        # Identify numbered clause patterns (2.6, 2.7, 2.8, etc.)
        clause_numbers = self._identify_clause_numbers(text)
        logger.info(f"Docling method found clause numbers: {clause_numbers}")
        
        if not clause_numbers:
            logger.warning("🔍 TIER 3: No clause numbers found with Docling method, using paragraph fallback")
            fallback_clauses = self._create_fallback_clauses(text, document_id, estimated_pages)
            method_counts["fallback"] = len(fallback_clauses)
            primary_method = "paragraph_fallback"
            return fallback_clauses, {"method_used": primary_method, **method_counts}
        
        # Extract content for each clause
        clauses_dict = self._extract_clause_content(text, clause_numbers)
        
        # Convert to ProcessedClause objects
        for clause_num in clause_numbers:
            if clause_num in clauses_dict:
                content = clauses_dict[clause_num]
                
                # Generate clause ID
                clause_id = self._generate_clause_id(content, clause_num, document_id)
                
                # Estimate coordinates
                coordinates = self._estimate_coordinates(
                    clause_num, text, content, estimated_pages
                )
                
                # Create clause title
                title = self._create_clause_title(clause_num, content)
                
                clause = ProcessedClause(
                    clause_id=clause_id,
                    text=content,
                    coordinates=coordinates,
                    title=title,
                    level=self._calculate_clause_level(clause_num),
                    clause_number=clause_num
                )
                
                clauses.append(clause)
                logger.debug(f"Created clause {clause_num}: {len(content)} chars")
        
        method_counts["docling"] = len(clauses)
        primary_method = "docling"
        logger.info(f"✅ Docling fallback extraction: {len(clauses)} clauses found")
        return clauses, {"method_used": primary_method, **method_counts}
    
    def _identify_clause_numbers(self, text: str) -> List[str]:
        """
        Identify clause numbers using patterns from successful testing.
        
        Args:
            text: Document text
            
        Returns:
            List of clause numbers found
        """
        # Pattern for numbered clauses (e.g., 2.6, 2.7, 3, 3.1)
        clause_pattern = r'\b(\d+(?:\.\d+)?)\s+'
        matches = re.findall(clause_pattern, text)
        
        # Filter and validate clause numbers
        valid_clauses = []
        for match in matches:
            if self._validate_clause_number(match):
                valid_clauses.append(match)
        
        # Remove duplicates and sort
        unique_clauses = sorted(set(valid_clauses), key=self._clause_sort_key)
        
        return unique_clauses
    
    def _validate_clause_number(self, clause_num: str) -> bool:
        """
        Validate if a number is a valid clause identifier.
        
        Args:
            clause_num: Clause number to validate
            
        Returns:
            True if valid clause number
        """
        try:
            if '.' in clause_num:
                # Handle decimal clauses (e.g., 2.6, 3.1)
                parts = clause_num.split('.')
                if len(parts) == 2:
                    main = int(parts[0])
                    sub = int(parts[1])
                    # Reasonable ranges for contract clauses
                    return 1 <= main <= 20 and 1 <= sub <= 50
            else:
                # Handle main clauses (e.g., 3, 4)
                main = int(clause_num)
                return 1 <= main <= 20
        except ValueError:
            return False
        
        return False
    
    def _clause_sort_key(self, clause_num: str) -> tuple:
        """
        Generate sort key for clause numbers.
        
        Args:
            clause_num: Clause number
            
        Returns:
            Tuple for sorting
        """
        if '.' in clause_num:
            parts = clause_num.split('.')
            return (int(parts[0]), int(parts[1]))
        else:
            return (int(clause_num), 0)
    
    def _extract_clause_content(self, text: str, clause_numbers: List[str]) -> Dict[str, str]:
        """
        Extract content for each identified clause.
        
        Args:
            text: Full document text
            clause_numbers: List of clause numbers
            
        Returns:
            Dictionary mapping clause numbers to content
        """
        clauses = {}
        
        for i, clause_num in enumerate(clause_numbers):
            # Find start of clause
            start_pattern = rf'\b{re.escape(clause_num)}\s+'
            start_match = re.search(start_pattern, text)
            
            if not start_match:
                continue
            
            start_pos = start_match.start()
            
            # Find end of clause (start of next clause or end of text)
            if i + 1 < len(clause_numbers):
                next_clause = clause_numbers[i + 1]
                end_pattern = rf'\b{re.escape(next_clause)}\s+'
                end_match = re.search(end_pattern, text[start_pos + len(start_match.group()):])
                if end_match:
                    end_pos = start_pos + len(start_match.group()) + end_match.start()
                else:
                    end_pos = len(text)
            else:
                end_pos = len(text)
            
            # Extract and clean content
            content = text[start_pos:end_pos].strip()
            content = self._clean_clause_content(content)
            
            if content and len(content) > 10:  # Filter very short content
                clauses[clause_num] = content
        
        return clauses
    
    def _clean_clause_content(self, content: str) -> str:
        """
        Clean clause content.
        
        Args:
            content: Raw clause content
            
        Returns:
            Cleaned content
        """
        # Remove multiple whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove any remaining Clicksign references
        content = re.sub(r'Clicksign\s+[a-f0-9-]+\s*', '', content, flags=re.IGNORECASE)
        
        # Remove isolated page numbers
        content = re.sub(r'^\s*\d+\s*$', '', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def _create_clause_title(self, clause_num: str, content: str) -> str:
        """
        Create a descriptive title for the clause.
        
        Args:
            clause_num: Clause number
            content: Clause content
            
        Returns:
            Formatted clause title
        """
        # Extract first line or first 100 characters as title base
        lines = content.split('\n')
        first_line = lines[0] if lines else content
        
        # Look for title after clause number
        title_match = re.match(rf'{re.escape(clause_num)}\s+(.+?)(?:\.|$)', first_line)
        if title_match:
            title_text = title_match.group(1).strip()
            if len(title_text) > 50:
                title_text = title_text[:50] + "..."
            return f"{clause_num}. {title_text}"
        
        # Fallback: use first 50 characters
        preview = first_line[:50].strip()
        if len(first_line) > 50:
            preview += "..."
        
        return f"Cláusula {clause_num}: {preview}"
    
    def _calculate_clause_level(self, clause_num: str) -> int:
        """
        Calculate hierarchical level of clause.
        
        Args:
            clause_num: Clause number
            
        Returns:
            Hierarchical level (1 = main, 2 = sub, etc.)
        """
        if '.' in clause_num:
            return len(clause_num.split('.'))
        return 1
    
    def _estimate_coordinates(
        self, 
        clause_num: str, 
        full_text: str, 
        content: str, 
        estimated_pages: int
    ) -> BoundingBox:
        """
        Estimate coordinates for clause positioning.
        
        Args:
            clause_num: Clause number
            full_text: Full document text
            content: Clause content
            estimated_pages: Number of pages
            
        Returns:
            Estimated bounding box
        """
        # Find position in text
        clause_pos = full_text.find(content)
        if clause_pos == -1:
            clause_pos = 0
        
        # Estimate page
        chars_per_page = len(full_text) / estimated_pages if estimated_pages > 0 else len(full_text)
        page_num = min(int(clause_pos / chars_per_page), estimated_pages - 1) if chars_per_page > 0 else 0
        
        # Estimate position within page
        page_start = page_num * chars_per_page
        pos_in_page = clause_pos - page_start
        y_ratio = pos_in_page / chars_per_page if chars_per_page > 0 else 0
        
        # Standard page dimensions
        page_width = 612
        page_height = 792
        
        top = y_ratio * page_height
        height = min(len(content) / chars_per_page * page_height, page_height / 3) if chars_per_page > 0 else 100
        
        return BoundingBox(
            x0=50,  # Left margin
            x1=page_width - 50,  # Right margin
            top=top,
            bottom=min(top + height, page_height),
            page_number=page_num,
            page_height=page_height
        )
    
    def _create_fallback_clauses(
        self, 
        text: str, 
        document_id: str, 
        estimated_pages: int
    ) -> List[ProcessedClause]:
        """
        Create fallback clauses when no numbered patterns are found.
        
        Args:
            text: Document text
            document_id: Document identifier
            estimated_pages: Number of pages
            
        Returns:
            List of fallback clauses
        """
        # Split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        # Filter valid paragraphs
        valid_paragraphs = [
            p.strip() for p in paragraphs 
            if len(p.strip()) > 100  # Minimum length for meaningful paragraphs
        ]
        
        if len(valid_paragraphs) <= 1:
            # Single clause for entire document
            clause_id = f"fallback_single_{document_id}"
            return [ProcessedClause(
                clause_id=clause_id,
                text=text,
                coordinates=BoundingBox(
                    x0=50, x1=562, top=50, bottom=742,
                    page_number=0, page_height=792
                ),
                title="Documento Completo",
                level=1
            )]
        
        # Multiple paragraph clauses
        clauses = []
        for i, paragraph in enumerate(valid_paragraphs):
            clause_id = f"fallback_para_{document_id}_{i+1}"
            
            # Create title from first 50 characters
            title = paragraph[:50].strip()
            if len(paragraph) > 50:
                title += "..."
            
            coordinates = self._estimate_coordinates(
                str(i+1), text, paragraph, estimated_pages
            )
            
            clauses.append(ProcessedClause(
                clause_id=clause_id,
                text=paragraph,
                coordinates=coordinates,
                title=f"Seção {i+1}: {title}",
                level=1
            ))
        
        logger.info(f"Created {len(clauses)} fallback clauses from paragraphs")
        return clauses
    
    def _estimate_page_count(self, text: str) -> int:
        """
        Estimate number of pages based on text length.
        
        Args:
            text: Document text
            
        Returns:
            Estimated page count
        """
        # Rough estimation: ~3000 characters per page
        chars_per_page = 3000
        estimated = max(1, len(text) // chars_per_page)
        return min(estimated, 50)  # Cap at reasonable maximum
    
    def _create_pdf_metadata(
        self, 
        file_content: bytes, 
        filename: str, 
        text: str
    ) -> PDFMetadata:
        """
        Create PDF metadata.
        
        Args:
            file_content: Original file bytes
            filename: Filename
            text: Extracted text
            
        Returns:
            PDFMetadata object
        """
        estimated_pages = self._estimate_page_count(text)
        
        return PDFMetadata(
            filename=filename,
            file_size=len(file_content),
            page_count=estimated_pages,
            creation_date=None,  # Docling doesn't easily expose metadata
            modification_date=None,
            title=None,
            author=None,
            subject=None
        )
    
    def _generate_document_id(self, file_content: bytes, filename: str) -> str:
        """
        Generate stable document ID.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            
        Returns:
            Document identifier
        """
        content_hash = hashlib.md5(file_content).hexdigest()
        filename_hash = hashlib.md5(filename.encode()).hexdigest()
        return f"docling_{content_hash[:8]}_{filename_hash[:8]}"
    
    def _generate_clause_id(
        self, 
        content: str, 
        clause_num: str, 
        document_id: str
    ) -> str:
        """
        Generate stable clause ID.
        
        Args:
            content: Clause content
            clause_num: Clause number
            document_id: Document ID
            
        Returns:
            Clause identifier
        """
        content_sample = content[:200].strip()
        id_string = f"{document_id}_clause_{clause_num}_{content_sample}"
        id_hash = hashlib.md5(id_string.encode()).hexdigest()
        return f"docling_clause_{id_hash[:12]}"