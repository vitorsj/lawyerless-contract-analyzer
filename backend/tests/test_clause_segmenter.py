"""
Tests for clause segmentation service.

This module tests clause boundary detection, Brazilian legal document
patterns, and clause ID generation for contract synchronization.
"""

import pytest
from unittest.mock import Mock

from app.services.clause_segmenter import ClauseSegmenter, ClauseMatch
from app.models import PDFExtractionResult, ProcessedClause


@pytest.mark.unit
class TestClauseSegmenter:
    """Test clause segmentation functionality."""
    
    def test_segmenter_initialization(self):
        """Test ClauseSegmenter initialization."""
        segmenter = ClauseSegmenter()
        assert segmenter.numbered_pattern is not None
        assert segmenter.clausula_pattern is not None
        assert segmenter.secao_pattern is not None
        assert len(segmenter.header_keywords) > 0
    
    def test_numbered_clause_detection(self):
        """Test detection of numbered clauses (1., 1.1., etc.)."""
        segmenter = ClauseSegmenter()
        
        test_text = """
1. OBJETO DO CONTRATO
O presente contrato tem por objeto...

1.1. Definição
Para efeitos deste contrato...

2. VALOR DO INVESTIMENTO  
O valor total do investimento é...

2.1. Forma de Pagamento
O pagamento será realizado...
"""
        
        matches = segmenter._detect_clause_boundaries(test_text)
        
        # Should detect numbered patterns
        numbered_matches = [m for m in matches if m.pattern_type == "numbered"]
        assert len(numbered_matches) >= 4
        
        # Check specific patterns
        objeto_matches = [m for m in matches if "OBJETO" in (m.title or "")]
        assert len(objeto_matches) > 0
        
        # Check hierarchy levels
        level_1_matches = [m for m in matches if m.level == 1]
        level_2_matches = [m for m in matches if m.level == 2]
        assert len(level_1_matches) >= 2  # 1., 2.
        assert len(level_2_matches) >= 2  # 1.1., 2.1.
    
    def test_clausula_pattern_detection(self):
        """Test detection of explicit CLÁUSULA patterns."""
        segmenter = ClauseSegmenter()
        
        test_text = """
CLÁUSULA 1ª - DO OBJETO
O objeto deste contrato é...

CLÁUSULA 2ª - DOS VALORES
O valor do investimento...

CLAUSULA 3 - PRAZO
O prazo de vigência...
"""
        
        matches = segmenter._detect_clause_boundaries(test_text)
        
        clausula_matches = [m for m in matches if m.pattern_type == "clausula"]
        assert len(clausula_matches) >= 3
        
        # Check confidence levels (should be high for explicit clauses)
        for match in clausula_matches:
            assert match.confidence >= 0.9
    
    def test_secao_pattern_detection(self):
        """Test detection of SEÇÃO patterns."""
        segmenter = ClauseSegmenter()
        
        test_text = """
SEÇÃO I - DISPOSIÇÕES GERAIS
As disposições gerais...

SEÇÃO II - DIREITOS E OBRIGAÇÕES
Os direitos das partes...

SECAO III - CONSIDERAÇÕES FINAIS
Para fins de...
"""
        
        matches = segmenter._detect_clause_boundaries(test_text)
        
        secao_matches = [m for m in matches if m.pattern_type == "secao"]
        assert len(secao_matches) >= 3
    
    def test_roman_numeral_detection(self):
        """Test detection of Roman numeral patterns."""
        segmenter = ClauseSegmenter()
        
        test_text = """
I - OBJETO DO CONTRATO
O presente instrumento...

II - PARTES CONTRATANTES
São partes neste contrato...

III - VALOR E FORMA DE PAGAMENTO
O valor total é...
"""
        
        matches = segmenter._detect_clause_boundaries(test_text)
        
        roman_matches = [m for m in matches if m.pattern_type == "roman"]
        assert len(roman_matches) >= 3
        
        # Check that section headers are properly identified
        objeto_match = next((m for m in roman_matches if "OBJETO" in (m.title or "")), None)
        assert objeto_match is not None
    
    def test_is_likely_section_header(self):
        """Test section header identification logic."""
        segmenter = ClauseSegmenter()
        
        # Should be identified as headers
        header_examples = [
            "OBJETO DO CONTRATO",
            "VALOR DO INVESTIMENTO", 
            "DIREITOS E OBRIGAÇÕES",
            "FORO E JURISDIÇÃO",
            "PRAZO DE VIGÊNCIA"
        ]
        
        for example in header_examples:
            assert segmenter._is_likely_section_header(example), f"'{example}' should be a header"
        
        # Should NOT be identified as headers
        non_header_examples = [
            "Este é um texto muito longo que não deveria ser considerado um cabeçalho de seção",
            "palavra", 
            "",
            "123"
        ]
        
        for example in non_header_examples:
            assert not segmenter._is_likely_section_header(example), f"'{example}' should NOT be a header"
    
    def test_overlapping_match_removal(self):
        """Test removal of overlapping matches with confidence priority."""
        segmenter = ClauseSegmenter()
        
        matches = [
            ClauseMatch(0, 10, "text1", "Title1", "1", 1, "numbered", 0.8),
            ClauseMatch(5, 15, "text2", "Title2", "1", 1, "clausula", 0.95),  # Higher confidence, overlaps
            ClauseMatch(20, 30, "text3", "Title3", "2", 1, "numbered", 0.9),
        ]
        
        filtered = segmenter._remove_overlapping_matches(matches)
        
        # Should keep the higher confidence match and the non-overlapping one
        assert len(filtered) == 2
        assert filtered[0].confidence == 0.95  # The clausula match
        assert filtered[1].start_pos == 20     # The non-overlapping match
    
    def test_generate_clause_id_consistency(self):
        """Test that clause IDs are generated consistently."""
        segmenter = ClauseSegmenter()
        
        text = "Esta é uma cláusula de teste"
        number = "1.1"
        pattern_type = "numbered"
        document_id = "doc_123"
        
        # Should generate same ID for same inputs
        id1 = segmenter._generate_clause_id(text, number, pattern_type, document_id)
        id2 = segmenter._generate_clause_id(text, number, pattern_type, document_id)
        assert id1 == id2
        
        # Should generate different IDs for different inputs
        id3 = segmenter._generate_clause_id("Different text", number, pattern_type, document_id)
        assert id1 != id3
        
        # IDs should have proper format
        assert id1.startswith("clause_")
        assert pattern_type in id1
        assert len(id1) > 20  # Should include hash
    
    def test_create_clause_title(self):
        """Test clause title creation."""
        segmenter = ClauseSegmenter()
        
        test_cases = [
            (ClauseMatch(0, 10, "text", "OBJETO DO CONTRATO", "1", 1, "clausula", 0.9), 
             "CLÁUSULA 1 - OBJETO DO CONTRATO"),
            (ClauseMatch(0, 10, "text", "DIREITOS", "2.1", 2, "numbered", 0.8),
             "ITEM 2.1 - DIREITOS"),
            (ClauseMatch(0, 10, "text", None, "I", 1, "roman", 0.7),
             "SEÇÃO I"),
            (ClauseMatch(0, 10, "text", "PAGAMENTO", None, 1, "secao", 0.85),
             "SEÇÃO - PAGAMENTO")
        ]
        
        for match, expected in test_cases:
            title = segmenter._create_clause_title(match)
            assert expected in title or title in expected  # Allow some flexibility
    
    @pytest.mark.asyncio
    async def test_segment_clauses_success(self, sample_pdf_extraction_result):
        """Test successful clause segmentation."""
        segmenter = ClauseSegmenter()
        
        # Use extraction result with Brazilian contract text
        result = await segmenter.segment_clauses(sample_pdf_extraction_result)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # All results should be ProcessedClause objects
        for clause in result:
            assert isinstance(clause, ProcessedClause)
            assert clause.clause_id is not None
            assert len(clause.text) > 0
            assert clause.coordinates is not None
    
    @pytest.mark.asyncio  
    async def test_segment_clauses_empty_text(self):
        """Test clause segmentation with empty text."""
        segmenter = ClauseSegmenter()
        
        # Create extraction result with no text
        empty_result = Mock()
        empty_result.full_text = ""
        empty_result.document_id = "empty_doc"
        
        result = await segmenter.segment_clauses(empty_result)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_segment_clauses_no_patterns_found(self):
        """Test clause segmentation when no patterns are detected."""
        segmenter = ClauseSegmenter()
        
        # Create extraction result with text but no clear clause patterns
        simple_result = Mock()
        simple_result.full_text = "Este é um documento simples sem padrões de cláusulas claros. Apenas texto corrido."
        simple_result.document_id = "simple_doc"
        simple_result.metadata = Mock()
        simple_result.metadata.page_count = 1
        
        result = await segmenter.segment_clauses(simple_result)
        
        # Should create single clause containing all text
        assert len(result) == 1
        assert result[0].title == "Documento Completo"
        assert result[0].clause_id == "single_clause_simple_doc"
    
    def test_estimate_clause_coordinates(self, sample_pdf_extraction_result):
        """Test clause coordinate estimation."""
        segmenter = ClauseSegmenter()
        
        full_text = sample_pdf_extraction_result.full_text
        start_pos = 100
        end_pos = 300
        
        coordinates = segmenter._estimate_clause_coordinates(
            start_pos, end_pos, full_text, sample_pdf_extraction_result
        )
        
        assert coordinates.x0 >= 0
        assert coordinates.x1 > coordinates.x0
        assert coordinates.top >= 0
        assert coordinates.bottom >= coordinates.top
        assert coordinates.page_number >= 0
        assert coordinates.page_height > 0


@pytest.mark.integration
class TestClauseSegmenterIntegration:
    """Integration tests for clause segmentation."""
    
    @pytest.mark.asyncio
    async def test_complete_brazilian_contract_segmentation(self):
        """Test segmentation of a complete Brazilian contract."""
        segmenter = ClauseSegmenter()
        
        # More comprehensive Brazilian contract text
        brazilian_contract = """
INSTRUMENTO PARTICULAR DE CONTRATO DE INVESTIMENTO SIMPLES PARA PARTICIPAÇÃO FUTURA

1. DAS PARTES
1.1. EMPRESA: Tech Startup Ltda., sociedade empresária limitada, inscrita no CNPJ sob o nº 12.345.678/0001-90.
1.2. INVESTIDOR: João Silva, brasileiro, solteiro, empresário, portador do CPF nº 123.456.789-00.

2. OBJETO DO CONTRATO
2.1. O presente instrumento tem por objeto o investimento de R$ 500.000,00 pelo INVESTIDOR na EMPRESA.
2.2. O investimento será realizado mediante transferência bancária.

CLÁUSULA 3ª - DA CONVERSÃO
3.1. O investimento será convertido em participação societária na próxima rodada qualificada.
3.2. Considera-se rodada qualificada a captação mínima de R$ 2.000.000,00.

SEÇÃO I - DOS DIREITOS DE INFORMAÇÃO
I. A EMPRESA fornecerá relatórios trimestrais ao INVESTIDOR.
II. Os relatórios deverão conter demonstrações financeiras básicas.

§ 1º. Em caso de atraso nos relatórios, será aplicada multa.
§ 2º. A multa será de 0,5% sobre o valor investido por dia de atraso.

4. DO FORO
4.1. Fica eleito o foro da Comarca de São Paulo/SP para dirimir questões oriundas deste contrato.
"""
        
        # Create mock extraction result
        extraction_result = Mock()
        extraction_result.full_text = brazilian_contract
        extraction_result.document_id = "brazilian_contract_test"
        extraction_result.metadata = Mock()
        extraction_result.metadata.page_count = 2
        
        result = await segmenter.segment_clauses(extraction_result)
        
        # Should detect multiple types of patterns
        assert len(result) >= 8  # Multiple clauses detected
        
        # Check that different pattern types are detected
        clause_titles = [clause.title for clause in result if clause.title]
        
        # Should have numbered patterns
        numbered_titles = [t for t in clause_titles if any(word in t for word in ["ITEM", "1.", "2.", "4."])]
        assert len(numbered_titles) > 0
        
        # Should have explicit clause patterns
        clausula_titles = [t for t in clause_titles if "CLÁUSULA" in t]
        assert len(clausula_titles) > 0
        
        # Should have section patterns  
        secao_titles = [t for t in clause_titles if "SEÇÃO" in t]
        assert len(secao_titles) > 0
        
        # All clauses should have proper IDs and coordinates
        for clause in result:
            assert clause.clause_id.startswith("clause_")
            assert clause.coordinates is not None
            assert clause.coordinates.page_height > 0
    
    @pytest.mark.asyncio
    async def test_complex_numbering_patterns(self):
        """Test handling of complex Brazilian legal numbering patterns."""
        segmenter = ClauseSegmenter()
        
        complex_text = """
1. PRIMEIRA SEÇÃO
1.1. Primeiro subitem
1.1.1. Primeiro sub-subitem
1.1.2. Segundo sub-subitem
1.2. Segundo subitem

2. SEGUNDA SEÇÃO  
2.1. Primeiro subitem da segunda seção
2.1.1. Detalhamento
2.2. Segundo subitem

CLÁUSULA TERCEIRA - DISPOSIÇÕES ESPECIAIS
a) Primeira alínea
b) Segunda alínea
c) Terceira alínea

§ 1º Primeiro parágrafo
§ 2º Segundo parágrafo

Art. 1º - ARTIGO PRIMEIRO
Parágrafo único. Disposição única.
"""
        
        extraction_result = Mock()
        extraction_result.full_text = complex_text
        extraction_result.document_id = "complex_numbering"
        extraction_result.metadata = Mock()
        extraction_result.metadata.page_count = 1
        
        result = await segmenter.segment_clauses(extraction_result)
        
        # Should detect different hierarchy levels
        levels = [clause.level for clause in result if hasattr(clause, 'level')]
        assert max(levels) >= 3  # Should have at least 3 levels (1., 1.1., 1.1.1.)
        
        # Should detect various pattern types
        pattern_types_found = set()
        for clause in result:
            if hasattr(clause, 'clause_number'):
                if clause.clause_number and '.' in clause.clause_number:
                    pattern_types_found.add('numbered')
                elif clause.clause_number in ['a', 'b', 'c']:
                    pattern_types_found.add('letter')
        
        assert 'numbered' in pattern_types_found
    
    def test_clause_text_boundaries(self):
        """Test that clause text boundaries are correctly identified."""
        segmenter = ClauseSegmenter()
        
        test_text = """
1. PRIMEIRA CLÁUSULA
Este é o texto da primeira cláusula.
Continua na segunda linha.

2. SEGUNDA CLÁUSULA  
Este é o texto da segunda cláusula.
Também tem múltiplas linhas.

3. TERCEIRA CLÁUSULA
Texto da terceira e última cláusula.
"""
        
        matches = segmenter._detect_clause_boundaries(test_text)
        
        # Sort matches by position
        matches.sort(key=lambda m: m.start_pos)
        
        # Should have 3 matches
        assert len(matches) >= 3
        
        # Check that boundaries don't overlap improperly
        for i in range(len(matches) - 1):
            assert matches[i].start_pos < matches[i + 1].start_pos
        
        # Text extraction should work correctly
        mock_extraction = Mock()
        mock_extraction.full_text = test_text
        mock_extraction.document_id = "boundary_test"
        mock_extraction.metadata = Mock()
        mock_extraction.metadata.page_count = 1
        
        # The _create_processed_clauses method would handle this
        # but we can test the boundary logic directly
        for i, match in enumerate(matches):
            start_pos = match.start_pos
            end_pos = matches[i + 1].start_pos if i + 1 < len(matches) else len(test_text)
            
            clause_text = test_text[start_pos:end_pos].strip()
            assert len(clause_text) > 0
            assert f"{i+1}." in clause_text or "CLÁUSULA" in clause_text.upper()