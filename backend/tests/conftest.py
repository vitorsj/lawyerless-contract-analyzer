"""
Pytest configuration and fixtures for Lawyerless backend tests.

This module provides test fixtures, mock data, and configuration
for testing PDF processing, contract analysis, and PydanticAI agents.
"""

import pytest
import asyncio
from io import BytesIO
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
import tempfile
import os

from pydantic_ai.models.test import TestModel

from app.models import (
    PDFExtractionResult,
    PDFMetadata,
    ProcessedClause,
    BoundingBox,
    ContractSummary,
    PartesContrato,
    DatasContrato,
    ValoresContrato,
    ConversaoTermos,
    DireitosInvestidor,
    ObrigacoesContrato,
    JurisdicaoContrato,
    Empresa,
    Parte,
    Valor,
    TipoInstrumento,
    TipoSocietario,
    TipoPessoa,
    Moeda,
    ClauseAnalysis,
    Bandeira
)
from app.agents.contract_analyzer import AnalysisDependencies


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Generate sample PDF content for testing."""
    # This is a minimal PDF content for testing
    # In a real scenario, you'd have actual PDF files
    pdf_header = b"%PDF-1.4\n"
    pdf_body = b"""1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
50 750 Td
(CONTRATO DE INVESTIMENTO) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
285
%%EOF"""
    
    return pdf_header + pdf_body


@pytest.fixture
def sample_brazilian_contract_text() -> str:
    """Sample Brazilian contract text for testing."""
    return """
INSTRUMENTO PARTICULAR DE CONTRATO DE INVESTIMENTO SIMPLES PARA PARTICIPAÇÃO FUTURA (SAFE)

1. PARTES
1.1. EMPRESA: Tech Startup Ltda., sociedade empresária limitada, inscrita no CNPJ sob o nº 12.345.678/0001-90.
1.2. INVESTIDOR: João Silva, brasileiro, solteiro, empresário, portador do CPF nº 123.456.789-00.

2. OBJETO DO CONTRATO
2.1. O presente instrumento tem por objeto o investimento de R$ 500.000,00 (quinhentos mil reais) pelo INVESTIDOR na EMPRESA.

3. CONVERSÃO
3.1. O investimento será convertido em participação societária na próxima rodada qualificada.
3.2. Rodada qualificada é definida como captação mínima de R$ 2.000.000,00.
3.3. A conversão terá desconto de 20% sobre o preço da rodada ou valuation cap de R$ 10.000.000,00.

4. DIREITOS DE INFORMAÇÃO
4.1. A EMPRESA fornecerá relatórios financeiros trimestrais ao INVESTIDOR.

5. FORO
5.1. Fica eleito o foro da Comarca de São Paulo/SP para dirimir questões oriundas deste contrato.
"""


@pytest.fixture
def sample_pdf_metadata() -> PDFMetadata:
    """Sample PDF metadata for testing."""
    return PDFMetadata(
        filename="contrato_safe_exemplo.pdf",
        file_size=1024,
        page_count=2,
        creation_date="2024-01-15T10:30:00",
        title="Contrato SAFE",
        author="Escritório Jurídico"
    )


@pytest.fixture
def sample_bounding_box() -> BoundingBox:
    """Sample bounding box for testing."""
    return BoundingBox(
        x0=50.0,
        x1=550.0,
        top=100.0,
        bottom=150.0,
        page_number=0,
        page_height=792.0
    )


@pytest.fixture
def sample_processed_clauses(sample_bounding_box) -> List[ProcessedClause]:
    """Sample processed clauses for testing."""
    return [
        ProcessedClause(
            clause_id="clause_partes_001",
            text="EMPRESA: Tech Startup Ltda., sociedade empresária limitada, inscrita no CNPJ sob o nº 12.345.678/0001-90.",
            coordinates=sample_bounding_box,
            title="PARTES",
            level=1,
            clause_number="1.1"
        ),
        ProcessedClause(
            clause_id="clause_objeto_001", 
            text="O presente instrumento tem por objeto o investimento de R$ 500.000,00 (quinhentos mil reais) pelo INVESTIDOR na EMPRESA.",
            coordinates=sample_bounding_box,
            title="OBJETO DO CONTRATO",
            level=1,
            clause_number="2.1"
        ),
        ProcessedClause(
            clause_id="clause_conversao_001",
            text="O investimento será convertido em participação societária na próxima rodada qualificada. Rodada qualificada é definida como captação mínima de R$ 2.000.000,00.",
            coordinates=sample_bounding_box,
            title="CONVERSÃO",
            level=1,
            clause_number="3.1"
        )
    ]


@pytest.fixture
def sample_pdf_extraction_result(sample_pdf_metadata, sample_processed_clauses, sample_brazilian_contract_text) -> PDFExtractionResult:
    """Sample PDF extraction result for testing."""
    return PDFExtractionResult(
        document_id="doc_test_123456",
        metadata=sample_pdf_metadata,
        clauses=sample_processed_clauses,
        full_text=sample_brazilian_contract_text,
        extraction_time=1.5,
        extraction_method="pdfplumber",
        warnings=[]
    )


@pytest.fixture
def sample_contract_summary() -> ContractSummary:
    """Sample contract summary for testing."""
    return ContractSummary(
        tipo_instrumento=TipoInstrumento.SAFE,
        partes=PartesContrato(
            empresa=Empresa(
                nome="Tech Startup Ltda.",
                tipo=TipoPessoa.PESSOA_JURIDICA,
                tipo_societario=TipoSocietario.LTDA,
                cnpj="12.345.678/0001-90"
            ),
            investidores=[Parte(
                nome="João Silva",
                tipo=TipoPessoa.PESSOA_FISICA,
                documento="123.456.789-00"
            )]
        ),
        datas=DatasContrato(),
        valores=ValoresContrato(
            principal=Valor(moeda=Moeda.BRL, valor=500000.0),
            desconto_percentual=20.0,
            valuation_cap=10000000.0
        ),
        conversao=ConversaoTermos(),
        direitos=DireitosInvestidor(),
        obrigacoes=ObrigacoesContrato(),
        jurisdicao=JurisdicaoContrato(foro="São Paulo/SP")
    )


@pytest.fixture
def sample_clause_analysis(sample_bounding_box) -> ClauseAnalysis:
    """Sample clause analysis for testing."""
    return ClauseAnalysis(
        clause_id="clause_conversao_001",
        titulo="CONVERSÃO",
        texto_original="O investimento será convertido em participação societária na próxima rodada qualificada.",
        tldr="Investimento vira ações quando empresa fizer nova rodada de investimento.",
        explicacao_simples="Quando a empresa buscar mais investimento no futuro, seu dinheiro será convertido em ações da empresa.",
        porque_importa="Define como e quando você se tornará sócio da empresa, afetando sua participação futura.",
        bandeira=Bandeira.VERDE,
        motivo_bandeira="Conversão automática em rodada qualificada é padrão de mercado",
        perguntas_negociacao=[
            "Qual o valor mínimo para ser considerada rodada qualificada?",
            "Existe prazo limite para acontecer a conversão?",
            "O que acontece se não houver rodada qualificada?",
            "Posso converter antes da rodada qualificada?",
            "Como fica a anti-diluição se houver down round?"
        ],
        coordenadas=sample_bounding_box,
        clausula_numero="3.1"
    )


@pytest.fixture
def test_dependencies() -> AnalysisDependencies:
    """Sample analysis dependencies for testing."""
    return AnalysisDependencies(
        document_id="doc_test_123456",
        perspectiva="fundador",
        include_risk_analysis=True,
        include_negotiation_questions=True,
        session_id="test_session_001"
    )


@pytest.fixture
def mock_pdf_processor():
    """Mock PDF processor for testing."""
    processor = Mock()
    processor.extract_text_with_coordinates = AsyncMock()
    return processor


@pytest.fixture
def mock_clause_segmenter():
    """Mock clause segmenter for testing."""
    segmenter = Mock()
    segmenter.segment_clauses = AsyncMock()
    return segmenter


@pytest.fixture
def mock_contract_extractor():
    """Mock contract extractor for testing."""
    extractor = Mock()
    extractor.extract_contract_summary = AsyncMock()
    return extractor


@pytest.fixture
def test_model():
    """TestModel for PydanticAI agent testing."""
    return TestModel()


@pytest.fixture
def test_model_with_custom_output():
    """TestModel with custom JSON output for structured testing."""
    custom_output = """{
        "clause_id": "test_clause_001",
        "titulo": "TESTE",
        "texto_original": "Texto de teste para validação.",
        "tldr": "Resumo de teste.",
        "explicacao_simples": "Esta é uma explicação simples de teste.",
        "porque_importa": "Importa para validar o funcionamento do sistema.",
        "bandeira": "verde",
        "motivo_bandeira": "Teste passou com sucesso",
        "perguntas_negociacao": [
            "Pergunta de teste 1?",
            "Pergunta de teste 2?"
        ],
        "coordenadas": {
            "x0": 0,
            "x1": 100,
            "top": 0,
            "bottom": 50,
            "page_number": 0,
            "page_height": 792
        },
        "clausula_numero": "1.1"
    }"""
    return TestModel(custom_output_text=custom_output)


@pytest.fixture
def function_model_success():
    """TestModel that returns successful analysis."""
    def success_function(messages, tools):
        return """{
            "clause_id": "function_test_001",
            "titulo": "FUNÇÃO TESTE",
            "texto_original": "Texto processado por função de teste.",
            "tldr": "Função executou com sucesso.",
            "explicacao_simples": "A função de teste processou corretamente a cláusula.",
            "porque_importa": "Validação do comportamento customizado do agente.",
            "bandeira": "verde",
            "motivo_bandeira": "Função personalizada funcionou corretamente",
            "perguntas_negociacao": [
                "A função está funcionando como esperado?",
                "Os parâmetros estão corretos?"
            ],
            "coordenadas": {
                "x0": 0,
                "x1": 100,
                "top": 0,
                "bottom": 50,
                "page_number": 0,
                "page_height": 792
            },
            "clausula_numero": "test"
        }"""
    
    return TestModel(success_function)


@pytest.fixture
def function_model_error():
    """TestModel that simulates error conditions."""
    def error_function(messages, tools):
        # Simulate different error conditions based on input
        last_message = messages[-1].content if messages else ""
        
        if "invalid" in last_message.lower():
            return '{"error": "Invalid input provided"}'
        elif "timeout" in last_message.lower():
            raise TimeoutError("Simulated timeout")
        else:
            return """{
                "clause_id": "error_test_001",
                "titulo": "ERRO SIMULADO",
                "texto_original": "Texto que causou erro.",
                "tldr": "Simulação de erro detectada.",
                "explicacao_simples": "Esta é uma simulação de como o sistema lida com erros.",
                "porque_importa": "Testa a robustez do sistema de análise.",
                "bandeira": "amarelo",
                "motivo_bandeira": "Erro simulado detectado e tratado",
                "perguntas_negociacao": [
                    "Como o sistema lida com erros?",
                    "Existe fallback adequado?"
                ],
                "coordenadas": {
                    "x0": 0,
                    "x1": 100,
                    "top": 0,
                    "bottom": 50,
                    "page_number": 0,
                    "page_height": 792
                },
                "clausula_numero": "error"
            }"""
    
    return TestModel(error_function)


@pytest.fixture
def sample_upload_file():
    """Mock UploadFile for FastAPI testing."""
    mock_file = Mock()
    mock_file.filename = "contrato_teste.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.read = AsyncMock(return_value=b"sample pdf content")
    return mock_file


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment with proper configuration."""
    # Set test environment variables
    monkeypatch.setenv("LLM_API_KEY", "test_key_123")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "agent: mark test as PydanticAI agent test"
    )


# Helper functions for tests
def assert_valid_clause_analysis(analysis: ClauseAnalysis):
    """Assert that a ClauseAnalysis object is valid."""
    assert analysis.clause_id is not None
    assert len(analysis.tldr) > 0
    assert len(analysis.explicacao_simples) > 10
    assert analysis.bandeira in [Bandeira.VERDE, Bandeira.AMARELO, Bandeira.VERMELHO]
    assert len(analysis.perguntas_negociacao) > 0
    assert analysis.coordenadas is not None


def create_test_pdf_content(contract_text: str) -> bytes:
    """Create test PDF content with given text."""
    # Simple PDF generation for testing
    # In production, you'd use a proper PDF library
    pdf_template = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length {len(contract_text.encode())}
>>
stream
BT
/F1 12 Tf
50 750 Td
({contract_text}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
{285 + len(contract_text.encode())}
%%EOF"""

    return pdf_template.encode()