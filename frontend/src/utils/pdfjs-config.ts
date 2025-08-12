/**
 * PDF.js configuration and utilities for Lawyerless frontend.
 * 
 * This module handles PDF.js setup, worker configuration, text layer extraction,
 * and coordinate transformation for web display with highlighting synchronization.
 */

import { GlobalWorkerOptions, getDocument } from 'pdfjs-dist'
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist'
import type { TextContent, TextItem } from 'pdfjs-dist/types/src/display/api'

// Configure PDF.js worker
// In development, use the local worker file
// In production, use the CDN version or built worker
if (typeof window !== 'undefined') {
  GlobalWorkerOptions.workerSrc = process.env.NODE_ENV === 'development'
    ? '/pdf-worker.js'
    : `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.js`
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
 * Text fragment with position information.
 */
export interface TextFragment {
  text: string
  coordinates: BoundingBox
  fontSize?: number
  fontName?: string
}

/**
 * PDF page rendering options.
 */
export interface RenderOptions {
  scale: number
  rotation?: number
  viewport?: any
}

/**
 * PDF document metadata.
 */
export interface PDFMetadata {
  title?: string
  author?: string
  subject?: string
  creator?: string
  producer?: string
  creationDate?: Date
  modificationDate?: Date
  pageCount: number
}

/**
 * Configuration options for PDF loading.
 */
export interface PDFLoadOptions {
  url?: string
  data?: ArrayBuffer | Uint8Array
  withCredentials?: boolean
  password?: string
}

/**
 * Error types for PDF processing.
 */
export enum PDFErrorType {
  LOAD_FAILED = 'LOAD_FAILED',
  PARSE_FAILED = 'PARSE_FAILED',
  RENDER_FAILED = 'RENDER_FAILED',
  TEXT_EXTRACTION_FAILED = 'TEXT_EXTRACTION_FAILED',
  INVALID_PDF = 'INVALID_PDF'
}

/**
 * PDF processing error class.
 */
export class PDFError extends Error {
  type: PDFErrorType
  originalError?: Error

  constructor(type: PDFErrorType, message: string, originalError?: Error) {
    super(message)
    this.name = 'PDFError'
    this.type = type
    this.originalError = originalError
  }
}

/**
 * Load PDF document from URL or data.
 */
export async function loadPDFDocument(options: PDFLoadOptions): Promise<PDFDocumentProxy> {
  try {
    const loadingTask = getDocument({
      url: options.url,
      data: options.data,
      withCredentials: options.withCredentials || false,
      password: options.password,
      // Disable streaming for better compatibility
      disableStream: true,
      // Disable auto-fetch for better control
      disableAutoFetch: true,
      // Use system fonts when possible
      useSystemFonts: true
    })

    // Add progress callback if needed
    loadingTask.onProgress = (progress: { loaded: number; total: number }) => {
      console.log(`PDF loading progress: ${(progress.loaded / progress.total * 100).toFixed(1)}%`)
    }

    const document = await loadingTask.promise
    return document

  } catch (error) {
    console.error('PDF loading failed:', error)
    throw new PDFError(
      PDFErrorType.LOAD_FAILED,
      'Falha ao carregar o documento PDF',
      error as Error
    )
  }
}

/**
 * Extract metadata from PDF document.
 */
export async function extractPDFMetadata(document: PDFDocumentProxy): Promise<PDFMetadata> {
  try {
    const metadata = await document.getMetadata()
    const info = metadata.info as any
    
    return {
      title: info?.Title || undefined,
      author: info?.Author || undefined,
      subject: info?.Subject || undefined,
      creator: info?.Creator || undefined,
      producer: info?.Producer || undefined,
      creationDate: info?.CreationDate || undefined,
      modificationDate: info?.ModDate || undefined,
      pageCount: document.numPages
    }

  } catch (error) {
    console.warn('Failed to extract PDF metadata:', error)
    return {
      pageCount: document.numPages
    }
  }
}

/**
 * Render PDF page to canvas.
 */
export async function renderPDFPage(
  page: PDFPageProxy,
  canvas: HTMLCanvasElement,
  options: RenderOptions = { scale: 1 }
): Promise<void> {
  try {
    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('Canvas context not available')
    }

    const viewport = page.getViewport({ 
      scale: options.scale,
      rotation: options.rotation || 0
    })

    canvas.height = viewport.height
    canvas.width = viewport.width

    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }

    await page.render(renderContext).promise

  } catch (error) {
    console.error('PDF page rendering failed:', error)
    throw new PDFError(
      PDFErrorType.RENDER_FAILED,
      'Falha ao renderizar a página do PDF',
      error as Error
    )
  }
}

/**
 * Extract text content with coordinates from PDF page.
 */
export async function extractTextWithCoordinates(
  page: PDFPageProxy,
  pageNumber: number
): Promise<TextFragment[]> {
  try {
    const textContent: TextContent = await page.getTextContent()

    const viewport = page.getViewport({ scale: 1 })
    const pageHeight = viewport.height
    const pageWidth = viewport.width

    const textFragments: TextFragment[] = []

    // Process text items
    for (const item of textContent.items) {
      // Type guard for TextItem (skip TextMarkedContent)
      if ('transform' in item && 'str' in item) {
        const textItem = item as TextItem

        // Skip empty text
        if (!textItem.str.trim()) {
          continue
        }

        // Extract coordinates from transform matrix
        // PDF.js transform: [scaleX, skewY, skewX, scaleY, translateX, translateY]
        const [, , , , x, y] = textItem.transform
        
        // Estimate text dimensions
        const fontSize = Math.abs(textItem.transform[3]) // scaleY gives font size
        const textWidth = textItem.width || (textItem.str.length * fontSize * 0.6)
        
        // Transform coordinates from PDF space to web space
        // PDF uses bottom-left origin, web uses top-left origin
        const webY = pageHeight - y
        const webBottom = webY - fontSize

        textFragments.push({
          text: textItem.str,
          coordinates: {
            x0: x,
            x1: x + textWidth,
            top: webBottom,
            bottom: webY,
            pageNumber,
            pageHeight,
            pageWidth
          },
          fontSize: fontSize,
          fontName: textItem.fontName
        })
      }
    }

    return textFragments

  } catch (error) {
    console.error('Text extraction failed:', error)
    throw new PDFError(
      PDFErrorType.TEXT_EXTRACTION_FAILED,
      'Falha ao extrair texto do PDF',
      error as Error
    )
  }
}

/**
 * Group text fragments into lines based on vertical position.
 */
export function groupTextIntoLines(fragments: TextFragment[], tolerance: number = 2): TextFragment[][] {
  if (fragments.length === 0) return []

  // Sort fragments by vertical position (top to bottom)
  const sorted = [...fragments].sort((a, b) => a.coordinates.top - b.coordinates.top)

  const lines: TextFragment[][] = []
  let currentLine: TextFragment[] = [sorted[0]]

  for (let i = 1; i < sorted.length; i++) {
    const current = sorted[i]
    const lastInLine = currentLine[currentLine.length - 1]

    // Check if fragments are on the same line (similar vertical position)
    const topDiff = Math.abs(current.coordinates.top - lastInLine.coordinates.top)
    
    if (topDiff <= tolerance) {
      // Add to current line
      currentLine.push(current)
    } else {
      // Start new line
      lines.push(currentLine)
      currentLine = [current]
    }
  }

  // Add the last line
  if (currentLine.length > 0) {
    lines.push(currentLine)
  }

  // Sort fragments within each line by horizontal position (left to right)
  return lines.map(line => 
    line.sort((a, b) => a.coordinates.x0 - b.coordinates.x0)
  )
}

/**
 * Transform PDF coordinates to screen coordinates for highlighting.
 */
export function transformCoordinatesForDisplay(
  pdfCoords: BoundingBox,
  scale: number,
  containerOffset: { x: number, y: number } = { x: 0, y: 0 }
): BoundingBox {
  return {
    x0: (pdfCoords.x0 * scale) + containerOffset.x,
    x1: (pdfCoords.x1 * scale) + containerOffset.x,
    top: (pdfCoords.top * scale) + containerOffset.y,
    bottom: (pdfCoords.bottom * scale) + containerOffset.y,
    pageNumber: pdfCoords.pageNumber,
    pageHeight: pdfCoords.pageHeight * scale,
    pageWidth: (pdfCoords.pageWidth || 0) * scale
  }
}

/**
 * Find text fragments that intersect with given coordinates.
 */
export function findTextAtCoordinates(
  fragments: TextFragment[],
  x: number,
  y: number,
  tolerance: number = 5
): TextFragment[] {
  return fragments.filter(fragment => {
    const coords = fragment.coordinates
    return (
      x >= coords.x0 - tolerance &&
      x <= coords.x1 + tolerance &&
      y >= coords.top - tolerance &&
      y <= coords.bottom + tolerance
    )
  })
}

/**
 * Create highlight overlay element for text coordinates.
 */
export function createHighlightOverlay(
  coordinates: BoundingBox,
  className: string = 'pdf-highlight'
): HTMLDivElement {
  const overlay = document.createElement('div')
  overlay.className = className
  overlay.style.position = 'absolute'
  overlay.style.left = `${coordinates.x0}px`
  overlay.style.top = `${coordinates.top}px`
  overlay.style.width = `${coordinates.x1 - coordinates.x0}px`
  overlay.style.height = `${coordinates.bottom - coordinates.top}px`
  overlay.style.backgroundColor = 'rgba(59, 130, 246, 0.3)'
  overlay.style.border = '1px solid rgb(59, 130, 246)'
  overlay.style.borderRadius = '2px'
  overlay.style.pointerEvents = 'none'
  overlay.style.zIndex = '10'
  
  return overlay
}

/**
 * Scroll to coordinates within a container.
 */
export function scrollToCoordinates(
  container: HTMLElement,
  coordinates: BoundingBox,
  offset: { x?: number, y?: number } = {}
): void {
  const scrollX = coordinates.x0 - (offset.x || 50)
  const scrollY = coordinates.top - (offset.y || 50)

  container.scrollTo({
    left: Math.max(0, scrollX),
    top: Math.max(0, scrollY),
    behavior: 'smooth'
  })
}

/**
 * Validate PDF file before processing.
 */
export function validatePDFFile(file: File): boolean {
  // Check file type
  if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
    throw new PDFError(
      PDFErrorType.INVALID_PDF,
      'Arquivo deve ser um PDF válido'
    )
  }

  // Check file size (50MB limit)
  const MAX_SIZE = 50 * 1024 * 1024 // 50MB
  if (file.size > MAX_SIZE) {
    throw new PDFError(
      PDFErrorType.INVALID_PDF,
      `Arquivo muito grande. Tamanho máximo: ${MAX_SIZE / (1024 * 1024)}MB`
    )
  }

  return true
}

/**
 * Convert File to ArrayBuffer for PDF.js.
 */
export async function fileToArrayBuffer(file: File): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = () => {
      if (reader.result instanceof ArrayBuffer) {
        resolve(reader.result)
      } else {
        reject(new Error('Failed to read file as ArrayBuffer'))
      }
    }
    
    reader.onerror = () => {
      reject(new Error('File reading failed'))
    }
    
    reader.readAsArrayBuffer(file)
  })
}