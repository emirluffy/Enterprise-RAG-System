import { useState, useEffect, useCallback, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';

export interface CollaborationUser {
  user_id: string;
  name: string;
  avatar?: string;
  joined_at: string;
  active: boolean;
}

export interface CollaborationRoom {
  room_id: string;
  room_type: string;
  users: Record<string, CollaborationUser>;
  typing_users: string[];
  user_count: number;
  created_at: string;
  last_activity: string;
}

export interface CollaborationMessage {
  message_id: string;
  room_id: string;
  user_id: string;
  content: string;
  message_type: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface RealtimeEvent {
  type: 'user_joined' | 'user_left' | 'message' | 'typing_status' | 'presence_update' | 'connection_established';
  user_id?: string;
  user_info?: CollaborationUser;
  room_state?: CollaborationRoom;
  content?: string;
  is_typing?: boolean;
  typing_users?: string[];
  users?: Record<string, CollaborationUser>;
  timestamp: string;
  [key: string]: any;
}

interface UseRealtimeCollaborationProps {
  roomId: string;
  userId: string;
  userInfo: {
    name: string;
    avatar?: string;
  };
  roomType?: string;
  serverUrl?: string;
}

interface UseRealtimeCollaborationReturn {
  // Connection state
  isConnected: boolean;
  connectionStatus: string;
  error: string | null;
  
  // Room state
  room: CollaborationRoom | null;
  messages: CollaborationMessage[];
  typingUsers: string[];
  
  // Actions
  sendMessage: (content: string, messageType?: string, metadata?: Record<string, any>) => Promise<void>;
  setTypingStatus: (isTyping: boolean) => void;
  joinRoom: () => Promise<void>;
  leaveRoom: () => Promise<void>;
  
  // User management
  isUserTyping: (userId: string) => boolean;
  getActiveUsers: () => CollaborationUser[];
}

const useRealtimeCollaboration = ({
  roomId,
  userId,
  userInfo,
  roomType = 'chat',
      serverUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8002'
}: UseRealtimeCollaborationProps): UseRealtimeCollaborationReturn => {
  
  // State management
  const [room, setRoom] = useState<CollaborationRoom | null>(null);
  const [messages, setMessages] = useState<CollaborationMessage[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [hasJoinedRoom, setHasJoinedRoom] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Refs for cleanup
  const typingTimeoutRef = useRef<NodeJS.Timeout>();
  const mountedRef = useRef(true);
  
  // Context7 verified: WebSocket URL configuration
  const socketUrl = `${serverUrl}/ws/collaboration`;
  
  // Context7 verified: useWebSocket hook with proper configuration
  const {
    lastMessage,
    readyState,
    getWebSocket
  } = useWebSocket(socketUrl, {
    // Context7 verified: Reconnection configuration
    shouldReconnect: (_closeEvent) => {
      // Don't reconnect if component is unmounted
      return mountedRef.current;
    },
    reconnectAttempts: 10,
    reconnectInterval: 3000, // 3 seconds between reconnect attempts
    
    // Context7 verified: Message handling with authentication
    onOpen: () => {
      console.log('🔗 WebSocket connected for collaboration');
      setError(null);
      
      // Context7 verified: Send authentication message immediately
      const authMessage = {
        session_id: `session_${userId}_${Date.now()}`,
        user_id: userId,
        room_id: roomId,
        user_info: userInfo
      };
      
      try {
        const ws = getWebSocket();
        if (ws && ws.readyState === WebSocket.OPEN) {
          (ws as WebSocket).send(JSON.stringify(authMessage));
          console.log('🔐 Authentication sent:', authMessage);
        }
      } catch (error) {
        console.error('❌ Error sending auth message:', error);
      }
    },
    
    onClose: () => {
      console.log('🔌 WebSocket disconnected');
      setHasJoinedRoom(false);
    },
    
    onError: (event) => {
      console.error('❌ WebSocket error:', event);
      setError('Connection error');
    },
    
    // Context7 verified: Message filtering
    filter: (message) => {
      try {
        const data = JSON.parse(message.data);
        return data.room_id === roomId || !data.room_id;
      } catch {
        return false;
      }
    }
  });
  
  // Context7 verified: Connection status mapping
  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Connected',
    [ReadyState.CLOSING]: 'Disconnecting',
    [ReadyState.CLOSED]: 'Disconnected',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
  }[readyState];
  
  const isConnected = readyState === ReadyState.OPEN;
  
  // Context7 verified: Message handling effect
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const event: RealtimeEvent = JSON.parse(lastMessage.data);
        handleRealtimeEvent(event);
      } catch (error) {
        console.error('❌ Error parsing message:', error);
      }
    }
  }, [lastMessage]);
  
  // Handle real-time events
  const handleRealtimeEvent = useCallback((event: RealtimeEvent) => {
    console.log('📨 Received event:', event.type, event);
    
    switch (event.type) {
      case 'connection_established':
        console.log('✅ WebSocket authentication successful');
        setIsAuthenticated(true);
        break;
        
      case 'user_joined':
      case 'user_left':
      case 'presence_update':
        if (event.room_state) {
          setRoom(event.room_state);
        }
        break;
        
      case 'message':
        console.log('💬 Received message event:', event);
        const message: CollaborationMessage = {
          message_id: event.message_id || '',
          room_id: event.room_id || roomId,
          user_id: event.user_id || '',
          content: event.content || '',
          message_type: event.message_type || 'text',
          timestamp: event.timestamp,
          metadata: event.metadata || {}
        };
        
        setMessages(prev => {
          // Avoid duplicates
          if (prev.some(m => m.message_id === message.message_id)) {
            return prev;
          }
          return [...prev, message].sort((a, b) => 
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          );
        });
        break;
        
      case 'typing_status':
        if (event.typing_users) {
          setTypingUsers(event.typing_users.filter(id => id !== userId));
        }
        break;
    }
  }, [roomId, userId, hasJoinedRoom]);
  
  // Join collaboration room
  const joinRoom = useCallback(async () => {
    if (!isConnected || hasJoinedRoom) return;
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api/v1'}/collaboration/rooms/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_id: roomId,
          user_id: userId,
          user_info: userInfo,
          room_type: roomType
        })
      });
      
      if (response.ok) {
        const roomState = await response.json();
        setRoom(roomState);
        setHasJoinedRoom(true);
        console.log('🏠 Joined room:', roomId);
      } else {
        throw new Error(`Failed to join room: ${response.statusText}`);
      }
    } catch (error) {
      console.error('❌ Error joining room:', error);
      setError('Failed to join room');
    }
  }, [isConnected, hasJoinedRoom, roomId, userId, userInfo, roomType]);
  
  // Leave collaboration room
  const leaveRoom = useCallback(async () => {
    if (!hasJoinedRoom) return;
    
    try {
      await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api/v1'}/collaboration/rooms/leave?room_id=${roomId}&user_id=${userId}`, {
        method: 'POST'
      });
      
      setHasJoinedRoom(false);
      setRoom(null);
      setMessages([]);
      setTypingUsers([]);
      console.log('👋 Left room:', roomId);
    } catch (error) {
      console.error('❌ Error leaving room:', error);
    }
  }, [hasJoinedRoom, roomId, userId]);
  
  // Send message to room
  const sendMessage = useCallback(async (
    content: string, 
    messageType: string = 'text', 
    metadata: Record<string, any> = {}
  ) => {
    if (!isConnected || !hasJoinedRoom) {
      throw new Error('Not connected to room');
    }
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api/v1'}/collaboration/rooms/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_id: roomId,
          user_id: userId,
          content,
          message_type: messageType,
          metadata
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }
      
      // Stop typing after sending message
      setTypingStatus(false);
      
    } catch (error) {
      console.error('❌ Error sending message:', error);
      throw error;
    }
  }, [isConnected, hasJoinedRoom, roomId, userId]);
  
  // Set typing status
  const setTypingStatus = useCallback((isTyping: boolean) => {
    if (!isConnected || !hasJoinedRoom) return;
    
    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Send typing status
    fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api/v1'}/collaboration/rooms/typing`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        room_id: roomId,
        user_id: userId,
        is_typing: isTyping
      })
    }).catch(error => {
      console.error('❌ Error setting typing status:', error);
    });
    
    // Auto-stop typing after 3 seconds
    if (isTyping) {
      typingTimeoutRef.current = setTimeout(() => {
        setTypingStatus(false);
      }, 3000);
    }
  }, [isConnected, hasJoinedRoom, roomId, userId]);
  
  // Utility functions
  const isUserTyping = useCallback((checkUserId: string) => {
    return typingUsers.includes(checkUserId);
  }, [typingUsers]);
  
  const getActiveUsers = useCallback((): CollaborationUser[] => {
    if (!room) return [];
    return Object.values(room.users).filter(user => user.active);
  }, [room]);
  
  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    
    return () => {
      mountedRef.current = false;
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (hasJoinedRoom) {
        leaveRoom();
      }
    };
  }, [hasJoinedRoom, leaveRoom]);
  
  // Auto-join room when connection is established
  useEffect(() => {
    if (isConnected && !hasJoinedRoom) {
      joinRoom();
    }
  }, [isConnected, hasJoinedRoom, joinRoom]);
  
  // Auto-join room after authentication
  useEffect(() => {
    if (isAuthenticated && !hasJoinedRoom) {
      joinRoom();
    }
  }, [isAuthenticated, hasJoinedRoom, joinRoom]);
  
  return {
    // Connection state
    isConnected,
    connectionStatus,
    error,
    
    // Room state
    room,
    messages,
    typingUsers,
    
    // Actions
    sendMessage,
    setTypingStatus,
    joinRoom,
    leaveRoom,
    
    // User management
    isUserTyping,
    getActiveUsers
  };
};

export default useRealtimeCollaboration; 