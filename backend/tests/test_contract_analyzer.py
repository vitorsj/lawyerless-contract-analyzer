"""
Tests for contract analyzer PydanticAI agent.

This module tests the contract analysis agent using TestModel
patterns for validation without requiring actual LLM API calls.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime

from pydantic_ai.models.test import TestModel

from app.agents.contract_analyzer import (
    ContractAnalyzer,
    contract_agent,
    summary_agent,
    AnalysisDependencies,
    analyze_contract_clauses,
    analyze_single_contract_clause
)
from app.models import (
    ClauseAnalysis,
    ContractAnalysisResponse,
    ProcessedClause,
    Bandeira,
    BoundingBox
)
from .conftest import assert_valid_clause_analysis


@pytest.mark.agent
class TestContractAnalyzerAgent:
    """Test the main contract analysis agent with TestModel."""
    
    def test_agent_initialization(self):
        """Test that the agent is properly initialized."""
        assert contract_agent is not None
        # Check that agent is configured properly
        assert hasattr(contract_agent, 'model')
        assert hasattr(contract_agent, 'system_prompt')
    
    @pytest.mark.asyncio
    async def test_agent_with_test_model(
        self, 
        test_model, 
        test_dependencies, 
        sample_processed_clauses
    ):
        """Test agent analysis with TestModel."""
        clause = sample_processed_clauses[0]
        
        with contract_agent.override(model=test_model):
            result = await contract_agent.run(
                f"Analise esta cláusula: {clause.text}",
                deps=test_dependencies
            )
            
            # TestModel should return a structured response wrapped in AgentRunResult
            assert result is not None
            # Access data from AgentRunResult
            output = result.data if hasattr(result, 'data') else result.output
            assert output is not None
    
    @pytest.mark.asyncio
    async def test_agent_with_custom_output(
        self, 
        test_model_with_custom_output, 
        test_dependencies
    ):
        """Test agent with custom TestModel output."""
        with contract_agent.override(model=test_model_with_custom_output):
            result = await contract_agent.run(
                "Teste com output customizado",
                deps=test_dependencies
            )
            
            # Extract data from AgentRunResult
            analysis = result.data if hasattr(result, 'data') else result.output
            assert analysis.clause_id == "test_clause_001"
            assert analysis.titulo == "TESTE"
            assert analysis.bandeira == Bandeira.VERDE
            assert len(analysis.perguntas_negociacao) == 2
            assert analysis.clausula_numero == "1.1"
    
    @pytest.mark.asyncio
    async def test_agent_with_function_model_success(
        self, 
        function_model_success, 
        test_dependencies
    ):
        """Test agent with TestModel for custom behavior."""
        with contract_agent.override(model=function_model_success):
            result = await contract_agent.run(
                "Teste função personalizada",
                deps=test_dependencies
            )
            
            analysis = result
            assert analysis.clause_id == "function_test_001"
            assert analysis.titulo == "FUNÇÃO TESTE"
            assert analysis.bandeira == Bandeira.VERDE
            assert "função" in analysis.explicacao_simples.lower()
    
    @pytest.mark.asyncio
    async def test_agent_with_function_model_error_handling(
        self, 
        function_model_error, 
        test_dependencies
    ):
        """Test agent error handling with TestModel."""
        with contract_agent.override(model=function_model_error):
            # Test normal case
            result = await contract_agent.run(
                "Teste normal",
                deps=test_dependencies
            )
            
            analysis = result
            assert analysis.titulo == "ERRO SIMULADO"
            assert analysis.bandeira == Bandeira.AMARELO
    
    @pytest.mark.asyncio
    async def test_agent_tools_availability(
        self, 
        test_model, 
        test_dependencies
    ):
        """Test that agent tools are properly registered."""
        with contract_agent.override(model=test_model):
            # The TestModel should have access to tools
            result = await contract_agent.run(
                "Use tools to analyze: tag along rights",
                deps=test_dependencies
            )
            
            # Should complete without errors
            assert result is not None


@pytest.mark.agent
class TestContractAnalyzerClass:
    """Test the ContractAnalyzer class functionality."""
    
    def test_analyzer_initialization(self):
        """Test ContractAnalyzer initialization."""
        analyzer = ContractAnalyzer()
        assert analyzer.chunk_size > 0
        assert analyzer.max_retries > 0
        assert analyzer.timeout > 0
    
    @pytest.mark.asyncio
    async def test_analyze_single_clause_success(
        self, 
        test_model_with_custom_output,
        sample_processed_clauses,
        test_dependencies
    ):
        """Test single clause analysis."""
        analyzer = ContractAnalyzer()
        clause = sample_processed_clauses[0]
        
        with patch('app.agents.contract_analyzer.contract_agent') as mock_agent:
            # Mock the agent run result
            mock_result = ClauseAnalysis(
                clause_id=clause.clause_id,
                titulo=clause.title,
                texto_original=clause.text,
                tldr="Teste TL;DR",
                explicacao_simples="Explicação de teste",
                porque_importa="Importância de teste",
                bandeira=Bandeira.VERDE,
                motivo_bandeira="Teste aprovado",
                perguntas_negociacao=["Pergunta teste?"],
                coordenadas=clause.coordinates,
                clausula_numero=clause.clause_number
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            
            result = await analyzer.analyze_single_clause(clause, test_dependencies)
            
            assert_valid_clause_analysis(result)
            assert result.clause_id == clause.clause_id
            assert result.coordenadas == clause.coordinates
    
    @pytest.mark.asyncio 
    async def test_analyze_single_clause_fallback(
        self,
        sample_processed_clauses,
        test_dependencies
    ):
        """Test single clause analysis fallback on error."""
        analyzer = ContractAnalyzer()
        clause = sample_processed_clauses[0]
        
        with patch('app.agents.contract_analyzer.contract_agent') as mock_agent:
            # Mock agent to raise exception
            mock_agent.run = AsyncMock(side_effect=Exception("LLM Error"))
            
            result = await analyzer.analyze_single_clause(clause, test_dependencies)
            
            # Should return fallback analysis
            assert result.clause_id == clause.clause_id
            assert result.bandeira == Bandeira.AMARELO
            assert "análise automática indisponível" in result.motivo_bandeira.lower()
            assert len(result.perguntas_negociacao) > 0
    
    @pytest.mark.asyncio
    async def test_full_contract_analysis(
        self,
        sample_pdf_extraction_result,
        sample_processed_clauses,
        sample_contract_summary,
        test_model
    ):
        """Test full contract analysis workflow."""
        analyzer = ContractAnalyzer()
        
        with patch('app.agents.contract_analyzer.contract_agent') as mock_agent:
            # Mock successful clause analyses
            mock_analyses = []
            for i, clause in enumerate(sample_processed_clauses):
                mock_result = ClauseAnalysis(
                    clause_id=clause.clause_id,
                    titulo=clause.title,
                    texto_original=clause.text,
                    tldr=f"TL;DR para cláusula {i+1}",
                    explicacao_simples=f"Explicação da cláusula {i+1}",
                    porque_importa=f"Importância da cláusula {i+1}",
                    bandeira=Bandeira.VERDE if i % 2 == 0 else Bandeira.AMARELO,
                    motivo_bandeira=f"Motivo da bandeira {i+1}",
                    perguntas_negociacao=[f"Pergunta {i+1}?"],
                    coordenadas=clause.coordinates,
                    clausula_numero=clause.clause_number
                )
                mock_analyses.append(mock_result)
            
            mock_agent.run = AsyncMock(side_effect=mock_analyses)
            
            result = await analyzer.analyze_full_contract(
                sample_pdf_extraction_result,
                sample_processed_clauses,
                sample_contract_summary,
                "fundador"
            )
            
            assert isinstance(result, ContractAnalysisResponse)
            assert result.document_id == sample_pdf_extraction_result.document_id
            assert len(result.clauses) == len(sample_processed_clauses)
            assert result.total_clauses == len(sample_processed_clauses)
            assert result.processing_time > 0
            assert result.confidence_score is not None
            assert "verde" in result.risk_summary
            assert "amarelo" in result.risk_summary
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        analyzer = ContractAnalyzer()
        
        # Test with successful analyses
        good_clauses = [
            ClauseAnalysis(
                clause_id="test_1",
                titulo="Teste",
                texto_original="Texto",
                tldr="TL;DR",
                explicacao_simples="Explicação detalhada com mais de 100 caracteres para testar o cálculo de qualidade",
                porque_importa="Importância",
                bandeira=Bandeira.VERDE,
                motivo_bandeira="Sucesso",
                perguntas_negociacao=["P1?", "P2?", "P3?"],
                coordenadas=BoundingBox(x0=0, x1=100, top=0, bottom=50, page_number=1, page_height=800),
                clausula_numero="1"
            )
        ]
        
        confidence = analyzer._calculate_confidence_score(good_clauses)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be high for good analyses
        
        # Test with fallback analyses
        fallback_clauses = [
            ClauseAnalysis(
                clause_id="test_2",
                titulo="Teste",
                texto_original="Texto",
                tldr="TL;DR",
                explicacao_simples="Curta",
                porque_importa="Importância",
                bandeira=Bandeira.AMARELO,
                motivo_bandeira="Análise automática indisponível - requer revisão manual",
                perguntas_negociacao=["P1?"],
                coordenadas=BoundingBox(x0=0, x1=100, top=0, bottom=50, page_number=1, page_height=800),
                clausula_numero="2"
            )
        ]
        
        confidence_fallback = analyzer._calculate_confidence_score(fallback_clauses)
        assert confidence_fallback < confidence  # Should be lower for fallbacks
    
    def test_calculate_risk_summary(self):
        """Test risk summary calculation."""
        analyzer = ContractAnalyzer()
        
        clauses = [
            Mock(bandeira=Bandeira.VERDE),
            Mock(bandeira=Bandeira.VERDE),
            Mock(bandeira=Bandeira.AMARELO),
            Mock(bandeira=Bandeira.VERMELHO)
        ]
        
        risk_summary = analyzer._calculate_risk_summary(clauses)
        
        assert risk_summary["verde"] == 2
        assert risk_summary["amarelo"] == 1
        assert risk_summary["vermelho"] == 1


@pytest.mark.agent 
@pytest.mark.integration
class TestConvenienceFunctions:
    """Test convenience functions for external use."""
    
    @pytest.mark.asyncio
    async def test_analyze_contract_clauses_function(
        self,
        sample_pdf_extraction_result,
        sample_processed_clauses,
        sample_contract_summary,
        test_model
    ):
        """Test the convenience function for contract analysis."""
        with patch('app.agents.contract_analyzer.ContractAnalyzer') as MockAnalyzer:
            # Mock the analyzer
            mock_analyzer_instance = Mock()
            mock_response = ContractAnalysisResponse(
                document_id="test_doc",
                filename="test.pdf",
                contract_summary=sample_contract_summary,
                clauses=[],
                total_pages=1,
                total_clauses=0,
                processing_time=1.0,
                llm_provider="test",
                llm_model="test-model"
            )
            mock_analyzer_instance.analyze_full_contract = AsyncMock(return_value=mock_response)
            MockAnalyzer.return_value = mock_analyzer_instance
            
            result = await analyze_contract_clauses(
                sample_pdf_extraction_result,
                sample_processed_clauses,
                sample_contract_summary,
                "fundador"
            )
            
            assert isinstance(result, ContractAnalysisResponse)
            MockAnalyzer.assert_called_once()
            mock_analyzer_instance.analyze_full_contract.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_single_contract_clause_function(
        self,
        sample_processed_clauses,
        test_model
    ):
        """Test the convenience function for single clause analysis."""
        clause = sample_processed_clauses[0]
        
        with patch('app.agents.contract_analyzer.ContractAnalyzer') as MockAnalyzer:
            # Mock the analyzer
            mock_analyzer_instance = Mock()
            mock_analysis = ClauseAnalysis(
                clause_id=clause.clause_id,
                titulo=clause.title,
                texto_original=clause.text,
                tldr="Test TL;DR",
                explicacao_simples="Test explanation",
                porque_importa="Test importance",
                bandeira=Bandeira.VERDE,
                motivo_bandeira="Test reason",
                perguntas_negociacao=["Test question?"],
                coordenadas=clause.coordinates,
                clausula_numero=clause.clause_number
            )
            mock_analyzer_instance.analyze_single_clause = AsyncMock(return_value=mock_analysis)
            MockAnalyzer.return_value = mock_analyzer_instance
            
            result = await analyze_single_contract_clause(
                clause,
                "test_doc_123",
                "fundador"
            )
            
            assert isinstance(result, ClauseAnalysis)
            assert result.clause_id == clause.clause_id
            MockAnalyzer.assert_called_once()


@pytest.mark.agent
class TestAgentErrorHandling:
    """Test error handling in agent operations."""
    
    @pytest.mark.asyncio
    async def test_agent_timeout_handling(
        self,
        test_dependencies,
        sample_processed_clauses
    ):
        """Test agent timeout handling."""
        analyzer = ContractAnalyzer()
        clause = sample_processed_clauses[0]
        
        with patch('app.agents.contract_analyzer.contract_agent') as mock_agent:
            # Mock timeout
            mock_agent.run = AsyncMock(side_effect=asyncio.TimeoutError("Request timed out"))
            
            # Should return fallback analysis instead of raising
            result = await analyzer.analyze_single_clause(clause, test_dependencies)
            
            assert result.bandeira == Bandeira.AMARELO
            assert "indisponível" in result.motivo_bandeira.lower()
    
    @pytest.mark.asyncio
    async def test_retry_logic(
        self,
        sample_processed_clauses,
        test_dependencies
    ):
        """Test retry logic for failed requests."""
        analyzer = ContractAnalyzer()
        clause = sample_processed_clauses[0]
        
        # Test the retry wrapper directly
        call_count = 0
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            return Mock(data=Mock())
        
        # Should retry and eventually succeed
        result = await analyzer._run_with_retry(failing_func, max_retries=3)
        assert call_count == 3
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_batch_processing_with_failures(
        self,
        sample_processed_clauses,
        test_dependencies
    ):
        """Test batch processing handles individual failures."""
        analyzer = ContractAnalyzer()
        
        with patch.object(analyzer, 'analyze_single_clause') as mock_analyze:
            # Mix of successful and failed analyses
            successful_analysis = Mock()
            mock_analyze.side_effect = [
                successful_analysis,  # First succeeds
                Exception("Second fails"),  # Second fails
                successful_analysis,  # Third succeeds
            ]
            
            results = await analyzer._analyze_clauses_batch(
                sample_processed_clauses, 
                test_dependencies,
                batch_size=2
            )
            
            # Should have results for all clauses (including fallback for failed one)
            assert len(results) == len(sample_processed_clauses)
            assert mock_analyze.call_count == len(sample_processed_clauses)