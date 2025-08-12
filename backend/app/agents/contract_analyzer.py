"""
Brazilian Contract Analyzer using PydanticAI.

This module implements the main PydanticAI agent for analyzing Brazilian
investment contracts with structured output, Portuguese explanations,
and risk flagging.
"""

import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from pydantic_ai import Agent, RunContext
try:
    from langsmith import traceable as ls_traceable  # type: ignore
except Exception:  # LangSmith opcional
    def ls_traceable(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func
        return decorator

from ..models import (
    ClauseAnalysis,
    ContractAnalysisResponse,
    ContractSummary,
    ProcessedClause,
    Bandeira,
    PDFExtractionResult
)
from ..settings import settings
from ..services.llm_providers import get_llm_model
from ..services.langsmith_integration import tracer, log_analysis_metrics
from .prompts import SYSTEM_PROMPT, CONTRACT_SUMMARY_PROMPT, CLAUSE_ANALYSIS_EXAMPLES
from .tools import (
    define_legal_term,
    analyze_clause_risk_factors,
    compare_with_market_standards,
    generate_negotiation_questions,
    identify_clause_category,
    extract_numeric_values
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisDependencies:
    """Dependencies for contract analysis agent."""
    document_id: str
    perspectiva: str = "fundador"  # "fundador" or "investidor"
    include_risk_analysis: bool = True
    include_negotiation_questions: bool = True
    session_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    llm_provider: Optional[str] = None  # Provider override for this analysis


class ContractAnalysisError(Exception):
    """Custom exception for contract analysis errors."""
    pass


def get_contract_llm_model(provider_name: Optional[str] = None):
    """Get configured LLM model from settings with provider selection."""
    try:
        return get_llm_model(provider_name)
    except Exception as e:
        logger.error(f"Failed to initialize LLM model: {e}")
        raise ContractAnalysisError(f"LLM initialization failed: {e}") from e


# Create the main contract analysis agent with structured output
contract_agent = Agent(
    get_contract_llm_model(),
    deps_type=AnalysisDependencies,
    output_type=ClauseAnalysis,  # Ensure structured output
    system_prompt=SYSTEM_PROMPT + "\n\n" + CLAUSE_ANALYSIS_EXAMPLES
)

# Create a separate agent for contract summary extraction with structured output
summary_agent = Agent(
    get_contract_llm_model(),
    deps_type=AnalysisDependencies,
    output_type=ContractSummary,  # Ensure structured output
    system_prompt=CONTRACT_SUMMARY_PROMPT
)


# Register tools with the contract analysis agent
@contract_agent.tool
def get_legal_term_definition(
    ctx: RunContext[AnalysisDependencies], 
    term: str
) -> str:
    """
    Get definition of a legal term.
    
    Args:
        term: Legal term to define (e.g., "tag along", "anti-diluição")
    
    Returns:
        Definition in Portuguese
    """
    return define_legal_term(ctx, term)


@contract_agent.tool
def analyze_risk_patterns(
    ctx: RunContext[AnalysisDependencies],
    clause_text: str,
    clause_type: str = ""
) -> Dict[str, Any]:
    """
    Analyze risk patterns in clause text.
    
    Args:
        clause_text: Text of the clause
        clause_type: Type of clause for context
    
    Returns:
        Risk analysis with identified patterns
    """
    return analyze_clause_risk_factors(ctx, clause_text, clause_type)


@contract_agent.tool  
def compare_to_market(
    ctx: RunContext[AnalysisDependencies],
    term_type: str,
    value: float
) -> Dict[str, Any]:
    """
    Compare contract term to market standards.
    
    Args:
        term_type: Type of term (e.g., "juros_mutuo", "desconto_conversao") 
        value: Numeric value to compare
    
    Returns:
        Market comparison analysis
    """
    return compare_with_market_standards(ctx, term_type, value)


@contract_agent.tool
def get_negotiation_questions(
    ctx: RunContext[AnalysisDependencies],
    category: str,
    context: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Generate negotiation questions for a clause category.
    
    Args:
        category: Clause category (e.g., "anti_diluicao", "drag_along")
        context: Additional context for customization
    
    Returns:
        List of negotiation questions in Portuguese
    """
    return generate_negotiation_questions(ctx, category, context)


@contract_agent.tool
def identify_clause_type(
    ctx: RunContext[AnalysisDependencies],
    clause_text: str,
    clause_title: str = ""
) -> str:
    """
    Identify the category/type of a clause.
    
    Args:
        clause_text: Text content of the clause
        clause_title: Title of the clause
    
    Returns:
        Category identifier
    """
    return identify_clause_category(ctx, clause_text, clause_title)


@contract_agent.tool
def extract_numbers(
    ctx: RunContext[AnalysisDependencies],
    text: str
) -> Dict[str, List[float]]:
    """
    Extract numeric values from text.
    
    Args:
        text: Text to analyze
    
    Returns:
        Dictionary of extracted values by type
    """
    return extract_numeric_values(ctx, text)


class ContractAnalyzer:
    """
    Main contract analyzer using PydanticAI for Brazilian legal documents.
    
    Handles clause-by-clause analysis, risk flagging, and structured
    output generation with Portuguese explanations.
    """
    
    def __init__(self, llm_provider: Optional[str] = None):
        """Initialize contract analyzer with optional provider override."""
        self.chunk_size = settings.pdf_chunk_size
        self.chunk_overlap = settings.pdf_chunk_overlap
        self.max_retries = settings.llm_max_retries
        self.timeout = settings.llm_timeout
        self.llm_provider = llm_provider  # Provider override
    
    async def analyze_full_contract(
        self,
        extraction_result: PDFExtractionResult,
        clauses: List[ProcessedClause],
        contract_summary: ContractSummary,
        perspectiva: str = "fundador"
    ) -> ContractAnalysisResponse:
        """
        Analyze complete contract with all clauses.
        
        Args:
            extraction_result: PDF extraction result
            clauses: List of processed clauses
            contract_summary: Contract summary
            perspectiva: Analysis perspective ("fundador" or "investidor")
        
        Returns:
            Complete contract analysis response
        """
        start_time = datetime.now()
        
        logger.info(f"Starting full contract analysis for {extraction_result.document_id}")
        logger.info(f"Analyzing {len(clauses)} clauses from perspective: {perspectiva}")
        
        # Initialize LangSmith tracing context (sets parent metadata)
        with tracer.trace_contract_analysis(
            document_id=extraction_result.document_id,
            filename=extraction_result.metadata.filename,
            perspectiva=perspectiva,
            llm_provider=self.llm_provider or settings.llm_provider,
            total_clauses=len(clauses),
            total_pages=extraction_result.metadata.page_count,
            file_size=extraction_result.metadata.file_size
        ):
            dependencies = AnalysisDependencies(
                document_id=extraction_result.document_id,
                perspectiva=perspectiva,
                include_risk_analysis=True,
                include_negotiation_questions=True,
                llm_provider=self.llm_provider
            )

            @ls_traceable(
                name="contract_analysis",
                metadata={
                    "document_id": extraction_result.document_id,
                    "filename": extraction_result.metadata.filename,
                    "perspectiva": perspectiva,
                    "llm_provider": self.llm_provider or settings.llm_provider,
                    "total_clauses": len(clauses),
                    "total_pages": extraction_result.metadata.page_count,
                },
                tags=["contract", "analysis", perspectiva, self.llm_provider or settings.llm_provider],
            )
            async def _run_contract_analysis_inner():
                try:
                    # Analyze clauses in batches to avoid overwhelming the LLM
                    analyzed_clauses = await self._analyze_clauses_batch(clauses, dependencies)

                    # Calculate processing time
                    processing_time = (datetime.now() - start_time).total_seconds()

                    # Generate risk summary
                    risk_summary = self._calculate_risk_summary(analyzed_clauses)

                    # Calculate confidence score based on analysis quality
                    confidence_score = self._calculate_confidence_score(analyzed_clauses)

                    # Log metrics to LangSmith
                    log_analysis_metrics(
                        document_id=extraction_result.document_id,
                        processing_time=processing_time,
                        clause_count=len(analyzed_clauses),
                        risk_summary=risk_summary,
                        confidence_score=confidence_score,
                    )

                    response = ContractAnalysisResponse(
                        document_id=extraction_result.document_id,
                        filename=extraction_result.metadata.filename,
                        contract_summary=contract_summary,
                        clauses=analyzed_clauses,
                        total_pages=extraction_result.metadata.page_count,
                        total_clauses=len(analyzed_clauses),
                        processing_time=processing_time,
                        llm_provider=self.llm_provider or settings.llm_provider,
                        llm_model=settings.get_current_model(),
                        confidence_score=confidence_score,
                        risk_summary=risk_summary,
                        created_at=datetime.now(),
                    )

                    logger.info(f"Contract analysis completed in {processing_time:.2f}s")
                    logger.info(f"Risk summary: {risk_summary}")

                    return response
                except Exception as e:
                    logger.error(f"Contract analysis failed: {str(e)}")
                    raise ContractAnalysisError(f"Analysis failed: {str(e)}") from e

            return await _run_contract_analysis_inner()
    
    async def analyze_single_clause(
        self,
        clause: ProcessedClause,
        dependencies: AnalysisDependencies,
        context: Optional[str] = None
    ) -> ClauseAnalysis:
        """
        Analyze a single clause with structured output.
        
        Args:
            clause: Clause to analyze
            dependencies: Analysis dependencies
            context: Additional context for analysis
        
        Returns:
            Structured clause analysis
        """
        logger.info(f"Analyzing clause: {clause.clause_id}")
        
        # Initialize LangSmith tracing for individual clause (parent context)
        with tracer.trace_clause_analysis(
            clause_id=clause.clause_id,
            clause_number=clause.clause_number,
            clause_level=clause.level or 1,
            clause_length=len(clause.text),
            pattern_type="numbered" if clause.clause_number else "paragraph",
        ):
            @ls_traceable(
                name="clause_analysis",
                metadata={
                    "clause_id": clause.clause_id,
                    "clause_number": clause.clause_number,
                    "clause_level": clause.level or 1,
                    "clause_length": len(clause.text),
                    "pattern_type": "numbered" if clause.clause_number else "paragraph",
                },
                tags=[
                    "clause",
                    "analysis",
                    "numbered" if clause.clause_number else "paragraph",
                    f"level_{clause.level or 1}",
                ],
            )
            async def _run_clause_analysis_inner():
                try:
                    # Prepare the prompt with clause information
                    clause_prompt = self._prepare_clause_prompt(clause, dependencies, context)

                    # Create agent with appropriate provider if specified
                    agent_to_use = contract_agent
                    if dependencies.llm_provider and dependencies.llm_provider != settings.llm_provider:
                        # Create temporary agent with different provider
                        agent_to_use = Agent(
                            get_contract_llm_model(dependencies.llm_provider),
                            deps_type=AnalysisDependencies,
                            output_type=ClauseAnalysis,
                            system_prompt=SYSTEM_PROMPT + "\n\n" + CLAUSE_ANALYSIS_EXAMPLES,
                        )
                        # Register tools with temporary agent
                        self._register_tools_with_agent(agent_to_use)

                    # Run analysis with retry logic, instrumented as a dedicated span
                    @ls_traceable(
                        name="llm_clause_run",
                        metadata={
                            "clause_id": clause.clause_id,
                            "clause_number": clause.clause_number,
                            "clause_level": clause.level or 1,
                            "clause_length": len(clause.text),
                        },
                        tags=[
                            "llm",
                            "clause",
                            "numbered" if clause.clause_number else "paragraph",
                            f"level_{clause.level or 1}",
                        ],
                    )
                    async def _traced_llm_run():
                        return await agent_to_use.run(clause_prompt, deps=dependencies)

                    result = await self._run_with_retry(_traced_llm_run)

                    # Extract analysis from result and ensure coordinates are preserved
                    if hasattr(result, "output"):
                        analysis = result.output
                    elif hasattr(result, "data"):
                        analysis = result.data
                    else:
                        # Fallback for direct result
                        analysis = result

                    # Ensure we have a ClauseAnalysis object
                    if not isinstance(analysis, ClauseAnalysis):
                        logger.error(
                            f"Expected ClauseAnalysis, got {type(analysis)}: {analysis}"
                        )
                        # Create fallback analysis
                        return self._create_fallback_analysis(
                            clause, f"Invalid result type: {type(analysis)}"
                        )

                    # Set coordinates and clause info
                    analysis.coordenadas = clause.coordinates
                    analysis.clause_id = clause.clause_id
                    analysis.clausula_numero = clause.clause_number

                    logger.info(
                        f"Clause analysis completed: {analysis.clause_id}, Flag: {analysis.bandeira}"
                    )
                    return analysis
                except Exception as e:
                    logger.error(f"Single clause analysis failed: {str(e)}")
                    # Return fallback analysis to avoid complete failure
                    return self._create_fallback_analysis(clause, str(e))

            return await _run_clause_analysis_inner()
    
    async def _analyze_clauses_batch(
        self,
        clauses: List[ProcessedClause],
        dependencies: AnalysisDependencies,
        batch_size: int = 5
    ) -> List[ClauseAnalysis]:
        """
        Analyze clauses in batches with proper error handling.
        
        Args:
            clauses: List of clauses to analyze
            dependencies: Analysis dependencies
            batch_size: Number of clauses per batch
        
        Returns:
            List of analyzed clauses
        """
        analyzed_clauses = []
        
        # Split clauses into batches
        batches = [clauses[i:i + batch_size] for i in range(0, len(clauses), batch_size)]
        
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i + 1}/{len(batches)} ({len(batch)} clauses)")
            
            # Process batch concurrently
            batch_tasks = [
                self.analyze_single_clause(clause, dependencies)
                for clause in batch
            ]
            
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Handle results and exceptions
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Batch {i + 1}, clause {j + 1} failed: {result}")
                        # Create fallback analysis
                        fallback = self._create_fallback_analysis(batch[j], str(result))
                        analyzed_clauses.append(fallback)
                    else:
                        analyzed_clauses.append(result)
                        
            except Exception as e:
                logger.error(f"Batch {i + 1} processing failed: {e}")
                # Create fallback analyses for the entire batch
                for clause in batch:
                    fallback = self._create_fallback_analysis(clause, str(e))
                    analyzed_clauses.append(fallback)
        
        return analyzed_clauses
    
    def _register_tools_with_agent(self, agent):
        """Register tools with a dynamic agent."""
        # Register the same tools as the main contract_agent
        @agent.tool
        def get_legal_term_definition(ctx, term: str) -> str:
            return define_legal_term(ctx, term)
        
        @agent.tool
        def analyze_risk_patterns(ctx, clause_text: str, clause_type: str = "") -> Dict[str, Any]:
            return analyze_clause_risk_factors(ctx, clause_text, clause_type)
        
        @agent.tool  
        def compare_to_market(ctx, term_type: str, value: float) -> Dict[str, Any]:
            return compare_with_market_standards(ctx, term_type, value)
        
        @agent.tool
        def get_negotiation_questions(ctx, category: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
            return generate_negotiation_questions(ctx, category, context)
        
        @agent.tool
        def identify_clause_type(ctx, clause_text: str, clause_title: str = "") -> str:
            return identify_clause_category(ctx, clause_text, clause_title)
        
        @agent.tool
        def extract_numbers(ctx, text: str) -> Dict[str, List[float]]:
            return extract_numeric_values(ctx, text)
    
    def _prepare_clause_prompt(
        self,
        clause: ProcessedClause,
        dependencies: AnalysisDependencies,
        context: Optional[str] = None
    ) -> str:
        """
        Prepare the prompt for clause analysis.
        
        Args:
            clause: Clause to analyze
            dependencies: Analysis dependencies
            context: Additional context
        
        Returns:
            Formatted prompt for the LLM
        """
        prompt_parts = []
        
        # Add clause information
        prompt_parts.append("## Cláusula para Análise:")
        if clause.title:
            prompt_parts.append(f"**Título:** {clause.title}")
        if clause.clause_number:
            prompt_parts.append(f"**Número:** {clause.clause_number}")
        
        prompt_parts.append("**Texto da Cláusula:**")
        prompt_parts.append(clause.text)
        
        # Add perspective
        prompt_parts.append(f"\n**Perspectiva de Análise:** {dependencies.perspectiva}")
        
        # Add context if provided
        if context:
            prompt_parts.append(f"\n**Contexto Adicional:** {context}")
        
        # Add specific instructions
        prompt_parts.append("""
## Instruções Específicas:
1. Analise esta cláusula considerando a legislação brasileira
2. Use linguagem clara para leigos adultos
3. Atribua bandeira de risco apropriada (verde/amarelo/vermelho)
4. Forneça até 5 perguntas estratégicas para negociação
5. Se aplicável, diferencie explicação geral vs. como está no contrato

Responda seguindo exatamente a estrutura JSON esperada.""")
        
        return "\n".join(prompt_parts)
    
    async def _run_with_retry(self, func, max_retries: Optional[int] = None):
        """Run function with retry logic."""
        max_retries = max_retries or self.max_retries
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                result = await asyncio.wait_for(func(), timeout=self.timeout)
                return result
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} timed out after {self.timeout}s")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        raise ContractAnalysisError(f"Failed after {max_retries} attempts") from last_exception
    
    def _create_fallback_analysis(self, clause: ProcessedClause, error: str) -> ClauseAnalysis:
        """Create fallback analysis when LLM analysis fails."""
        return ClauseAnalysis(
            clause_id=clause.clause_id,
            titulo=clause.title or "Cláusula",
            texto_original=clause.text[:200] + "..." if len(clause.text) > 200 else clause.text,
            tldr="Análise não disponível devido a erro técnico.",
            explicacao_simples="Esta cláusula requer revisão manual devido a falha na análise automática.",
            porque_importa="Recomendamos consultar assessoria jurídica para análise detalhada desta cláusula.",
            bandeira=Bandeira.AMARELO,
            motivo_bandeira="Análise automática indisponível - requer revisão manual",
            perguntas_negociacao=[
                "Esta cláusula pode ser simplificada?",
                "Quais são os principais riscos desta disposição?",
                "Como isso se compara com padrões de mercado?",
                "Existem alternativas menos restritivas?",
                "Preciso de assessoria jurídica para esta cláusula?"
            ],
            coordenadas=clause.coordinates,
            clausula_numero=clause.clause_number
        )
    
    def _calculate_risk_summary(self, clauses: List[ClauseAnalysis]) -> Dict[str, int]:
        """Calculate risk flag summary."""
        risk_counts = {"verde": 0, "amarelo": 0, "vermelho": 0}
        
        for clause in clauses:
            risk_counts[clause.bandeira.value] += 1
        
        return risk_counts
    
    def _calculate_confidence_score(self, clauses: List[ClauseAnalysis]) -> float:
        """Calculate overall confidence score based on analysis quality."""
        if not clauses:
            return 0.0
        
        # Simple heuristic: confidence decreases with more fallback analyses
        fallback_count = sum(1 for c in clauses if c.motivo_bandeira == "Análise automática indisponível - requer revisão manual")
        success_rate = 1 - (fallback_count / len(clauses))
        
        # Adjust based on clause complexity and detail
        detail_score = sum(
            1 if len(c.explicacao_simples) > 100 and len(c.perguntas_negociacao) >= 3 else 0.5
            for c in clauses
        ) / len(clauses)
        
        confidence = (success_rate * 0.7) + (detail_score * 0.3)
        return round(confidence, 2)


# Convenience functions for external use
async def analyze_contract_clauses(
    extraction_result: PDFExtractionResult,
    clauses: List[ProcessedClause],
    contract_summary: ContractSummary,
    perspectiva: str = "fundador",
    llm_provider: Optional[str] = None
) -> ContractAnalysisResponse:
    """
    Convenience function to analyze contract clauses.
    
    Args:
        extraction_result: PDF extraction result
        clauses: List of processed clauses
        contract_summary: Contract summary
        perspectiva: Analysis perspective
        llm_provider: LLM provider override
    
    Returns:
        Complete contract analysis response
    """
    analyzer = ContractAnalyzer(llm_provider=llm_provider)
    return await analyzer.analyze_full_contract(
        extraction_result, 
        clauses, 
        contract_summary, 
        perspectiva
    )


async def analyze_single_contract_clause(
    clause: ProcessedClause,
    document_id: str,
    perspectiva: str = "fundador",
    llm_provider: Optional[str] = None
) -> ClauseAnalysis:
    """
    Convenience function to analyze a single clause.
    
    Args:
        clause: Clause to analyze
        document_id: Document identifier
        perspectiva: Analysis perspective
        llm_provider: LLM provider override
    
    Returns:
        Clause analysis result
    """
    analyzer = ContractAnalyzer(llm_provider=llm_provider)
    dependencies = AnalysisDependencies(
        document_id=document_id,
        perspectiva=perspectiva,
        llm_provider=llm_provider
    )
    
    return await analyzer.analyze_single_clause(clause, dependencies)