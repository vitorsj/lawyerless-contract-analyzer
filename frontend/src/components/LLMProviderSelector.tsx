'use client'

import { useState, useEffect } from 'react'

interface Provider {
  provider: string
  model: string
  base_url: string
  available: boolean
  api_key_configured: boolean
  error?: string
}

interface LLMProviderSelectorProps {
  selectedProvider: string
  onProviderChange: (provider: string) => void
  disabled?: boolean
}

export default function LLMProviderSelector({ 
  selectedProvider, 
  onProviderChange, 
  disabled = false 
}: LLMProviderSelectorProps) {
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchProviders = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/llm/providers')
      if (!response.ok) {
        throw new Error('Falha ao carregar provedores LLM')
      }
      
      const data = await response.json()
      setProviders(data.providers || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProviders()
  }, [])

  const getProviderDisplayName = (provider: string) => {
    switch (provider) {
      case 'openai': return 'OpenAI'
      case 'lm_studio': return 'LM Studio (Local)'
      default: return provider
    }
  }

  const getProviderDescription = (provider: Provider) => {
    switch (provider.provider) {
      case 'openai':
        return `Modelo: ${provider.model} - Requer chave API`
      case 'lm_studio':
        return `Modelo: ${provider.model} - Servidor local`
      default:
        return provider.model
    }
  }

  const getStatusIcon = (provider: Provider) => {
    if (!provider.available) {
      return (
        <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      )
    }
    return (
      <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    )
  }

  if (loading) {
    return (
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Provedor de IA
        </label>
        <div className="animate-pulse bg-gray-200 rounded-lg h-20"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Provedor de IA
        </label>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span className="text-sm text-red-700">{error}</span>
          </div>
          <button
            onClick={fetchProviders}
            className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Provedor de IA
      </label>
      <div className="space-y-2">
        {providers.map((provider) => (
          <div
            key={provider.provider}
            className={`relative rounded-lg border p-3 cursor-pointer transition-all ${
              selectedProvider === provider.provider
                ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                : provider.available
                ? 'border-gray-200 bg-white hover:border-gray-300'
                : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
            } ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}
            onClick={() => {
              if (!disabled && provider.available) {
                onProviderChange(provider.provider)
              }
            }}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center">
                <input
                  type="radio"
                  name="llm-provider"
                  value={provider.provider}
                  checked={selectedProvider === provider.provider}
                  onChange={() => {
                    if (!disabled && provider.available) {
                      onProviderChange(provider.provider)
                    }
                  }}
                  disabled={disabled || !provider.available}
                  className="mr-3 h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                />
                <div>
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900">
                      {getProviderDisplayName(provider.provider)}
                    </span>
                    <div className="ml-2">
                      {getStatusIcon(provider)}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {getProviderDescription(provider)}
                  </p>
                  {!provider.available && provider.error && (
                    <p className="text-xs text-red-500 mt-1">
                      {provider.error}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {providers.length === 0 && (
        <div className="text-center py-4 text-gray-500">
          <p className="text-sm">Nenhum provedor disponível</p>
        </div>
      )}
    </div>
  )
}