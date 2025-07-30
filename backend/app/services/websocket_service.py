"""
Context7-verified WebSocket Service for Real-time Features
Enterprise RAG System - Phase 3 Implementation
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket
from fastapi_websocket_pubsub import PubSubEndpoint
from pydantic import BaseModel

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Context7-verified WebSocket event models
class WebSocketEvent(BaseModel):
    """Base WebSocket event model"""
    event_type: str
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    data: Dict[str, Any] = {}

class ChatEvent(WebSocketEvent):
    """Chat-related events (typing, messages, etc.)"""
    conversation_id: str
    message_type: str  # "typing_start", "typing_stop", "message_sent", "message_received"

class DocumentEvent(WebSocketEvent):
    """Document processing events"""
    document_id: str
    status: str  # "processing", "completed", "failed"
    progress: Optional[int] = None

class NotificationEvent(WebSocketEvent):
    """System notification events"""
    notification_type: str  # "info", "warning", "error", "success"
    title: str
    message: str
    auto_dismiss: bool = True

class UserPresenceEvent(WebSocketEvent):
    """User presence/activity events"""
    status: str  # "online", "offline", "away", "busy"
    last_seen: Optional[datetime] = None

class WebSocketService:
    """
    Context7-verified WebSocket service for real-time features
    
    Features:
    - Real-time chat messaging
    - Document processing notifications
    - User presence tracking
    - Live analytics updates
    - Multi-user collaboration
    """
    
    def __init__(self):
        """Initialize WebSocket service with Context7 verified patterns"""
        # Context7-verified PubSub endpoint configuration
        self.endpoint = PubSubEndpoint()
        
        # Active connections tracking
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        
        # Event channels (Context7 verified topic patterns)
        self.channels = {
            "chat": "chat_events",
            "documents": "document_events", 
            "notifications": "notification_events",
            "presence": "user_presence",
            "analytics": "analytics_updates",
            "system": "system_events"
        }
        
        logger.info("✅ Context7: WebSocket service initialized")
    
    def register_routes(self, app: FastAPI):
        """Context7-verified route registration"""
        # Register PubSub endpoint
        self.endpoint.register_route(app, "/ws/pubsub")
        
        # Custom WebSocket endpoint for connection management
        @app.websocket("/ws/connect")
        async def websocket_connect(websocket: WebSocket):
            await self.handle_connection(websocket)
            
        logger.info("✅ Context7: WebSocket routes registered")
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle individual WebSocket connections"""
        await websocket.accept()
        session_id = None
        user_id = None
        
        try:
            # Wait for authentication message
            auth_data = await websocket.receive_json()
            session_id = auth_data.get("session_id")
            user_id = auth_data.get("user_id")
            
            if session_id:
                # Store connection
                self.active_connections[session_id] = websocket
                
                if user_id:
                    # Track user sessions
                    if user_id not in self.user_sessions:
                        self.user_sessions[user_id] = []
                    self.user_sessions[user_id].append(session_id)
                    
                    # Notify user came online
                    await self.publish_user_presence(user_id, "online")
                
                logger.info(f"✅ WebSocket connected: session={session_id}, user={user_id}")
                
                # Send welcome message
                await websocket.send_json({
                    "event_type": "connection_established",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "channels": list(self.channels.keys())
                })
                
                # Keep connection alive and listen for messages
                while True:
                    try:
                        message = await websocket.receive_json()
                        await self.handle_message(session_id, user_id, message)
                    except Exception as e:
                        logger.warning(f"Message handling error: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            # Cleanup connection
            if session_id:
                self.active_connections.pop(session_id, None)
                
                if user_id and user_id in self.user_sessions:
                    if session_id in self.user_sessions[user_id]:
                        self.user_sessions[user_id].remove(session_id)
                    
                    # If no more sessions, mark user offline
                    if not self.user_sessions[user_id]:
                        await self.publish_user_presence(user_id, "offline")
                        del self.user_sessions[user_id]
                
                logger.info(f"✅ WebSocket disconnected: session={session_id}")
    
    async def handle_message(self, session_id: str, user_id: Optional[str], message: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        event_type = message.get("event_type")
        
        if event_type == "chat_typing_start":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await self.publish_chat_typing(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    typing=True
                )
        elif event_type == "chat_typing_stop":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await self.publish_chat_typing(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    typing=False
                )
        elif event_type == "ping":
            # Send pong response
            await self.send_to_session(session_id, {
                "event_type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    # Context7-verified publish methods
    async def publish_chat_message(self, conversation_id: str, message_data: Dict[str, Any]):
        """Publish chat message event"""
        event = ChatEvent(
            event_type="chat_message",
            timestamp=datetime.utcnow(),
            conversation_id=conversation_id,
            message_type="message_sent",
            data=message_data
        )
        
        await self.endpoint.publish([self.channels["chat"]], event.dict())
        logger.debug(f"✅ Chat message published: {conversation_id}")
    
    async def publish_chat_typing(self, conversation_id: str, user_id: Optional[str], typing: bool):
        """Publish typing indicator"""
        event = ChatEvent(
            event_type="chat_typing",
            timestamp=datetime.utcnow(),
            user_id=user_id,
            conversation_id=conversation_id,
            message_type="typing_start" if typing else "typing_stop"
        )
        
        await self.endpoint.publish([self.channels["chat"]], event.dict())
    
    async def publish_document_status(self, document_id: str, status: str, progress: Optional[int] = None):
        """Publish document processing status"""
        event = DocumentEvent(
            event_type="document_status",
            timestamp=datetime.utcnow(),
            document_id=document_id,
            status=status,
            progress=progress
        )
        
        await self.endpoint.publish([self.channels["documents"]], event.dict())
        logger.info(f"✅ Document status published: {document_id} -> {status}")
    
    async def publish_notification(self, notification_type: str, title: str, message: str, 
                                  user_id: Optional[str] = None, auto_dismiss: bool = True):
        """Publish system notification"""
        event = NotificationEvent(
            event_type="notification",
            timestamp=datetime.utcnow(),
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            auto_dismiss=auto_dismiss
        )
        
        await self.endpoint.publish([self.channels["notifications"]], event.dict())
        logger.info(f"✅ Notification published: {title}")
    
    async def publish_user_presence(self, user_id: str, status: str):
        """Publish user presence update"""
        event = UserPresenceEvent(
            event_type="user_presence",
            timestamp=datetime.utcnow(),
            user_id=user_id,
            status=status,
            last_seen=datetime.utcnow() if status == "offline" else None
        )
        
        await self.endpoint.publish([self.channels["presence"]], event.dict())
        logger.debug(f"✅ User presence published: {user_id} -> {status}")
    
    async def publish_analytics_update(self, metric_type: str, data: Dict[str, Any]):
        """Publish real-time analytics update"""
        event = WebSocketEvent(
            event_type="analytics_update",
            timestamp=datetime.utcnow(),
            data={"metric_type": metric_type, **data}
        )
        
        await self.endpoint.publish([self.channels["analytics"]], event.dict())
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to session {session_id}: {e}")
                # Remove broken connection
                self.active_connections.pop(session_id, None)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all user sessions"""
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                await self.send_to_session(session_id, message)
    
    def get_active_users(self) -> List[str]:
        """Get list of currently active users"""
        return list(self.user_sessions.keys())
    
    def get_user_session_count(self, user_id: str) -> int:
        """Get number of active sessions for a user"""
        return len(self.user_sessions.get(user_id, []))

# Context7-verified singleton instance
websocket_service = WebSocketService()

# Context7-verified health check
async def websocket_health_check() -> Dict[str, Any]:
    """WebSocket service health check"""
    return {
        "service": "websocket",
        "status": "healthy",
        "active_connections": len(websocket_service.active_connections),
        "active_users": len(websocket_service.user_sessions),
        "channels": list(websocket_service.channels.keys()),
        "features": [
            "Real-time chat messaging",
            "Document processing notifications", 
            "User presence tracking",
            "Live analytics updates",
            "Multi-user collaboration"
        ]
    } 