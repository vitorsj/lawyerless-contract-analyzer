/**
 * TypeScript type definitions for Lawyerless frontend.
 * 
 * These types mirror the backend Pydantic models for consistent data handling
 * between frontend and backend services.
 */

/**
 * Risk flag levels for clause analysis.
 */
export enum RiskFlag {
  VERDE = "Verde",
  AMARELO = "Amarelo", 
  VERMELHO = "Vermelho"
}

/**
 * Contract types supported by the system.
 */
export enum ContractType {
  SAFE = "SAFE",
  CONVERTIBLE_NOTE = "Convertible Note",
  TERM_SHEET = "Term Sheet", 
  SHAREHOLDER_AGREEMENT = "Shareholder Agreement",
  SIDE_LETTER = "Side Letter",
  OTHER = "Other"
}

/**
 * Bounding box coordinates for text highlighting.
 */
export interface BoundingBox {
  x0: number
  x1: number
  top: number
  bottom: number
  pageNumber: number
  pageHeight: number
  pageWidth?: number
}

/**
 * Individual clause analysis result.
 */
export interface ClauseAnalysis {
  clauseId: string
  originalText: string
  summary: string
  riskFlag: RiskFlag
  explanation: string
  negotiationQuestions: string[]
  coordinates: BoundingBox
}

/**
 * Complete contract analysis response.
 */
export interface ContractAnalysis {
  contractId: string
  filename: string
  contractType: ContractType
  totalClauses: number
  analyzedClauses: ClauseAnalysis[]
  overallRisk: RiskFlag
  summary: ContractSummary
  processingTime: number
  createdAt: string
}

/**
 * Contract summary (ficha do contrato).
 */
export interface ContractSummary {
  parties: string[]
  mainPurpose: string
  keyTerms: Record<string, string>
  importantDates: Record<string, string>
  financialTerms: Record<string, string>
  governingLaw: string
  mainRisks: string[]
  recommendations: string[]
}

/**
 * File upload progress tracking.
 */
export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  message?: string
}

/**
 * Analysis progress tracking.
 */
export interface AnalysisProgress {
  stage: 'upload' | 'processing' | 'segmenting' | 'analyzing' | 'completed' | 'error'
  currentClause?: number
  totalClauses?: number
  message: string
  percentage: number
}

/**
 * API response wrapper.
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

/**
 * Error response structure.
 */
export interface ApiError {
  detail: string
  type?: string
  code?: string
}

/**
 * PDF document metadata.
 */
export interface PDFDocumentInfo {
  filename: string
  size: number
  pageCount: number
  title?: string
  author?: string
  creationDate?: string
  modificationDate?: string
}

/**
 * Text fragment with coordinates for highlighting.
 */
export interface TextFragment {
  text: string
  coordinates: BoundingBox
  fontSize?: number
  fontName?: string
}

/**
 * PDF rendering options.
 */
export interface PDFRenderOptions {
  scale: number
  rotation?: number
}

/**
 * Highlight overlay configuration.
 */
export interface HighlightConfig {
  clauseId: string
  coordinates: BoundingBox
  riskFlag: RiskFlag
  isActive?: boolean
}

/**
 * WebSocket message types for real-time analysis updates.
 */
export interface WebSocketMessage {
  type: 'progress' | 'error' | 'completed'
  contractId: string
  data: AnalysisProgress | ApiError | ContractAnalysis
}

/**
 * Component props for PDF viewer.
 */
export interface PDFViewerProps {
  file?: File
  url?: string
  highlights?: HighlightConfig[]
  onTextSelect?: (text: string, coordinates: BoundingBox) => void
  onPageChange?: (pageNumber: number) => void
  scale?: number
  className?: string
}

/**
 * Component props for analysis panel.
 */
export interface AnalysisPanelProps {
  analysis: ContractAnalysis
  selectedClause?: string
  onClauseSelect?: (clauseId: string) => void
  onHighlightClause?: (clauseId: string) => void
  isLoading?: boolean
  className?: string
}

/**
 * Component props for contract summary card.
 */
export interface SummaryCardProps {
  summary: ContractSummary
  overallRisk: RiskFlag
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  className?: string
}

/**
 * Hook return types.
 */
export interface UseContractAnalysisReturn {
  analysis: ContractAnalysis | null
  isLoading: boolean
  error: string | null
  progress: AnalysisProgress | null
  
  // Actions
  analyzeContract: (
    file: File, 
    contractType?: ContractType, 
    options?: {
      priority?: 'normal' | 'high'
      includeNegotiationTips?: boolean
    }
  ) => Promise<void>
  reset: () => void
  retryAnalysis: () => void
  
  // Utilities
  getCurrentContractId: () => string | null
  getProgressPercentage: () => number
  isComplete: () => boolean
  checkAnalysisStatus: (contractId: string) => Promise<{
    status: 'pending' | 'processing' | 'completed' | 'error'
    progress?: number
    message?: string
  }>
  retrieveAnalysis: (contractId: string) => Promise<ContractAnalysis | null>
}

export interface UsePDFViewerReturn {
  document: any | null
  currentPage: number
  totalPages: number
  scale: number
  isLoading: boolean
  error: string | null
  selectedText: { text: string; coordinates: BoundingBox } | null
  
  // Navigation
  loadDocument: (file: File | string) => Promise<void>
  goToPage: (pageNumber: number) => void
  goToPreviousPage: () => void
  goToNextPage: () => void
  
  // Zoom controls
  setScale: (scale: number) => void
  zoomIn: () => void
  zoomOut: () => void
  resetZoom: () => void
  fitToWidth: (containerWidth: number) => void
  
  // Text handling
  handleTextSelection: (text: string, coordinates: BoundingBox) => void
  clearTextSelection: () => void
  cacheTextFragments: (pageNumber: number, fragments: TextFragment[]) => void
  getTextFragments: (pageNumber: number) => TextFragment[] | undefined
  searchText: (query: string) => Promise<Array<{
    pageNumber: number
    matches: Array<{ text: string; coordinates: BoundingBox }>
  }>>
  
  // Utility functions
  getDocumentInfo: () => Promise<any>
  getProgress: () => number
  reset: () => void
}

/**
 * Form data interfaces.
 */
export interface AnalysisFormData {
  file: File
  contractType?: ContractType
  priority?: 'normal' | 'high'
  includeNegotiationTips?: boolean
}

/**
 * Settings and preferences.
 */
export interface UserPreferences {
  language: 'pt-BR' | 'en-US'
  theme: 'light' | 'dark' | 'auto'
  defaultScale: number
  showCoordinates: boolean
  highlightAllClauses: boolean
  autoScrollToClause: boolean
}

/**
 * Navigation and routing.
 */
export interface RouteParams {
  contractId?: string
  analysisId?: string
}

/**
 * Component state interfaces.
 */
export interface ViewerState {
  selectedClause: string | null
  highlightedClauses: string[]
  sidebarCollapsed: boolean
  summaryCollapsed: boolean
}

export interface UploadState {
  isDragOver: boolean
  isUploading: boolean
  selectedFile: File | null
  uploadProgress: UploadProgress | null
}

/**
 * Utility type for partial updates.
 */
export type PartialUpdate<T> = Partial<T>

/**
 * Generic loading state.
 */
export interface LoadingState {
  isLoading: boolean
  error: string | null
  data: any | null
}

/**
 * Export commonly used type combinations.
 */
export type ClauseWithHighlight = ClauseAnalysis & {
  isHighlighted?: boolean
  isSelected?: boolean
}

export type ContractWithProgress = {
  analysis: ContractAnalysis | null
  progress: AnalysisProgress | null
  isComplete: boolean
}