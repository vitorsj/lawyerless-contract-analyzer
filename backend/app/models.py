"""
Pydantic models for Lawyerless contract analysis.

This module defines all data models used for Brazilian investment contract
analysis, including clause analysis, contract summaries, and API responses.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum


# Enums for structured data
class TipoInstrumento(str, Enum):
    """Types of investment instruments supported."""
    MUTUO_CONVERSIVEL = "mutuo_conversivel"
    SAFE = "safe"
    TERM_SHEET = "term_sheet"
    ACORDO_ACIONISTAS = "acordo_acionistas"
    SIDE_LETTER = "side_letter"


class TipoSocietario(str, Enum):
    """Company types in Brazil."""
    LTDA = "LTDA"
    SA = "SA"
    EIRELI = "EIRELI"
    EMPRESARIO_INDIVIDUAL = "EI"


class TipoPessoa(str, Enum):
    """Person types."""
    PESSOA_FISICA = "PF"
    PESSOA_JURIDICA = "PJ"


class Moeda(str, Enum):
    """Supported currencies."""
    BRL = "BRL"
    USD = "USD"
    EUR = "EUR"


class Indexador(str, Enum):
    """Economic indexers used in Brazil."""
    IPCA = "IPCA"
    SELIC = "SELIC"
    CDI = "CDI"
    IGP_M = "IGP_M"
    NA = "NA"


class Bandeira(str, Enum):
    """Risk flag colors for clause analysis."""
    VERDE = "verde"
    AMARELO = "amarelo" 
    VERMELHO = "vermelho"


# Coordinate and positioning models
class BoundingBox(BaseModel):
    """Bounding box coordinates for text highlighting."""
    x0: float = Field(..., description="Left coordinate")
    x1: float = Field(..., description="Right coordinate")
    top: float = Field(..., description="Top coordinate") 
    bottom: float = Field(..., description="Bottom coordinate")
    page_number: int = Field(..., description="Page number (0-indexed)")
    page_height: float = Field(..., description="Page height for coordinate transformation")


class TextFragment(BaseModel):
    """Text fragment with position information."""
    text: str = Field(..., description="Text content")
    coordinates: BoundingBox = Field(..., description="Position coordinates")
    font_size: Optional[float] = Field(None, description="Font size")
    font_name: Optional[str] = Field(None, description="Font name")


# Contract entity models
class Parte(BaseModel):
    """Contract party information."""
    nome: str = Field(..., description="Party name")
    tipo: TipoPessoa = Field(..., description="Person type (PF/PJ)")
    documento: Optional[str] = Field(None, description="CPF/CNPJ number")
    endereco: Optional[str] = Field(None, description="Address")


class Empresa(Parte):
    """Company party with additional fields."""
    tipo_societario: Optional[TipoSocietario] = Field(None, description="Company type")
    cnpj: Optional[str] = Field(None, description="CNPJ number")
    nome_fantasia: Optional[str] = Field(None, description="Trade name")


class Valor(BaseModel):
    """Monetary value with currency."""
    moeda: Moeda = Field(default=Moeda.BRL, description="Currency")
    valor: float = Field(..., ge=0, description="Amount")
    
    @validator('valor')
    def validate_positive_value(cls, v):
        """Ensure value is positive."""
        if v < 0:
            raise ValueError('Value must be positive')
        return v


# Contract analysis models
class ExplicacaoGeraleContrato(BaseModel):
    """General vs contract-specific explanation."""
    explicacao_geral: str = Field(..., description="General legal concept explanation")
    como_esta_no_contrato: str = Field(..., description="How it's specifically defined in this contract")
    diferencas: Optional[str] = Field(None, description="Differences from market standard")


class ClauseAnalysis(BaseModel):
    """Analysis for individual contract clause."""
    clause_id: str = Field(..., description="Stable clause identifier")
    titulo: Optional[str] = Field(None, description="Clause title/header")
    texto_original: str = Field(..., description="Original clause text")
    
    # Core analysis fields
    tldr: str = Field(..., max_length=200, description="1-2 sentence summary in Portuguese")
    explicacao_simples: str = Field(..., description="Simple Portuguese explanation for laypeople")
    porque_importa: str = Field(..., description="Why this matters / practical impact")
    
    # Risk assessment
    bandeira: Bandeira = Field(..., description="Risk flag color")
    motivo_bandeira: str = Field(..., description="Reason for the flag color")
    
    # Actionable insights
    perguntas_negociacao: List[str] = Field(
        ..., 
        max_items=5, 
        description="Negotiation questions in Portuguese"
    )
    
    # Advanced analysis
    geral_vs_contrato: Optional[ExplicacaoGeraleContrato] = Field(
        None, 
        description="General vs contract-specific explanation"
    )
    
    # Position information
    coordenadas: BoundingBox = Field(..., description="Bounding box coordinates for highlighting")
    
    # Metadata
    clausula_numero: Optional[str] = Field(None, description="Clause number (e.g., '1.1', '2.3.1')")
    nivel_complexidade: Optional[int] = Field(None, ge=1, le=5, description="Complexity level 1-5")
    termos_tecnicos: List[str] = Field(default_factory=list, description="Technical legal terms found")


# Contract summary models (ficha do contrato)
class PartesContrato(BaseModel):
    """Contract parties information."""
    empresa: Empresa = Field(..., description="Company information")
    investidores: List[Parte] = Field(..., description="Investor information")
    garantidores: List[Parte] = Field(default_factory=list, description="Guarantors")


class DatasContrato(BaseModel):
    """Contract dates."""
    assinatura: Optional[str] = Field(None, description="Signature date")
    vigencia_inicio: Optional[str] = Field(None, description="Start date")
    vigencia_fim: Optional[str] = Field(None, description="End date")
    vencimento_mutuo: Optional[str] = Field(None, description="Note maturity date")


class ValoresContrato(BaseModel):
    """Contract financial terms."""
    principal: Valor = Field(..., description="Principal amount")
    juros_aa: Optional[float] = Field(None, ge=0, le=100, description="Annual interest rate %")
    indexador: Optional[Indexador] = Field(None, description="Economic indexer")
    valuation_cap: Optional[float] = Field(None, ge=0, description="Valuation cap")
    desconto_percentual: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage")
    tamanho_rodada: Optional[float] = Field(None, ge=0, description="Round size")
    valuation_pre: Optional[float] = Field(None, ge=0, description="Pre-money valuation")
    valuation_post: Optional[float] = Field(None, ge=0, description="Post-money valuation")


class ConversaoTermos(BaseModel):
    """Conversion terms."""
    gatilhos: List[str] = Field(
        default_factory=lambda: ["rodada_qualificada", "maturidade", "evento_liquidez"],
        description="Conversion triggers"
    )
    definicao_rodada_qualificada: str = Field(default="", description="Qualified round definition")
    formula: str = Field(default="cap", description="Conversion formula")
    mfn: bool = Field(default=True, description="Most Favored Nation clause")


class DireitosInvestidor(BaseModel):
    """Investor rights."""
    pro_rata: Dict[str, Any] = Field(
        default_factory=lambda: {"existe": False, "percentual": None},
        description="Pro rata rights"
    )
    informacao: Dict[str, Any] = Field(
        default_factory=lambda: {"periodicidade": "trimestral", "escopo": ""},
        description="Information rights"
    )
    anti_diluicao: str = Field(default="na", description="Anti-dilution protection")
    preferencia_liquidacao: Dict[str, Any] = Field(
        default_factory=lambda: {"multiplo": None, "participativa": False},
        description="Liquidation preference"
    )
    tag_along: Dict[str, Any] = Field(
        default_factory=lambda: {"percentual": None, "condicoes": ""},
        description="Tag along rights"
    )
    drag_along: Dict[str, Any] = Field(
        default_factory=lambda: {"percentual": None, "condicoes": ""},
        description="Drag along rights"
    )
    veto: List[str] = Field(
        default_factory=lambda: ["endividamento", "mudanca_objeto", "emissao_novas_quotas_acoes"],
        description="Veto rights"
    )


class ObrigacoesContrato(BaseModel):
    """Contract obligations."""
    covenants: List[str] = Field(
        default_factory=lambda: ["nao_concorrencia", "nao_aliciamento"],
        description="Covenants"
    )
    condicoes_precedentes: List[str] = Field(default_factory=list, description="Conditions precedent")
    restricoes_cessao: str = Field(default="", description="Assignment restrictions")


class JurisdicaoContrato(BaseModel):
    """Jurisdiction and governing law."""
    lei_aplicavel: str = Field(default="Brasil", description="Governing law")
    foro: str = Field(default="", description="Jurisdiction/forum")
    arbitragem: Optional[bool] = Field(None, description="Arbitration clause present")


class ContractSummary(BaseModel):
    """Structured contract summary (ficha do contrato)."""
    tipo_instrumento: TipoInstrumento = Field(..., description="Type of investment instrument")
    partes: PartesContrato = Field(..., description="Contract parties")
    datas: DatasContrato = Field(..., description="Key dates")
    valores: ValoresContrato = Field(..., description="Financial terms")
    conversao: ConversaoTermos = Field(..., description="Conversion terms")
    direitos: DireitosInvestidor = Field(..., description="Investor rights and preferences")
    obrigacoes: ObrigacoesContrato = Field(..., description="Obligations and covenants")
    jurisdicao: JurisdicaoContrato = Field(..., description="Jurisdiction and governing law")
    observacoes: str = Field(default="", description="Additional observations")


# API Response models
class ContractAnalysisResponse(BaseModel):
    """Complete contract analysis response."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    contract_summary: ContractSummary = Field(..., description="Contract summary card")
    clauses: List[ClauseAnalysis] = Field(..., description="Clause-by-clause analysis")
    total_pages: int = Field(..., ge=1, description="Total PDF pages")
    total_clauses: int = Field(..., ge=0, description="Total clauses analyzed")
    processing_time: float = Field(..., description="Analysis duration in seconds")
    llm_provider: str = Field(..., description="LLM provider used")
    llm_model: str = Field(..., description="LLM model used")
    analysis_language: str = Field(default="pt-BR", description="Analysis language")
    created_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    
    # Analysis quality metrics
    confidence_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Overall analysis confidence score"
    )
    risk_summary: Dict[str, int] = Field(
        default_factory=lambda: {"verde": 0, "amarelo": 0, "vermelho": 0},
        description="Risk flag count summary"
    )


class AnalysisRequest(BaseModel):
    """Request model for contract analysis."""
    document_id: str = Field(..., description="Document identifier")
    analysis_type: str = Field(default="completa", description="Analysis type")
    include_risk_analysis: bool = Field(default=True, description="Include risk flags")
    include_negotiation_questions: bool = Field(default=True, description="Include negotiation questions")
    perspectiva: Literal["fundador", "investidor"] = Field(
        default="fundador", 
        description="Analysis perspective"
    )


class AnalysisStatus(BaseModel):
    """Analysis status response."""
    document_id: str = Field(..., description="Document identifier")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ..., 
        description="Analysis status"
    )
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    message: str = Field(..., description="Status message in Portuguese")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_details: Optional[str] = Field(None, description="Error details if failed")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: bool = Field(default=True, description="Error flag")
    message: str = Field(..., description="Error message in Portuguese")
    status_code: int = Field(..., description="HTTP status code")
    error_id: Optional[str] = Field(None, description="Error identifier for tracking")
    detail: Optional[Any] = Field(None, description="Additional error details")


# PDF Processing models
class PDFMetadata(BaseModel):
    """PDF document metadata."""
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Number of pages")
    creation_date: Optional[str] = Field(None, description="PDF creation date")
    modification_date: Optional[str] = Field(None, description="PDF modification date")
    title: Optional[str] = Field(None, description="PDF title")
    author: Optional[str] = Field(None, description="PDF author")
    subject: Optional[str] = Field(None, description="PDF subject")


class ProcessedClause(BaseModel):
    """Processed clause from PDF extraction."""
    clause_id: str = Field(..., description="Unique clause identifier")
    text: str = Field(..., description="Clause text content")
    coordinates: BoundingBox = Field(..., description="Position coordinates")
    title: Optional[str] = Field(None, description="Clause title")
    level: int = Field(default=1, description="Clause hierarchy level")
    parent_clause_id: Optional[str] = Field(None, description="Parent clause ID")
    clause_number: Optional[str] = Field(None, description="Clause numbering")


class PDFExtractionResult(BaseModel):
    """Result of PDF text extraction and segmentation."""
    document_id: str = Field(..., description="Document identifier")
    metadata: PDFMetadata = Field(..., description="PDF metadata")
    clauses: List[ProcessedClause] = Field(..., description="Extracted clauses")
    full_text: str = Field(..., description="Complete document text")
    extraction_time: float = Field(..., description="Extraction duration in seconds")
    extraction_method: str = Field(..., description="Extraction method used")
    warnings: List[str] = Field(default_factory=list, description="Extraction warnings")