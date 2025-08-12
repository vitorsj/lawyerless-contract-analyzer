"""
Tests for PDF processing service.

This module tests PDF text extraction with pdfplumber and pypdf,
coordinate transformation, and fallback mechanisms.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app.services.pdf_processor import PDFProcessor, PDFProcessingError
from app.models import PDFExtractionResult, BoundingBox


@pytest.mark.unit
class TestPDFProcessor:
    """Test PDF processor functionality."""
    
    def test_processor_initialization(self):
        """Test PDFProcessor initialization."""
        processor = PDFProcessor()
        assert processor.max_pages > 0
        assert processor.processing_timeout > 0
        assert processor.chunk_size > 0
    
    @pytest.mark.asyncio
    async def test_extract_text_basic_success(self, sample_pdf_content):
        """Test basic PDF text extraction."""
        processor = PDFProcessor()
        filename = "test_contract.pdf"
        
        with patch('app.services.pdf_processor.pdfplumber') as mock_pdfplumber:
            # Mock pdfplumber functionality
            mock_pdf = Mock()
            mock_page = Mock()
            mock_page.extract_words.return_value = [
                {
                    'text': 'CONTRATO',
                    'x0': 50, 'x1': 150, 
                    'top': 700, 'bottom': 720,
                    'size': 12, 'fontname': 'Arial'
                },
                {
                    'text': 'DE', 
                    'x0': 160, 'x1': 180,
                    'top': 700, 'bottom': 720,
                    'size': 12, 'fontname': 'Arial'
                },
                {
                    'text': 'INVESTIMENTO',
                    'x0': 190, 'x1': 320,
                    'top': 700, 'bottom': 720, 
                    'size': 12, 'fontname': 'Arial'
                }
            ]
            mock_page.height = 792
            mock_page.width = 612
            
            mock_pdf.pages = [mock_page]
            mock_pdf.metadata = {'Title': 'Test Contract'}
            mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
            
            result = await processor.extract_text_with_coordinates(
                sample_pdf_content, filename
            )
            
            assert isinstance(result, PDFExtractionResult)
            assert result.metadata.filename == filename
            assert result.extraction_method == "pdfplumber"
            assert len(result.clauses) > 0
            assert "CONTRATO" in result.full_text
    
    @pytest.mark.asyncio 
    async def test_extract_text_fallback_to_pypdf(self, sample_pdf_content):
        """Test fallback to pypdf when pdfplumber fails."""
        processor = PDFProcessor()
        filename = "test_contract.pdf"
        
        with patch('app.services.pdf_processor.pdfplumber') as mock_pdfplumber, \
             patch('app.services.pdf_processor.PdfReader') as mock_pypdf:
            
            # Make pdfplumber fail
            mock_pdfplumber.open.side_effect = Exception("pdfplumber failed")
            
            # Mock pypdf success
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "CONTRATO DE INVESTIMENTO\nTexto do contrato..."
            mock_reader.pages = [mock_page]
            mock_reader.metadata = {'/Title': 'Test Contract'}
            mock_pypdf.return_value = mock_reader
            
            result = await processor.extract_text_with_coordinates(
                sample_pdf_content, filename
            )
            
            assert isinstance(result, PDFExtractionResult)
            assert result.extraction_method == "pypdf"
            assert "CONTRATO" in result.full_text
            assert len(result.warnings) > 0
            assert "fallback" in result.warnings[0].lower()
    
    @pytest.mark.asyncio
    async def test_extract_text_both_methods_fail(self, sample_pdf_content):
        """Test when both pdfplumber and pypdf fail."""
        processor = PDFProcessor()
        filename = "corrupted.pdf"
        
        with patch('app.services.pdf_processor.pdfplumber') as mock_pdfplumber, \
             patch('app.services.pdf_processor.PdfReader') as mock_pypdf:
            
            # Make both methods fail
            mock_pdfplumber.open.side_effect = Exception("pdfplumber failed")
            mock_pypdf.side_effect = Exception("pypdf failed")
            
            with pytest.raises(PDFProcessingError):
                await processor.extract_text_with_coordinates(
                    sample_pdf_content, filename
                )
    
    @pytest.mark.asyncio
    async def test_extract_text_too_many_pages(self, sample_pdf_content):
        """Test handling of PDFs with too many pages."""
        processor = PDFProcessor()
        processor.max_pages = 2  # Set low limit for testing
        filename = "large_document.pdf"
        
        with patch('app.services.pdf_processor.pdfplumber') as mock_pdfplumber, \
             patch('app.services.pdf_processor.PdfReader') as mock_pdf_reader:
            
            # Mock pdfplumber to return PDF with too many pages
            mock_pdf = Mock()
            mock_pdf.pages = [Mock() for _ in range(5)]  # 5 pages > 2 max_pages
            mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
            
            # Mock PdfReader similarly for fallback
            mock_reader = Mock()
            mock_reader.pages = [Mock() for _ in range(5)]
            mock_pdf_reader.return_value = mock_reader
            
            # Both methods should fail with page limit error
            with pytest.raises(PDFProcessingError, match="maximum allowed"):
                await processor.extract_text_with_coordinates(
                    sample_pdf_content, filename
                )
    
    def test_group_words_into_lines(self):
        """Test word grouping into lines functionality."""
        processor = PDFProcessor()
        
        words = [
            {'text': 'CONTRATO', 'x0': 50, 'x1': 150, 'top': 700, 'bottom': 720},
            {'text': 'DE', 'x0': 160, 'x1': 180, 'top': 700, 'bottom': 720},
            {'text': 'Segunda', 'x0': 50, 'x1': 120, 'top': 680, 'bottom': 700},
            {'text': 'linha', 'x0': 130, 'x1': 180, 'top': 680, 'bottom': 700},
        ]
        
        lines = processor._group_words_into_lines(words, 792)
        
        assert len(lines) == 2
        assert len(lines[0]['words']) == 2  # "CONTRATO DE"
        assert len(lines[1]['words']) == 2  # "Segunda linha"
        assert lines[0]['words'][0]['text'] == 'CONTRATO'
        assert lines[1]['words'][0]['text'] == 'Segunda'
    
    def test_generate_document_id(self):
        """Test document ID generation."""
        processor = PDFProcessor()
        
        content1 = b"PDF content 1"
        content2 = b"PDF content 2"
        filename = "test.pdf"
        
        id1 = processor._generate_document_id(content1, filename)
        id2 = processor._generate_document_id(content2, filename)
        id3 = processor._generate_document_id(content1, filename)
        
        assert id1 != id2  # Different content should give different IDs
        assert id1 == id3   # Same content should give same ID
        assert id1.startswith("doc_")
    
    def test_format_pdf_date(self):
        """Test PDF date formatting."""
        processor = PDFProcessor()
        
        # Test various PDF date formats
        test_cases = [
            ("D:20240115123000+00'00'", "2024-01-15T12:30:00"),
            ("D:20240115", "2024-01-15T00:00:00"),
            ("D:20240115120000", "2024-01-15T12:00:00"),
            (None, None),
            ("invalid", None)
        ]
        
        for input_date, expected in test_cases:
            result = processor._format_pdf_date(input_date)
            if expected:
                assert expected in result
            else:
                assert result is None
    
    def test_coordinate_transformation(self, sample_bounding_box):
        """Test coordinate transformation for web display."""
        processor = PDFProcessor()
        
        # Test with scale factor
        scale_factor = 1.5
        transformed = processor.transform_coordinates_for_web(
            sample_bounding_box, scale_factor
        )
        
        assert transformed.x0 == sample_bounding_box.x0 * scale_factor
        assert transformed.x1 == sample_bounding_box.x1 * scale_factor
        assert transformed.page_height == sample_bounding_box.page_height * scale_factor
        assert transformed.page_number == sample_bounding_box.page_number
    
    @pytest.mark.asyncio
    async def test_extract_page_with_no_words(self):
        """Test handling of pages with no extractable words."""
        processor = PDFProcessor()
        
        mock_page = Mock()
        mock_page.extract_words.return_value = []  # No words found
        mock_page.extract_text.return_value = "Some text without word coordinates"
        mock_page.height = 792
        mock_page.width = 612
        
        fragments = await processor._extract_page_with_coordinates(mock_page, 0)
        
        assert len(fragments) == 1  # Should create fallback fragment
        assert fragments[0].text == "Some text without word coordinates"
        assert fragments[0].coordinates.page_number == 0
    
    @pytest.mark.asyncio
    async def test_extract_page_completely_empty(self):
        """Test handling of completely empty pages."""
        processor = PDFProcessor()
        
        mock_page = Mock()
        mock_page.extract_words.return_value = []
        mock_page.extract_text.return_value = ""  # No text at all
        mock_page.height = 792
        mock_page.width = 612
        
        fragments = await processor._extract_page_with_coordinates(mock_page, 0)
        
        assert len(fragments) == 0  # No fragments for empty page
    
    def test_create_temp_clauses_from_fragments(self, sample_bounding_box):
        """Test creating temporary clauses from text fragments."""
        processor = PDFProcessor()
        
        from app.models import TextFragment
        
        fragments = [
            TextFragment(
                text="First line of text",
                coordinates=BoundingBox(
                    x0=50, x1=300, top=100, bottom=120,
                    page_number=0, page_height=792
                )
            ),
            TextFragment(
                text="Second line of text", 
                coordinates=BoundingBox(
                    x0=50, x1=350, top=130, bottom=150,
                    page_number=0, page_height=792
                )
            ),
            TextFragment(
                text="Text on second page",
                coordinates=BoundingBox(
                    x0=50, x1=250, top=100, bottom=120,
                    page_number=1, page_height=792
                )
            )
        ]
        
        clauses = processor._create_temp_clauses_from_fragments(fragments)
        
        assert len(clauses) == 2  # Two pages
        assert clauses[0].coordinates.page_number == 0
        assert clauses[1].coordinates.page_number == 1
        assert "First line" in clauses[0].text
        assert "Text on second" in clauses[1].text


@pytest.mark.integration
class TestPDFProcessorIntegration:
    """Integration tests for PDF processor."""
    
    @pytest.mark.asyncio
    async def test_real_pdf_processing_workflow(self, sample_brazilian_contract_text):
        """Test the complete PDF processing workflow."""
        processor = PDFProcessor()
        
        # Create a more realistic PDF content for testing
        from .conftest import create_test_pdf_content
        pdf_content = create_test_pdf_content(sample_brazilian_contract_text)
        
        with patch('app.services.pdf_processor.pdfplumber') as mock_pdfplumber:
            # Mock realistic pdfplumber response
            mock_pdf = Mock()
            mock_page = Mock()
            
            # Simulate extracting words from the contract text
            words = []
            x_pos = 50
            y_pos = 700
            for word in sample_brazilian_contract_text.split()[:20]:  # First 20 words
                words.append({
                    'text': word,
                    'x0': x_pos, 'x1': x_pos + len(word) * 8,
                    'top': y_pos, 'bottom': y_pos + 20,
                    'size': 12, 'fontname': 'Arial'
                })
                x_pos += len(word) * 8 + 5
                if x_pos > 500:  # Wrap to next line
                    x_pos = 50
                    y_pos -= 25
            
            mock_page.extract_words.return_value = words
            mock_page.height = 792
            mock_page.width = 612
            mock_pdf.pages = [mock_page]
            mock_pdf.metadata = {
                'Title': 'Contrato SAFE',
                'Author': 'Sistema Jurídico',
                'CreationDate': 'D:20240115120000+00\'00\''
            }
            mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
            
            result = await processor.extract_text_with_coordinates(
                pdf_content, "contrato_safe.pdf"
            )
            
            # Validate complete result
            assert isinstance(result, PDFExtractionResult)
            assert result.document_id.startswith("doc_")
            assert result.metadata.filename == "contrato_safe.pdf"
            assert result.metadata.title == "Contrato SAFE"
            assert result.extraction_method == "pdfplumber"
            assert result.extraction_time > 0
            assert len(result.clauses) > 0
            assert len(result.full_text) > 0
            
            # Check that coordinates are properly set
            for clause in result.clauses:
                assert clause.coordinates.page_height == 792
                assert clause.coordinates.x0 >= 0
                assert clause.coordinates.page_number >= 0