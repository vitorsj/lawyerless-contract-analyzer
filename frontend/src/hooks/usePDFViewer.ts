'use client'

import { useState, useCallback, useRef } from 'react'
import { validatePDFFile, fileToArrayBuffer } from '@/utils/pdfjs-config'
import type { UsePDFViewerReturn, TextFragment, BoundingBox } from '@/types'
import type { PDFDocumentProxy } from 'pdfjs-dist'

/**
 * Custom hook for managing PDF viewer state and operations.
 * 
 * Provides a unified interface for PDF document management,
 * including loading, navigation, text extraction, and error handling.
 */
export function usePDFViewer(): UsePDFViewerReturn {
  // Core document state
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [scale, setScale] = useState(1.5)
  
  // Loading and error states
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Text extraction cache
  const textFragmentsRef = useRef<Map<number, TextFragment[]>>(new Map())
  const [selectedText, setSelectedText] = useState<{
    text: string
    coordinates: BoundingBox
  } | null>(null)

  /**
   * Load PDF document from file or URL.
   */
  const loadDocument = useCallback(async (source: File | string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      // Validate file if it's a File object
      if (source instanceof File) {
        validatePDFFile(source)
      }

      // Dynamic import to avoid SSR issues
      const { loadPDFDocument } = await import('@/utils/pdfjs-config')
      
      let loadOptions
      if (typeof source === 'string') {
        loadOptions = { url: source }
      } else {
        const arrayBuffer = await fileToArrayBuffer(source)
        loadOptions = { data: new Uint8Array(arrayBuffer) }
      }

      const pdfDoc = await loadPDFDocument(loadOptions)
      
      setDocument(pdfDoc)
      setTotalPages(pdfDoc.numPages)
      setCurrentPage(1)
      
      // Clear previous state
      textFragmentsRef.current.clear()
      setSelectedText(null)
      setError(null)

    } catch (err: any) {
      console.error('PDF loading error:', err)
      
      let errorMessage = 'Erro ao carregar o documento PDF.'
      
      if (err.name === 'InvalidPDFException') {
        errorMessage = 'Arquivo PDF inválido ou corrompido.'
      } else if (err.name === 'MissingPDFException') {
        errorMessage = 'Arquivo PDF não encontrado.'
      } else if (err.name === 'UnexpectedResponseException') {
        errorMessage = 'Erro de rede ao carregar o PDF.'
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      setDocument(null)
      setTotalPages(0)
      
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Navigate to specific page.
   */
  const goToPage = useCallback((pageNumber: number) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber)
      setError(null) // Clear any page-specific errors
    } else {
      setError(`Página ${pageNumber} não existe. Documento tem ${totalPages} páginas.`)
    }
  }, [totalPages])

  /**
   * Navigate to previous page.
   */
  const goToPreviousPage = useCallback(() => {
    if (currentPage > 1) {
      goToPage(currentPage - 1)
    }
  }, [currentPage, goToPage])

  /**
   * Navigate to next page.
   */
  const goToNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      goToPage(currentPage + 1)
    }
  }, [currentPage, totalPages, goToPage])

  /**
   * Update scale/zoom level.
   */
  const updateScale = useCallback((newScale: number) => {
    const clampedScale = Math.max(0.5, Math.min(newScale, 3.0))
    setScale(clampedScale)
  }, [])

  /**
   * Zoom in by 20%.
   */
  const zoomIn = useCallback(() => {
    updateScale(scale * 1.2)
  }, [scale, updateScale])

  /**
   * Zoom out by 20%.
   */
  const zoomOut = useCallback(() => {
    updateScale(scale / 1.2)
  }, [scale, updateScale])

  /**
   * Reset zoom to default (150%).
   */
  const resetZoom = useCallback(() => {
    setScale(1.5)
  }, [])

  /**
   * Fit page to container width.
   */
  const fitToWidth = useCallback((containerWidth: number) => {
    if (!document) return
    
    // This is a simplified calculation
    // In production, you'd want to get actual page dimensions
    const estimatedPageWidth = 612 // Standard PDF page width in points
    const newScale = (containerWidth - 40) / estimatedPageWidth // 40px padding
    updateScale(newScale)
  }, [document, updateScale])

  /**
   * Cache text fragments for a page.
   */
  const cacheTextFragments = useCallback((pageNumber: number, fragments: TextFragment[]) => {
    textFragmentsRef.current.set(pageNumber, fragments)
  }, [])

  /**
   * Get cached text fragments for a page.
   */
  const getTextFragments = useCallback((pageNumber: number): TextFragment[] | undefined => {
    return textFragmentsRef.current.get(pageNumber)
  }, [])

  /**
   * Handle text selection.
   */
  const handleTextSelection = useCallback((text: string, coordinates: BoundingBox) => {
    setSelectedText({ text, coordinates })
  }, [])

  /**
   * Clear text selection.
   */
  const clearTextSelection = useCallback(() => {
    setSelectedText(null)
  }, [])

  /**
   * Search for text in the document (basic implementation).
   */
  const searchText = useCallback(async (query: string): Promise<Array<{
    pageNumber: number
    matches: Array<{ text: string; coordinates: BoundingBox }>
  }>> => {
    if (!document || !query.trim()) return []
    
    const results = []
    
    try {
      // Search through cached text fragments
      for (const [pageNumber, fragments] of textFragmentsRef.current) {
        const matches = fragments
          .filter(fragment => 
            fragment.text.toLowerCase().includes(query.toLowerCase())
          )
          .map(fragment => ({
            text: fragment.text,
            coordinates: fragment.coordinates
          }))
        
        if (matches.length > 0) {
          results.push({ pageNumber, matches })
        }
      }
      
      return results
      
    } catch (err) {
      console.error('Text search error:', err)
      return []
    }
  }, [document])

  /**
   * Get document information/metadata.
   */
  const getDocumentInfo = useCallback(async () => {
    if (!document) return null
    
    try {
      const { extractPDFMetadata } = await import('@/utils/pdfjs-config')
      return await extractPDFMetadata(document)
    } catch (err) {
      console.warn('Failed to extract document metadata:', err)
      return {
        pageCount: totalPages,
        title: undefined,
        author: undefined
      }
    }
  }, [document, totalPages])

  /**
   * Reset all state.
   */
  const reset = useCallback(() => {
    setDocument(null)
    setCurrentPage(1)
    setTotalPages(0)
    setScale(1.5)
    setIsLoading(false)
    setError(null)
    setSelectedText(null)
    textFragmentsRef.current.clear()
  }, [])

  /**
   * Get current page progress (percentage).
   */
  const getProgress = useCallback(() => {
    if (totalPages === 0) return 0
    return Math.round((currentPage / totalPages) * 100)
  }, [currentPage, totalPages])

  return {
    // Core state
    document,
    currentPage,
    totalPages,
    scale,
    isLoading,
    error,
    
    // Navigation
    loadDocument,
    goToPage,
    goToPreviousPage,
    goToNextPage,
    
    // Zoom controls
    setScale: updateScale,
    zoomIn,
    zoomOut,
    resetZoom,
    fitToWidth,
    
    // Text handling
    selectedText,
    handleTextSelection,
    clearTextSelection,
    cacheTextFragments,
    getTextFragments,
    searchText,
    
    // Utility functions
    getDocumentInfo,
    getProgress,
    reset
  }
}