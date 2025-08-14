"""
Advanced clause extraction using improved regex patterns and heuristics.

This module implements the improved clause extraction algorithm from IMPROVEMENTS.md
that provides better identification of contract clauses than standard PDF processors.

Based on the updated code from IMPROVEMENTS.md with integration adaptations for the
existing Lawyerless system.
"""

from __future__ import annotations
import re
import logging
import hashlib
import bisect
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from ..models import (
    PDFMetadata, 
    ProcessedClause, 
    BoundingBox, 
    PDFExtractionResult
)
from ..settings import settings

logger = logging.getLogger(__name__)


@dataclass
class Secao:
    """Seção de documento extraída."""
    number: str
    title: str
    text: str
    start: int
    end: int


class AdvancedClauseExtractionError(Exception):
    """Custom exception for advanced clause extraction errors."""
    pass


# Portuguese stopwords for title case detection
_PT_STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", 
    "para", "por", "em", "no", "na", "nos", "nas", "um", "uma"
}

# Top-level: "1 Objeto", "2 Das Partes", "3 Condições..." (aceita traço/–/—/:)
_TOP_HEADER_RE = re.compile(r"(?m)^\s*[-•]?\s*(?P<num>\d{1,2})\s*[-–—:]?\s+(?P<title>.{1,100})$")

# Subcláusulas: "2.1", "2.6.1", etc.
_SUB_HEADER_RE = re.compile(r"(?m)^\s*[-•]?\s*(?P<num>(?:\d+\.)+\d+)\s+(?P<title>.+)$")


def _upper_ratio(s: str) -> float:
    """Calculate ratio of uppercase letters in string."""
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def _titlecase_ratio(s: str) -> float:
    """Calculate ratio of titlecase words in string."""
    words = [w for w in re.split(r"\s+", s.strip()) if w]
    if not words:
        return 0.0
    good = 0
    for w in words:
        if w.lower() in _PT_STOPWORDS:
            good += 1
        elif w[0].isupper():
            good += 1
    return good / len(words)


def _is_probable_header(line: str, prev_line: str, next_line: str, title: str) -> bool:
    """
    Determine if a line is probably a clause header using improved heuristics.
    
    Args:
        line: Current line
        prev_line: Previous line
        next_line: Next line
        title: Extracted title
        
    Returns:
        True if likely a header
    """
    # Regras de descarte diretas
    if len(title) > 90:               # Título muito longo
        return False
    if title.endswith((".", ";", ",")):  # Geralmente cabeçalho não termina com pontuação
        return False

    # Heurísticas de formatação/estrutura
    spaced_block = (prev_line.strip() == "" or next_line.strip() == "")
    looks_upper = _upper_ratio(title) >= 0.55  # maioria em MAIÚSCULAS
    looks_titlecase = _titlecase_ratio(title) >= 0.7 and len(title.split()) <= 10

    # Se isola por linhas vazias OU "parece título" (maiúsculas/Title Case)
    if spaced_block or looks_upper or looks_titlecase:
        # Evita linhas que claramente continuam a frase anterior:
        if prev_line and prev_line.strip() and not re.search(r"[.:;!?]\s*$", prev_line.strip()):
            if not (looks_upper or looks_titlecase):
                return False
        return True
    return False


def find_top_headers(text: str) -> List[Tuple[int, str, str]]:
    """
    Find main clause headers (1, 2, 3, etc.) using improved heuristics.
    
    Args:
        text: Normalized text
        
    Returns:
        List of (position, number, title) tuples
    """
    headers: List[Tuple[int, str, str]] = []

    lines = text.splitlines()
    # offsets por linha para mapear índice absoluto -> linha
    offsets, off = [], 0
    for ln in lines:
        offsets.append(off)
        off += len(ln) + 1  # +1 pelo '\n'

    for m in _TOP_HEADER_RE.finditer(text):
        start = m.start()
        # localizar índice da linha via busca binária
        idx = bisect.bisect_right(offsets, start) - 1

        prev_line = lines[idx - 1] if idx - 1 >= 0 else ""
        this_line = lines[idx]
        next_line = lines[idx + 1] if idx + 1 < len(lines) else ""

        num = m.group("num").strip()
        title = m.group("title").strip()

        if _is_probable_header(this_line, prev_line, next_line, title):
            headers.append((start, num, title))

    headers.sort(key=lambda x: x[0])
    return headers


def find_sub_headers(text: str) -> List[Tuple[int, str, str]]:
    """
    Find subclause headers (2.6, 2.7, 3.1, etc.).
    
    Args:
        text: Normalized text
        
    Returns:
        List of (position, number, title) tuples
    """
    headers: List[Tuple[int, str, str]] = []
    for m in _SUB_HEADER_RE.finditer(text):
        start = m.start()
        num = m.group("num").strip()
        title = m.group("title").strip()
        # Evita linhas que terminam com pontuação (normalmente não são cabeçalhos)
        if not title.endswith((".", ";", ",")):
            headers.append((start, num, title))
    headers.sort(key=lambda x: x[0])
    return headers


def segment_sections(text: str, headers: List[Tuple[int, str, str]]) -> List[Secao]:
    """
    Segment text into sections based on headers.
    
    Args:
        text: Full text
        headers: List of (position, number, title) tuples
        
    Returns:
        List of Secao objects
    """
    if not headers:
        return []
    sections: List[Secao] = []
    for i, (start, num, title) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        body = text[start:end].strip()
        sections.append(Secao(number=num, title=title, text=body, start=start, end=end))
    return sections


def normalize_text(text: str) -> str:
    """
    Normaliza o texto para facilitar o parsing jurídico.
    - Remove NBSP
    - Remove espaços à direita por linha
    - Compacta múltiplas linhas vazias
    """
    text = text.replace("\xa0", " ")
    text = "\n".join(ln.rstrip() for ln in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


class AdvancedClauseExtractor:
    """
    Advanced clause extractor using improved regex patterns and heuristics.
    
    This implementation is based on the improved algorithm from IMPROVEMENTS.md
    that provides superior clause identification compared to standard PDF processors.
    """
    
    def __init__(self):
        """Initialize advanced clause extractor with improved patterns."""
        self.max_pages = settings.max_pdf_pages
    
    async def extract_clauses_from_text(
        self, 
        text: str, 
        document_id: str,
        estimated_pages: int = 1
    ) -> List[ProcessedClause]:
        """
        Extract clauses from text using advanced patterns.
        
        Args:
            text: Extracted text from PDF
            document_id: Document identifier
            estimated_pages: Estimated number of pages
            
        Returns:
            List of ProcessedClause objects
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting advanced clause extraction for {document_id}")
            
            # Normalize text
            normalized_text = normalize_text(text)
            
            # Extract sections using the improved algorithm
            result = self._extract_clauses_from_text_internal(
                normalized_text, 
                include_top_level=True, 
                include_subclauses=True
            )
            
            # Convert Secao objects to ProcessedClause objects
            clauses = []
            
            # Process top-level clauses
            if "top" in result:
                for secao in result["top"]:
                    clause = self._convert_secao_to_clause(
                        secao, document_id, estimated_pages, "main"
                    )
                    clauses.append(clause)
            
            # Process subclauses
            if "sub" in result:
                for secao in result["sub"]:
                    clause = self._convert_secao_to_clause(
                        secao, document_id, estimated_pages, "sub"
                    )
                    clauses.append(clause)
            
            # Sort clauses by position in text
            clauses.sort(key=lambda c: c.coordinates.top if c.coordinates else 0)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Advanced extraction completed in {processing_time:.2f}s: {len(clauses)} clauses")
            
            return clauses
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Advanced clause extraction failed after {processing_time:.2f}s: {str(e)}")
            raise AdvancedClauseExtractionError(f"Advanced extraction failed: {str(e)}") from e
    
    def _extract_clauses_from_text_internal(
        self,
        text: str,
        *,
        include_top_level: bool = True,
        include_subclauses: bool = True
    ) -> Dict[str, List[Secao]]:
        """
        Internal method to extract clauses using the improved algorithm.
        
        Args:
            text: Normalized text
            include_top_level: Include top-level clauses
            include_subclauses: Include subclauses
            
        Returns:
            Dictionary with "top" and/or "sub" keys containing lists of Secao
        """
        result: Dict[str, List[Secao]] = {}
        
        if include_top_level:
            top_headers = find_top_headers(text)
            result["top"] = segment_sections(text, top_headers)
            
        if include_subclauses:
            sub_headers = find_sub_headers(text)
            result["sub"] = segment_sections(text, sub_headers)
            
        return result
    
    def _convert_secao_to_clause(
        self, 
        secao: Secao, 
        document_id: str,
        estimated_pages: int,
        clause_type: str
    ) -> ProcessedClause:
        """
        Convert Secao object to ProcessedClause.
        
        Args:
            secao: Secao object
            document_id: Document ID
            estimated_pages: Number of pages
            clause_type: "main" or "sub"
            
        Returns:
            ProcessedClause object
        """
        # Generate clause ID
        clause_id = self._generate_clause_id(
            secao.text, secao.number, document_id, clause_type
        )
        
        # Estimate coordinates
        coordinates = self._estimate_coordinates(
            secao.start, secao.end, secao.text, estimated_pages
        )
        
        # Create title
        title = f"{secao.number}. {secao.title[:50]}"
        if len(secao.title) > 50:
            title += "..."
        
        # Calculate level
        level = len(secao.number.split('.'))
        
        return ProcessedClause(
            clause_id=clause_id,
            text=secao.text,
            coordinates=coordinates,
            title=title,
            level=level,
            clause_number=secao.number
        )
    
    def _generate_clause_id(
        self, 
        text: str, 
        number: str, 
        document_id: str,
        clause_type: str
    ) -> str:
        """Generate stable clause ID."""
        content_sample = text[:200].strip()
        id_string = f"{document_id}_{clause_type}_{number}_{content_sample}"
        id_hash = hashlib.md5(id_string.encode()).hexdigest()
        return f"advanced_{clause_type}_{id_hash[:12]}"
    
    def _estimate_coordinates(
        self, 
        start_pos: int, 
        end_pos: int, 
        text: str,
        estimated_pages: int
    ) -> BoundingBox:
        """
        Estimate coordinates for clause positioning.
        
        Args:
            start_pos: Start position in text
            end_pos: End position in text
            text: Full text
            estimated_pages: Number of pages
            
        Returns:
            Estimated bounding box
        """
        # Estimate page based on position
        total_chars = end_pos
        chars_per_page = total_chars / estimated_pages if estimated_pages > 0 else total_chars
        page_num = min(int(start_pos / chars_per_page), estimated_pages - 1) if chars_per_page > 0 else 0
        
        # Estimate position within page
        page_start = page_num * chars_per_page
        pos_in_page = start_pos - page_start
        y_ratio = pos_in_page / chars_per_page if chars_per_page > 0 else 0
        
        # Standard page dimensions
        page_width = 612
        page_height = 792
        
        top = y_ratio * page_height
        clause_length = end_pos - start_pos
        height = min(clause_length / chars_per_page * page_height, page_height / 3) if chars_per_page > 0 else 100
        
        return BoundingBox(
            x0=50,  # Left margin
            x1=page_width - 50,  # Right margin
            top=top,
            bottom=min(top + height, page_height),
            page_number=page_num,
            page_height=page_height
        )


# Integration function to use with existing PDF processors
async def extract_clauses_with_advanced_method(
    text: str,
    document_id: str,
    estimated_pages: int = 1
) -> List[ProcessedClause]:
    """
    Convenience function to extract clauses using the advanced method.
    
    Args:
        text: PDF text
        document_id: Document identifier
        estimated_pages: Estimated page count
        
    Returns:
        List of ProcessedClause objects
    """
    extractor = AdvancedClauseExtractor()
    return await extractor.extract_clauses_from_text(text, document_id, estimated_pages)


def extract_clauses_from_pdf(
    pdf_path: Path | str,
    *,
    include_top_level: bool = True,
    include_subclauses: bool = True
) -> Dict[str, List[Secao]]:
    """
    Extrai cláusulas de um PDF.
    Retorna um dicionário com chaves "top" e/ou "sub" contendo listas de Secao.
    
    Note: This function is included for compatibility but requires PDF reading capabilities.
    Use extract_clauses_with_advanced_method for integration with existing system.
    """
    # This would require PDF reading implementation
    # For now, we'll use the existing Docling-based system
    raise NotImplementedError(
        "Direct PDF reading not implemented. Use extract_clauses_with_advanced_method with Docling text."
    )