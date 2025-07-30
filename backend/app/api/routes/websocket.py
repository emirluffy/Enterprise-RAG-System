"""
Context7-verified WebSocket API Routes
Enterprise RAG System - Phase 3 Implementation
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict, Any
import logging
from datetime import datetime

from app.services.websocket_service import websocket_service, websocket_health_check
from app.services.realtime_collaboration_service import collaboration_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Context7 verified: WebSocket collaboration endpoint
@router.websocket("/collaboration")
async def websocket_collaboration_endpoint(websocket: WebSocket):
    """
    Context7 verified: Real-time collaboration WebSocket endpoint
    
    Handles multi-user collaboration features:
    - Real-time messaging
    - User presence tracking  
    - Typing indicators
    - Document collaboration
    """
    await websocket.accept()
    logger.info("🔌 WebSocket collaboration connection accepted")
    
    session_id = None
    user_id = None
    
    try:
        # Wait for authentication/initialization message
        auth_data = await websocket.receive_json()
        session_id = auth_data.get("session_id")
        user_id = auth_data.get("user_id")
        room_id = auth_data.get("room_id", "banking-support-room")
        
        if session_id and user_id:
            # Register connection with WebSocket service for broadcasting
            websocket_service.active_connections[session_id] = websocket
            
            if user_id not in websocket_service.user_sessions:
                websocket_service.user_sessions[user_id] = []
            if session_id not in websocket_service.user_sessions[user_id]:
                websocket_service.user_sessions[user_id].append(session_id)
            
            logger.info(f"✅ Collaboration WebSocket registered: session={session_id}, user={user_id}")
            
            # Send confirmation
            await websocket.send_json({
                "type": "connection_established",
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep connection alive and handle messages
            while True:
                try:
                    # Receive message from client  
                    data = await websocket.receive_json()
                    logger.debug(f"📨 Received collaboration message: {data}")
                    
                    # Handle different message types
                    message_type = data.get("type")
                    
                    if message_type == "message":
                        # Broadcast message to room via collaboration service
                        message_content = data.get("content", "")
                        await collaboration_service.send_message(
                            room_id=room_id,
                            user_id=user_id,
                            message={
                                "content": message_content,
                                "message_type": "text"
                            }
                        )
                    elif message_type == "typing":
                        # Handle typing indicators
                        is_typing = data.get("is_typing", False)
                        await collaboration_service.set_typing_status(
                            room_id=room_id,
                            user_id=user_id,
                            is_typing=is_typing
                        )
                    
                except WebSocketDisconnect:
                    logger.info(f"🔌 WebSocket collaboration disconnected: {user_id}")
                    break
                except Exception as e:
                    logger.error(f"❌ WebSocket collaboration message error: {e}")
                    
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication required: session_id and user_id"
            })
                    
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket collaboration connection closed")
    except Exception as e:
        logger.error(f"❌ WebSocket collaboration endpoint error: {e}")
        await websocket.close(code=1011, reason=f"Server error: {str(e)}")
    finally:
        # Cleanup connection
        if session_id and session_id in websocket_service.active_connections:
            websocket_service.active_connections.pop(session_id, None)
            
        if user_id and user_id in websocket_service.user_sessions:
            if session_id in websocket_service.user_sessions[user_id]:
                websocket_service.user_sessions[user_id].remove(session_id)
            
            # If no more sessions, clean up user
            if not websocket_service.user_sessions[user_id]:
                del websocket_service.user_sessions[user_id]
        
        logger.info(f"✅ Collaboration WebSocket cleaned up: session={session_id}")

@router.get("/health", summary="WebSocket Service Health Check")
async def get_websocket_health() -> Dict[str, Any]:
    """
    Get WebSocket service health and status
    
    Returns:
        WebSocket service health information including:
        - Service status
        - Active connections count
        - Active users count
        - Available channels
        - Supported features
    """
    return await websocket_health_check()

@router.get("/status", summary="WebSocket Service Status")
async def get_websocket_status() -> Dict[str, Any]:
    """
    Get detailed WebSocket service status
    
    Returns:
        Detailed status information for monitoring and debugging
    """
    return {
        "service": "websocket",
        "status": "operational",
        "connections": {
            "active_connections": len(websocket_service.active_connections),
            "active_users": len(websocket_service.user_sessions),
            "user_sessions": {
                user_id: len(sessions) 
                for user_id, sessions in websocket_service.user_sessions.items()
            }
        },
        "channels": websocket_service.channels,
        "endpoints": [
            "/ws/pubsub - PubSub WebSocket endpoint",
            "/ws/connect - Connection management endpoint"
        ],
        "features": {
            "real_time_chat": True,
            "document_notifications": True,
            "user_presence": True,
            "analytics_updates": True,
            "multi_user_support": True
        }
    }

@router.get("/channels", summary="WebSocket Channels Information")
async def get_websocket_channels() -> Dict[str, Any]:
    """
    Get information about available WebSocket channels
    
    Returns:
        List of available channels and their purposes
    """
    return {
        "channels": {
            "chat_events": {
                "description": "Real-time chat messaging and typing indicators",
                "events": ["chat_message", "chat_typing", "message_sent", "message_received"]
            },
            "document_events": {
                "description": "Document processing status updates",
                "events": ["document_status", "processing", "completed", "failed"]
            },
            "notification_events": {
                "description": "System notifications and alerts",
                "events": ["notification", "info", "warning", "error", "success"]
            },
            "user_presence": {
                "description": "User online/offline status and activity",
                "events": ["user_presence", "online", "offline", "away", "busy"]
            },
            "analytics_updates": {
                "description": "Real-time analytics and metrics updates",
                "events": ["analytics_update", "metric_update", "dashboard_refresh"]
            },
            "system_events": {
                "description": "System-wide events and maintenance notifications",
                "events": ["system_event", "maintenance", "update", "announcement"]
            }
        },
        "usage": {
            "client_connection": "/ws/connect",
            "pubsub_endpoint": "/ws/pubsub",
            "authentication": "Required - send session_id and user_id on connect"
        }
    } 