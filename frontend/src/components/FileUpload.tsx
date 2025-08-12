'use client'

import React, { useState, useRef, useCallback } from 'react'
import {
  CloudArrowUpIcon,
  DocumentIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { validatePDFFile } from '@/utils/pdfjs-config'
import { UploadProgress, UploadState } from '@/types'
import clsx from 'clsx'

export interface FileUploadProps {
  onFileSelect: (file: File) => void
  onFileRemove?: () => void
  uploadProgress?: UploadProgress | null
  disabled?: boolean
  className?: string
  accept?: string
  maxSize?: number
  selectedFile?: File | null
}

/**
 * FileUpload component for PDF contract uploads.
 * 
 * Features:
 * - Drag and drop interface
 * - File validation (PDF only, size limits)
 * - Upload progress tracking
 * - Error handling with Portuguese messages
 * - Visual feedback for different states
 * - Touch-friendly mobile design
 */
export default function FileUpload({
  onFileSelect,
  onFileRemove,
  uploadProgress,
  disabled = false,
  className,
  accept = '.pdf,application/pdf',
  maxSize = 50 * 1024 * 1024, // 50MB default
  selectedFile
}: FileUploadProps) {
  // Local state
  const [uploadState, setUploadState] = useState<UploadState>({
    isDragOver: false,
    isUploading: false,
    selectedFile: selectedFile || null,
    uploadProgress: uploadProgress || null
  })
  const [error, setError] = useState<string | null>(null)
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropZoneRef = useRef<HTMLDivElement>(null)

  /**
   * Handle file selection from input or drag-drop
   */
  const handleFileSelection = useCallback(async (file: File) => {
    setError(null)
    
    try {
      // Validate file
      validatePDFFile(file)
      
      // Additional size check
      if (file.size > maxSize) {
        throw new Error(`Arquivo muito grande. Tamanho máximo: ${Math.round(maxSize / (1024 * 1024))}MB`)
      }

      // Update state
      setUploadState(prev => ({
        ...prev,
        selectedFile: file,
        uploadProgress: null
      }))

      // Notify parent component
      onFileSelect(file)

    } catch (err: any) {
      console.error('File validation error:', err)
      setError(err.message || 'Erro ao validar o arquivo')
      
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }, [onFileSelect, maxSize])

  /**
   * Handle file removal
   */
  const handleFileRemove = useCallback(() => {
    setUploadState(prev => ({
      ...prev,
      selectedFile: null,
      uploadProgress: null
    }))
    setError(null)
    
    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    
    onFileRemove?.()
  }, [onFileRemove])

  /**
   * Handle drag over
   */
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!disabled) {
      setUploadState(prev => ({ ...prev, isDragOver: true }))
    }
  }, [disabled])

  /**
   * Handle drag leave
   */
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Only set isDragOver to false if we're leaving the drop zone entirely
    if (dropZoneRef.current && !dropZoneRef.current.contains(e.relatedTarget as Node)) {
      setUploadState(prev => ({ ...prev, isDragOver: false }))
    }
  }, [])

  /**
   * Handle drop
   */
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    setUploadState(prev => ({ ...prev, isDragOver: false }))
    
    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelection(files[0])
    }
  }, [disabled, handleFileSelection])

  /**
   * Handle file input change
   */
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelection(files[0])
    }
  }, [handleFileSelection])

  /**
   * Trigger file input click
   */
  const triggerFileSelect = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click()
    }
  }, [disabled])

  /**
   * Format file size
   */
  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }, [])

  // Determine current state
  const isUploading = uploadProgress?.status === 'uploading' || uploadProgress?.status === 'processing'
  const isCompleted = uploadProgress?.status === 'completed'
  const hasError = uploadProgress?.status === 'error' || !!error
  const currentFile = uploadState.selectedFile || selectedFile

  return (
    <div className={clsx('w-full', className)}>
      {/* Main Upload Area */}
      <div
        ref={dropZoneRef}
        className={clsx(
          'dropzone relative border-2 border-dashed rounded-lg transition-all duration-200',
          {
            // Default state
            'border-gray-300 hover:border-gray-400': !uploadState.isDragOver && !disabled && !hasError && !isCompleted,
            
            // Drag over state
            'border-primary-500 bg-primary-50': uploadState.isDragOver,
            
            // Disabled state
            'border-gray-200 bg-gray-50 cursor-not-allowed': disabled,
            
            // Error state
            'border-red-300 bg-red-50': hasError,
            
            // Success state
            'border-green-300 bg-green-50': isCompleted,
            
            // With file selected
            'border-primary-300 bg-primary-50/50': currentFile && !hasError && !isCompleted
          }
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInputChange}
          className="hidden"
          disabled={disabled}
        />

        {/* Upload content */}
        <div className="p-8">
          {/* No file selected state */}
          {!currentFile && !isUploading && (
            <div className="text-center">
              <CloudArrowUpIcon className={clsx(
                'mx-auto mb-4',
                hasError ? 'w-12 h-12 text-red-400' : 'w-16 h-16 text-gray-400'
              )} />
              
              <div className="mb-4">
                <h3 className={clsx(
                  'text-lg font-medium mb-2',
                  hasError ? 'text-red-900' : 'text-gray-900'
                )}>
                  {hasError ? 'Erro no arquivo' : 'Selecione seu contrato'}
                </h3>
                
                <p className={clsx(
                  'text-sm mb-4',
                  hasError ? 'text-red-600' : 'text-gray-600'
                )}>
                  {hasError 
                    ? (error || 'Erro ao processar o arquivo') 
                    : 'Arraste e solte aqui ou clique para selecionar'
                  }
                </p>
              </div>

              <button
                onClick={triggerFileSelect}
                disabled={disabled}
                className={clsx(
                  'btn px-6 py-3 mb-4',
                  hasError ? 'btn-outline border-red-300 text-red-700 hover:bg-red-50' : 'btn-primary',
                  disabled && 'opacity-50 cursor-not-allowed'
                )}
              >
                {hasError ? 'Tentar Novamente' : 'Selecionar Arquivo'}
              </button>

              <div className="text-xs text-gray-500 space-y-1">
                <p>Tipos aceitos: PDF</p>
                <p>Tamanho máximo: {Math.round(maxSize / (1024 * 1024))}MB</p>
              </div>
            </div>
          )}

          {/* File selected state */}
          {currentFile && !isUploading && !isCompleted && (
            <div className="text-center">
              <DocumentIcon className="w-12 h-12 text-blue-600 mx-auto mb-4" />
              
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-1">
                  Arquivo selecionado
                </h3>
                <p className="text-sm text-gray-600 font-medium">
                  {currentFile.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(currentFile.size)}
                </p>
              </div>

              <div className="flex items-center justify-center space-x-3">
                <button
                  onClick={handleFileRemove}
                  className="btn btn-ghost text-sm px-4 py-2"
                  disabled={disabled}
                >
                  Remover
                </button>
                <button
                  onClick={triggerFileSelect}
                  className="btn btn-outline text-sm px-4 py-2"
                  disabled={disabled}
                >
                  Alterar
                </button>
              </div>
            </div>
          )}

          {/* Upload progress state */}
          {isUploading && uploadProgress && (
            <div className="text-center">
              <div className="loading-spinner w-8 h-8 mx-auto mb-4"></div>
              
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {uploadProgress.status === 'uploading' ? 'Enviando arquivo...' : 'Processando...'}
                </h3>
                
                {uploadProgress.message && (
                  <p className="text-sm text-gray-600 mb-3">
                    {uploadProgress.message}
                  </p>
                )}

                {/* Progress bar */}
                <div className="progress-bar mb-2">
                  <div 
                    className="progress-fill"
                    style={{ width: `${uploadProgress.percentage}%` }}
                  />
                </div>
                
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{uploadProgress.percentage}% concluído</span>
                  {uploadProgress.loaded && uploadProgress.total && (
                    <span>
                      {formatFileSize(uploadProgress.loaded)} / {formatFileSize(uploadProgress.total)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Upload completed state */}
          {isCompleted && (
            <div className="text-center">
              <CheckCircleIcon className="w-12 h-12 text-green-600 mx-auto mb-4" />
              
              <div className="mb-4">
                <h3 className="text-lg font-medium text-green-900 mb-2">
                  Arquivo processado com sucesso!
                </h3>
                <p className="text-sm text-green-600">
                  {uploadProgress?.message || 'Análise concluída'}
                </p>
              </div>

              {currentFile && (
                <div className="text-xs text-gray-600 mb-4">
                  <p className="font-medium">{currentFile.name}</p>
                  <p>{formatFileSize(currentFile.size)}</p>
                </div>
              )}

              <button
                onClick={triggerFileSelect}
                className="btn btn-outline text-sm px-4 py-2"
                disabled={disabled}
              >
                Analisar outro arquivo
              </button>
            </div>
          )}
        </div>

        {/* Upload status overlay for drag-over */}
        {uploadState.isDragOver && (
          <div className="absolute inset-0 bg-primary-500 bg-opacity-20 border-2 border-primary-500 rounded-lg flex items-center justify-center">
            <div className="text-center text-primary-700">
              <CloudArrowUpIcon className="w-12 h-12 mx-auto mb-2" />
              <p className="text-lg font-medium">Solte o arquivo aqui</p>
            </div>
          </div>
        )}
      </div>

      {/* Error message display */}
      {hasError && error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start space-x-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-red-900">Erro no arquivo</h4>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Upload tips */}
      {!currentFile && !error && (
        <div className="mt-4 text-xs text-gray-500 space-y-1">
          <p><strong>Tipos de contratos suportados:</strong></p>
          <p>• SAFE (Simple Agreement for Future Equity)</p>
          <p>• Convertible Notes</p>
          <p>• Term Sheets</p>
          <p>• Acordos de Acionistas</p>
          <p>• Side Letters</p>
        </div>
      )}
    </div>
  )
}