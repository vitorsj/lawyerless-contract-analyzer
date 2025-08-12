'use client'

import React, { useState, useMemo } from 'react'
import { 
  ChevronDownIcon,
  ChevronUpIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import { 
  ClauseAnalysis, 
  RiskFlag, 
  AnalysisPanelProps,
  ClauseWithHighlight
} from '@/types'
import clsx from 'clsx'

/**
 * AnalysisPanel component for displaying contract clause analysis.
 * 
 * Features:
 * - Clause-by-clause breakdown
 * - Risk flag filtering and sorting
 * - Search functionality in Portuguese
 * - Expandable clause details
 * - Click-to-highlight integration
 * - Risk statistics overview
 */
export default function AnalysisPanel({
  analysis,
  selectedClause,
  onClauseSelect,
  onHighlightClause,
  isLoading = false,
  className
}: AnalysisPanelProps) {
  // Local state for UI interactions
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRiskFilter, setSelectedRiskFilter] = useState<RiskFlag | 'all'>('all')
  const [expandedClauses, setExpandedClauses] = useState<Set<string>>(new Set())
  const [sortBy, setSortBy] = useState<'order' | 'risk' | 'length'>('order')

  /**
   * Filter and sort clauses based on current settings
   */
  const filteredAndSortedClauses = useMemo((): ClauseWithHighlight[] => {
    if (!analysis) return []

    let clauses = analysis.analyzedClauses.map(clause => ({
      ...clause,
      isHighlighted: selectedClause === clause.clauseId,
      isSelected: selectedClause === clause.clauseId
    }))

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      clauses = clauses.filter(clause =>
        clause.originalText.toLowerCase().includes(query) ||
        clause.summary.toLowerCase().includes(query) ||
        clause.explanation.toLowerCase().includes(query) ||
        clause.negotiationQuestions.some(q => q.toLowerCase().includes(query))
      )
    }

    // Apply risk filter
    if (selectedRiskFilter !== 'all') {
      clauses = clauses.filter(clause => clause.riskFlag === selectedRiskFilter)
    }

    // Apply sorting
    clauses.sort((a, b) => {
      switch (sortBy) {
        case 'risk':
          const riskOrder = { [RiskFlag.VERMELHO]: 0, [RiskFlag.AMARELO]: 1, [RiskFlag.VERDE]: 2 }
          return riskOrder[a.riskFlag] - riskOrder[b.riskFlag]
        case 'length':
          return b.originalText.length - a.originalText.length
        case 'order':
        default:
          return a.clauseId.localeCompare(b.clauseId, 'pt-BR', { numeric: true })
      }
    })

    return clauses
  }, [analysis, searchQuery, selectedRiskFilter, sortBy, selectedClause])

  /**
   * Calculate risk statistics
   */
  const riskStats = useMemo(() => {
    if (!analysis) return { verde: 0, amarelo: 0, vermelho: 0, total: 0 }

    return analysis.analyzedClauses.reduce(
      (stats, clause) => {
        stats.total++
        switch (clause.riskFlag) {
          case RiskFlag.VERDE:
            stats.verde++
            break
          case RiskFlag.AMARELO:
            stats.amarelo++
            break
          case RiskFlag.VERMELHO:
            stats.vermelho++
            break
        }
        return stats
      },
      { verde: 0, amarelo: 0, vermelho: 0, total: 0 }
    )
  }, [analysis])

  /**
   * Toggle clause expansion
   */
  const toggleClauseExpansion = (clauseId: string) => {
    setExpandedClauses(prev => {
      const newSet = new Set(prev)
      if (newSet.has(clauseId)) {
        newSet.delete(clauseId)
      } else {
        newSet.add(clauseId)
      }
      return newSet
    })
  }

  /**
   * Handle clause selection
   */
  const handleClauseClick = (clauseId: string) => {
    onClauseSelect?.(clauseId)
    onHighlightClause?.(clauseId)
  }

  /**
   * Get risk flag icon
   */
  const getRiskIcon = (risk: RiskFlag) => {
    switch (risk) {
      case RiskFlag.VERDE:
        return <CheckCircleIcon className="w-5 h-5 text-risk-green" />
      case RiskFlag.AMARELO:
        return <ExclamationTriangleIcon className="w-5 h-5 text-risk-yellow" />
      case RiskFlag.VERMELHO:
        return <XCircleIcon className="w-5 h-5 text-risk-red" />
    }
  }

  /**
   * Get risk flag color classes
   */
  const getRiskClasses = (risk: RiskFlag) => {
    switch (risk) {
      case RiskFlag.VERDE:
        return 'border-l-risk-green bg-risk-green/5'
      case RiskFlag.AMARELO:
        return 'border-l-risk-yellow bg-risk-yellow/5'
      case RiskFlag.VERMELHO:
        return 'border-l-risk-red bg-risk-red/5'
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={clsx('panel bg-white h-full', className)}>
        <div className="panel-header">
          <h2 className="text-lg font-semibold text-gray-900">Análise de Cláusulas</h2>
        </div>
        <div className="panel-content">
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="loading-pulse h-24 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // No analysis state
  if (!analysis) {
    return (
      <div className={clsx('panel bg-white h-full', className)}>
        <div className="panel-header">
          <h2 className="text-lg font-semibold text-gray-900">Análise de Cláusulas</h2>
        </div>
        <div className="panel-content">
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-sm">Nenhuma análise disponível</p>
              <p className="text-xs text-gray-400">Faça upload de um contrato para começar</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx('panel bg-white h-full', className)}>
      {/* Panel Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Análise de Cláusulas
          </h2>
          <div className="text-sm text-gray-500">
            {filteredAndSortedClauses.length} de {analysis.totalClauses} cláusulas
          </div>
        </div>

        {/* Risk Statistics */}
        <div className="flex items-center space-x-4 mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-risk-green rounded-full"></div>
            <span className="text-sm text-gray-700">{riskStats.verde} Baixo</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-risk-yellow rounded-full"></div>
            <span className="text-sm text-gray-700">{riskStats.amarelo} Médio</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-risk-red rounded-full"></div>
            <span className="text-sm text-gray-700">{riskStats.vermelho} Alto</span>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="space-y-3">
          {/* Search Input */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar em cláusulas, explicações..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input pl-10 text-sm"
            />
          </div>

          {/* Filter Controls */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <FunnelIcon className="w-4 h-4 text-gray-400" />
              <select
                value={selectedRiskFilter}
                onChange={(e) => setSelectedRiskFilter(e.target.value as RiskFlag | 'all')}
                className="text-sm border-gray-300 rounded-md"
              >
                <option value="all">Todos os riscos</option>
                <option value={RiskFlag.VERMELHO}>Alto risco</option>
                <option value={RiskFlag.AMARELO}>Médio risco</option>
                <option value={RiskFlag.VERDE}>Baixo risco</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Ordenar:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'order' | 'risk' | 'length')}
                className="text-sm border-gray-300 rounded-md"
              >
                <option value="order">Por ordem</option>
                <option value="risk">Por risco</option>
                <option value="length">Por tamanho</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Panel Content */}
      <div className="panel-content">
        {filteredAndSortedClauses.length === 0 ? (
          <div className="text-center py-8">
            <MagnifyingGlassIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500">Nenhuma cláusula encontrada</p>
            <p className="text-xs text-gray-400">Tente ajustar os filtros de busca</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredAndSortedClauses.map((clause) => {
              const isExpanded = expandedClauses.has(clause.clauseId)
              const isSelected = selectedClause === clause.clauseId

              return (
                <div
                  key={clause.clauseId}
                  className={clsx(
                    'clause-item border-l-4 transition-all duration-200',
                    getRiskClasses(clause.riskFlag),
                    isSelected && 'ring-2 ring-primary-500 ring-opacity-50'
                  )}
                >
                  {/* Clause Header */}
                  <div 
                    className="flex items-start justify-between p-4 cursor-pointer hover:bg-gray-50/50"
                    onClick={() => handleClauseClick(clause.clauseId)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <div className="flex items-center space-x-2">
                          {getRiskIcon(clause.riskFlag)}
                          <span className="text-sm font-medium text-gray-900">
                            Cláusula {clause.clauseId}
                          </span>
                        </div>
                        <span className={`risk-flag-${clause.riskFlag.toLowerCase()}`}>
                          {clause.riskFlag}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">
                        {clause.summary}
                      </p>
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleClauseExpansion(clause.clauseId)
                      }}
                      className="flex-shrink-0 p-1 ml-2 text-gray-400 hover:text-gray-600"
                    >
                      {isExpanded ? (
                        <ChevronUpIcon className="w-4 h-4" />
                      ) : (
                        <ChevronDownIcon className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="px-4 pb-4 space-y-4 border-t border-gray-100">
                      {/* Original Text */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">
                          Texto Original:
                        </h4>
                        <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded-md">
                          {clause.originalText}
                        </div>
                      </div>

                      {/* Explanation */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">
                          Explicação:
                        </h4>
                        <div className="text-sm text-gray-700">
                          {clause.explanation}
                        </div>
                      </div>

                      {/* Negotiation Questions */}
                      {clause.negotiationQuestions.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">
                            Perguntas para Negociação:
                          </h4>
                          <ul className="text-sm text-gray-700 space-y-1">
                            {clause.negotiationQuestions.map((question, index) => (
                              <li key={index} className="flex items-start space-x-2">
                                <span className="text-primary-600 flex-shrink-0">•</span>
                                <span>{question}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex items-center space-x-2 pt-2">
                        <button
                          onClick={() => onHighlightClause?.(clause.clauseId)}
                          className="btn btn-ghost text-sm px-3 py-1"
                        >
                          Destacar no PDF
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}