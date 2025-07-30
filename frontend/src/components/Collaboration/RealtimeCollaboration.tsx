import React, { useState, useRef, useEffect } from 'react';
import useRealtimeCollaboration, { CollaborationUser, CollaborationMessage } from '../../hooks/useRealtimeCollaboration';

interface RealtimeCollaborationProps {
  roomId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  roomType?: string;
  className?: string;
}

const RealtimeCollaboration: React.FC<RealtimeCollaborationProps> = ({
  roomId,
  userId,
  userName,
  userAvatar,
  roomType = 'chat',
  className = ''
}) => {
  const [newMessage, setNewMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Context7 verified: Real-time collaboration hook
  const {
    isConnected,
    connectionStatus,
    error,
    room,
    messages,
    typingUsers,
    sendMessage,
    setTypingStatus,
    isUserTyping,
    getActiveUsers
  } = useRealtimeCollaboration({
    roomId,
    userId,
    userInfo: {
      name: userName,
      avatar: userAvatar
    },
    roomType
  });
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Handle message input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setNewMessage(value);
    
    // Manage typing status
    if (value.length > 0 && !isTyping) {
      setIsTyping(true);
      setTypingStatus(true);
    } else if (value.length === 0 && isTyping) {
      setIsTyping(false);
      setTypingStatus(false);
    }
  };
  
  // Handle sending message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newMessage.trim() || !isConnected) return;
    
    try {
      await sendMessage(newMessage.trim());
      setNewMessage('');
      setIsTyping(false);
      setTypingStatus(false);
      inputRef.current?.focus();
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };
  
  // Stop typing on blur
  const handleInputBlur = () => {
    if (isTyping) {
      setIsTyping(false);
      setTypingStatus(false);
    }
  };
  
  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Get user display info
  const getUserInfo = (userId: string): CollaborationUser | null => {
    return room?.users[userId] || null;
  };
  
  const activeUsers = getActiveUsers();
  
  return (
    <div className={`flex flex-col h-full bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-white/20">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">
              Real-time Collaboration
            </h3>
            <p className="text-sm text-blue-200">
              Room: {roomId} • {roomType}
            </p>
          </div>
          
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-400' : 'bg-red-400'
            }`} />
            <span className="text-sm text-blue-200">{connectionStatus}</span>
          </div>
        </div>
        
        {/* Active Users */}
        <div className="mt-3">
          <p className="text-xs text-blue-200 mb-2">
            Active Users ({activeUsers.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {activeUsers.map((user) => (
              <div
                key={user.user_id}
                className="flex items-center gap-1 bg-blue-500/20 rounded-full px-2 py-1"
              >
                <div className="w-4 h-4 bg-blue-400 rounded-full flex items-center justify-center text-xs text-white">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <span className="text-xs text-blue-200">{user.name}</span>
                {user.user_id === userId && (
                  <span className="text-xs text-green-400">(You)</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Error Display */}
      {error && (
        <div className="p-3 m-4 bg-red-500/20 border border-red-400/30 rounded-lg">
          <p className="text-red-300 text-sm">❌ {error}</p>
        </div>
      )}
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-blue-200">No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((message) => {
            const user = getUserInfo(message.user_id);
            const isOwnMessage = message.user_id === userId;
            
            return (
              <div
                key={message.message_id}
                className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[70%] ${
                  isOwnMessage 
                    ? 'bg-blue-600/80 text-white' 
                    : 'bg-white/20 text-blue-100'
                } rounded-lg p-3`}>
                  {/* Message Header */}
                  {!isOwnMessage && (
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-5 h-5 bg-blue-400 rounded-full flex items-center justify-center text-xs text-white">
                        {user?.name.charAt(0).toUpperCase() || '?'}
                      </div>
                      <span className="text-xs text-blue-200">{user?.name || 'Unknown'}</span>
                    </div>
                  )}
                  
                  {/* Message Content */}
                  <p className="text-sm">{message.content}</p>
                  
                  {/* Message Time */}
                  <p className={`text-xs mt-1 ${
                    isOwnMessage ? 'text-blue-200' : 'text-blue-300'
                  }`}>
                    {formatTime(message.timestamp)}
                  </p>
                </div>
              </div>
            );
          })
        )}
        
        {/* Typing Indicators */}
        {typingUsers.length > 0 && (
          <div className="flex items-center gap-2 text-blue-300">
            <div className="flex space-x-1">
              <div key="dot1" className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
              <div key="dot2" className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
              <div key="dot3" className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
            </div>
            <span className="text-sm">
              {typingUsers.map((id, index) => getUserInfo(id)?.name).filter(Boolean).join(', ')} 
              {typingUsers.length === 1 ? ' is' : ' are'} typing...
            </span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Message Input */}
      <div className="p-4 border-t border-white/20">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={newMessage}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            placeholder={isConnected ? "Type a message..." : "Connecting..."}
            disabled={!isConnected}
            className="flex-1 bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-blue-300 focus:outline-none focus:border-blue-400 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!newMessage.trim() || !isConnected}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default RealtimeCollaboration; 