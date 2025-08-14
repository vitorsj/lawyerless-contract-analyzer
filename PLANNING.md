# Lawyerless - Project Planning & Architecture

## 🎯 Project Overview

**Lawyerless** is a Brazilian contract analysis system that helps non-technical users understand complex investment contracts through AI-powered clause-by-clause explanations in Portuguese.

### Target Users
- Founders and entrepreneurs
- Small to medium businesses (SMBs) 
- B2B professionals
- Anyone dealing with Brazilian investment documents

### Core Value Proposition
Transform complex legal jargon into clear, actionable insights with risk flagging and negotiation guidance.

## 🏗️ System Architecture

### High-Level Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Engine    │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PydanticAI)   │
│                 │    │                 │    │   + OpenAI      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
│                                               │
▼                                               ▼
┌─────────────────┐                    ┌─────────────────┐
│   PDF.js        │                    │   Legal Tools   │
│   (Rendering)   │                    │   (Risk, Terms) │
└─────────────────┘                    └─────────────────┘
```

### Technology Stack

#### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **PDF Rendering**: PDF.js
- **State Management**: React hooks + Context
- **Communication**: REST API + WebSocket (real-time updates)

#### Backend  
- **Framework**: FastAPI (Python 3.13+)
- **AI Integration**: PydanticAI 0.6.2
- **LLM Provider**: OpenAI (GPT-4o-mini default)
- **PDF Processing**: pdfplumber + pypdf
- **Data Validation**: Pydantic v2
- **Async Support**: asyncio + httpx

#### AI & NLP
- **Agent Framework**: PydanticAI with structured outputs
- **LLM Model**: GPT-4o-mini (fast, cost-effective)
- **Knowledge Base**: Brazilian legal patterns & templates
- **Tool Functions**: Risk analysis, term definitions, market comparisons

### File Structure & Modularity

```
Lawyerless/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── agents/         # PydanticAI agents (< 500 lines each)
│   │   │   ├── contract_analyzer.py  # Main analysis agent
│   │   │   ├── prompts.py           # System prompts
│   │   │   └── tools.py             # Agent tool functions
│   │   ├── services/       # Core business logic
│   │   │   ├── pdf_processor.py      # PDF text extraction
│   │   │   ├── clause_segmenter.py   # Brazilian clause patterns
│   │   │   ├── contract_extractor.py # Structured data extraction
│   │   │   ├── docling_processor.py  # Alternative PDF processor
│   │   │   ├── advanced_clause_extractor.py # Enhanced extraction
│   │   │   ├── extraction_reporter.py # Analysis reporting
│   │   │   ├── langsmith_integration.py # LLM observability
│   │   │   └── llm_providers.py     # Multi-provider LLM support
│   │   ├── api/           # REST endpoints
│   │   │   └── routes.py  # FastAPI routes
│   │   ├── models.py      # Pydantic data models
│   │   ├── settings.py    # Configuration management
│   │   └── main.py        # FastAPI application
│   ├── tests/             # Pytest test suite (TO BE CREATED)
│   ├── extraction_reports/ # Generated analysis reports
│   ├── requirements.txt   # Production dependencies
│   ├── requirements-dev.txt # Development dependencies
│   └── venv_linux/        # Python virtual environment
├── frontend/              # Next.js React frontend
│   ├── src/
│   │   ├── app/          # Next.js 14 app router
│   │   ├── components/   # React components (< 500 lines each)
│   │   │   ├── AnalysisPanel.tsx    # Clause analysis display
│   │   │   ├── ContractSummary.tsx  # Contract overview card
│   │   │   ├── FileUpload.tsx       # PDF upload interface
│   │   │   ├── LLMProviderSelector.tsx # Provider selection
│   │   │   └── PDFViewer.tsx        # PDF.js integration
│   │   ├── hooks/        # Custom React hooks
│   │   │   ├── useContractAnalysis.ts # API integration
│   │   │   ├── useLocalStorage.ts   # Local state persistence
│   │   │   ├── usePDFViewer.ts      # PDF viewing logic
│   │   │   └── useWebSocket.ts      # Real-time updates
│   │   ├── types/        # TypeScript type definitions
│   │   │   └── index.ts  # Contract analysis types
│   │   └── utils/        # Utility functions
│   │       └── pdfjs-config.ts # PDF.js configuration
│   ├── public/
│   │   └── pdf-worker.js # PDF.js worker for processing
│   ├── package.json      # Node.js dependencies
│   ├── next.config.js    # Next.js configuration
│   ├── tailwind.config.js # Styling configuration
│   └── tsconfig.json     # TypeScript configuration
├── docker/               # Docker configurations
│   ├── postgres/         # PostgreSQL setup
│   └── redis/           # Redis configuration
├── scripts/             # Development scripts
│   └── dev-setup.sh     # Environment setup
├── PRPs/                # Project Requirements & Planning
│   └── lawyerless-contract-analyzer.md # Comprehensive PRP
├── docker-compose.yml   # Development environment
├── Makefile            # Development commands
├── CLAUDE.md           # AI coding instructions
├── PLANNING.md         # This architecture document
├── TASK.md             # Task management
└── README.md           # Project overview and setup
```

## 🧠 AI Analysis Pipeline

### 1. Document Processing
```python
PDF Upload → Text Extraction → Clause Segmentation → Coordinate Mapping
```

### 2. AI Analysis Workflow
```python
def analyze_contract():
    # Stage 1: Document Understanding
    contract_summary = extract_contract_metadata(pdf_text)
    
    # Stage 2: Clause Analysis (batched)
    for clause_batch in clauses:
        analyses = await analyze_clauses_parallel(clause_batch)
    
    # Stage 3: Risk Assessment
    risk_summary = calculate_risk_flags(analyses)
    
    # Stage 4: Structured Response
    return ContractAnalysisResponse(
        summary=contract_summary,
        clauses=analyses,
        risk_summary=risk_summary
    )
```

### 3. PydanticAI Agent Design

```python
# Main contract analysis agent with tools
contract_agent = Agent(
    model=OpenAIModel("gpt-4o-mini"),
    deps_type=AnalysisDependencies,
    system_prompt=BRAZILIAN_CONTRACT_PROMPT
)

# Available tools for the agent
@contract_agent.tool
def get_legal_term_definition(term: str) -> str: ...

@contract_agent.tool 
def analyze_risk_patterns(clause_text: str) -> Dict[str, Any]: ...

@contract_agent.tool
def generate_negotiation_questions(category: str) -> List[str]: ...
```

## 📋 Data Models & Schemas

### Core Analysis Output
```python
class ClauseAnalysis(BaseModel):
    clause_id: str
    titulo: str
    texto_original: str
    tldr: str                    # 1-2 sentences summary
    explicacao_simples: str      # Plain language explanation
    porque_importa: str          # Practical impact
    bandeira: Bandeira          # Verde/Amarelo/Vermelho
    motivo_bandeira: str        # Risk justification
    perguntas_negociacao: List[str]  # Up to 5 questions
    coordenadas: BoundingBox    # PDF coordinates for highlighting
```

### Risk Flag System
```python
class Bandeira(str, Enum):
    VERDE = "verde"      # Low risk, standard terms
    AMARELO = "amarelo"  # Medium risk, review recommended  
    VERMELHO = "vermelho" # High risk, negotiate or avoid
```

### Supported Document Types
- **SAFE**: Simple Agreement for Future Equity
- **Mútuo Conversível**: Convertible loan agreements
- **Term Sheet**: Investment terms and conditions
- **Acordo de Acionistas/Quotistas**: Shareholder agreements
- **Side Letters**: Supplementary agreements

## 🔍 Brazilian Legal Pattern Recognition

### Clause Segmentation Patterns
```python
BRAZILIAN_PATTERNS = {
    "numbered_clauses": r"\b(\d+)\.?\s*[^.]{1,200}",
    "clausula_headers": r"(?i)cláusula\s+(\d+[\.\w]*)",
    "secao_headers": r"(?i)seção\s+([IVX]+|\d+)",
    "roman_numerals": r"\b([IVX]{1,10})\.\s*",
    "brazilian_articles": r"(?i)artigo\s+(\d+)"
}
```

### Risk Assessment Heuristics
```python
RED_FLAGS = {
    "drag_along": "< 66% threshold without minority protection",
    "anti_dilution": "Full ratchet without time limits", 
    "qualified_round": "Extremely restrictive definition",
    "founder_buyback": "Below-market valuation triggers"
}

YELLOW_FLAGS = {
    "missing_cap": "Discount without valuation cap",
    "high_interest": "Above market rates for mútuo",
    "distant_jurisdiction": "Forum clause without justification"
}
```

## 🚀 Development Workflow

### Code Organization Principles
1. **Modularity**: No file > 500 lines, clear separation of concerns
2. **Testing**: Pytest for backend, unit tests for all core functions
3. **Type Safety**: Full type hints in Python, TypeScript for frontend
4. **Documentation**: Google-style docstrings, inline reasoning comments

### Key Conventions
- **Relative imports** within packages
- **Environment variables** via python-dotenv
- **Async/await** for all I/O operations
- **Pydantic models** for all data validation
- **Brazilian Portuguese** for user-facing text

### Performance Targets
- **Analysis time**: 10-30 seconds per document
- **File size limit**: 50MB per PDF
- **Page limit**: 50 pages per document
- **Concurrent processing**: Up to 5 documents

### Quality Gates
```bash
# Before commit
make format     # Black + Prettier
make lint       # Ruff + ESLint  
make type-check # mypy + tsc
make test       # pytest + jest
```

## 🛡️ Security & Compliance

### Data Protection
- **No persistent storage** of uploaded documents
- **Temporary processing** with automatic cleanup
- **API key protection** via environment variables
- **CORS configuration** for frontend-only access

### Legal Disclaimers
- **Not legal advice**: Clear persistent warning
- **Educational tool**: Emphasis on learning/understanding
- **Professional consultation**: Recommendation for complex cases

## 📊 Monitoring & Observability

### Key Metrics
- **Processing time** per document type
- **Success/failure rates** for AI analysis
- **User interaction patterns** (most analyzed clauses)
- **Performance degradation** alerts

### Error Handling
- **Graceful degradation**: Fallback analyses when AI fails
- **Retry logic**: 3 attempts with exponential backoff
- **User feedback**: Clear error messages in Portuguese
- **Logging**: Structured logs with correlation IDs

---

## 🔄 Future Roadmap

### Phase 1 (Current) - MVP
- ✅ Core PDF processing pipeline (pdf_processor.py, docling_processor.py)
- ✅ PydanticAI integration (contract_analyzer.py with 0.6.2)
- ✅ Advanced clause extraction (advanced_clause_extractor.py)
- ✅ LangSmith observability (langsmith_integration.py)
- ✅ Multi-provider LLM support (llm_providers.py)
- ✅ Portuguese explanations and prompts
- ✅ Next.js frontend with PDF.js integration
- ✅ TypeScript type safety throughout
- ⚠️ Test suite needs creation (tests/ directory missing)
- ⚠️ End-to-end workflow testing needed

### 🔥 CRÍTICO - Melhorias de Produto (2025-08-14)
- 🚨 **Extração de contratos precisa melhorar** - Está ruim, reformular
- 🎯 **Perspectiva sempre pro-investidor** - Análise deve defender investidor
- ❌ **Remover perguntas de negociação** - Funcionalidade descontinuada
- 💬 **Mostrar complexidade para usuário** - LLM não está sendo exibido
- ❌ **Remover TLDR** - Simplificar interface
- ❌ **Remover resumo do contrato** - Foco só nas cláusulas
- 📝 **Atualizar prompts** - Reescrever para foco no investidor

### Phase 2 - Enhancement
- Multi-language support (English)
- Custom risk profile settings
- Document comparison features
- Export functionality (PDF reports)

### Phase 3 - Scale
- Multi-tenant architecture
- Usage analytics dashboard
- Advanced ML models
- Integration APIs

This architecture ensures scalability, maintainability, and delivers on the core promise of making complex legal documents accessible to non-technical Brazilian users.