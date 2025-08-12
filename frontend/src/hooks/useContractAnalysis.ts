'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import {
  ContractAnalysis,
  AnalysisProgress,
  UseContractAnalysisReturn,
  ApiResponse,
  WebSocketMessage,
  ContractType
} from '@/types'

/**
 * Custom hook for managing contract analysis workflow.
 * 
 * Handles the complete analysis process including:
 * - File upload to backend
 * - WebSocket connection for real-time progress
 * - Analysis result retrieval
 * - Error handling and retry logic
 * - Progress tracking and status updates
 */
export function useContractAnalysis(): UseContractAnalysisReturn {
  // Core state
  const [analysis, setAnalysis] = useState<ContractAnalysis | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<AnalysisProgress | null>(null)

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null)
  const currentContractIdRef = useRef<string | null>(null)
  const retryCountRef = useRef(0)
  const maxRetries = 3

  /**
   * Get backend API URL
   */
  const getApiUrl = useCallback((path: string): string => {
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    return `${baseUrl}/api/v1${path}`
  }, [])

  /**
   * Get WebSocket URL
   */
  const getWsUrl = useCallback((contractId: string): string => {
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    const wsUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://')
    return `${wsUrl}/api/v1/contracts/${contractId}/ws`
  }, [])

  /**
   * Setup WebSocket connection for real-time updates
   */
  const setupWebSocket = useCallback((contractId: string) => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    try {
      const ws = new WebSocket(getWsUrl(contractId))
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected for contract:', contractId)
        setError(null)
        retryCountRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          if (message.contractId !== contractId) {
            return // Ignore messages for different contracts
          }

          switch (message.type) {
            case 'progress':
              const progressData = message.data as AnalysisProgress
              setProgress(progressData)
              
              // Update loading state based on progress stage
              if (progressData.stage === 'completed') {
                setIsLoading(false)
              }
              break

            case 'completed':
              const analysisData = message.data as ContractAnalysis
              setAnalysis(analysisData)
              setProgress({
                stage: 'completed',
                percentage: 100,
                message: 'Análise concluída com sucesso!'
              })
              setIsLoading(false)
              setError(null)
              break

            case 'error':
              const errorData = message.data as any
              setError(errorData.detail || 'Erro durante a análise')
              setProgress({
                stage: 'error',
                percentage: 0,
                message: errorData.detail || 'Erro durante a análise'
              })
              setIsLoading(false)
              break
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('Erro de conexão com o servidor')
      }

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        wsRef.current = null

        // Retry connection if it was unexpected and we haven't exceeded max retries
        if (event.code !== 1000 && retryCountRef.current < maxRetries && currentContractIdRef.current) {
          retryCountRef.current++
          console.log(`Retrying WebSocket connection (${retryCountRef.current}/${maxRetries})`)
          
          setTimeout(() => {
            if (currentContractIdRef.current) {
              setupWebSocket(currentContractIdRef.current)
            }
          }, 2000 * retryCountRef.current) // Exponential backoff
        }
      }

    } catch (err) {
      console.error('Failed to setup WebSocket:', err)
      setError('Falha ao conectar com o servidor para atualizações em tempo real')
    }
  }, [getWsUrl])

  /**
   * Upload file and start analysis
   */
  const uploadAndAnalyze = useCallback(async (
    file: File, 
    contractType?: ContractType,
    options?: {
      priority?: 'normal' | 'high'
      includeNegotiationTips?: boolean
    }
  ): Promise<string | null> => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      if (contractType) {
        formData.append('contract_type', contractType)
      }
      
      if (options?.priority) {
        formData.append('priority', options.priority)
      }
      
      if (options?.includeNegotiationTips !== undefined) {
        formData.append('include_negotiation_tips', String(options.includeNegotiationTips))
      }

      const response = await fetch(getApiUrl('/contracts/upload'), {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type for FormData, browser will set it with boundary
        }
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }))
        throw new Error(errorData.detail || `Erro HTTP: ${response.status}`)
      }

      const result: ApiResponse<{ contract_id: string }> = await response.json()
      
      if (!result.success || !result.data?.contract_id) {
        throw new Error(result.error || 'Falha no upload do arquivo')
      }

      return result.data.contract_id

    } catch (err: any) {
      console.error('Upload error:', err)
      throw new Error(err.message || 'Erro ao fazer upload do arquivo')
    }
  }, [getApiUrl])

  /**
   * Retrieve analysis result by contract ID
   */
  const retrieveAnalysis = useCallback(async (contractId: string): Promise<ContractAnalysis | null> => {
    try {
      const response = await fetch(getApiUrl(`/contracts/${contractId}/analysis`))
      
      if (!response.ok) {
        if (response.status === 404) {
          return null // Analysis not ready yet
        }
        const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }))
        throw new Error(errorData.detail || `Erro HTTP: ${response.status}`)
      }

      const result: ApiResponse<ContractAnalysis> = await response.json()
      
      if (!result.success || !result.data) {
        throw new Error(result.error || 'Falha ao recuperar análise')
      }

      return result.data

    } catch (err: any) {
      console.error('Retrieve analysis error:', err)
      throw new Error(err.message || 'Erro ao recuperar análise')
    }
  }, [getApiUrl])

  /**
   * Main analysis function
   */
  const analyzeContract = useCallback(async (
    file: File,
    contractType?: ContractType,
    options?: {
      priority?: 'normal' | 'high'
      includeNegotiationTips?: boolean
    }
  ) => {
    setIsLoading(true)
    setError(null)
    setAnalysis(null)
    setProgress({
      stage: 'upload',
      percentage: 0,
      message: 'Preparando upload...'
    })

    try {
      // Step 1: Upload file and get contract ID
      setProgress({
        stage: 'upload',
        percentage: 10,
        message: 'Fazendo upload do arquivo...'
      })

      const contractId = await uploadAndAnalyze(file, contractType, options)
      if (!contractId) {
        throw new Error('Falha ao obter ID do contrato')
      }

      currentContractIdRef.current = contractId

      // Step 2: Setup WebSocket for real-time updates
      setProgress({
        stage: 'processing',
        percentage: 20,
        message: 'Conectando para atualizações em tempo real...'
      })

      setupWebSocket(contractId)

      // Step 3: Initial progress update
      setProgress({
        stage: 'processing',
        percentage: 30,
        message: 'Processando documento...'
      })

      // The rest of the process will be handled by WebSocket messages

    } catch (err: any) {
      console.error('Analysis error:', err)
      setError(err.message || 'Erro durante a análise')
      setProgress({
        stage: 'error',
        percentage: 0,
        message: err.message || 'Erro durante a análise'
      })
      setIsLoading(false)
      
      // Clean up
      currentContractIdRef.current = null
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [uploadAndAnalyze, setupWebSocket])

  /**
   * Retry analysis
   */
  const retryAnalysis = useCallback(() => {
    if (currentContractIdRef.current) {
      setupWebSocket(currentContractIdRef.current)
    }
  }, [setupWebSocket])

  /**
   * Check analysis status by contract ID
   */
  const checkAnalysisStatus = useCallback(async (contractId: string): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'error'
    progress?: number
    message?: string
  }> => {
    try {
      const response = await fetch(getApiUrl(`/contracts/${contractId}/status`))
      
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }

      const result = await response.json()
      return result

    } catch (err) {
      console.error('Status check error:', err)
      return { status: 'error', message: 'Erro ao verificar status' }
    }
  }, [getApiUrl])

  /**
   * Reset all state
   */
  const reset = useCallback(() => {
    setAnalysis(null)
    setIsLoading(false)
    setError(null)
    setProgress(null)
    
    // Clean up WebSocket
    currentContractIdRef.current = null
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    retryCountRef.current = 0
  }, [])

  /**
   * Clean up on unmount
   */
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [])

  /**
   * Get current contract ID
   */
  const getCurrentContractId = useCallback(() => {
    return currentContractIdRef.current
  }, [])

  /**
   * Get analysis progress percentage
   */
  const getProgressPercentage = useCallback(() => {
    return progress?.percentage || 0
  }, [progress])

  /**
   * Check if analysis is complete
   */
  const isComplete = useCallback(() => {
    return progress?.stage === 'completed' && !!analysis
  }, [progress, analysis])

  return {
    // State
    analysis,
    isLoading,
    error,
    progress,
    
    // Actions
    analyzeContract,
    reset,
    retryAnalysis,
    
    // Utilities
    getCurrentContractId,
    getProgressPercentage,
    isComplete,
    checkAnalysisStatus,
    retrieveAnalysis
  }
}