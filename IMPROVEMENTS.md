# Lawyerless - Improvements & Feature Requests

USE Agrosmart.pdf as an example contract for every problem

## 🚀 High Priority Improvements

### 1. Results
"Análise por Cláusula
Documento Completo
AMARELO
--- Página 1 --- Clicksign c56c3a57-da0f-4df6-bb19-8d0790b2231e Contrato, incluindo, sem limitação, atos societários que viabilizem as emissões de ações, registros necessários para conferir plena efi...
Resumo:
Análise não disponível devido a erro técnico.

Explicação:
Esta cláusula requer revisão manual devido a falha na análise automática.

Motivo da classificação:
Análise automática indisponível - requer revisão manual"

Analisys not available. There's problably an error here. There should be a Summary, an Explanation, and a reason for the each flag. But it all returns the same thing.

probably:  GET /site.webmanifest 404 in 414ms

### 2. Hardcoded
A lot of things are hardcoded. I want the LLM to decide if it is a red flag, yellow flag, or green flag, for example. Give the LLM more autonomy, it should define the meaning of each clause, it should not be hardcoded. 

### 3. Clause Numbering Enhancement
- **Issue**: Current system needs better hierarchical numbering (1, 1.1, 1.2, 2, 2.1, etc.)
- **Impact**: Critical for proper Brazilian contract structure
- **Effort**: Medium (2-3 days)
- **Status**: Identified
- **Files to modify**: 
  - `backend/app/services/clause_segmenter.py`
  - Update Brazilian patterns regex
  - Add hierarchical relationship tracking

### 4. Test Suite Fixes
- **Issue**: 8 failing tests in clause segmentation
- **Impact**: Medium (affects reliability)
- **Effort**: Low (1-2 days)
- **Status**: In Progress
- **Files**: `tests/test_clause_segmenter.py`

### 5. End-to-End Testing
- **Issue**: Need full PDF upload → analysis → results workflow testing
- **Impact**: High (production readiness)
- **Effort**: Medium (2-3 days)
- **Status**: Pending
