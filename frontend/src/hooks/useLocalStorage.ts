'use client'

import { useState, useEffect, useCallback } from 'react'

/**
 * Custom hook for managing localStorage with TypeScript support and SSR compatibility.
 * 
 * Features:
 * - Type-safe storage operations
 * - SSR/hydration safe
 * - Automatic JSON serialization/deserialization
 * - Error handling for storage failures
 * - Storage event listening for cross-tab synchronization
 * - Default value support
 */
export function useLocalStorage<T>(
  key: string,
  defaultValue: T
): [T, (value: T | ((prevValue: T) => T)) => void, () => void] {
  // Initialize state with default value
  const [storedValue, setStoredValue] = useState<T>(defaultValue)
  const [isLoaded, setIsLoaded] = useState(false)

  /**
   * Get value from localStorage
   */
  const getValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return defaultValue
    }

    try {
      const item = window.localStorage.getItem(key)
      if (item === null) {
        return defaultValue
      }
      return JSON.parse(item)
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return defaultValue
    }
  }, [key, defaultValue])

  /**
   * Set value in localStorage
   */
  const setValue = useCallback(
    (value: T | ((prevValue: T) => T)) => {
      try {
        // Allow value to be a function so we have the same API as useState
        const valueToStore = value instanceof Function ? value(storedValue) : value
        
        setStoredValue(valueToStore)

        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, JSON.stringify(valueToStore))
          
          // Dispatch a custom event to notify other components/hooks
          window.dispatchEvent(new Event('local-storage-change'))
        }
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error)
      }
    },
    [key, storedValue]
  )

  /**
   * Remove value from localStorage
   */
  const removeValue = useCallback(() => {
    try {
      setStoredValue(defaultValue)
      
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key)
        window.dispatchEvent(new Event('local-storage-change'))
      }
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error)
    }
  }, [key, defaultValue])

  /**
   * Initialize value from localStorage on mount
   */
  useEffect(() => {
    if (typeof window !== 'undefined' && !isLoaded) {
      const initialValue = getValue()
      setStoredValue(initialValue)
      setIsLoaded(true)
    }
  }, [getValue, isLoaded])

  /**
   * Listen for storage changes from other tabs/windows
   */
  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          const newValue = JSON.parse(e.newValue)
          setStoredValue(newValue)
        } catch (error) {
          console.warn(`Error parsing localStorage change for key "${key}":`, error)
        }
      } else if (e.key === key && e.newValue === null) {
        // Key was removed
        setStoredValue(defaultValue)
      }
    }

    const handleCustomStorageChange = () => {
      const newValue = getValue()
      setStoredValue(newValue)
    }

    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('local-storage-change', handleCustomStorageChange)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('local-storage-change', handleCustomStorageChange)
    }
  }, [key, defaultValue, getValue])

  return [storedValue, setValue, removeValue]
}

/**
 * Hook for managing user preferences with predefined keys
 */
export function useUserPreferences() {
  const [theme, setTheme] = useLocalStorage<'light' | 'dark' | 'auto'>('lawyerless-theme', 'light')
  const [language, setLanguage] = useLocalStorage<'pt-BR' | 'en-US'>('lawyerless-language', 'pt-BR')
  const [defaultScale, setDefaultScale] = useLocalStorage<number>('lawyerless-pdf-scale', 1.5)
  const [showCoordinates, setShowCoordinates] = useLocalStorage<boolean>('lawyerless-show-coordinates', false)
  const [highlightAllClauses, setHighlightAllClauses] = useLocalStorage<boolean>('lawyerless-highlight-all', true)
  const [autoScrollToClause, setAutoScrollToClause] = useLocalStorage<boolean>('lawyerless-auto-scroll', true)
  const [sidebarCollapsed, setSidebarCollapsed] = useLocalStorage<boolean>('lawyerless-sidebar-collapsed', false)

  /**
   * Reset all preferences to defaults
   */
  const resetPreferences = useCallback(() => {
    setTheme('light')
    setLanguage('pt-BR')
    setDefaultScale(1.5)
    setShowCoordinates(false)
    setHighlightAllClauses(true)
    setAutoScrollToClause(true)
    setSidebarCollapsed(false)
  }, [
    setTheme, 
    setLanguage, 
    setDefaultScale, 
    setShowCoordinates, 
    setHighlightAllClauses, 
    setAutoScrollToClause,
    setSidebarCollapsed
  ])

  /**
   * Export preferences as JSON
   */
  const exportPreferences = useCallback(() => {
    return {
      theme,
      language,
      defaultScale,
      showCoordinates,
      highlightAllClauses,
      autoScrollToClause,
      sidebarCollapsed
    }
  }, [theme, language, defaultScale, showCoordinates, highlightAllClauses, autoScrollToClause, sidebarCollapsed])

  /**
   * Import preferences from JSON
   */
  const importPreferences = useCallback((preferences: any) => {
    try {
      if (preferences.theme !== undefined) setTheme(preferences.theme)
      if (preferences.language !== undefined) setLanguage(preferences.language)
      if (preferences.defaultScale !== undefined) setDefaultScale(preferences.defaultScale)
      if (preferences.showCoordinates !== undefined) setShowCoordinates(preferences.showCoordinates)
      if (preferences.highlightAllClauses !== undefined) setHighlightAllClauses(preferences.highlightAllClauses)
      if (preferences.autoScrollToClause !== undefined) setAutoScrollToClause(preferences.autoScrollToClause)
      if (preferences.sidebarCollapsed !== undefined) setSidebarCollapsed(preferences.sidebarCollapsed)
    } catch (error) {
      console.warn('Error importing preferences:', error)
    }
  }, [
    setTheme, 
    setLanguage, 
    setDefaultScale, 
    setShowCoordinates, 
    setHighlightAllClauses, 
    setAutoScrollToClause,
    setSidebarCollapsed
  ])

  return {
    // Individual preferences
    theme,
    setTheme,
    language,
    setLanguage,
    defaultScale,
    setDefaultScale,
    showCoordinates,
    setShowCoordinates,
    highlightAllClauses,
    setHighlightAllClauses,
    autoScrollToClause,
    setAutoScrollToClause,
    sidebarCollapsed,
    setSidebarCollapsed,

    // Utility functions
    resetPreferences,
    exportPreferences,
    importPreferences
  }
}

/**
 * Hook for managing analysis history
 */
export function useAnalysisHistory() {
  const [history, setHistory] = useLocalStorage<Array<{
    id: string
    filename: string
    contractType: string
    analyzedAt: string
    overallRisk: string
  }>>('lawyerless-analysis-history', [])

  /**
   * Add analysis to history
   */
  const addToHistory = useCallback((analysis: {
    id: string
    filename: string
    contractType: string
    overallRisk: string
  }) => {
    setHistory(prev => {
      const newEntry = {
        ...analysis,
        analyzedAt: new Date().toISOString()
      }
      
      // Remove duplicate if exists and add to beginning
      const filtered = prev.filter(item => item.id !== analysis.id)
      const updated = [newEntry, ...filtered].slice(0, 50) // Keep last 50 analyses
      
      return updated
    })
  }, [setHistory])

  /**
   * Remove analysis from history
   */
  const removeFromHistory = useCallback((id: string) => {
    setHistory(prev => prev.filter(item => item.id !== id))
  }, [setHistory])

  /**
   * Clear all history
   */
  const clearHistory = useCallback(() => {
    setHistory([])
  }, [setHistory])

  /**
   * Get recent analyses (last N days)
   */
  const getRecentAnalyses = useCallback((days: number = 30) => {
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - days)
    
    return history.filter(item => 
      new Date(item.analyzedAt) >= cutoffDate
    )
  }, [history])

  return {
    history,
    addToHistory,
    removeFromHistory,
    clearHistory,
    getRecentAnalyses
  }
}