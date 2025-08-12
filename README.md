# Lawyerless - Análise de Contratos de Investimento

![Lawyerless](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)

Sistema inteligente para análise de contratos de investimento brasileiros com IA, processamento de PDF com coordenadas e explicações em português para leigos.

## 🎯 Funcionalidades

- **Análise Automática**: Análise cláusula por cláusula com IA (PydanticAI + OpenAI)
- **Visualização PDF**: Viewer integrado com destaque sincronizado por coordenadas
- **Bandeiras de Risco**: Sistema Verde/Amarelo/Vermelho para avaliação de riscos
- **Explicações Simples**: Linguagem clara para leigos adultos
- **Perguntas Estratégicas**: Até 5 perguntas de negociação por cláusula
- **Suporte Brasileiro**: Documentos SAFE, mútuo conversível, term sheets, etc.
- **Tempo Real**: Atualizações WebSocket durante o processamento
- **API RESTful**: Endpoints completos para integração

## 🚀 Quick Start

### Pré-requisitos

- Python 3.13+
- Node.js 18+
- OpenAI API Key
- Git

### 1. Clone e Setup

```bash
git clone <repository-url>
cd Lawerless
```

### 2. 🔑 Configurar API Token

**⚠️ IMPORTANTE**: Você precisa configurar sua chave da OpenAI para que a análise de IA funcione.

#### Opção A: Arquivo .env (Recomendado)

Crie um arquivo `.env` na pasta `backend/`:

```bash
# backend/.env
LLM_API_KEY=sk-your-openai-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1

# Outras configurações opcionais
DEBUG=true
LOG_LEVEL=INFO
MAX_FILE_SIZE=52428800  # 50MB
PDF_MAX_PAGES=50
```

#### Opção B: Variáveis de Ambiente

```bash
export LLM_API_KEY=sk-your-openai-api-key-here
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4o-mini
```

#### Como Obter a API Key da OpenAI

1. Visite [platform.openai.com](https://platform.openai.com/)
2. Faça login ou crie uma conta
3. Vá em "API Keys" no menu
4. Clique "Create new secret key"
5. Copie a chave (formato: `sk-...`)

### 3. Backend Setup

```bash
cd backend

# Criar ambiente virtual
python3 -m venv venv_linux
source venv_linux/bin/activate  # Linux/Mac
# ou
venv_linux\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar servidor
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Instalar dependências
npm install

# Executar servidor de desenvolvimento
npm run dev
```

### 5. Acessar Sistema

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🏗️ Arquitetura

```
├── backend/          # FastAPI + PydanticAI
│   ├── app/
│   │   ├── agents/   # Agentes de análise com IA
│   │   ├── services/ # PDF processing & clause segmentation
│   │   ├── api/      # REST endpoints
│   │   └── models/   # Pydantic models
│   └── tests/        # Unit tests with pytest
├── frontend/         # Next.js + PDF.js
│   ├── src/
│   │   ├── components/ # PDF viewer, analysis panels
│   │   ├── hooks/      # React hooks for API
│   │   └── utils/      # PDF.js configuration
└── docker-compose.yml # Development environment
```

## 📋 Usando o Sistema

### Upload e Análise

1. Acesse http://localhost:3000
2. Faça upload de um PDF de contrato brasileiro
3. Selecione perspectiva (fundador/investidor)
4. Acompanhe o progresso em tempo real
5. Visualize a análise cláusula por cláusula

### Via API

```bash
# Upload do PDF
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@contrato.pdf" \
  -F "perspectiva=fundador"

# Verificar status
curl "http://localhost:8000/api/v1/analysis/{document_id}/status"

# Obter resultado
curl "http://localhost:8000/api/v1/analysis/{document_id}"
```

## 🧪 Testes

```bash
# Backend tests
cd backend
source venv_linux/bin/activate
python -m pytest -v

# Frontend build test
cd frontend
npm run build
npm run type-check
```

## 🐳 Docker (Desenvolvimento)

```bash
# Subir todos os serviços
docker-compose up -d

# Logs
docker-compose logs -f

# Parar
docker-compose down
```

## 📁 Documentos Suportados

- **SAFE**: Simple Agreement for Future Equity
- **Mútuo Conversível**: Contratos de empréstimo conversível
- **Term Sheet**: Termos e condições de investimento
- **Acordo de Acionistas/Quotistas**: Direitos e deveres societários
- **Side Letters**: Acordos complementares

## 🔧 Configuração Avançada

### Backend Settings

Edite `backend/app/settings.py` ou use variáveis de ambiente:

```bash
# API Configuration
LLM_API_KEY=your-key
LLM_PROVIDER=openai  # ou anthropic, azure
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_MAX_RETRIES=3
LLM_TIMEOUT=120

# PDF Processing
MAX_FILE_SIZE=52428800  # 50MB
PDF_MAX_PAGES=50
PDF_CHUNK_SIZE=4000
PDF_CHUNK_OVERLAP=200

# Server
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend Configuration

Edite `frontend/next.config.js` para configuração do PDF.js:

```javascript
module.exports = {
  // PDF.js worker configuration
  serverComponentsExternalPackages: ['pdfjs-dist'],
  // ... outras configurações
}
```

## 🔍 Troubleshooting

### Erro 401 na API OpenAI
```
❌ "invalid_api_key"
✅ Verificar se LLM_API_KEY está configurado corretamente
✅ Confirmar que a chave é válida no OpenAI dashboard
```

### PDF não carrega no frontend
```
❌ PDF.js worker error
✅ Verificar se pdf-worker.js está em public/
✅ Verificar configuração do Next.js
```

### Erro de CORS
```
❌ CORS policy error
✅ Verificar CORS_ORIGINS no backend
✅ Confirmar que frontend roda na porta correta
```

### Falha na segmentação de cláusulas
```
❌ Cláusulas não identificadas
✅ Verificar padrões brasileiros em clause_segmenter.py
✅ Testar com documento padrão (SAFE, term sheet)
```

## 📊 Monitoramento

### Logs Importantes

```bash
# Backend logs
tail -f backend/logs/app.log

# Status da análise
curl http://localhost:8000/api/v1/health

# Métricas
curl http://localhost:8000/api/v1/api/health
```

### Performance

- **Tempo típico**: 10-30 segundos por documento
- **Limite de páginas**: 50 páginas por PDF
- **Limite de arquivo**: 50MB por upload
- **Concurrent processing**: Até 5 documentos simultâneos

## 🚀 Produção

### Deploy Checklist

- [ ] Configurar LLM_API_KEY production
- [ ] Definir DEBUG=false
- [ ] Configurar CORS_ORIGINS para domínio real
- [ ] Configurar SSL/HTTPS
- [ ] Configurar rate limiting
- [ ] Configurar monitoring (logs, metrics)
- [ ] Backup de dados de análise

### Variáveis de Ambiente Produção

```bash
LLM_API_KEY=sk-prod-key-here
DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=["https://yourdomain.com"]
MAX_FILE_SIZE=104857600  # 100MB
```

## 🤝 Desenvolvimento

### Estrutura de Código

```bash
backend/app/
├── agents/           # PydanticAI agents
│   ├── contract_analyzer.py  # Main analysis agent
│   ├── prompts.py            # System prompts
│   └── tools.py              # Agent tools
├── services/         # Core services
│   ├── pdf_processor.py      # PDF extraction
│   ├── clause_segmenter.py   # Brazilian patterns
│   └── contract_extractor.py # Structured extraction
├── api/             # REST endpoints
│   └── routes.py    # FastAPI routes
├── models/          # Pydantic models
│   └── __init__.py  # All data models
└── main.py          # FastAPI app
```

### Adicionando Novos Tipos de Documento

1. Adicionar padrões em `clause_segmenter.py`
2. Definir tipo em `models.py` (TipoInstrumento)
3. Atualizar extractor em `contract_extractor.py`
4. Adicionar prompts específicos em `prompts.py`

## 📝 Changelog

### v1.0.0 (Current)
- ✅ Sistema completo de análise de contratos
- ✅ Interface web com PDF viewer
- ✅ Integração PydanticAI + OpenAI
- ✅ Suporte completo a documentos brasileiros
- ✅ API REST + WebSocket
- ✅ Testes unitários
- ✅ Docker development environment

## 🆘 Suporte

Para problemas ou dúvidas:

1. Verificar este README
2. Consultar logs do sistema
3. Testar com documento exemplo
4. Verificar configuração da API key

## 📄 Licença

MIT License - Veja LICENSE para detalhes.

---

**💡 Dica**: Para melhor performance, use documentos com texto selecionável (não escaneados). O sistema funciona melhor com contratos estruturados seguindo padrões brasileiros.