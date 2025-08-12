name: "Lawyerless Contract Analyzer - Full-Stack Implementation PRP v1.0"
description: |

## Purpose
Complete implementation of Lawyerless - A Portuguese contract explanation tool for Brazilian investment documents with clause-by-clause analysis, risk flagging, and negotiation insights. This PRP provides comprehensive context for building a production-ready MVP with Next.js frontend, FastAPI backend, and LLM integration.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats for legal document processing
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix for both frontend and backend
3. **Information Dense**: Use keywords and patterns from PDF processing and LLM integration research
4. **Progressive Success**: Start with core PDF parsing, validate, then enhance with LLM analysis
5. **Global rules**: Follow all rules in CLAUDE.md, especially Python standards and testing requirements

---

## Goal
Build Lawyerless MVP - a web application that analyzes Brazilian investment contracts (SAFE, Convertible Notes, Term Sheets, Shareholder Agreements, Side Letters) and provides clause-by-clause explanations in Portuguese with risk flagging and negotiation insights.

## Why
- **Business value**: Democratize legal document understanding for Brazilian founders and SMEs
- **Integration with existing features**: Foundation for broader legal tech platform in Brazilian market
- **Problems this solves**: Brazilian founders struggle with complex investment documents written in legal Portuguese, leading to uninformed decisions and missed negotiation opportunities
- **Target users**: Founders, PMEs, B2E professionals in Brazil who need to understand investment agreements quickly

## What
**User-visible behavior**: Upload PDF → Split-screen view with contract on left, clause-by-clause analysis on right showing TL;DR, simple explanations, risk flags (Green/Yellow/Red), and negotiation questions.

**Technical requirements**: 
- Frontend: Next.js + PDF.js for rendering with text layer extraction and bounding boxes
- Backend: FastAPI + pypdf/pdfplumber for parsing + PydanticAI for LLM orchestration
- Document processing: Clause segmentation with stable IDs, coordinate extraction for sync highlighting
- LLM integration: Function calling for structured JSON output with clause analysis
- Contract summary: Automated extraction of key terms into structured "ficha do contrato"

### Success Criteria
- [ ] Upload and display Brazilian investment contract PDFs with text layer extraction
- [ ] Segment documents into clauses with stable IDs and bounding box coordinates  
- [ ] Generate clause-by-clause analysis with TL;DR, explanations, risk flags, and negotiation questions
- [ ] Display contract summary card with extracted key terms (parties, values, dates, rights)
- [ ] Synchronized highlighting between PDF viewer and analysis panel
- [ ] Support for 5 document types: SAFE, Convertible Notes, Term Sheets, Shareholder Agreements, Side Letters
- [ ] All explanations and UI in Portuguese (pt-BR)
- [ ] Proper legal disclaimers and non-advisory warnings

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window

# PDF Processing Research (2024)
- url: https://github.com/jsvine/pdfplumber
  why: Primary library for coordinate-based text extraction and clause segmentation
  critical: Can extract text with coordinates (x0, x1, top, bottom) essential for highlighting sync

- url: https://pypdf.readthedocs.io/en/stable/user/extract-text.html  
  why: Fallback for text extraction, better for simple PDFs
  critical: Pure Python, good for splitting/merging, but limited layout analysis

- url: https://medium.com/@azhar-sayyad/a-step-by-step-guide-to-parsing-pdfs-using-the-pdfplumber-library-in-python-c12d94ae9f07
  why: Step-by-step pdfplumber implementation patterns
  critical: Shows coordinate extraction and word-level positioning

# Next.js + PDF.js Integration (2024)
- url: https://stackoverflow.com/questions/78121846/how-to-get-pdfjs-dist-working-with-next-js-14
  why: Current Next.js 14 PDF.js integration challenges and solutions
  critical: Server-side processing requires specific Next.js configuration workarounds

- url: https://github.com/mozilla/pdf.js/issues/5643
  why: PDF.js bounding box extraction for text highlighting
  critical: getTextContent() returns transform matrix with X,Y coordinates

# LLM Contract Analysis Research (2024)  
- url: https://arxiv.org/html/2508.03080
  why: ContractEval benchmark - clause-level legal risk identification best practices
  critical: Open-source LLMs need fine-tuning for legal accuracy, focus on recall over precision

- url: https://zuva.ai/blog/problems-with-prompts-measurability-predictability-of-llm-accuracy/
  why: LLM accuracy challenges in contract analysis
  critical: Contract users care more about recall (avoiding misses) than precision

- url: https://medium.com/@nayan.j.paul/extract-contract-details-using-llm-and-gen-ai-a196f84f96c5
  why: LLM structured output patterns for contract data extraction
  critical: Function calling with JSON schema for consistent contract parsing

# Brazilian Legal Context
- url: https://nvca.org/model-legal-documents/
  why: Standard investment agreement structures (adapt to Brazilian context)
  critical: SAFE agreements, convertible notes, term sheet patterns

# FastAPI + PydanticAI Patterns  
- file: use-cases/pydantic-ai/examples/main_agent_reference/agent.py
  why: Environment-based model configuration pattern
  critical: Use load_dotenv() and Settings class for API key management

- file: use-cases/pydantic-ai/examples/structured_output_agent/agent.py  
  why: Structured output with result_type for contract analysis JSON
  critical: Use result_type=ContractAnalysis for function calling JSON responses

- file: use-cases/pydantic-ai/examples/main_agent_reference/models.py
  why: Pydantic model patterns for data validation
  critical: Field validation, Config examples, datetime handling

- docfile: use-cases/pydantic-ai/CLAUDE.md
  why: PydanticAI global rules and anti-patterns
  critical: Never use result_type unless structured output needed, async/sync patterns
```

### Current Codebase Tree
```bash
/Users/vitorjuliatto/Arquivos Locais/Projetos/Lawerless
├── PRPs/
├── examples/
├── use-cases/
│   ├── pydantic-ai/examples/  # Reference patterns
│   └── mcp-server/            # FastAPI patterns
├── CLAUDE.md                  # Global rules
├── INITIAL.md                 # Feature specification
└── README.md
```

### Desired Codebase Tree with Files to be Added
```bash
Lawerless/
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app with CORS, routes
│   │   ├── models.py         # Pydantic models for contract analysis
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── contract_analyzer.py  # Main PydanticAI agent
│   │   │   ├── prompts.py    # System prompts for Portuguese analysis
│   │   │   └── tools.py      # Agent tools for clause analysis  
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_processor.py    # pdfplumber/pypdf parsing logic
│   │   │   ├── clause_segmenter.py # Clause detection and ID generation
│   │   │   └── contract_extractor.py # Contract summary extraction
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py     # PDF upload and analysis endpoints
│   │   └── settings.py       # Environment configuration with load_dotenv()
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py      # Pytest configuration and fixtures  
│   │   ├── test_pdf_processor.py
│   │   ├── test_clause_segmenter.py
│   │   ├── test_contract_analyzer.py  # TestModel/FunctionModel tests
│   │   └── fixtures/
│   │       └── sample_contracts.pdf   # Test PDFs
│   ├── requirements.txt      # Python dependencies
│   └── .env.example         # Environment variables template
├── frontend/                 # Next.js frontend  
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx    # Root layout with Portuguese metadata
│   │   │   ├── page.tsx      # Main upload and analysis page
│   │   │   └── api/
│   │   │       └── analyze/
│   │   │           └── route.ts  # Proxy to FastAPI backend
│   │   ├── components/
│   │   │   ├── PDFViewer.tsx     # PDF.js integration component
│   │   │   ├── AnalysisPanel.tsx # Clause analysis display
│   │   │   ├── ContractCard.tsx  # Contract summary card
│   │   │   ├── ClauseList.tsx    # Navigation and clause index
│   │   │   └── UploadZone.tsx    # PDF upload interface
│   │   ├── hooks/
│   │   │   ├── usePDFAnalysis.ts  # API integration hook
│   │   │   └── usePDFHighlight.ts # Coordinate-based highlighting
│   │   ├── types/
│   │   │   └── contracts.ts      # TypeScript interfaces
│   │   └── utils/
│   │       ├── pdfjs-config.ts   # PDF.js worker configuration
│   │       └── coordinate-utils.ts # PDF coordinate transformation
│   ├── public/
│   │   └── pdf-worker.js     # PDF.js worker for text extraction
│   ├── package.json
│   ├── next.config.js       # Next.js configuration for PDF.js
│   └── tailwind.config.js   # Styling configuration
├── docker-compose.yml       # Development environment
├── README.md               # Setup and usage instructions
└── .env.example           # Environment variables for both services
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: pdfplumber coordinate system
# pdfplumber uses bottom-left origin, web uses top-left
# Must transform coordinates: web_y = pdf_height - pdf_y

# CRITICAL: PDF.js Next.js integration (2024)
# Next.js 14 requires specific webpack configuration in next.config.js:
# serverComponentsExternalPackages: ['pdfjs-dist']
# Also need to configure PDF.js worker path properly

# CRITICAL: PydanticAI structured output for contracts
# Use result_type ONLY for structured JSON output (ContractAnalysis)
# For simple text responses, use default string output to avoid validation issues

# CRITICAL: Brazilian Portuguese legal terminology
# Must use specific terms: "Mútuo Conversível", "SAFE", "Cláusula", "Foro", etc.
# LLM prompts must specify pt-BR and Brazilian legal context

# CRITICAL: File upload limits
# PDFs can be large - configure FastAPI max file size
# Use streaming for large files, implement progress indicators

# CRITICAL: pdfplumber vs pypdf choice
# pdfplumber: Better for coordinate extraction, table detection, complex layouts
# pypdf: Faster for simple text extraction, better for PDF manipulation
# Use pdfplumber as primary, pypdf as fallback

# CRITICAL: LLM token limits  
# Investment contracts can be 50+ pages, exceed context windows
# Must implement chunking strategy with context overlap
# Use Claude-3.5-Sonnet for large context or GPT-4-turbo with chunking

# CRITICAL: Async patterns in FastAPI
# All LLM calls must be async to prevent blocking
# Use asyncio.gather() for parallel clause processing
# Implement proper timeout handling (30s+ for complex analysis)
```

## Implementation Blueprint

### Data Models and Structure

Create the core data models ensuring type safety and consistency between frontend TypeScript and backend Python.

```python
# Backend Pydantic Models (app/models.py)
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class ClauseAnalysis(BaseModel):
    """Analysis for individual contract clause."""
    clause_id: str = Field(..., description="Stable clause identifier")
    tldr: str = Field(..., max_length=200, description="1-2 sentence summary")  
    explicacao_simples: str = Field(..., description="Simple Portuguese explanation")
    porque_importa: str = Field(..., description="Why this matters / practical impact")
    bandeira: Literal["verde", "amarelo", "vermelho"] = Field(..., description="Risk flag color")
    motivo_bandeira: str = Field(..., description="Reason for the flag color")
    perguntas_negociacao: List[str] = Field(..., max_items=5, description="Negotiation questions")
    geral_vs_contrato: Optional[dict] = Field(None, description="General vs contract-specific explanation")
    coordenadas: dict = Field(..., description="Bounding box coordinates for highlighting")

class ContractSummary(BaseModel):
    """Structured contract summary (ficha do contrato)."""
    tipo_instrumento: Literal["mutuo_conversivel", "safe", "term_sheet", "acordo_acionistas", "side_letter"]
    partes: dict = Field(..., description="Company and investor information")
    datas: dict = Field(..., description="Key dates")
    valores: dict = Field(..., description="Financial terms")  
    conversao: dict = Field(..., description="Conversion terms")
    direitos: dict = Field(..., description="Rights and preferences")
    obrigacoes: dict = Field(..., description="Obligations and covenants")
    jurisdicao: dict = Field(..., description="Jurisdiction and governing law")

class ContractAnalysisResponse(BaseModel):
    """Complete contract analysis response."""
    document_id: str = Field(..., description="Unique document identifier")
    contract_summary: ContractSummary = Field(..., description="Contract summary card")
    clauses: List[ClauseAnalysis] = Field(..., description="Clause-by-clause analysis")
    processing_time: float = Field(..., description="Analysis duration in seconds")
    created_at: datetime = Field(default_factory=datetime.now)
```

### List of Tasks to Complete the PRP (In Order)

```yaml
Task 1 - Backend Foundation:
CREATE backend/app/settings.py:
  - MIRROR pattern from: use-cases/pydantic-ai/examples/main_agent_reference/settings.py
  - MODIFY for FastAPI-specific settings (CORS, file upload limits)
  - ADD pdfplumber and pypdf dependencies
  - KEEP load_dotenv() pattern identical

CREATE backend/app/main.py:
  - PATTERN: FastAPI app with CORS for frontend communication
  - ADD file upload endpoints with size limits (50MB max)
  - INCLUDE proper error handling for malformed PDFs
  - ADD health check endpoint

Task 2 - PDF Processing Service:
CREATE backend/app/services/pdf_processor.py:
  - USE pdfplumber as primary library for coordinate extraction
  - IMPLEMENT text extraction with bounding boxes (x0, x1, top, bottom)
  - ADD pypdf fallback for simple text extraction
  - INCLUDE coordinate transformation utilities (PDF to web coordinates)
  - HANDLE edge cases: multi-column PDFs, headers/footers, page breaks

CREATE backend/app/services/clause_segmenter.py:  
  - DETECT clause boundaries using heuristics (numbered sections, "Cláusula", "Seção")
  - GENERATE stable clause IDs (hash-based for consistency)
  - PRESERVE coordinate information for highlighting synchronization
  - HANDLE Brazilian legal document patterns (Roman numerals, subsections)

Task 3 - LLM Integration with PydanticAI:
CREATE backend/app/agents/contract_analyzer.py:
  - MIRROR pattern from: use-cases/pydantic-ai/examples/structured_output_agent/agent.py
  - USE result_type=ContractAnalysisResponse for structured output
  - IMPLEMENT Portuguese legal analysis with Brazilian context
  - ADD chunking strategy for large documents (4000 token chunks with overlap)
  - INCLUDE retry logic for LLM timeouts

CREATE backend/app/agents/prompts.py:
  - DEFINE system prompts in Portuguese for legal analysis
  - INCLUDE Brazilian legal terminology and context
  - SPECIFY risk flagging criteria (red: restrictive terms, yellow: unclear terms, green: favorable)
  - ADD examples of clause analysis in Portuguese

CREATE backend/app/agents/tools.py:
  - IMPLEMENT @agent.tool for clause analysis
  - ADD @agent.tool for contract summary extraction
  - INCLUDE legal term definition lookups
  - HANDLE clause comparison with market standards

Task 4 - FastAPI Routes:
CREATE backend/app/api/routes.py:
  - ADD POST /analyze endpoint for PDF upload and processing
  - IMPLEMENT GET /analysis/{document_id} for retrieving results
  - INCLUDE WebSocket endpoint for real-time processing updates
  - ADD proper HTTP status codes and error responses
  - IMPLEMENT file validation (PDF only, size limits)

Task 5 - Backend Testing:
CREATE backend/tests/conftest.py:
  - MIRROR pattern from: use-cases/pydantic-ai/examples/testing_examples/test_agent_patterns.py
  - SETUP TestModel and FunctionModel for agent testing
  - CREATE fixtures for sample PDF files
  - INCLUDE mock dependencies for LLM calls

CREATE backend/tests/test_contract_analyzer.py:
  - TEST agent with TestModel for clause analysis
  - VALIDATE structured output format
  - TEST error handling for malformed contracts
  - INCLUDE edge cases: empty clauses, missing sections

Task 6 - Frontend Foundation:  
CREATE frontend/next.config.js:
  - CONFIGURE webpack for PDF.js integration
  - ADD serverComponentsExternalPackages: ['pdfjs-dist']
  - SETUP worker path configuration
  - INCLUDE CORS settings for backend communication

CREATE frontend/src/utils/pdfjs-config.ts:
  - CONFIGURE PDF.js worker path
  - SETUP text layer extraction utilities
  - IMPLEMENT coordinate transformation functions
  - ADD error handling for PDF loading failures

Task 7 - PDF Viewer Component:
CREATE frontend/src/components/PDFViewer.tsx:
  - INTEGRATE PDF.js for document rendering
  - IMPLEMENT text layer extraction with getTextContent()
  - ADD coordinate-based highlighting synchronization
  - INCLUDE zoom, navigation, and search functionality
  - HANDLE multi-page documents with performance optimization

Task 8 - Analysis Panel Component:
CREATE frontend/src/components/AnalysisPanel.tsx:
  - DISPLAY clause-by-clause analysis with Portuguese labels
  - IMPLEMENT risk flag visualization (green/yellow/red badges)
  - ADD expandable sections for detailed explanations
  - INCLUDE negotiation questions with copy functionality
  - SYNCHRONIZE scrolling with PDF viewer

Task 9 - Contract Summary Card:
CREATE frontend/src/components/ContractCard.tsx:
  - DISPLAY structured contract information ("ficha do contrato")
  - IMPLEMENT collapsible sections for different data categories  
  - ADD visual indicators for key terms (valuation cap, conversion triggers)
  - INCLUDE export functionality for contract summary

Task 10 - API Integration:
CREATE frontend/src/hooks/usePDFAnalysis.ts:
  - IMPLEMENT file upload with progress tracking
  - ADD polling for analysis completion
  - HANDLE error states and retry logic
  - INCLUDE caching for analyzed documents

Task 11 - Integration Testing:
CREATE docker-compose.yml:
  - SETUP development environment with both services
  - INCLUDE environment variable configuration
  - ADD volume mounts for development
  - CONFIGURE networking between frontend and backend

Task 12 - End-to-End Validation:
TEST complete workflow:
  - UPLOAD sample Brazilian SAFE agreement PDF
  - VERIFY clause segmentation and coordinate extraction
  - VALIDATE LLM analysis quality and Portuguese output
  - TEST highlighting synchronization between viewer and panel
  - CONFIRM contract summary accuracy
```

### Integration Points
```yaml
DATABASE:
  - Optional: Add PostgreSQL for document storage and analysis caching
  - Schema: documents, analyses, clause_mappings tables
  - Consider for MVP+: User accounts and document history

CONFIG:
  - Backend: LLM API keys, file upload limits, CORS origins
  - Frontend: Backend API URL, PDF.js worker paths
  - Shared: Document processing timeouts, supported file types

EXTERNAL SERVICES:
  - LLM Provider: OpenAI GPT-4o or Anthropic Claude-3.5-Sonnet for Portuguese
  - Optional: Brazilian legal database for clause validation
  - Consider: Portuguese legal dictionary API for term definitions

MONITORING:  
  - Backend: FastAPI built-in metrics, PDF processing times
  - Frontend: Upload success rates, user interaction analytics
  - LLM: Token usage, analysis quality metrics
```

## Validation Loop

### Level 1: Backend Syntax & Style
```bash
# Setup virtual environment and dependencies
cd backend
python -m venv venv_linux
source venv_linux/bin/activate  # On Linux/Mac
pip install -r requirements.txt

# Run linting and type checking
ruff check app/ --fix
mypy app/

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Backend Unit Tests
```python
# Test PDF processing with sample files
def test_pdf_text_extraction():
    """Test basic PDF text extraction with coordinates"""
    processor = PDFProcessor()
    result = processor.extract_text_with_coordinates("fixtures/sample_safe.pdf")
    assert len(result.clauses) > 0
    assert all(clause.coordinates for clause in result.clauses)

def test_clause_segmentation():
    """Test clause boundary detection for Brazilian contracts"""
    segmenter = ClauseSegmenter()
    text = "1. OBJETO DO CONTRATO\n1.1. A empresa...\n\n2. VALOR DO INVESTIMENTO"
    clauses = segmenter.segment_clauses(text)
    assert len(clauses) == 2
    assert clauses[0].title == "OBJETO DO CONTRATO"

def test_contract_analyzer_with_test_model():
    """Test agent with TestModel for Portuguese analysis"""
    from pydantic_ai.models.test import TestModel
    
    test_model = TestModel()
    analyzer = ContractAnalyzer()
    
    with analyzer.agent.override(model=test_model):
        result = analyzer.analyze_clause("Cláusula de conversão automática...")
        assert result.bandeira in ["verde", "amarelo", "vermelho"]
        assert len(result.explicacao_simples) > 0
```

```bash
# Run backend tests
cd backend
source venv_linux/bin/activate
pytest tests/ -v --cov=app

# Expected: All tests pass with >80% coverage
```

### Level 3: Frontend Setup & Build
```bash
# Install dependencies and build
cd frontend  
npm install
npm run build

# Expected: Successful build with no TypeScript errors
```

### Level 4: Integration Test
```bash
# Start both services
cd backend && source venv_linux/bin/activate && uvicorn app.main:app --reload &
cd frontend && npm run dev &

# Test PDF upload and analysis
curl -X POST http://localhost:8000/analyze \
  -F "file=@fixtures/sample_safe.pdf" \
  -H "Accept: application/json"

# Expected: JSON response with contract analysis
# Frontend at http://localhost:3000 should display upload interface
```

### Level 5: End-to-End Validation
```bash
# Test complete workflow
1. Open http://localhost:3000
2. Upload a Brazilian SAFE agreement PDF
3. Verify PDF renders with text layer
4. Confirm clause-by-clause analysis appears in Portuguese  
5. Test highlighting synchronization by clicking clauses
6. Validate contract summary card with extracted terms
7. Check risk flags and negotiation questions

# Expected: Smooth user experience with accurate Portuguese analysis
```

## Final Validation Checklist
- [ ] All backend tests pass: `pytest backend/tests/ -v`
- [ ] No linting errors: `ruff check backend/app/`  
- [ ] No type errors: `mypy backend/app/`
- [ ] Frontend builds successfully: `npm run build`
- [ ] Integration test successful: PDF upload and analysis complete
- [ ] Portuguese output validated by native speaker
- [ ] Risk flagging accuracy tested with known problematic clauses
- [ ] Coordinate-based highlighting works across different PDF types
- [ ] Contract summary extraction accuracy >90% on test documents
- [ ] Performance acceptable: <30s for 20-page contract analysis
- [ ] Error handling graceful for malformed PDFs and LLM failures
- [ ] Legal disclaimer prominent and clear
- [ ] Documentation updated with setup instructions

---

## Anti-Patterns to Avoid  
- ❌ Don't skip coordinate extraction - highlighting sync is critical UX
- ❌ Don't use generic English prompts - must be Brazilian Portuguese legal context
- ❌ Don't ignore PDF parsing errors - implement graceful degradation  
- ❌ Don't hardcode LLM responses - use structured output validation
- ❌ Don't skip chunking strategy - contracts exceed token limits
- ❌ Don't ignore async patterns - FastAPI and LLM calls must be non-blocking
- ❌ Don't forget legal disclaimers - this is not legal advice
- ❌ Don't use result_type unless structured JSON output needed
- ❌ Don't skip TestModel validation - test agent logic before real LLM calls

**PRP Quality Score: 9/10** - Comprehensive context provided with specific Brazilian legal requirements, detailed implementation roadmap, proper technology choices based on 2024 research, and complete validation strategy. High confidence for one-pass implementation success.