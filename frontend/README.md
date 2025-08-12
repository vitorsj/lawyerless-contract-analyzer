# Lawyerless Frontend

Frontend da aplicação Lawyerless para análise de contratos de investimento, construído com Next.js 14, TypeScript e Tailwind CSS.

## 📋 Pré-requisitos

- Node.js 18.0.0 ou superior
- npm ou yarn
- Backend Lawyerless rodando na porta 8000

## 🚀 Instalação

1. **Instalar dependências:**
```bash
npm install
```

2. **Configurar variáveis de ambiente:**
```bash
cp .env.local.example .env.local
# Editar .env.local com suas configurações
```

3. **Executar em modo de desenvolvimento:**
```bash
npm run dev
```

A aplicação estará disponível em http://localhost:3000

## 📁 Estrutura do Projeto

```
frontend/
├── src/
│   ├── app/                    # App Router (Next.js 14)
│   │   ├── globals.css         # Estilos globais + Tailwind
│   │   ├── layout.tsx          # Layout raiz da aplicação
│   │   ├── page.tsx            # Página inicial
│   │   └── api/                # API routes
│   ├── components/             # Componentes React reutilizáveis
│   │   ├── PDFViewer.tsx       # Visualizador de PDF com PDF.js
│   │   ├── AnalysisPanel.tsx   # Painel de análise de cláusulas
│   │   └── ContractSummary.tsx # Resumo do contrato
│   ├── hooks/                  # Custom hooks
│   │   ├── useContractAnalysis.ts
│   │   ├── usePDFViewer.ts
│   │   └── useWebSocket.ts
│   ├── types/                  # Definições TypeScript
│   │   └── index.ts            # Tipos principais
│   └── utils/                  # Utilitários
│       └── pdfjs-config.ts     # Configuração PDF.js
├── public/                     # Arquivos estáticos
├── package.json               # Dependências e scripts
├── next.config.js             # Configuração Next.js
├── tailwind.config.js         # Configuração Tailwind
├── tsconfig.json              # Configuração TypeScript
└── postcss.config.js          # Configuração PostCSS
```

## 🛠️ Scripts Disponíveis

```bash
npm run dev         # Executar em desenvolvimento
npm run build       # Build para produção
npm run start       # Executar build de produção
npm run lint        # Executar ESLint
npm run type-check  # Verificar tipos TypeScript
```

## 🎨 Tecnologias Utilizadas

### Core
- **Next.js 14** - Framework React com App Router
- **TypeScript** - Tipagem estática
- **React 18** - Biblioteca de interface

### Estilização
- **Tailwind CSS** - Framework CSS utilitário
- **@tailwindcss/forms** - Estilos para formulários
- **@tailwindcss/typography** - Estilos tipográficos
- **@headlessui/react** - Componentes acessíveis
- **@heroicons/react** - Ícones SVG
- **Framer Motion** - Animações

### PDF e Documentos
- **PDF.js (pdfjs-dist)** - Renderização e extração de texto
- **Coordinate-based highlighting** - Sistema de destaque sincronizado

### Utilitários
- **clsx** - Manipulação de classes CSS
- **lucide-react** - Ícones adicionais

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# .env.local
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### PDF.js Setup

O PDF.js é configurado para funcionar com Next.js 14:

1. **Worker Configuration**: Configurado em `next.config.js`
2. **Server Components**: Adicionado a `serverComponentsExternalPackages`
3. **Webpack Aliases**: Mapeamento correto dos workers
4. **Type Definitions**: Tipos TypeScript para PDF.js

### Tailwind CSS

Configuração customizada com:

- **Cores de risco**: Verde, Amarelo, Vermelho
- **Grid layouts**: Para viewer e painel de análise  
- **Animações**: Fade in, slide up, highlight
- **Componentes**: Cards, botões, indicators de risco
- **Utilitários**: Classes para PDF highlighting

## 📱 Funcionalidades

### Visualizador PDF
- Renderização de páginas com canvas
- Extração de camada de texto
- Sistema de coordenadas sincronizado
- Zoom e navegação
- Highlighting de cláusulas

### Análise de Contratos
- Upload de arquivos PDF
- Progresso em tempo real via WebSocket
- Análise cláusula por cláusula
- Classificação de riscos (Verde/Amarelo/Vermelho)
- Explicações em português
- Perguntas para negociação

### Interface Responsiva
- Design mobile-first
- Sidebar colapsável
- Layout adaptativo
- Touch-friendly em mobile

## 🔍 Desenvolvimento

### Componentes Principais

1. **PDFViewer** - Renderização e interação com PDF
2. **AnalysisPanel** - Exibição de análises
3. **ContractSummary** - Resumo executivo
4. **FileUpload** - Interface de upload

### Hooks Customizados

1. **useContractAnalysis** - Gerenciamento de análise
2. **usePDFViewer** - Controle do visualizador  
3. **useWebSocket** - Comunicação tempo real

### Tipos TypeScript

Todos os tipos estão definidos em `src/types/index.ts` e espelham os modelos Pydantic do backend.

## 🧪 Testes

```bash
# Verificação de tipos
npm run type-check

# Linting
npm run lint

# Build test
npm run build
```

## 🚀 Deploy

### Build de Produção

```bash
npm run build
npm run start
```

### Variáveis de Produção

```bash
NODE_ENV=production
NEXT_PUBLIC_APP_URL=https://yourdomain.com
NEXT_PUBLIC_BACKEND_URL=https://api.yourdomain.com
```

### Docker (quando disponível)

```bash
docker build -t lawyerless-frontend .
docker run -p 3000:3000 lawyerless-frontend
```

## 📚 Próximos Passos

1. **Implementar Componentes**:
   - PDFViewer com highlighting
   - AnalysisPanel com filtros
   - ContractSummary interativo

2. **Adicionar Funcionalidades**:
   - Sistema de autenticação
   - Histórico de análises
   - Exportação de relatórios
   - Comparação de contratos

3. **Melhorias de UX**:
   - Loading skeletons
   - Error boundaries
   - Offline support
   - PWA features

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

MIT License - veja o arquivo LICENSE para detalhes.