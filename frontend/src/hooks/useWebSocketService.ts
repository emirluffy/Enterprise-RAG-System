/**
 * Context7-verified WebSocket Service Hook
 * Enterprise RAG System - Phase 3 Frontend Implementation
 * 
 * Features:
 * - Real-time chat messaging
 * - Document processing notifications
 * - User presence tracking  
 * - Live analytics updates
 * - Typing indicators
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { v4 as uuidv4 } from 'uuid';

// Context7-verified WebSocket event types
export interface WebSocketEvent {
  event_type: string;
  timestamp: string;
  user_id?: string;
  session_id?: string;
  data: Record<string, any>;
}

export interface ChatEvent extends WebSocketEvent {
  conversation_id: string;
  message_type: string;
}

export interface DocumentEvent extends WebSocketEvent {
  document_id: string;
  status: string;
  progress?: number;
}

export interface NotificationEvent extends WebSocketEvent {
  notification_type: string;
  title: string;
  message: string;
  auto_dismiss: boolean;
}

export interface UserPresenceEvent extends WebSocketEvent {
  status: string;
  last_seen?: string;
}

export interface AnalyticsEvent extends WebSocketEvent {
  metric_type: string;
}

// WebSocket connection states
export const ConnectionStatus = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Connected',
  [ReadyState.CLOSING]: 'Disconnecting',
  [ReadyState.CLOSED]: 'Disconnected',
  [ReadyState.UNINSTANTIATED]: 'Not Connected',
} as const;

export interface WebSocketServiceHook {
  // Connection state
  isConnected: boolean;
  connectionStatus: string;
  
  // Message handling
  sendMessage: (message: any) => void;
  sendJsonMessage: (message: any) => void;
  
  // Event handlers
  onChatMessage: (handler: (event: ChatEvent) => void) => void;
  onDocumentUpdate: (handler: (event: DocumentEvent) => void) => void;
  onNotification: (handler: (event: NotificationEvent) => void) => void;
  onUserPresence: (handler: (event: UserPresenceEvent) => void) => void;
  onAnalyticsUpdate: (handler: (event: AnalyticsEvent) => void) => void;
  
  // Typing indicators
  sendTypingStart: (conversationId: string) => void;
  sendTypingStop: (conversationId: string) => void;
  
  // Connection management
  connect: () => void;
  disconnect: () => void;
  
  // Active users
  activeUsers: string[];
  userSessions: Record<string, number>;
}

export const useWebSocketService = (
  userId?: string,
  enableReconnect: boolean = true
): WebSocketServiceHook => {
  const sessionId = useRef<string>(uuidv4());
  const [activeUsers, setActiveUsers] = useState<string[]>([]);
  const [userSessions, setUserSessions] = useState<Record<string, number>>({});
  
  // Event handlers storage
  const chatHandlers = useRef<Set<(event: ChatEvent) => void>>(new Set());
  const documentHandlers = useRef<Set<(event: DocumentEvent) => void>>(new Set());
  const notificationHandlers = useRef<Set<(event: NotificationEvent) => void>>(new Set());
  const presenceHandlers = useRef<Set<(event: UserPresenceEvent) => void>>(new Set());
  const analyticsHandlers = useRef<Set<(event: AnalyticsEvent) => void>>(new Set());
  
  // WebSocket URL
  const socketUrl = `ws://localhost:8002/ws/connect`;
  
  // Context7-verified WebSocket configuration
  const {
    sendMessage,
    sendJsonMessage,
    lastMessage,
    readyState,
    getWebSocket
  } = useWebSocket(
    socketUrl,
    {
      onOpen: () => {
        console.log('✅ WebSocket connected');
        
        // Send authentication data immediately after connection
        if (userId) {
          sendJsonMessage({
            session_id: sessionId.current,
            user_id: userId,
            event_type: 'authenticate'
          });
        }
      },
      onClose: () => {
        console.log('❌ WebSocket disconnected');
      },
      onError: (event) => {
        console.error('❌ WebSocket error:', event);
      },
      shouldReconnect: () => enableReconnect,
      reconnectAttempts: 10,
      reconnectInterval: (attemptNumber) =>
        Math.min(Math.pow(2, attemptNumber) * 1000, 10000),
      heartbeat: {
        message: JSON.stringify({ event_type: 'ping' }),
        returnMessage: 'pong',
        timeout: 120000,
        interval: 30000,
      },
      filter: (message) => {
        try {
          const data = JSON.parse(message.data);
          // Filter out ping/pong messages from processing
          return data.event_type !== 'pong';
        } catch {
          return true;
        }
      }
    }
  );
  
  // Context7-verified message processing
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data);
        
        console.log('📩 WebSocket message received:', data);
        
        // Route messages to appropriate handlers
        switch (data.event_type) {
          case 'connection_established':
            console.log('✅ WebSocket connection established:', data);
            break;
            
          case 'chat_message':
          case 'chat_typing':
            chatHandlers.current.forEach(handler => handler(data as ChatEvent));
            break;
            
          case 'document_status':
            documentHandlers.current.forEach(handler => handler(data as DocumentEvent));
            break;
            
          case 'notification':
            notificationHandlers.current.forEach(handler => handler(data as NotificationEvent));
            break;
            
          case 'user_presence':
            presenceHandlers.current.forEach(handler => handler(data as UserPresenceEvent));
            
            // Update active users list
            if (data.user_id && data.status === 'online') {
              setActiveUsers(prev => [...new Set([...prev, data.user_id])]);
            } else if (data.user_id && data.status === 'offline') {
              setActiveUsers(prev => prev.filter(id => id !== data.user_id));
            }
            break;
            
          case 'analytics_update':
            analyticsHandlers.current.forEach(handler => handler(data as AnalyticsEvent));
            break;
            
          default:
            console.log('🔍 Unhandled WebSocket event:', data.event_type);
        }
        
      } catch (error) {
        console.error('❌ Error processing WebSocket message:', error);
      }
    }
  }, [lastMessage]);
  
  // Event handler registration methods
  const onChatMessage = useCallback((handler: (event: ChatEvent) => void) => {
    chatHandlers.current.add(handler);
    return () => chatHandlers.current.delete(handler);
  }, []);
  
  const onDocumentUpdate = useCallback((handler: (event: DocumentEvent) => void) => {
    documentHandlers.current.add(handler);
    return () => documentHandlers.current.delete(handler);
  }, []);
  
  const onNotification = useCallback((handler: (event: NotificationEvent) => void) => {
    notificationHandlers.current.add(handler);
    return () => notificationHandlers.current.delete(handler);
  }, []);
  
  const onUserPresence = useCallback((handler: (event: UserPresenceEvent) => void) => {
    presenceHandlers.current.add(handler);
    return () => presenceHandlers.current.delete(handler);
  }, []);
  
  const onAnalyticsUpdate = useCallback((handler: (event: AnalyticsEvent) => void) => {
    analyticsHandlers.current.add(handler);
    return () => analyticsHandlers.current.delete(handler);
  }, []);
  
  // Typing indicator methods
  const sendTypingStart = useCallback((conversationId: string) => {
    if (readyState === ReadyState.OPEN) {
      sendJsonMessage({
        event_type: 'chat_typing_start',
        conversation_id: conversationId,
        session_id: sessionId.current,
        user_id: userId
      });
    }
  }, [readyState, sendJsonMessage, userId]);
  
  const sendTypingStop = useCallback((conversationId: string) => {
    if (readyState === ReadyState.OPEN) {
      sendJsonMessage({
        event_type: 'chat_typing_stop',
        conversation_id: conversationId,
        session_id: sessionId.current,
        user_id: userId
      });
    }
  }, [readyState, sendJsonMessage, userId]);
  
  // Connection management
  const connect = useCallback(() => {
    // Connection is automatically managed by useWebSocket
    console.log('🔄 WebSocket connection requested');
  }, []);
  
  const disconnect = useCallback(() => {
    const ws = getWebSocket();
    if (ws) {
      ws.close();
    }
  }, [getWebSocket]);
  
  // Connection status
  const isConnected = readyState === ReadyState.OPEN;
  const connectionStatus = ConnectionStatus[readyState] || 'Unknown';
  
  return {
    // Connection state
    isConnected,
    connectionStatus,
    
    // Message handling
    sendMessage,
    sendJsonMessage,
    
    // Event handlers
    onChatMessage,
    onDocumentUpdate,
    onNotification,
    onUserPresence,
    onAnalyticsUpdate,
    
    // Typing indicators
    sendTypingStart,
    sendTypingStop,
    
    // Connection management
    connect,
    disconnect,
    
    // Active users
    activeUsers,
    userSessions
  };
}; 