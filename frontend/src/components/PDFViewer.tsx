'use client'

import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react'
import { 
  ChevronLeftIcon, 
  ChevronRightIcon, 
  MagnifyingGlassPlusIcon,
  MagnifyingGlassMinusIcon
} from '@heroicons/react/24/outline'
import { 
  loadPDFDocument, 
  renderPDFPage, 
  extractTextWithCoordinates,
  transformCoordinatesForDisplay,
  createHighlightOverlay,
  scrollToCoordinates,
  PDFError,
  PDFErrorType
} from '@/utils/pdfjs-config'
import type { 
  PDFViewerProps, 
  TextFragment, 
  HighlightConfig, 
  BoundingBox 
} from '@/types'
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist'
import clsx from 'clsx'

/**
 * PDFViewer component for rendering PDF documents with text highlighting.
 * 
 * Features:
 * - PDF rendering with PDF.js
 * - Text layer extraction with coordinates
 * - Coordinate-based highlighting for clauses
 * - Zoom controls and navigation
 * - Touch support for mobile
 * - Error handling and loading states
 */
export default function PDFViewer({
  file,
  url,
  highlights = [],
  onTextSelect,
  onPageChange,
  scale = 1.5,
  className
}: PDFViewerProps) {
  // Refs for DOM manipulation
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRefs = useRef<Map<number, HTMLCanvasElement>>(new Map())
  const overlayRefs = useRef<Map<number, HTMLDivElement>>(new Map())

  // State management
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [currentScale, setCurrentScale] = useState(scale)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [textFragments, setTextFragments] = useState<Map<number, TextFragment[]>>(new Map())
  const [isTextExtracting, setIsTextExtracting] = useState(false)

  // Loading state for individual pages
  const [pageLoadingStates, setPageLoadingStates] = useState<Map<number, boolean>>(new Map())

  /**
   * Load PDF document from file or URL
   */
  const loadDocument = useCallback(async (source: File | string) => {
    setIsLoading(true)
    setError(null)

    try {
      let loadOptions
      
      if (typeof source === 'string') {
        loadOptions = { url: source }
      } else {
        const arrayBuffer = await source.arrayBuffer()
        loadOptions = { data: new Uint8Array(arrayBuffer) }
      }

      const pdfDoc = await loadPDFDocument(loadOptions)
      setDocument(pdfDoc)
      setTotalPages(pdfDoc.numPages)
      setCurrentPage(1)

      // Clear previous text fragments
      setTextFragments(new Map())

    } catch (err) {
      console.error('PDF loading error:', err)
      if (err instanceof PDFError) {
        setError(err.message)
      } else {
        setError('Erro ao carregar o documento PDF. Verifique se o arquivo é válido.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Render a specific PDF page
   */
  const renderPage = useCallback(async (pageNum: number) => {
    if (!document) return

    const canvas = canvasRefs.current.get(pageNum)
    if (!canvas) return

    setPageLoadingStates(prev => new Map(prev).set(pageNum, true))

    try {
      const page = await document.getPage(pageNum)
      await renderPDFPage(page, canvas, { scale: currentScale })
      
      // Extract text fragments if not already cached
      if (!textFragments.has(pageNum)) {
        setIsTextExtracting(true)
        try {
          const fragments = await extractTextWithCoordinates(page, pageNum)
          setTextFragments(prev => new Map(prev).set(pageNum, fragments))
        } catch (textError) {
          console.warn(`Text extraction failed for page ${pageNum}:`, textError)
        } finally {
          setIsTextExtracting(false)
        }
      }

    } catch (err) {
      console.error(`Error rendering page ${pageNum}:`, err)
      setError(`Erro ao renderizar a página ${pageNum}`)
    } finally {
      setPageLoadingStates(prev => {
        const newStates = new Map(prev)
        newStates.delete(pageNum)
        return newStates
      })
    }
  }, [document, currentScale, textFragments])

  /**
   * Navigation functions
   */
  const goToPreviousPage = useCallback(() => {
    if (currentPage > 1) {
      const newPage = currentPage - 1
      setCurrentPage(newPage)
      onPageChange?.(newPage)
    }
  }, [currentPage, onPageChange])

  const goToNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      const newPage = currentPage + 1
      setCurrentPage(newPage)
      onPageChange?.(newPage)
    }
  }, [currentPage, totalPages, onPageChange])

  const goToPage = useCallback((pageNum: number) => {
    if (pageNum >= 1 && pageNum <= totalPages) {
      setCurrentPage(pageNum)
      onPageChange?.(pageNum)
    }
  }, [totalPages, onPageChange])

  /**
   * Zoom functions
   */
  const zoomIn = useCallback(() => {
    setCurrentScale(prev => Math.min(prev * 1.2, 3.0))
  }, [])

  const zoomOut = useCallback(() => {
    setCurrentScale(prev => Math.max(prev / 1.2, 0.5))
  }, [])

  const resetZoom = useCallback(() => {
    setCurrentScale(1.5)
  }, [])

  /**
   * Handle text selection
   */
  const handleTextSelection = useCallback(() => {
    if (!onTextSelect) return

    const selection = window.getSelection()
    if (!selection || selection.rangeCount === 0) return

    const selectedText = selection.toString().trim()
    if (!selectedText) return

    // Get selection coordinates (simplified - in production you'd want more precise coordinates)
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    
    if (containerRef.current) {
      const containerRect = containerRef.current.getBoundingClientRect()
      const coordinates: BoundingBox = {
        x0: rect.left - containerRect.left,
        x1: rect.right - containerRect.left,
        top: rect.top - containerRect.top,
        bottom: rect.bottom - containerRect.top,
        pageNumber: currentPage,
        pageHeight: rect.height,
        pageWidth: rect.width
      }

      onTextSelect(selectedText, coordinates)
    }
  }, [onTextSelect, currentPage])

  /**
   * Create highlight overlays for clauses
   */
  const createHighlights = useCallback(() => {
    // Clear existing highlights
    overlayRefs.current.forEach(overlay => {
      if (overlay.parentNode) {
        overlay.parentNode.removeChild(overlay)
      }
    })
    overlayRefs.current.clear()

    if (!containerRef.current || highlights.length === 0) return

    highlights.forEach((highlight, index) => {
      if (highlight.coordinates.pageNumber !== currentPage) return

      const transformedCoords = transformCoordinatesForDisplay(
        highlight.coordinates,
        currentScale,
        { x: 0, y: 0 }
      )

      // Create highlight overlay
      const overlay = createHighlightOverlay(
        transformedCoords,
        `pdf-highlight risk-${highlight.riskFlag.toLowerCase()} ${highlight.isActive ? 'active' : ''}`
      )

      // Add click handler
      overlay.addEventListener('click', () => {
        // Scroll to highlight if needed
        if (containerRef.current) {
          scrollToCoordinates(containerRef.current, transformedCoords)
        }
      })

      // Find appropriate parent container for the overlay
      const canvas = canvasRefs.current.get(currentPage)
      if (canvas && canvas.parentElement && containerRef.current) {
        // Position relative to canvas
        const canvasRect = canvas.getBoundingClientRect()
        const containerRect = containerRef.current.getBoundingClientRect()
        
        overlay.style.left = `${canvasRect.left - containerRect.left + transformedCoords.x0}px`
        overlay.style.top = `${canvasRect.top - containerRect.top + transformedCoords.top}px`
        
        containerRef.current.appendChild(overlay)
        overlayRefs.current.set(index, overlay)
      }
    })
  }, [highlights, currentPage, currentScale])

  /**
   * Load document when file or url changes
   */
  useEffect(() => {
    if (file) {
      loadDocument(file)
    } else if (url) {
      loadDocument(url)
    }
  }, [file, url, loadDocument])

  /**
   * Render current page when document or page changes
   */
  useEffect(() => {
    if (document && currentPage) {
      renderPage(currentPage)
    }
  }, [document, currentPage, renderPage])

  /**
   * Update highlights when they change
   */
  useEffect(() => {
    if (document) {
      // Small delay to ensure canvas is rendered
      const timer = setTimeout(createHighlights, 100)
      return () => clearTimeout(timer)
    }
  }, [createHighlights, document])

  /**
   * Keyboard navigation
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!document) return

      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault()
          goToPreviousPage()
          break
        case 'ArrowRight':
          event.preventDefault()
          goToNextPage()
          break
        case '+':
        case '=':
          event.preventDefault()
          zoomIn()
          break
        case '-':
          event.preventDefault()
          zoomOut()
          break
        case '0':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault()
            resetZoom()
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [document, goToPreviousPage, goToNextPage, zoomIn, zoomOut, resetZoom])

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      // Clean up highlights
      overlayRefs.current.forEach(overlay => {
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay)
        }
      })
      overlayRefs.current.clear()
      
      // Clean up canvas refs
      canvasRefs.current.clear()
    }
  }, [])

  // Error state
  if (error) {
    return (
      <div className={clsx('pdf-viewer flex items-center justify-center', className)}>
        <div className="text-center p-8">
          <svg 
            className="w-16 h-16 text-red-400 mx-auto mb-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.664-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" 
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Erro ao carregar PDF</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => setError(null)}
            className="btn btn-primary"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    )
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={clsx('pdf-viewer flex items-center justify-center', className)}>
        <div className="text-center p-8">
          <div className="loading-spinner w-8 h-8 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando documento...</p>
        </div>
      </div>
    )
  }

  // No document state
  if (!document) {
    return (
      <div className={clsx('pdf-viewer flex items-center justify-center bg-gray-50', className)}>
        <div className="text-center p-8">
          <svg 
            className="w-16 h-16 text-gray-400 mx-auto mb-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum documento carregado</h3>
          <p className="text-gray-600">Selecione um arquivo PDF para começar a análise.</p>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx('pdf-viewer flex flex-col h-full', className)}>
      {/* Toolbar */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between">
          {/* Navigation Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={goToPreviousPage}
              disabled={currentPage <= 1}
              className="btn btn-ghost p-2 disabled:opacity-50"
              title="Página anterior"
            >
              <ChevronLeftIcon className="w-5 h-5" />
            </button>
            
            <div className="flex items-center space-x-2">
              <input
                type="number"
                value={currentPage}
                onChange={(e) => {
                  const page = parseInt(e.target.value)
                  if (!isNaN(page)) {
                    goToPage(page)
                  }
                }}
                min={1}
                max={totalPages}
                className="w-16 px-2 py-1 text-center border rounded text-sm"
              />
              <span className="text-sm text-gray-500">de {totalPages}</span>
            </div>

            <button
              onClick={goToNextPage}
              disabled={currentPage >= totalPages}
              className="btn btn-ghost p-2 disabled:opacity-50"
              title="Próxima página"
            >
              <ChevronRightIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={zoomOut}
              className="btn btn-ghost p-2"
              title="Diminuir zoom"
            >
              <MagnifyingGlassMinusIcon className="w-5 h-5" />
            </button>
            
            <button
              onClick={resetZoom}
              className="btn btn-ghost px-3 py-1 text-sm"
              title="Resetar zoom"
            >
              {Math.round(currentScale * 100)}%
            </button>
            
            <button
              onClick={zoomIn}
              className="btn btn-ghost p-2"
              title="Aumentar zoom"
            >
              <MagnifyingGlassPlusIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Status Indicators */}
          <div className="flex items-center space-x-4">
            {isTextExtracting && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <div className="loading-spinner w-4 h-4"></div>
                <span>Extraindo texto...</span>
              </div>
            )}
            
            {highlights.length > 0 && (
              <div className="text-sm text-gray-600">
                {highlights.filter(h => h.coordinates.pageNumber === currentPage).length} destaques
              </div>
            )}
          </div>
        </div>
      </div>

      {/* PDF Content */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto bg-gray-100 p-4"
        onMouseUp={handleTextSelection}
      >
        <div className="flex justify-center">
          <div className="relative">
            {pageLoadingStates.get(currentPage) && (
              <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-20">
                <div className="loading-spinner w-8 h-8"></div>
              </div>
            )}
            
            <canvas
              ref={(canvas) => {
                if (canvas) {
                  canvasRefs.current.set(currentPage, canvas)
                }
              }}
              className="pdf-page shadow-lg"
              style={{ 
                maxWidth: '100%',
                height: 'auto'
              }}
            />
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="flex-shrink-0 bg-gray-50 border-t border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div>
            Página {currentPage} de {totalPages}
          </div>
          <div className="flex items-center space-x-4">
            {textFragments.has(currentPage) && (
              <span>{textFragments.get(currentPage)?.length || 0} fragmentos de texto</span>
            )}
            <span>Zoom: {Math.round(currentScale * 100)}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}