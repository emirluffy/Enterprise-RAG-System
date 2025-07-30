/**
 * Context7-verified WebSocket Notifications Component
 * Enterprise RAG System - Phase 3 Frontend Implementation
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useWebSocketService, NotificationEvent, DocumentEvent } from '../hooks/useWebSocketService';

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: Date;
  autoDismiss: boolean;
}

interface WebSocketNotificationsProps {
  userId?: string;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  maxNotifications?: number;
}

export const WebSocketNotifications: React.FC<WebSocketNotificationsProps> = ({
  userId,
  position = 'top-right',
  maxNotifications = 5
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const wsService = useWebSocketService(userId);

  // Add notification helper
  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date()
    };

    setNotifications(prev => {
      const updated = [newNotification, ...prev];
      return updated.slice(0, maxNotifications);
    });

    // Auto-dismiss notifications
    if (notification.autoDismiss) {
      setTimeout(() => {
        removeNotification(newNotification.id);
      }, 5000);
    }
  }, [maxNotifications]);

  // Remove notification
  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  // WebSocket event handlers
  useEffect(() => {
    // Handle general notifications
    wsService.onNotification((event: NotificationEvent) => {
      addNotification({
        type: event.notification_type as 'info' | 'warning' | 'error' | 'success',
        title: event.title,
        message: event.message,
        autoDismiss: event.auto_dismiss
      });
    });

    // Handle document processing notifications
    wsService.onDocumentUpdate((event: DocumentEvent) => {
      if (event.status === 'completed') {
        addNotification({
          type: 'success',
          title: 'Document Ready',
          message: `Document processing completed successfully`,
          autoDismiss: true
        });
      } else if (event.status === 'failed') {
        addNotification({
          type: 'error',
          title: 'Processing Failed',
          message: `Document processing failed`,
          autoDismiss: false
        });
      } else if (event.status === 'processing') {
        addNotification({
          type: 'info',
          title: 'Processing Document',
          message: `Document processing started...`,
          autoDismiss: true
        });
      }
    });
  }, [wsService, addNotification]);

  // Position classes
  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  };

  // Notification type styles
  const getNotificationStyles = (type: Notification['type']) => {
    const baseStyles = 'border-l-4 p-4 mb-3 rounded-r-lg shadow-lg backdrop-blur-lg';
    
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-50/90 border-green-400 text-green-800`;
      case 'error':
        return `${baseStyles} bg-red-50/90 border-red-400 text-red-800`;
      case 'warning':
        return `${baseStyles} bg-yellow-50/90 border-yellow-400 text-yellow-800`;
      case 'info':
      default:
        return `${baseStyles} bg-blue-50/90 border-blue-400 text-blue-800`;
    }
  };

  // Icon for notification type
  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
      default:
        return 'ℹ️';
    }
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className={`fixed ${positionClasses[position]} z-50 w-80 max-w-sm`}>
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`${getNotificationStyles(notification.type)} animate-slide-in`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <span className="text-lg flex-shrink-0">
                {getNotificationIcon(notification.type)}
              </span>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm">
                  {notification.title}
                </p>
                <p className="text-sm mt-1 break-words">
                  {notification.message}
                </p>
                <p className="text-xs mt-2 opacity-70">
                  {notification.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
            <button
              onClick={() => removeNotification(notification.id)}
              className="ml-2 text-gray-500 hover:text-gray-700 transition-colors flex-shrink-0"
              aria-label="Close notification"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      ))}
      
      {/* Connection Status Indicator */}
      <div className="mt-2 p-2 rounded-lg bg-gray-50/90 backdrop-blur-lg border border-gray-200 text-xs">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            wsService.isConnected ? 'bg-green-400' : 'bg-red-400'
          }`} />
          <span className="text-gray-600">
            {wsService.connectionStatus}
          </span>
          {wsService.activeUsers.length > 0 && (
            <span className="text-gray-500">
              • {wsService.activeUsers.length} online
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebSocketNotifications; 