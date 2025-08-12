'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { WebSocketMessage } from '@/types'

export interface UseWebSocketOptions {
  /**
   * Reconnection settings
   */
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  
  /**
   * Connection settings
   */
  protocols?: string[]
  
  /**
   * Event handlers
   */
  onOpen?: (event: Event) => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

export interface UseWebSocketReturn {
  /**
   * WebSocket connection state
   */
  socket: WebSocket | null
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  
  /**
   * Connection control
   */
  connect: () => void
  disconnect: () => void
  reconnect: () => void
  
  /**
   * Message handling
   */
  sendMessage: (message: any) => boolean
  lastMessage: WebSocketMessage | null
  
  /**
   * Connection stats
   */
  reconnectAttempts: number
  connectionState: 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'
}

/**
 * Custom hook for WebSocket connections with automatic reconnection.
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Connection state management
 * - Typed message handling
 * - Error recovery
 * - Connection statistics
 */
export function useWebSocket(
  url: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    reconnect = true,
    reconnectInterval = 1000,
    maxReconnectAttempts = 5,
    protocols,
    onOpen,
    onClose,
    onError,
    onMessage
  } = options

  // State management
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [connectionState, setConnectionState] = useState<'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'>('CLOSED')

  // Refs for stable references
  const urlRef = useRef(url)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldReconnectRef = useRef(true)
  const mountedRef = useRef(true)

  /**
   * Update URL reference
   */
  useEffect(() => {
    urlRef.current = url
  }, [url])

  /**
   * Clear reconnect timeout
   */
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  /**
   * Create WebSocket connection
   */
  const createConnection = useCallback(() => {
    const currentUrl = urlRef.current
    if (!currentUrl || !mountedRef.current) {
      return null
    }

    try {
      setIsConnecting(true)
      setError(null)
      setConnectionState('CONNECTING')

      const ws = protocols ? new WebSocket(currentUrl, protocols) : new WebSocket(currentUrl)

      ws.onopen = (event) => {
        if (!mountedRef.current) {
          ws.close()
          return
        }

        console.log('WebSocket connected:', currentUrl)
        setSocket(ws)
        setIsConnected(true)
        setIsConnecting(false)
        setError(null)
        setReconnectAttempts(0)
        setConnectionState('OPEN')
        clearReconnectTimeout()

        onOpen?.(event)
      }

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        
        setSocket(null)
        setIsConnected(false)
        setIsConnecting(false)
        setConnectionState('CLOSED')

        if (!mountedRef.current) {
          return
        }

        onClose?.(event)

        // Handle reconnection
        if (
          shouldReconnectRef.current &&
          reconnect &&
          reconnectAttempts < maxReconnectAttempts &&
          event.code !== 1000 // Not a normal closure
        ) {
          const delay = Math.min(reconnectInterval * Math.pow(2, reconnectAttempts), 30000)
          console.log(`Scheduling reconnect in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current && shouldReconnectRef.current) {
              setReconnectAttempts(prev => prev + 1)
              createConnection()
            }
          }, delay)
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          setError(`Falha ao conectar após ${maxReconnectAttempts} tentativas`)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('Erro de conexão WebSocket')
        onError?.(event)
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          onMessage?.(message)
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
          setError('Erro ao processar mensagem do servidor')
        }
      }

      return ws

    } catch (err: any) {
      console.error('Failed to create WebSocket connection:', err)
      setError(err.message || 'Falha ao criar conexão WebSocket')
      setIsConnecting(false)
      setConnectionState('CLOSED')
      return null
    }
  }, [protocols, onOpen, onClose, onError, onMessage, reconnect, reconnectAttempts, maxReconnectAttempts, reconnectInterval, clearReconnectTimeout])

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (socket?.readyState === WebSocket.OPEN || isConnecting) {
      return // Already connected or connecting
    }

    shouldReconnectRef.current = true
    createConnection()
  }, [socket, isConnecting, createConnection])

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    clearReconnectTimeout()
    
    if (socket) {
      setConnectionState('CLOSING')
      socket.close(1000, 'Manual disconnect')
    }
    
    setSocket(null)
    setIsConnected(false)
    setIsConnecting(false)
    setConnectionState('CLOSED')
    setReconnectAttempts(0)
  }, [socket, clearReconnectTimeout])

  /**
   * Manual reconnect
   */
  const manualReconnect = useCallback(() => {
    disconnect()
    setError(null)
    setReconnectAttempts(0)
    
    // Small delay before reconnecting
    setTimeout(() => {
      connect()
    }, 100)
  }, [disconnect, connect])

  /**
   * Send message through WebSocket
   */
  const sendMessage = useCallback((message: any): boolean => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.warn('Cannot send message: WebSocket is not open')
      return false
    }

    try {
      const messageString = typeof message === 'string' ? message : JSON.stringify(message)
      socket.send(messageString)
      return true
    } catch (err) {
      console.error('Failed to send WebSocket message:', err)
      setError('Falha ao enviar mensagem')
      return false
    }
  }, [socket])

  /**
   * Auto-connect when URL is provided
   */
  useEffect(() => {
    if (url && shouldReconnectRef.current) {
      connect()
    }

    return () => {
      shouldReconnectRef.current = false
    }
  }, [url, connect])

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      mountedRef.current = false
      shouldReconnectRef.current = false
      clearReconnectTimeout()
      
      if (socket) {
        socket.close(1000, 'Component unmounting')
      }
    }
  }, [socket, clearReconnectTimeout])

  /**
   * Update connection state based on socket state
   */
  useEffect(() => {
    if (socket) {
      const updateState = () => {
        switch (socket.readyState) {
          case WebSocket.CONNECTING:
            setConnectionState('CONNECTING')
            break
          case WebSocket.OPEN:
            setConnectionState('OPEN')
            break
          case WebSocket.CLOSING:
            setConnectionState('CLOSING')
            break
          case WebSocket.CLOSED:
            setConnectionState('CLOSED')
            break
        }
      }

      updateState()

      // Poll for state changes (as a backup to event handlers)
      const interval = setInterval(updateState, 1000)
      return () => clearInterval(interval)
    }
  }, [socket])

  return {
    // State
    socket,
    isConnected,
    isConnecting,
    error,
    lastMessage,
    reconnectAttempts,
    connectionState,

    // Actions
    connect,
    disconnect,
    reconnect: manualReconnect,
    sendMessage
  }
}