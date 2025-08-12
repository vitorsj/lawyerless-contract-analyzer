"""
PDF processing service using pdfplumber and pypdf.

This module handles PDF text extraction with coordinate information,
coordinate transformation for web display, and fallback mechanisms.
"""

import logging
import hashlib
import re
from io import BytesIO
from typing import List, Dict, Optional
from datetime import datetime

import pdfplumber
from pypdf import PdfReader

from ..models import (
    PDFMetadata, 
    TextFragment, 
    BoundingBox, 
    PDFExtractionResult,
    ProcessedClause
)
from ..settings import settings

logger = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors."""
    pass


class PDFProcessor:
    """
    PDF processing service with coordinate extraction and fallback mechanisms.
    
    Primary method: pdfplumber for coordinate-based extraction
    Fallback method: pypdf for simple text extraction
    """
    
    def __init__(self):
        """Initialize PDF processor with configuration."""
        self.max_pages = settings.max_pdf_pages
        self.processing_timeout = settings.pdf_processing_timeout
        self.chunk_size = settings.pdf_chunk_size
        self.chunk_overlap = settings.pdf_chunk_overlap
    
    async def extract_text_with_coordinates(
        self, 
        file_content: bytes, 
        filename: str
    ) -> PDFExtractionResult:
        """
        Extract text with coordinate information from PDF.
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
        
        Returns:
            PDFExtractionResult with text, coordinates, and metadata
        
        Raises:
            PDFProcessingError: If extraction fails
        """
        start_time = datetime.now()
        
        try:
            # Generate document ID
            document_id = self._generate_document_id(file_content, filename)
            
            # Try pdfplumber first for coordinate extraction
            try:
                result = await self._extract_with_pdfplumber(
                    file_content, filename, document_id
                )
                logger.info(f"Successfully extracted PDF with pdfplumber: {filename}")
                return result
                
            except Exception as plumber_error:
                logger.warning(f"pdfplumber failed for {filename}: {plumber_error}")
                
                # Fallback to pypdf
                try:
                    result = await self._extract_with_pypdf(
                        file_content, filename, document_id
                    )
                    logger.info(f"Successfully extracted PDF with pypdf fallback: {filename}")
                    return result
                    
                except Exception as pypdf_error:
                    logger.error(f"Both pdfplumber and pypdf failed for {filename}")
                    logger.error(f"pdfplumber error: {plumber_error}")
                    logger.error(f"pypdf error: {pypdf_error}")
                    
                    # If both errors are the same page limit error, re-raise the original
                    if (isinstance(plumber_error, PDFProcessingError) and 
                        isinstance(pypdf_error, PDFProcessingError) and
                        "maximum allowed" in str(plumber_error) and 
                        "maximum allowed" in str(pypdf_error)):
                        raise plumber_error
                    
                    raise PDFProcessingError(
                        f"Failed to extract PDF with both methods: {filename}"
                    ) from pypdf_error
        
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"PDF processing failed after {processing_time:.2f}s: {str(e)}")
            raise PDFProcessingError(f"PDF processing failed: {str(e)}") from e
    
    async def _extract_with_pdfplumber(
        self, 
        file_content: bytes, 
        filename: str, 
        document_id: str
    ) -> PDFExtractionResult:
        """
        Extract PDF using pdfplumber for coordinate information.
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
            document_id: Document identifier
        
        Returns:
            PDFExtractionResult with coordinate information
        """
        start_time = datetime.now()
        
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            # Validate page count
            if len(pdf.pages) > self.max_pages:
                raise PDFProcessingError(
                    f"PDF has {len(pdf.pages)} pages, maximum allowed is {self.max_pages}"
                )
            
            # Extract metadata
            metadata = self._extract_pdf_metadata(pdf, file_content, filename)
            
            # Extract text fragments with coordinates
            all_text_fragments = []
            full_text = ""
            warnings = []
            
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_fragments = await self._extract_page_with_coordinates(
                        page, page_num
                    )
                    all_text_fragments.extend(page_fragments)
                    
                    # Build full text
                    page_text = "\n".join(fragment.text for fragment in page_fragments)
                    full_text += f"\n\n--- Página {page_num + 1} ---\n\n" + page_text
                    
                    # Debug logging for text structure
                    logger.debug(f"Page {page_num + 1} extracted {len(page_fragments)} fragments")
                    logger.debug(f"Page {page_num + 1} text preview: {page_text[:200]}...")
                    
                except Exception as page_error:
                    warning = f"Failed to process page {page_num + 1}: {str(page_error)}"
                    warnings.append(warning)
                    logger.warning(warning)
                    
                    # Try to extract text without coordinates as fallback
                    try:
                        page_text = page.extract_text() or ""
                        full_text += f"\n\n--- Página {page_num + 1} (sem coordenadas) ---\n\n" + page_text
                    except Exception:
                        warnings.append(f"Completely failed to extract page {page_num + 1}")
            
            # Create temporary clauses from text fragments (will be segmented later)
            temp_clauses = self._create_temp_clauses_from_fragments(all_text_fragments)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return PDFExtractionResult(
                document_id=document_id,
                metadata=metadata,
                clauses=temp_clauses,
                full_text=full_text.strip(),
                extraction_time=processing_time,
                extraction_method="pdfplumber",
                warnings=warnings
            )
    
    async def _extract_page_with_coordinates(
        self, 
        page, 
        page_num: int
    ) -> List[TextFragment]:
        """
        Extract text fragments with coordinates from a single page.
        
        Args:
            page: pdfplumber page object
            page_num: Page number (0-indexed)
        
        Returns:
            List of TextFragment objects with coordinates
        """
        fragments = []
        
        # Get page dimensions
        page_height = float(page.height)
        page_width = float(page.width)
        
        # Extract words with coordinates
        words = page.extract_words()
        
        if not words:
            # Fallback: try to extract text without detailed coordinates
            text = page.extract_text()
            if text:
                # Create a single fragment covering the whole page
                fragments.append(TextFragment(
                    text=text,
                    coordinates=BoundingBox(
                        x0=0,
                        x1=page_width,
                        top=0,
                        bottom=page_height,
                        page_number=page_num,
                        page_height=page_height
                    )
                ))
            return fragments
        
        # Group words into lines based on vertical position
        lines = self._group_words_into_lines(words, page_height)
        
        for line in lines:
            if not line['words']:
                continue
                
            # Combine words in the line
            line_text = " ".join(word['text'] for word in line['words'])
            
            # Calculate line bounding box
            min_x0 = min(word['x0'] for word in line['words'])
            max_x1 = max(word['x1'] for word in line['words'])
            
            # Transform coordinates: pdfplumber uses bottom-left origin, we need top-left
            web_top = page_height - line['bottom']
            web_bottom = page_height - line['top']
            
            fragments.append(TextFragment(
                text=line_text,
                coordinates=BoundingBox(
                    x0=min_x0,
                    x1=max_x1,
                    top=web_top,
                    bottom=web_bottom,
                    page_number=page_num,
                    page_height=page_height
                ),
                font_size=line.get('font_size'),
                font_name=line.get('font_name')
            ))
        
        return fragments
    
    def _group_words_into_lines(
        self, 
        words: List[Dict], 
        page_height: float,
        tolerance: float = 5.0  # Increased tolerance for better line grouping
    ) -> List[Dict]:
        """
        Group words into lines based on vertical position.
        
        Args:
            words: List of word dictionaries with coordinates
            page_height: Page height for coordinate transformation
            tolerance: Vertical tolerance for grouping into lines
        
        Returns:
            List of line dictionaries with grouped words
        """
        if not words:
            return []
        
        # Sort words by vertical position (top to bottom)
        sorted_words = sorted(words, key=lambda w: -w['top'])  # Negative for top-to-bottom
        
        lines = []
        current_line = None
        
        for word in sorted_words:
            if current_line is None:
                # Start new line
                current_line = {
                    'words': [word],
                    'top': word['top'],
                    'bottom': word['bottom'],
                    'font_size': word.get('size'),
                    'font_name': word.get('fontname')
                }
            else:
                # Check if word belongs to current line (similar vertical position)
                if abs(word['top'] - current_line['top']) <= tolerance:
                    # Add to current line
                    current_line['words'].append(word)
                    current_line['top'] = max(current_line['top'], word['top'])
                    current_line['bottom'] = min(current_line['bottom'], word['bottom'])
                else:
                    # Finish current line and start new one
                    lines.append(current_line)
                    current_line = {
                        'words': [word],
                        'top': word['top'],
                        'bottom': word['bottom'],
                        'font_size': word.get('size'),
                        'font_name': word.get('fontname')
                    }
        
        # Add last line
        if current_line:
            lines.append(current_line)
        
        # Sort lines by vertical position and sort words within each line horizontally
        for line in lines:
            line['words'].sort(key=lambda w: w['x0'])
        
        return lines
    
    async def _extract_with_pypdf(
        self, 
        file_content: bytes, 
        filename: str, 
        document_id: str
    ) -> PDFExtractionResult:
        """
        Fallback extraction using pypdf (no coordinate information).
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
            document_id: Document identifier
        
        Returns:
            PDFExtractionResult without coordinate information
        """
        start_time = datetime.now()
        
        reader = PdfReader(BytesIO(file_content))
        
        # Validate page count
        if len(reader.pages) > self.max_pages:
            raise PDFProcessingError(
                f"PDF has {len(reader.pages)} pages, maximum allowed is {self.max_pages}"
            )
        
        # Extract metadata
        metadata = PDFMetadata(
            filename=filename,
            file_size=len(file_content),
            page_count=len(reader.pages),
            creation_date=self._format_pdf_date(reader.metadata.get('/CreationDate')),
            modification_date=self._format_pdf_date(reader.metadata.get('/ModDate')),
            title=reader.metadata.get('/Title'),
            author=reader.metadata.get('/Author'),
            subject=reader.metadata.get('/Subject')
        )
        
        # Extract text from all pages
        full_text = ""
        temp_clauses = []
        
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    full_text += f"\n\n--- Página {page_num + 1} ---\n\n" + page_text
                    
                    # Create a temporary clause for the whole page (no coordinates)
                    clause_id = hashlib.md5(
                        f"{document_id}_page_{page_num}_{page_text[:100]}".encode()
                    ).hexdigest()[:16]
                    
                    temp_clauses.append(ProcessedClause(
                        clause_id=clause_id,
                        text=page_text,
                        coordinates=BoundingBox(
                            x0=0,
                            x1=612,  # Standard page width
                            top=0,
                            bottom=792,  # Standard page height
                            page_number=page_num,
                            page_height=792
                        ),
                        title=f"Página {page_num + 1}"
                    ))
                    
            except Exception as page_error:
                logger.warning(f"Failed to extract page {page_num + 1} with pypdf: {page_error}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return PDFExtractionResult(
            document_id=document_id,
            metadata=metadata,
            clauses=temp_clauses,
            full_text=full_text.strip(),
            extraction_time=processing_time,
            extraction_method="pypdf",
            warnings=["Extracted without coordinate information (fallback method)"]
        )
    
    def _create_temp_clauses_from_fragments(
        self, 
        fragments: List[TextFragment]
    ) -> List[ProcessedClause]:
        """
        Create temporary clauses from text fragments (to be properly segmented later).
        
        Args:
            fragments: List of text fragments with coordinates
        
        Returns:
            List of temporary ProcessedClause objects
        """
        temp_clauses = []
        
        # Group fragments by page
        pages = {}
        for fragment in fragments:
            page_num = fragment.coordinates.page_number
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(fragment)
        
        # Create temporary clauses per page
        for page_num, page_fragments in pages.items():
            if not page_fragments:
                continue
                
            # Combine all fragments on the page
            page_text = "\n".join(fragment.text for fragment in page_fragments)
            
            # Calculate page bounding box
            min_x0 = min(f.coordinates.x0 for f in page_fragments)
            max_x1 = max(f.coordinates.x1 for f in page_fragments) 
            min_top = min(f.coordinates.top for f in page_fragments)
            max_bottom = max(f.coordinates.bottom for f in page_fragments)
            page_height = page_fragments[0].coordinates.page_height
            
            # Generate temporary clause ID
            clause_id = hashlib.md5(
                f"temp_page_{page_num}_{page_text[:100]}".encode()
            ).hexdigest()[:16]
            
            temp_clauses.append(ProcessedClause(
                clause_id=clause_id,
                text=page_text,
                coordinates=BoundingBox(
                    x0=min_x0,
                    x1=max_x1,
                    top=min_top,
                    bottom=max_bottom,
                    page_number=page_num,
                    page_height=page_height
                ),
                title=f"Página {page_num + 1} (temporária)"
            ))
        
        return temp_clauses
    
    def _extract_pdf_metadata(
        self, 
        pdf, 
        file_content: bytes, 
        filename: str
    ) -> PDFMetadata:
        """
        Extract PDF metadata using pdfplumber.
        
        Args:
            pdf: pdfplumber PDF object
            file_content: Original file bytes
            filename: Original filename
        
        Returns:
            PDFMetadata object
        """
        metadata_dict = pdf.metadata or {}
        
        return PDFMetadata(
            filename=filename,
            file_size=len(file_content),
            page_count=len(pdf.pages),
            creation_date=self._format_pdf_date(metadata_dict.get('CreationDate')),
            modification_date=self._format_pdf_date(metadata_dict.get('ModDate')),
            title=metadata_dict.get('Title'),
            author=metadata_dict.get('Author'),
            subject=metadata_dict.get('Subject')
        )
    
    def _format_pdf_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Format PDF date string to ISO format.
        
        Args:
            date_str: PDF date string (e.g., "D:20240101120000+00'00'")
        
        Returns:
            ISO formatted date string or None
        """
        if not date_str:
            return None
            
        try:
            # Remove PDF date prefix and timezone info for simplicity
            clean_date = re.sub(r"^D:", "", date_str)
            clean_date = re.sub(r"[+\-]\d{2}'\d{2}'?$", "", clean_date)
            
            # Parse date (YYYYMMDDHHMMSS format)
            if len(clean_date) >= 8:
                year = int(clean_date[:4])
                month = int(clean_date[4:6])
                day = int(clean_date[6:8])
                
                if len(clean_date) >= 14:
                    hour = int(clean_date[8:10])
                    minute = int(clean_date[10:12])
                    second = int(clean_date[12:14])
                    dt = datetime(year, month, day, hour, minute, second)
                else:
                    dt = datetime(year, month, day)
                
                return dt.isoformat()
                
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse PDF date '{date_str}': {e}")
            
        return None
    
    def _generate_document_id(self, file_content: bytes, filename: str) -> str:
        """
        Generate stable document ID based on content and filename.
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
        
        Returns:
            Unique document identifier
        """
        # Create hash from file content and name
        content_hash = hashlib.md5(file_content).hexdigest()
        filename_hash = hashlib.md5(filename.encode()).hexdigest()
        
        return f"doc_{content_hash[:8]}_{filename_hash[:8]}"
    
    def transform_coordinates_for_web(
        self, 
        pdf_coordinates: BoundingBox,
        scale_factor: float = 1.0
    ) -> BoundingBox:
        """
        Transform PDF coordinates to web coordinates.
        
        PDF uses bottom-left origin, web uses top-left origin.
        
        Args:
            pdf_coordinates: Original PDF coordinates
            scale_factor: Scale factor for zoom/display
        
        Returns:
            Transformed coordinates for web display
        """
        return BoundingBox(
            x0=pdf_coordinates.x0 * scale_factor,
            x1=pdf_coordinates.x1 * scale_factor,
            top=pdf_coordinates.top * scale_factor,  # Already transformed in extraction
            bottom=pdf_coordinates.bottom * scale_factor,  # Already transformed in extraction
            page_number=pdf_coordinates.page_number,
            page_height=pdf_coordinates.page_height * scale_factor
        )