"""
Clause segmentation service for Brazilian legal documents.

This module handles clause boundary detection using heuristics specific to
Brazilian legal documents, including numbered sections, "Cláusula", "Seção",
Roman numerals, and complex subsection patterns.
"""

import logging
import hashlib
import re
from typing import List, Optional
from dataclasses import dataclass

from ..models import (
    ProcessedClause, 
    BoundingBox, 
    PDFExtractionResult
)

logger = logging.getLogger(__name__)


@dataclass
class ClauseMatch:
    """Detected clause boundary information."""
    start_pos: int
    end_pos: int
    text: str
    title: Optional[str]
    number: Optional[str]
    level: int
    pattern_type: str
    confidence: float


class ClauseSegmenter:
    """
    Clause segmentation service for Brazilian legal documents.
    
    Detects clause boundaries using multiple heuristics:
    - Numbered sections (1., 2., 1.1., etc.)
    - "Cláusula" patterns 
    - "Seção" patterns
    - Roman numerals (I, II, III, etc.)
    - Brazilian legal subsection patterns
    """
    
    def __init__(self):
        """Initialize clause segmenter with Brazilian legal patterns."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regular expressions for clause detection."""
        
        # Pattern 1: Numbered clauses (1, 1.1, 1.2, 2, 2.1, 2.2.1, etc.)
        # Matches hierarchical numbering at the beginning of lines
        self.numbered_pattern = re.compile(
            r'(?:^|\n)\s*(\d+(?:\.\d+)*)\s*\.?\s*[-–—]?\s*([^\r\n]*)',
            re.MULTILINE
        )
        
        # Pattern 2: "CLÁUSULA" patterns - Enhanced for continuous text
        self.clausula_pattern = re.compile(
            r'(?:^|\n)\s*(?:CLÁUSULA|CLAUSULA)\s*(\d+(?:\.\d+)*)?[ªº]?\s*[-–—]?\s*([^\n]*?)(?=\n\s*(?:CLÁUSULA|SEÇÃO|\d+\.|$))',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern 3: "SEÇÃO" patterns - Enhanced for continuous text
        self.secao_pattern = re.compile(
            r'(?:^|\s)(?:SEÇÃO|SECAO)\s*([IVXLCDM]+|\d+(?:\.\d+)*)?[ªº]?\s*[-–—]?\s*([A-ZÁÊÇÕÜ][^\n]*?)(?=\s*(?:\d+(?:\.\d+)*\.|CLÁUSULA|SEÇÃO|$))',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern 4: Roman numerals
        self.roman_pattern = re.compile(
            r'(?:^|\n)\s*([IVXLCDM]+)\s*[-–—]?\s*([A-ZÁÊÇÕÜ][A-ZÁÉÍÓÚÀÂÊÔÇÕÜa-záéíóúàâêôçõü\s]{0,100}?)(?:\n|$)',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern 5: Article patterns
        self.artigo_pattern = re.compile(
            r'(?:^|\n)\s*(?:ARTIGO|Art\.|ARTIGO|ART)\s*(\d+(?:\.\d+)*)[ªº]?\s*[-–—]?\s*([A-ZÁÊÇÕÜ][A-ZÁÉÍÓÚÀÂÊÔÇÕÜa-záéíóúàâêôçõü\s]{0,100}?)(?:\n|$)',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern 6: Paragraph patterns
        self.paragrafo_pattern = re.compile(
            r'(?:^|\n)\s*(?:PARÁGRAFO|Parágrafo|§)\s*(\d+(?:\.\d+)*)[ªº]?\s*[-–—]?\s*([A-ZÁÊÇÕÜ][A-ZÁÉÍÓÚÀÂÊÔÇÕÜa-záéíóúàâêôçõü\s]{0,100}?)(?:\n|$)',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern 7: Letter subsections (a), b), etc.)
        self.letter_pattern = re.compile(
            r'(?:^|\n)\s*([a-z])\)\s*([A-ZÁÊÇÕÜ][A-ZÁÉÍÓÚÀÂÊÔÇÕÜa-záéíóúàâêôçõü\s]{0,100}?)(?:\n|$)',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Common Brazilian legal document section headers
        self.header_keywords = {
            'object': r'(?:OBJETO|FINALIDADE|PROPÓSITO)',
            'parties': r'(?:PARTES|DAS PARTES|QUALIFICAÇÃO)',
            'definitions': r'(?:DEFINIÇÕES|CONCEITOS|TERMOS)',
            'investment': r'(?:INVESTIMENTO|VALOR|MONTANTE)',
            'conversion': r'(?:CONVERSÃO|TRANSFORMAÇÃO)',
            'rights': r'(?:DIREITOS|PRERROGATIVAS)', 
            'obligations': r'(?:OBRIGAÇÕES|DEVERES|COMPROMISSOS)',
            'governance': r'(?:GOVERNANÇA|ADMINISTRAÇÃO)',
            'information': r'(?:INFORMAÇÕES|PRESTAÇÃO DE CONTAS)',
            'transfer': r'(?:TRANSFERÊNCIA|CESSÃO|ALIENAÇÃO)',
            'liquidation': r'(?:LIQUIDAÇÃO|DISSOLUÇÃO)',
            'term': r'(?:PRAZO|VIGÊNCIA|DURAÇÃO)',
            'jurisdiction': r'(?:FORO|JURISDIÇÃO|LEI APLICÁVEL)',
            'miscellaneous': r'(?:DISPOSIÇÕES GERAIS|VÁRIAS|OUTRAS DISPOSIÇÕES)'
        }
    
    async def segment_clauses(
        self, 
        extraction_result: PDFExtractionResult
    ) -> List[ProcessedClause]:
        """
        Segment PDF text into clauses using Brazilian legal document heuristics.
        
        Args:
            extraction_result: Result from PDF extraction
        
        Returns:
            List of segmented ProcessedClause objects
        """
        logger.info(f"Starting clause segmentation for document {extraction_result.document_id}")
        
        # Get full text for pattern matching
        full_text = extraction_result.full_text
        
        if not full_text.strip():
            logger.warning("No text found for clause segmentation")
            return []
        
        logger.info(f"Full text length: {len(full_text)} characters")
        logger.debug(f"Full text preview: {full_text[:500]}...")
        
        # Detect clause boundaries using multiple patterns
        clause_matches = self._detect_clause_boundaries(full_text)
        
        logger.info(f"Detected {len(clause_matches)} clause matches")
        for i, match in enumerate(clause_matches):
            logger.debug(f"Match {i+1}: {match.pattern_type} - {match.number} - '{match.title}' (confidence: {match.confidence})")
        
        if not clause_matches:
            logger.warning("No clause patterns detected, trying paragraph-based segmentation")
            # Try paragraph-based segmentation as fallback
            paragraph_clauses = self._create_paragraph_based_clauses(extraction_result)
            if len(paragraph_clauses) > 1:
                logger.info(f"Created {len(paragraph_clauses)} clauses using paragraph segmentation")
                return paragraph_clauses
            else:
                logger.warning("Paragraph segmentation also failed, creating single clause")
                return self._create_single_clause(extraction_result)
        
        # Sort matches by position
        clause_matches.sort(key=lambda m: m.start_pos)
        
        # Create processed clauses with coordinate information
        processed_clauses = await self._create_processed_clauses(
            clause_matches, 
            full_text,
            extraction_result
        )
        
        # Filter out empty clauses and validate
        processed_clauses = [c for c in processed_clauses if c.text.strip()]
        
        logger.info(f"Segmented into {len(processed_clauses)} clauses")
        return processed_clauses
    
    def _detect_clause_boundaries(self, text: str) -> List[ClauseMatch]:
        """
        Detect clause boundaries using multiple pattern matching approaches.
        
        Args:
            text: Full document text
        
        Returns:
            List of ClauseMatch objects
        """
        all_matches = []
        
        # Pattern 1: Numbered clauses
        matches = list(self.numbered_pattern.finditer(text))
        logger.debug(f"Found {len(matches)} numbered clause matches")
        for match in matches:
            confidence = 0.9  # High confidence for numbered patterns
            title_text = match.group(2).strip() if match.group(2) else None
            logger.debug(f"Numbered match: '{match.group(1)}' - '{title_text}' at {match.start()}-{match.end()}")
            all_matches.append(ClauseMatch(
                start_pos=match.start(),
                end_pos=match.end(),
                text=match.group(0),
                title=title_text,
                number=match.group(1),
                level=len(match.group(1).split('.')),
                pattern_type="numbered",
                confidence=confidence
            ))
        
        # Pattern 2: CLÁUSULA patterns  
        matches = list(self.clausula_pattern.finditer(text))
        logger.debug(f"Found {len(matches)} CLAUSULA clause matches")
        for match in matches:
            confidence = 0.95  # Very high confidence for explicit clauses
            number = match.group(1) if match.group(1) else None
            title_text = match.group(2).strip() if match.group(2) else None
            logger.debug(f"Clausula match: '{number}' - '{title_text}' at {match.start()}-{match.end()}")
            all_matches.append(ClauseMatch(
                start_pos=match.start(),
                end_pos=match.end(),
                text=match.group(0),
                title=title_text,
                number=number,
                level=self._calculate_hierarchical_level(number, "clausula"),
                pattern_type="clausula",
                confidence=confidence
            ))
        
        # Pattern 3: SEÇÃO patterns
        matches = self.secao_pattern.finditer(text)
        for match in matches:
            confidence = 0.85
            number = match.group(1) if match.group(1) else None
            all_matches.append(ClauseMatch(
                start_pos=match.start(),
                end_pos=match.end(),
                text=match.group(0),
                title=match.group(2).strip() if match.group(2) else None,
                number=number,
                level=self._calculate_hierarchical_level(number, "secao"),
                pattern_type="secao",
                confidence=confidence
            ))
        
        # Pattern 4: Roman numerals
        matches = self.roman_pattern.finditer(text)
        for match in matches:
            # Only include if it looks like a section header
            if self._is_likely_section_header(match.group(2) or ""):
                confidence = 0.7
                number = match.group(1)
                all_matches.append(ClauseMatch(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    text=match.group(0),
                    title=match.group(2).strip() if match.group(2) else None,
                    number=number,
                    level=self._calculate_hierarchical_level(number, "roman"),
                    pattern_type="roman",
                    confidence=confidence
                ))
        
        # Pattern 5: ARTIGO patterns
        matches = self.artigo_pattern.finditer(text)
        for match in matches:
            confidence = 0.8
            number = match.group(1) if match.group(1) else None
            all_matches.append(ClauseMatch(
                start_pos=match.start(),
                end_pos=match.end(),
                text=match.group(0),
                title=match.group(2).strip() if match.group(2) else None,
                number=number,
                level=self._calculate_hierarchical_level(number, "artigo"),
                pattern_type="artigo",
                confidence=confidence
            ))
        
        # Pattern 6: Paragraph patterns
        matches = self.paragrafo_pattern.finditer(text)
        for match in matches:
            confidence = 0.6
            number = match.group(1) if match.group(1) else None
            all_matches.append(ClauseMatch(
                start_pos=match.start(),
                end_pos=match.end(),
                text=match.group(0),
                title=match.group(2).strip() if match.group(2) else None,
                number=number,
                level=self._calculate_hierarchical_level(number, "paragraph"),
                pattern_type="paragrafo",
                confidence=confidence
            ))
        
        # Pattern 7: Letter subsections
        matches = self.letter_pattern.finditer(text)
        for match in matches:
            confidence = 0.5  # Lower confidence as letters can be part of text
            number = match.group(1)
            all_matches.append(ClauseMatch(
                start_pos=match.start(),
                end_pos=match.end(),
                text=match.group(0),
                title=match.group(2).strip() if match.group(2) else None,
                number=number,
                level=self._calculate_hierarchical_level(number, "letter"),
                pattern_type="letter",
                confidence=confidence
            ))
        
        # Remove overlapping matches with lower confidence
        filtered_matches = self._remove_overlapping_matches(all_matches)
        
        return filtered_matches
    
    def _calculate_hierarchical_level(self, number: str, pattern_type: str) -> int:
        """Calculate the hierarchical level based on numbering pattern."""
        if not number:
            # Default levels for non-numbered patterns
            level_map = {
                "clausula": 1,    # "CLÁUSULA" patterns are top-level
                "secao": 1,       # "SEÇÃO" patterns are top-level  
                "artigo": 1,      # "ARTIGO" patterns are top-level
                "roman": 1,       # Roman numerals are typically top-level
                "paragraph": 2,    # Paragraphs are sub-level
                "letter": 3        # Letter subsections are deeper
            }
            return level_map.get(pattern_type, 1)
        
        # For numbered patterns, count the dots
        if '.' in number:
            return len(number.split('.'))
        
        # Single numbers are level 1
        return 1
    
    def _is_likely_section_header(self, text: str) -> bool:
        """
        Check if text is likely a section header based on keywords.
        
        Args:
            text: Text to check
        
        Returns:
            True if likely a section header
        """
        if not text or len(text) > 100:
            return False
        
        # Reject if it's too long or contains typical sentence patterns
        if len(text) > 50 or ' que ' in text.lower() or ' para ' in text.lower():
            return False
            
        text_upper = text.upper()
        
        # Check for common section keywords
        for category, pattern in self.header_keywords.items():
            if re.search(pattern, text_upper):
                return True
        
        # Check for other indicators (using word boundaries)
        header_indicators = [
            r'\bDO\b', r'\bDA\b', r'\bDOS\b', r'\bDAS\b',  # Portuguese articles
            r'\bSOBRE\b', r'\bACERCA\b',
            r'\bTERMO\b', r'\bACORDO\b',
            r'\bVALOR\b', r'\bPRAZO\b',
            r'\bFORMA\b', r'\bMODO\b',
            r'\bCONDIÇÕES\b', r'\bCONDICOES\b'
        ]
        
        for pattern in header_indicators:
            if re.search(pattern, text_upper):
                return True
        
        return False
    
    def _remove_overlapping_matches(self, matches: List[ClauseMatch]) -> List[ClauseMatch]:
        """
        Remove overlapping matches, keeping those with higher confidence.
        
        Args:
            matches: List of clause matches
        
        Returns:
            Filtered list without overlaps
        """
        if not matches:
            return []
        
        # Sort by start position, then by confidence (descending)
        matches.sort(key=lambda m: (m.start_pos, -m.confidence))
        
        filtered = []
        
        for match in matches:
            # Check if this match overlaps with any already filtered match
            overlaps = False
            for existing in filtered:
                if (match.start_pos < existing.end_pos and 
                    match.end_pos > existing.start_pos):
                    # There's an overlap
                    if match.confidence > existing.confidence:
                        # Replace the existing match with this higher confidence one
                        filtered.remove(existing)
                        break
                    else:
                        # Keep existing, skip this match
                        overlaps = True
                        break
            
            if not overlaps:
                filtered.append(match)
        
        return filtered
    
    async def _create_processed_clauses(
        self, 
        clause_matches: List[ClauseMatch],
        full_text: str,
        extraction_result: PDFExtractionResult
    ) -> List[ProcessedClause]:
        """
        Create ProcessedClause objects from clause matches.
        
        Args:
            clause_matches: Detected clause boundaries
            full_text: Full document text
            extraction_result: Original extraction result
        
        Returns:
            List of ProcessedClause objects
        """
        processed_clauses = []
        
        for i, match in enumerate(clause_matches):
            # For numbered clauses, find the actual start of the clause content
            # The regex match might only capture the number + first line
            if match.pattern_type == "numbered":
                # Find the full line that contains the clause number
                lines = full_text.split('\n')
                clause_start_line_idx = None
                
                # Find which line contains this clause number
                for line_idx, line in enumerate(lines):
                    if match.number and line.strip().startswith(match.number):
                        clause_start_line_idx = line_idx
                        break
                
                if clause_start_line_idx is not None:
                    # Calculate character position of this line
                    start_pos = sum(len(line) + 1 for line in lines[:clause_start_line_idx])  # +1 for \n
                    
                    # Find end position (start of next clause or end of document)
                    if i + 1 < len(clause_matches):
                        # Find the next clause's line
                        next_match = clause_matches[i + 1]
                        end_pos = next_match.start_pos
                        
                        # For numbered clauses, be more precise
                        if next_match.pattern_type == "numbered":
                            for next_line_idx, line in enumerate(lines[clause_start_line_idx + 1:], start=clause_start_line_idx + 1):
                                if next_match.number and line.strip().startswith(next_match.number):
                                    end_pos = sum(len(line) + 1 for line in lines[:next_line_idx])
                                    break
                    else:
                        end_pos = len(full_text)
                else:
                    # Fallback to original positions
                    start_pos = match.start_pos
                    end_pos = clause_matches[i + 1].start_pos if i + 1 < len(clause_matches) else len(full_text)
            else:
                # For non-numbered clauses, use original logic
                start_pos = match.start_pos
                end_pos = clause_matches[i + 1].start_pos if i + 1 < len(clause_matches) else len(full_text)
            
            # Extract clause text
            clause_text = full_text[start_pos:end_pos].strip()
            
            if not clause_text:
                continue
            
            # Clean up clause text (remove extra whitespace, normalize line breaks)
            clause_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clause_text)  # Normalize multiple line breaks
            clause_text = re.sub(r'[ \t]+', ' ', clause_text)  # Normalize spaces
            
            # Generate stable clause ID
            clause_id = self._generate_clause_id(
                clause_text, 
                match.number, 
                match.pattern_type,
                extraction_result.document_id
            )
            
            # Estimate coordinates
            coordinates = self._estimate_clause_coordinates(
                start_pos, 
                end_pos, 
                full_text,
                extraction_result
            )
            
            # Create title - for numbered clauses, extract title from first line content
            if match.pattern_type == "numbered" and match.title:
                title = f"{match.number}. {match.title.strip()}"
            else:
                title = self._create_clause_title(match)
            
            processed_clause = ProcessedClause(
                clause_id=clause_id,
                text=clause_text,
                coordinates=coordinates,
                title=title,
                level=match.level,
                clause_number=match.number
            )
            
            processed_clauses.append(processed_clause)
            
            logger.debug(f"Created clause {match.number}: {len(clause_text)} chars, title: '{title}'")
        
        return processed_clauses
    
    def _generate_clause_id(
        self, 
        text: str, 
        number: Optional[str], 
        pattern_type: str,
        document_id: str
    ) -> str:
        """
        Generate stable clause ID based on content and position.
        
        Args:
            text: Clause text
            number: Clause number if available
            pattern_type: Pattern type used for detection
            document_id: Document identifier
        
        Returns:
            Stable clause identifier
        """
        # Create components for ID generation
        content_sample = text[:200].strip()  # First 200 chars for uniqueness
        number_part = number or "unnumbered"
        
        # Create hash
        id_string = f"{document_id}_{pattern_type}_{number_part}_{content_sample}"
        id_hash = hashlib.md5(id_string.encode()).hexdigest()
        
        return f"clause_{pattern_type}_{id_hash[:12]}"
    
    def _estimate_clause_coordinates(
        self, 
        start_pos: int, 
        end_pos: int,
        full_text: str,
        extraction_result: PDFExtractionResult
    ) -> BoundingBox:
        """
        Estimate clause coordinates based on text position.
        
        This is a simplified implementation. In practice, you'd want to
        map text positions to actual PDF coordinates more accurately.
        
        Args:
            start_pos: Start position in full text
            end_pos: End position in full text
            full_text: Full document text
            extraction_result: Original extraction result
        
        Returns:
            Estimated bounding box
        """
        # Simple estimation: assume uniform text distribution across pages
        total_chars = len(full_text)
        total_pages = extraction_result.metadata.page_count
        
        if total_chars == 0 or total_pages == 0:
            # Fallback coordinates
            return BoundingBox(
                x0=0,
                x1=612,
                top=0,
                bottom=792,
                page_number=0,
                page_height=792
            )
        
        # Estimate page based on character position
        chars_per_page = total_chars / total_pages
        estimated_page = min(int(start_pos / chars_per_page), total_pages - 1)
        
        # Estimate position within page
        page_start_char = estimated_page * chars_per_page
        char_in_page = start_pos - page_start_char
        position_ratio = char_in_page / chars_per_page if chars_per_page > 0 else 0
        
        # Standard page dimensions (US Letter)
        page_width = 612
        page_height = 792
        
        # Estimate Y position (assuming text flows top to bottom)
        estimated_top = position_ratio * page_height
        
        # For clause length estimation
        clause_length = end_pos - start_pos
        estimated_height = min(clause_length / chars_per_page * page_height, page_height / 4)
        
        return BoundingBox(
            x0=50,  # Typical margin
            x1=page_width - 50,  # Typical margin
            top=estimated_top,
            bottom=min(estimated_top + estimated_height, page_height),
            page_number=estimated_page,
            page_height=page_height
        )
    
    def _create_clause_title(self, match: ClauseMatch) -> str:
        """
        Create a readable title for the clause.
        
        Args:
            match: Clause match information
        
        Returns:
            Formatted clause title
        """
        if match.title:
            title = match.title.strip()
        else:
            title = ""
        
        # Add pattern type and number information
        if match.pattern_type == "clausula":
            prefix = "CLÁUSULA"
        elif match.pattern_type == "secao":
            prefix = "SEÇÃO"
        elif match.pattern_type == "artigo":
            prefix = "ARTIGO"
        elif match.pattern_type == "paragrafo":
            prefix = "PARÁGRAFO"
        elif match.pattern_type == "numbered":
            prefix = "ITEM"
        elif match.pattern_type == "roman":
            prefix = "SEÇÃO"
        elif match.pattern_type == "letter":
            prefix = "ALÍNEA"
        else:
            prefix = "CLÁUSULA"
        
        if match.number:
            if title:
                return f"{prefix} {match.number} - {title}"
            else:
                return f"{prefix} {match.number}"
        else:
            if title:
                return f"{prefix} - {title}"
            else:
                return f"{prefix}"
    
    def _create_paragraph_based_clauses(self, extraction_result: PDFExtractionResult) -> List[ProcessedClause]:
        """
        Create clauses based on paragraph breaks as fallback.
        
        Args:
            extraction_result: PDF extraction result
        
        Returns:
            List of ProcessedClause objects based on paragraphs
        """
        full_text = extraction_result.full_text
        
        # Split by double line breaks (paragraphs)
        paragraphs = re.split(r'\n\s*\n', full_text.strip())
        
        # Filter out very short paragraphs and page markers
        valid_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if (len(para) > 50 and  # At least 50 characters
                not re.match(r'^---\s*Página\s+\d+\s*---$', para) and  # Skip page markers
                not para.lower().startswith('página')):  # Skip page references
                valid_paragraphs.append(para)
        
        if len(valid_paragraphs) <= 1:
            return []  # Fall back to single clause
        
        clauses = []
        char_position = 0
        
        for i, paragraph in enumerate(valid_paragraphs):
            # Find position of this paragraph in the full text
            para_start = full_text.find(paragraph, char_position)
            if para_start == -1:
                para_start = char_position
            
            para_end = para_start + len(paragraph)
            char_position = para_end
            
            # Generate clause ID
            clause_id = f"para_{extraction_result.document_id}_{i+1}_{hashlib.md5(paragraph[:100].encode()).hexdigest()[:8]}"
            
            # Estimate coordinates
            coordinates = self._estimate_clause_coordinates(
                para_start, para_end, full_text, extraction_result
            )
            
            # Create title based on first 50 characters
            title = paragraph[:50].strip()
            if len(paragraph) > 50:
                title += "..."
                
            clauses.append(ProcessedClause(
                clause_id=clause_id,
                text=paragraph,
                coordinates=coordinates,
                title=f"Parágrafo {i+1}: {title}",
                level=1
            ))
        
        return clauses

    def _create_single_clause(self, extraction_result: PDFExtractionResult) -> List[ProcessedClause]:
        """
        Create single clause when no patterns are detected.
        
        Args:
            extraction_result: PDF extraction result
        
        Returns:
            Single ProcessedClause containing all text
        """
        clause_id = f"single_clause_{extraction_result.document_id}"
        
        # Use first temporary clause coordinates if available
        try:
            if extraction_result.clauses and len(extraction_result.clauses) > 0:
                coordinates = extraction_result.clauses[0].coordinates
            else:
                raise IndexError("No clauses available")
        except (IndexError, TypeError, AttributeError):
            coordinates = BoundingBox(
                x0=0,
                x1=612,
                top=0,
                bottom=792,
                page_number=0,
                page_height=792
            )
        
        return [ProcessedClause(
            clause_id=clause_id,
            text=extraction_result.full_text,
            coordinates=coordinates,
            title="Documento Completo",
            level=1
        )]