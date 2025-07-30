import React, { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

interface DocumentNotification {
  id: string;
  document_id: string;
  change_type: string;
  description: string;
  urgency: 'NORMAL' | 'URGENT' | 'CRITICAL';
  affected_systems: string[];
  created_at: string;
  acknowledged: boolean;
}

const NotificationSystem: React.FC = () => {
  const [notifications, setNotifications] = useState<DocumentNotification[]>([]);
  const [connected, setConnected] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showPanel, setShowPanel] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Initialize Socket.IO connection with Context7 fix
    const socket = io('http://localhost:8002', {
      transports: ['polling', 'websocket'], // Context7 fix: Try polling first
      timeout: 5000,
      reconnection: true,
      reconnectionAttempts: 3,     
      reconnectionDelay: 1000
    });

    socketRef.current = socket;

    // Connection events
    socket.on('connect', () => {
      console.log('✅ Connected to notification system');
      setConnected(true);
      
      // Join operations room to receive all notifications
      socket.emit('join_room', 'operations');
    });

    socket.on('disconnect', () => {
      console.log('❌ Disconnected from notification system');
      setConnected(false);
    });

    // Document update notifications
    socket.on('document_update', (notification: DocumentNotification) => {
      console.log('📢 New document update notification:', notification);
      
      setNotifications(prev => [notification, ...prev]);
      setUnreadCount(prev => prev + 1);
      
      // Show browser notification for urgent updates
      if (notification.urgency === 'URGENT' || notification.urgency === 'CRITICAL') {
        showBrowserNotification(notification);
      }
      
      // Auto-open panel for critical updates
      if (notification.urgency === 'CRITICAL') {
        setShowPanel(true);
      }
    });

    // Bulk update progress
    socket.on('bulk_update_progress', (data: any) => {
      console.log('📊 Bulk update progress:', data);
      // Could show progress bar here
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const showBrowserNotification = (notification: DocumentNotification) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(`${notification.urgency === 'URGENT' ? '🚨' : '📢'} Doküman Güncellemesi`, {
        body: notification.description,
        icon: '/assets/images/favicon.png',
        tag: notification.id
      });
    }
  };

  const acknowledgeNotification = async (notificationId: string) => {
    try {
      // Send acknowledgment to server
      socketRef.current?.emit('acknowledge_notification', {
        notification_id: notificationId,
        acknowledged_by: 'current_user@company.com' // Get from auth context
      });

      // Update local state
      setNotifications(prev => 
        prev.map(n => 
          n.id === notificationId ? { ...n, acknowledged: true } : n
        )
      );
      
      setUnreadCount(prev => Math.max(0, prev - 1));
      
    } catch (error) {
      console.error('Error acknowledging notification:', error);
    }
  };

  const clearAllNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'CRITICAL': return 'bg-red-500 text-white';
      case 'URGENT': return 'bg-orange-500 text-white';
      default: return 'bg-blue-500 text-white';
    }
  };

  const getUrgencyIcon = (urgency: string) => {
    switch (urgency) {
      case 'CRITICAL': return '🚨';
      case 'URGENT': return '⚠️';
      default: return '📢';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      {/* Notification Button */}
      <button
        onClick={() => setShowPanel(!showPanel)}
        className={`relative p-3 rounded-full shadow-lg transition-all ${
          connected ? 'bg-green-500 hover:bg-green-600' : 'bg-gray-500'
        } text-white`}
      >
        <span className="text-lg">🔔</span>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Panel */}
      {showPanel && (
        <div className="absolute top-16 right-0 w-96 bg-white rounded-lg shadow-xl border max-h-96 overflow-hidden">
          {/* Panel Header */}
          <div className="flex items-center justify-between p-4 border-b bg-gray-50">
            <h3 className="font-semibold text-gray-800">
              Doküman Güncellemeleri
              <span className={`ml-2 text-xs px-2 py-1 rounded-full ${
                connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {connected ? 'Bağlı' : 'Bağlantı Yok'}
              </span>
            </h3>
            <div className="flex space-x-2">
              {notifications.length > 0 && (
                <button
                  onClick={clearAllNotifications}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  Tümünü Temizle
                </button>
              )}
              <button
                onClick={() => setShowPanel(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                Henüz bildirim yok
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b hover:bg-gray-50 ${
                    !notification.acknowledged ? 'bg-blue-50' : ''
                  }`}
                >
                  {/* Notification Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getUrgencyIcon(notification.urgency)}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getUrgencyColor(notification.urgency)}`}>
                        {notification.urgency}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(notification.created_at).toLocaleTimeString('tr-TR')}
                    </span>
                  </div>

                  {/* Notification Content */}
                  <div className="mb-2">
                    <p className="text-sm font-medium text-gray-800 mb-1">
                      Doküman: {notification.document_id}
                    </p>
                    <p className="text-sm text-gray-600">
                      {notification.description}
                    </p>
                  </div>

                  {/* Affected Systems */}
                  {notification.affected_systems.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs text-gray-500 mb-1">Etkilenen Sistemler:</p>
                      <div className="flex flex-wrap gap-1">
                        {notification.affected_systems.map((system, index) => (
                          <span
                            key={index}
                            className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
                          >
                            {system}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex justify-end">
                    {!notification.acknowledged && (
                      <button
                        onClick={() => acknowledgeNotification(notification.id)}
                        className="text-xs bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
                      >
                        Okundu İşaretle
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationSystem; 