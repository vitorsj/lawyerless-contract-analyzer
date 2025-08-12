'use client'

import React, { useState } from 'react'
import {
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentTextIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  ScaleIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  UsersIcon
} from '@heroicons/react/24/outline'
import { 
  ContractSummary as ContractSummaryType, 
  RiskFlag, 
  SummaryCardProps 
} from '@/types'
import clsx from 'clsx'

/**
 * ContractSummary component for displaying the contract overview.
 * 
 * Features:
 * - Executive summary in Portuguese
 * - Key contract terms breakdown
 * - Risk assessment overview
 * - Important dates tracking
 * - Financial terms summary
 * - Collapsible sections
 * - Visual risk indicators
 */
export default function ContractSummary({
  summary,
  overallRisk,
  isCollapsed = false,
  onToggleCollapse,
  className
}: SummaryCardProps) {
  // Local state for section expansion
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']))

  /**
   * Toggle section expansion
   */
  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      return newSet
    })
  }

  /**
   * Get overall risk styling
   */
  const getRiskStyling = (risk: RiskFlag) => {
    switch (risk) {
      case RiskFlag.VERDE:
        return {
          bgColor: 'bg-risk-green/10',
          textColor: 'text-risk-green',
          borderColor: 'border-risk-green/30'
        }
      case RiskFlag.AMARELO:
        return {
          bgColor: 'bg-risk-yellow/10',
          textColor: 'text-risk-yellow',
          borderColor: 'border-risk-yellow/30'
        }
      case RiskFlag.VERMELHO:
        return {
          bgColor: 'bg-risk-red/10',
          textColor: 'text-risk-red',
          borderColor: 'border-risk-red/30'
        }
    }
  }

  const riskStyling = getRiskStyling(overallRisk)

  /**
   * Format risk level in Portuguese
   */
  const formatRiskLevel = (risk: RiskFlag) => {
    switch (risk) {
      case RiskFlag.VERDE:
        return 'Baixo Risco'
      case RiskFlag.AMARELO:
        return 'Médio Risco'
      case RiskFlag.VERMELHO:
        return 'Alto Risco'
    }
  }

  /**
   * Collapsible section component
   */
  const CollapsibleSection = ({ 
    id, 
    title, 
    icon: Icon, 
    children,
    defaultExpanded = false 
  }: {
    id: string
    title: string
    icon: React.ComponentType<any>
    children: React.ReactNode
    defaultExpanded?: boolean
  }) => {
    const isExpanded = expandedSections.has(id)
    
    return (
      <div className="border-b border-gray-200 last:border-b-0">
        <button
          onClick={() => toggleSection(id)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50"
        >
          <div className="flex items-center space-x-3">
            <Icon className="w-5 h-5 text-gray-600" />
            <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
          </div>
          {isExpanded ? (
            <ChevronUpIcon className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDownIcon className="w-4 h-4 text-gray-500" />
          )}
        </button>
        
        {isExpanded && (
          <div className="px-4 pb-4">
            {children}
          </div>
        )}
      </div>
    )
  }

  if (isCollapsed) {
    return (
      <div className={clsx('card', className)}>
        <div className="card-content p-4">
          <button
            onClick={onToggleCollapse}
            className="w-full flex items-center justify-between text-left"
          >
            <div className="flex items-center space-x-3">
              <DocumentTextIcon className="w-5 h-5 text-gray-600" />
              <span className="text-sm font-semibold text-gray-900">
                Resumo do Contrato
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={clsx('text-xs font-medium px-2 py-1 rounded-full', riskStyling.bgColor, riskStyling.textColor)}>
                {formatRiskLevel(overallRisk)}
              </span>
              <ChevronDownIcon className="w-4 h-4 text-gray-500" />
            </div>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx('card', className)}>
      {/* Card Header */}
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <DocumentTextIcon className="w-6 h-6 text-gray-700" />
            <h2 className="text-lg font-semibold text-gray-900">
              Ficha do Contrato
            </h2>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className={clsx(
              'px-3 py-2 rounded-lg border text-sm font-medium',
              riskStyling.bgColor,
              riskStyling.textColor,
              riskStyling.borderColor
            )}>
              {formatRiskLevel(overallRisk)}
            </div>
            
            {onToggleCollapse && (
              <button
                onClick={onToggleCollapse}
                className="p-2 text-gray-400 hover:text-gray-600"
              >
                <ChevronUpIcon className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Card Content */}
      <div className="card-content p-0">
        {/* Overview Section */}
        <CollapsibleSection
          id="overview"
          title="Visão Geral"
          icon={DocumentTextIcon}
          defaultExpanded
        >
          <div className="space-y-4">
            {/* Main Purpose */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">Objetivo Principal:</h4>
              <p className="text-sm text-gray-700">{summary.mainPurpose}</p>
            </div>

            {/* Parties */}
            {summary.parties.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Partes Envolvidas:</h4>
                <div className="space-y-1">
                  {summary.parties.map((party, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <UsersIcon className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{party}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Governing Law */}
            {summary.governingLaw && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Lei Aplicável:</h4>
                <div className="flex items-center space-x-2">
                  <ScaleIcon className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-700">{summary.governingLaw}</span>
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>

        {/* Key Terms Section */}
        {Object.keys(summary.keyTerms).length > 0 && (
          <CollapsibleSection
            id="key-terms"
            title="Termos Principais"
            icon={DocumentTextIcon}
          >
            <div className="space-y-3">
              {Object.entries(summary.keyTerms).map(([key, value]) => (
                <div key={key} className="flex flex-col space-y-1">
                  <h5 className="text-sm font-medium text-gray-900">{key}:</h5>
                  <p className="text-sm text-gray-700 pl-4 border-l-2 border-gray-200">
                    {value}
                  </p>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Financial Terms Section */}
        {Object.keys(summary.financialTerms).length > 0 && (
          <CollapsibleSection
            id="financial-terms"
            title="Termos Financeiros"
            icon={CurrencyDollarIcon}
          >
            <div className="space-y-3">
              {Object.entries(summary.financialTerms).map(([key, value]) => (
                <div key={key} className="flex justify-between items-start p-3 bg-gray-50 rounded-md">
                  <h5 className="text-sm font-medium text-gray-900">{key}:</h5>
                  <p className="text-sm text-gray-700 text-right max-w-xs">{value}</p>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Important Dates Section */}
        {Object.keys(summary.importantDates).length > 0 && (
          <CollapsibleSection
            id="important-dates"
            title="Datas Importantes"
            icon={CalendarIcon}
          >
            <div className="space-y-3">
              {Object.entries(summary.importantDates).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between p-3 bg-blue-50 rounded-md">
                  <div className="flex items-center space-x-2">
                    <CalendarIcon className="w-4 h-4 text-blue-600" />
                    <h5 className="text-sm font-medium text-gray-900">{key}</h5>
                  </div>
                  <p className="text-sm text-gray-700">{value}</p>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Main Risks Section */}
        {summary.mainRisks.length > 0 && (
          <CollapsibleSection
            id="main-risks"
            title="Principais Riscos"
            icon={ExclamationTriangleIcon}
          >
            <div className="space-y-2">
              {summary.mainRisks.map((risk, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-red-50 rounded-md">
                  <ExclamationTriangleIcon className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-gray-700">{risk}</p>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Recommendations Section */}
        {summary.recommendations.length > 0 && (
          <CollapsibleSection
            id="recommendations"
            title="Recomendações"
            icon={LightBulbIcon}
          >
            <div className="space-y-2">
              {summary.recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-green-50 rounded-md">
                  <LightBulbIcon className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-gray-700">{recommendation}</p>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}
      </div>

      {/* Card Footer */}
      <div className="card-footer">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Análise gerada automaticamente</span>
          <span>Sempre consulte um advogado qualificado</span>
        </div>
      </div>
    </div>
  )
}