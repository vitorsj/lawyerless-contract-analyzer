'use client'

import { useState } from 'react'
import FileUpload from '@/components/FileUpload'

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState<any>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [isUploading, setIsUploading] = useState(false)

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file)
    setIsUploading(true)
    setUploadProgress({ status: 'uploading', percentage: 0, message: 'Iniciando upload...' })

    try {
      // Create form data
      const formData = new FormData()
      formData.append('file', file)
      formData.append('perspectiva', 'fundador') // Default perspective

      // Upload to backend
      const response = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`)
      }

      const result = await response.json()
      const documentId = result.document_id

      setUploadProgress({ status: 'processing', percentage: 50, message: 'Processando documento...' })

      // Poll for results
      let attempts = 0
      const maxAttempts = 120 // 4 minutes timeout for complex documents
      
      const pollResults = async () => {
        try {
          const statusResponse = await fetch(`http://localhost:8000/api/v1/analysis/${documentId}`)
          
          if (statusResponse.status === 200) {
            // Analysis completed successfully
            const analysisResult = await statusResponse.json()
            setAnalysis(analysisResult)
            setUploadProgress({ status: 'completed', percentage: 100, message: 'Análise concluída!' })
            setIsUploading(false)
            return
          } else if (statusResponse.status === 202) {
            // Analysis still in progress
            attempts++
            if (attempts < maxAttempts) {
              setTimeout(pollResults, 2000) // Poll every 2 seconds for longer tasks
              setUploadProgress({ 
                status: 'processing', 
                percentage: Math.min(60 + (attempts * 1.5), 98), 
                message: 'Analisando documento... Isso pode levar alguns minutos.' 
              })
            } else {
              throw new Error('Timeout na análise - tente novamente')
            }
          } else {
            // Error status
            const errorData = await statusResponse.json().catch(() => ({ message: 'Erro desconhecido' }))
            throw new Error(errorData.message || `Erro HTTP: ${statusResponse.status}`)
          }
        } catch (err) {
          console.error('Polling error:', err)
          const errorMessage = err instanceof Error ? err.message : 'Erro na análise'
          setUploadProgress({ status: 'error', percentage: 0, message: errorMessage })
          setIsUploading(false)
        }
      }

      // Start polling
      setTimeout(pollResults, 2000) // Wait 2 seconds before first poll

    } catch (error: any) {
      console.error('Upload error:', error)
      setUploadProgress({ status: 'error', percentage: 0, message: error.message || 'Erro no upload' })
      setIsUploading(false)
    }
  }

  const handleFileRemove = () => {
    setSelectedFile(null)
    setUploadProgress(null)
    setAnalysis(null)
    setIsUploading(false)
  }
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white">
      {/* Header */}
      <header className="bg-white shadow-soft border-b border-gray-200">
        <div className="container-responsive py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <svg 
                  className="w-6 h-6 text-white" 
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
              </div>
              <h1 className="text-2xl font-bold text-gray-900">
                Lawyerless
              </h1>
            </div>
            <div className="text-sm text-gray-600">
              Versão {process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container-responsive py-12">
        <div className="max-w-4xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Análise Inteligente de Contratos de Investimento
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
              Faça upload de seu contrato de investimento e receba uma análise detalhada com 
              identificação de riscos, explicações em linguagem simples e perguntas para negociação.
            </p>
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-risk-green rounded-full mr-2"></div>
                <span>Baixo Risco</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-risk-yellow rounded-full mr-2"></div>
                <span>Médio Risco</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-risk-red rounded-full mr-2"></div>
                <span>Alto Risco</span>
              </div>
            </div>
          </div>

          {/* File Upload Section */}
          <div className="max-w-2xl mx-auto mb-12">
            <FileUpload
              onFileSelect={handleFileSelect}
              onFileRemove={handleFileRemove}
              uploadProgress={uploadProgress}
              disabled={isUploading}
              selectedFile={selectedFile}
            />
          </div>

          {/* Analysis Results */}
          {analysis && (
            <div className="max-w-4xl mx-auto mt-12">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  Análise do Contrato: {analysis.filename}
                </h2>
                
                {/* Risk Summary */}
                <div className="flex items-center justify-center space-x-6 mb-6">
                  <div className="text-center">
                    <div className="w-8 h-8 bg-risk-green rounded-full mx-auto mb-2"></div>
                    <span className="text-sm text-gray-600">Verde: {analysis.risk_summary?.verde || 0}</span>
                  </div>
                  <div className="text-center">
                    <div className="w-8 h-8 bg-risk-yellow rounded-full mx-auto mb-2"></div>
                    <span className="text-sm text-gray-600">Amarelo: {analysis.risk_summary?.amarelo || 0}</span>
                  </div>
                  <div className="text-center">
                    <div className="w-8 h-8 bg-risk-red rounded-full mx-auto mb-2"></div>
                    <span className="text-sm text-gray-600">Vermelho: {analysis.risk_summary?.vermelho || 0}</span>
                  </div>
                </div>

                {/* Contract Summary */}
                {analysis.contract_summary && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Resumo do Contrato</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p><strong>Tipo:</strong> {analysis.contract_summary.tipo_instrumento?.toUpperCase() || 'N/A'}</p>
                      <p><strong>Total de Cláusulas:</strong> {analysis.total_clauses}</p>
                      <p><strong>Tempo de Processamento:</strong> {analysis.processing_time?.toFixed(2)}s</p>
                    </div>
                  </div>
                )}

                {/* Clauses */}
                {analysis.clauses && analysis.clauses.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">Análise por Cláusula</h3>
                    {analysis.clauses.map((clause: any, index: number) => (
                      <div key={clause.clause_id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="text-md font-semibold text-gray-900">
                            {clause.titulo || `Cláusula ${index + 1}`}
                          </h4>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            clause.bandeira === 'verde' ? 'bg-green-100 text-green-800' :
                            clause.bandeira === 'amarelo' ? 'bg-yellow-100 text-yellow-800' :
                            clause.bandeira === 'vermelho' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {clause.bandeira?.toUpperCase() || 'N/A'}
                          </span>
                        </div>
                        
                        <div className="text-sm text-gray-600 mb-2 bg-gray-50 p-2 rounded">
                          {clause.texto_original || 'Texto não disponível'}
                        </div>
                        
                        <div className="space-y-2">
                          {clause.tldr && (
                            <div>
                              <strong className="text-sm">Resumo:</strong>
                              <p className="text-sm text-gray-600">{clause.tldr}</p>
                            </div>
                          )}
                          
                          {clause.explicacao_simples && (
                            <div>
                              <strong className="text-sm">Explicação:</strong>
                              <p className="text-sm text-gray-600">{clause.explicacao_simples}</p>
                            </div>
                          )}
                          
                          {clause.motivo_bandeira && (
                            <div>
                              <strong className="text-sm">Motivo da classificação:</strong>
                              <p className="text-sm text-gray-600">{clause.motivo_bandeira}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Features Section */}
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="text-center">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg 
                  className="w-6 h-6 text-primary-600" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" 
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Análise Cláusula por Cláusula
              </h3>
              <p className="text-gray-600">
                Cada cláusula é analisada individualmente com classificação de risco 
                e explicações detalhadas em linguagem simples.
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg 
                  className="w-6 h-6 text-primary-600" 
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
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Identificação de Riscos
              </h3>
              <p className="text-gray-600">
                Sistema de flags coloridos (Verde, Amarelo, Vermelho) para 
                identificar rapidamente os pontos de atenção do contrato.
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg 
                  className="w-6 h-6 text-primary-600" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Perguntas para Negociação
              </h3>
              <p className="text-gray-600">
                Receba sugestões de perguntas estratégicas para fazer durante 
                a negociação e due diligence do investimento.
              </p>
            </div>
          </div>

          {/* Supported Document Types */}
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Tipos de Documentos Suportados
            </h3>
            <div className="flex flex-wrap justify-center gap-3">
              {[
                'SAFE (Simple Agreement for Future Equity)',
                'Convertible Notes',
                'Term Sheets',
                'Acordos de Acionistas',
                'Side Letters'
              ].map((type) => (
                <span 
                  key={type}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700"
                >
                  {type}
                </span>
              ))}
            </div>
          </div>

          {/* Information Notice */}
          <div className="bg-primary-50 border border-primary-200 rounded-lg p-6 mt-12">
            <div className="flex">
              <svg 
                className="w-6 h-6 text-primary-600 flex-shrink-0 mr-3 mt-0.5" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                />
              </svg>
              <div>
                <h4 className="text-sm font-semibold text-primary-900 mb-1">
                  Importante
                </h4>
                <p className="text-sm text-primary-700">
                  Esta ferramenta fornece análises automatizadas para fins informativos. 
                  Sempre consulte um advogado qualificado antes de tomar decisões legais 
                  ou assinar contratos de investimento.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="container-responsive py-8">
          <div className="text-center">
            <p className="text-sm text-gray-500">
              © {new Date().getFullYear()} Lawyerless. 
              Desenvolvido para ajudar empreendedores e investidores.
            </p>
            <div className="mt-4 flex justify-center space-x-6 text-sm text-gray-500">
              <a href="#" className="hover:text-gray-700">Privacidade</a>
              <a href="#" className="hover:text-gray-700">Termos</a>
              <a href="#" className="hover:text-gray-700">Suporte</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}